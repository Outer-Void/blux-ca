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
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
from trl import SFTTrainer

from prepare_dataset import prepare_dataset
from validate_dataset import validate_dataset


def _load_yaml(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _write_json(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def _resolve_dataset_dir(raw: Optional[Path]) -> Path:
    if raw:
        return raw
    env_dir = os.environ.get("DATASET_DIR")
    if env_dir:
        return Path(env_dir)
    raise ValueError("Dataset directory is required. Provide --dataset-dir or set DATASET_DIR")


def _load_base_model_name(config: Dict, override: Optional[str]) -> str:
    env_override = os.environ.get("BASE_MODEL")
    if env_override:
        return env_override
    if override:
        return override
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


def _init_model(base_model: str, quant_config: Optional[BitsAndBytesConfig]):
    kwargs = {"device_map": "auto"}
    if quant_config is not None:
        kwargs["quantization_config"] = quant_config
    else:
        kwargs["torch_dtype"] = torch.float32
        kwargs["low_cpu_mem_usage"] = True
    return AutoModelForCausalLM.from_pretrained(base_model, **kwargs)


def _init_tokenizer(base_model: str):
    tokenizer = AutoTokenizer.from_pretrained(base_model, use_fast=True)
    tokenizer.padding_side = "right"
    if tokenizer.pad_token is None:
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
        raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")

    train_cfg = _load_yaml(args.config)
    mix_cfg = _load_yaml(args.mix_config)
    if args.max_samples is not None:
        mix_cfg = {**mix_cfg, "max_samples": args.max_samples, "__override_max_samples": True}
    base_model = _load_base_model_name(train_cfg, args.base_model)

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
        strict=False,
    )
    run_dir = prepared_path.parent

    resolved_mix_cfg = mix_cfg
    resolved_mix_path = run_dir / "mix_config_resolved.yaml"
    if resolved_mix_path.exists():
        resolved_mix_cfg = _load_yaml(resolved_mix_path)

    quant_config = _quantization_config()
    tokenizer = _init_tokenizer(base_model)
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
        _ = _init_model(base_model, quant_config)
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
