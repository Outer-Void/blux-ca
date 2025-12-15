"""Adapter training entrypoint for BLUX-cA (LoRA/QLoRA).

This script prepares a deterministic training mix, supports dry-runs,
smoke runs (via --max-samples), and full training on the BLUX-cA dataset.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

import torch
import yaml
from datasets import load_dataset
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, GPT2Config, TrainingArguments
from trl import SFTTrainer

from prepare_dataset import prepare_dataset
from validate_dataset import run_cli_validator, validate_dataset


def _load_yaml(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _write_json(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


EXAMPLE_DATASET_CMD = "export DATASET_DIR=/absolute/path/to/blux-ca-dataset"


def _resolve_dataset_dir(raw: Optional[Path]) -> Path:
    if raw:
        return raw
    env_dir = os.environ.get("DATASET_DIR")
    if env_dir:
        return Path(env_dir)
    raise ValueError(
        f"Dataset directory is required. Provide --dataset-dir or set DATASET_DIR (e.g., {EXAMPLE_DATASET_CMD})"
    )


def _load_base_model_name(config: Dict, override: Optional[str], prefer_cpu_safe: bool = False) -> str:
    env_override = os.environ.get("BASE_MODEL")
    if env_override:
        return env_override
    if override:
        return override
    if prefer_cpu_safe:
        return config.get("cpu_base_model", "Qwen/Qwen2.5-1.5B-Instruct")
    return config.get("base_model", "Qwen/Qwen2.5-7B-Instruct")


def _quantization_config() -> Optional[BitsAndBytesConfig]:
    if not torch.cuda.is_available():
        return None
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
    )


def _format_messages(messages: List[Dict], tokenizer) -> str:
    if hasattr(tokenizer, "apply_chat_template"):
        return tokenizer.apply_chat_template(messages, tokenize=False)
    parts = []
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        parts.append(f"[{role}] {content}")
    return "\n".join(parts)


def _build_dataset(prepared_path: Path, tokenizer):
    dataset = load_dataset("json", data_files=str(prepared_path))["train"]

    def add_text(example):
        example["text"] = _format_messages(example.get("messages", []), tokenizer)
        return example

    return dataset.map(add_text, remove_columns=[])


def _init_model(base_model: str, quant_config: Optional[BitsAndBytesConfig], allow_stub: bool = False):
    kwargs = {"device_map": "auto"}
    if quant_config is not None:
        kwargs["quantization_config"] = quant_config
    else:
        kwargs["torch_dtype"] = torch.float32
        kwargs["low_cpu_mem_usage"] = True
    try:
        return AutoModelForCausalLM.from_pretrained(base_model, **kwargs)
    except Exception as exc:  # pragma: no cover - fallback for offline environments
        if not allow_stub:
            raise
        print(f"Model load failed ({exc}); using stub GPT-2 config for dry-run.")
        tiny_config = GPT2Config(n_embd=64, n_layer=2, n_head=2, n_positions=128, vocab_size=256)
        return AutoModelForCausalLM.from_config(tiny_config)


class _StubTokenizer:
    def __init__(self) -> None:
        self.pad_token = "<|pad|>"
        self.eos_token = "</s>"
        self.padding_side = "right"

    def apply_chat_template(self, messages: List[Dict], tokenize: bool = False, **_: Dict) -> str:
        return "\n".join(f"{m.get('role')}: {m.get('content')}" for m in messages)

    def __call__(self, texts, max_length: int = 2048, truncation: bool = True, padding: str = "longest") -> Dict:
        if isinstance(texts, str):
            texts = [texts]
        input_ids = []
        for text in texts:
            length = min(len(text.split()), max_length)
            input_ids.append(list(range(length)))
        return {"input_ids": input_ids}


def _init_tokenizer(base_model: str, allow_stub: bool = False):
    try:
        tokenizer = AutoTokenizer.from_pretrained(base_model, use_fast=True)
    except Exception as exc:  # pragma: no cover - fallback for offline environments
        if not allow_stub:
            raise
        print(f"Tokenizer load failed ({exc}); using stub tokenizer for dry-run.")
        tokenizer = _StubTokenizer()
    tokenizer.padding_side = "right"
    if getattr(tokenizer, "pad_token", None) is None:
        tokenizer.pad_token = tokenizer.eos_token
    return tokenizer


def _build_lora_config(cfg: Dict) -> LoraConfig:
    lora_cfg = cfg.get("lora", {})
    return LoraConfig(
        r=int(lora_cfg.get("r", 16)),
        lora_alpha=int(lora_cfg.get("alpha", 32)),
        target_modules=lora_cfg.get("target_modules", []),
        lora_dropout=float(lora_cfg.get("dropout", 0.05)),
        bias="none",
        task_type="CAUSAL_LM",
    )


def _persist_config_snapshot(run_dir: Path, train_cfg: Dict, mix_config: Dict, base_model: str) -> None:
    snapshot = {
        "base_model": base_model,
        "train": train_cfg,
        "mix_config": mix_config,
    }
    with (run_dir / "config_snapshot.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(snapshot, handle, sort_keys=False)


def train(args: argparse.Namespace) -> Path:
    dataset_dir = _resolve_dataset_dir(args.dataset_dir)
    if not dataset_dir.exists():
        raise FileNotFoundError(
            f"Dataset directory not found: {dataset_dir}. Set DATASET_DIR first (e.g., `{EXAMPLE_DATASET_CMD}`)."
        )

    train_cfg = _load_yaml(args.config)
    mix_cfg = _load_yaml(args.mix_config)
    if args.max_samples is not None:
        mix_cfg = {**mix_cfg, "max_samples": args.max_samples, "__override_max_samples": True}
    prefer_cpu_safe = args.dry_run and not torch.cuda.is_available() and not args.base_model and not os.environ.get(
        "BASE_MODEL"
    )
    base_model = _load_base_model_name(train_cfg, args.base_model, prefer_cpu_safe=prefer_cpu_safe)

    validation_errors = run_cli_validator(dataset_dir)
    if validation_errors:
        raise ValueError("\n".join(validation_errors))

    if args.strict:
        _, errors = validate_dataset(dataset_dir, strict=True)
        if errors:
            raise ValueError("\n".join(errors))

    prepared_path = prepare_dataset(
        dataset_dir,
        args.mix_config,
        args.output_root,
        run_name=args.run_name,
        override_max_samples=args.max_samples,
        strict=args.strict,
    )
    run_dir = prepared_path.parent

    resolved_mix_cfg = mix_cfg
    resolved_mix_path = run_dir / "mix_config_resolved.yaml"
    if resolved_mix_path.exists():
        resolved_mix_cfg = _load_yaml(resolved_mix_path)

    quant_config = _quantization_config()
    tokenizer = _init_tokenizer(base_model, allow_stub=args.dry_run)
    train_dataset = _build_dataset(prepared_path, tokenizer)

    # Dry-run: load a few samples and ensure tokenization + model load succeed.
    if args.dry_run:
        sample = train_dataset.select(range(min(5, len(train_dataset))))
        _ = tokenizer(
            sample["text"],
            max_length=train_cfg.get("max_seq_length", 2048),
            truncation=True,
            padding="longest",
        )
        _ = _init_model(base_model, quant_config, allow_stub=True)
        _persist_config_snapshot(run_dir, train_cfg, resolved_mix_cfg, base_model)
        print("Dry-run successful: dataset prepared, tokenizer + model loaded, tokenization OK.")
        return run_dir

    model = _init_model(base_model, quant_config)
    lora_config = _build_lora_config(train_cfg)
    model = get_peft_model(model, lora_config)

    training_args = TrainingArguments(
        output_dir=str(run_dir / "adapter"),
        num_train_epochs=int(train_cfg.get("epochs", 3)),
        per_device_train_batch_size=int(train_cfg.get("per_device_train_batch_size", 1)),
        gradient_accumulation_steps=int(train_cfg.get("gradient_accumulation_steps", 1)),
        learning_rate=float(train_cfg.get("learning_rate", 2e-4)),
        warmup_ratio=float(train_cfg.get("warmup_ratio", 0.0)),
        logging_steps=10,
        save_strategy="epoch",
        bf16=bool(train_cfg.get("bf16", torch.cuda.is_available())),
        fp16=bool(train_cfg.get("fp16", False)),
        gradient_checkpointing=True,
        report_to=[],
        seed=int(train_cfg.get("seed", 42)),
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        dataset_text_field="text",
        packing=False,
        max_seq_length=int(train_cfg.get("max_seq_length", 2048)),
        args=training_args,
    )

    trainer.train()
    trainer.model.save_pretrained(training_args.output_dir)
    tokenizer.save_pretrained(training_args.output_dir)

    _write_json(run_dir / "training_args.json", training_args.to_dict())
    _persist_config_snapshot(run_dir, train_cfg, resolved_mix_cfg, base_model)

    print(f"Training complete. Adapter saved to {training_args.output_dir}")
    return run_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a BLUX-cA LoRA/QLoRA adapter")
    parser.add_argument("--dataset-dir", type=Path, default=None, help="Path to dataset repository (or set DATASET_DIR)")
    parser.add_argument("--config", type=Path, default=Path("train/configs/train.yaml"), help="Training config path")
    parser.add_argument("--mix-config", type=Path, default=Path("train/configs/dataset_mix.yaml"), help="Dataset mixing config")
    parser.add_argument("--output-root", type=Path, default=Path("runs"), help="Root directory for outputs")
    parser.add_argument("--run-name", type=str, default=os.environ.get("RUN_NAME"), help="Optional run folder name")
    parser.add_argument("--base-model", type=str, default=None, help="Override base model without editing config")
    parser.add_argument("--max-samples", type=int, default=None, help="Override mix max_samples for smoke runs")
    parser.add_argument("--dry-run", action="store_true", help="Load model/tokenizer and tokenize sample without training")
    parser.add_argument("--strict", action="store_true", help="Strictly validate dataset before running")
    return parser.parse_args()


if __name__ == "__main__":
    cli_args = parse_args()
    try:
        train(cli_args)
    except (FileNotFoundError, ValueError) as exc:
        print(exc)
        raise SystemExit(1)
