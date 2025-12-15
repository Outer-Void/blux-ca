"""QLoRA training pipeline for BLUX-cA adapters."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

import torch
import yaml
from datasets import load_dataset
from peft import LoraConfig
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from trl import SFTTrainer

from prepare_dataset import prepare_dataset
from validate_dataset import load_system_prompt, run_cli_validator, validate_file


EXAMPLE_DATASET_CMD = "export DATASET_DIR=/absolute/path/to/blux-ca-dataset"


def _load_yaml(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _write_json(path: Path, payload: Dict) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def _resolve_dataset_dir(raw: Optional[Path]) -> Path:
    if raw:
        return raw
    env_dir = os.environ.get("DATASET_DIR")
    if env_dir:
        return Path(env_dir)
    raise ValueError(
        f"Dataset directory is required. Provide --dataset-dir or set DATASET_DIR (e.g., {EXAMPLE_DATASET_CMD})"
    )


def _resolve_base_model(cfg: Dict, prefer_cpu_safe: bool = False) -> str:
    env_base_model = os.environ.get("BASE_MODEL")
    if env_base_model:
        return env_base_model
    if prefer_cpu_safe:
        return cfg.get("cpu_base_model", cfg.get("base_model"))
    return cfg.get("base_model")


def _validate_sources(dataset_dir: Path, mix_config: Path) -> None:
    mix_cfg = _load_yaml(mix_config)
    data_dir = dataset_dir / "data"
    errors: List[str] = []
    canonical_prompt = load_system_prompt(dataset_dir)
    for source in mix_cfg.get("sources", []):
        path = data_dir / source.get("file", "")
        if not path.exists():
            errors.append(f"Missing file: {path}")
            continue
        _, _, file_errors = validate_file(path, strict=True, canonical_prompt=canonical_prompt)
        errors.extend(file_errors)
    if errors:
        joined = "\n".join(errors)
        raise ValueError(f"Dataset validation failed:\n{joined}")


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
        example["text"] = _format_messages(example["messages"], tokenizer)
        return example

    text_dataset = dataset.map(add_text, remove_columns=[])

    return text_dataset


def _init_model(base_model: str, lora_config: Dict) -> AutoModelForCausalLM:
    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
    )
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        quantization_config=quant_config,
        device_map="auto",
    )
    peft_config = LoraConfig(
        r=int(lora_config.get("r", 16)),
        lora_alpha=int(lora_config.get("alpha", 32)),
        target_modules=lora_config.get("target_modules", []),
        lora_dropout=float(lora_config.get("dropout", 0.05)),
        bias="none",
        task_type="CAUSAL_LM",
    )
    model.add_adapter(peft_config)
    return model


def train(args: argparse.Namespace) -> Path:
    dataset_dir = _resolve_dataset_dir(args.dataset_dir)
    if not dataset_dir.exists():
        raise FileNotFoundError(
            f"Dataset directory not found: {dataset_dir}. Set DATASET_DIR first (e.g., `{EXAMPLE_DATASET_CMD}`)."
        )
    if not args.config.exists():
        raise FileNotFoundError(f"Config not found: {args.config}")
    if not args.mix_config.exists():
        raise FileNotFoundError(f"Mix config not found: {args.mix_config}")

    qlora_cfg = _load_yaml(args.config)
    mix_config = args.mix_config

    prefer_cpu_safe = args.dry_run and not torch.cuda.is_available() and not os.environ.get("BASE_MODEL")
    qlora_cfg["base_model"] = _resolve_base_model(qlora_cfg, prefer_cpu_safe=prefer_cpu_safe)

    validation_errors = run_cli_validator(dataset_dir)
    if validation_errors:
        raise ValueError("\n".join(validation_errors))

    _validate_sources(dataset_dir, mix_config)

    prepared_path = prepare_dataset(dataset_dir, mix_config, args.output_root, run_name=args.run_name, strict=args.strict)
    run_dir = prepared_path.parent

    tokenizer = AutoTokenizer.from_pretrained(qlora_cfg["base_model"], use_fast=True)
    tokenizer.padding_side = "right"
    tokenizer.pad_token = tokenizer.eos_token

    train_dataset = _build_dataset(prepared_path, tokenizer)

    if args.dry_run:
        sample = train_dataset.select(range(min(5, len(train_dataset))))
        _ = tokenizer(
            sample["text"],
            max_length=qlora_cfg["max_seq_length"],
            truncation=True,
            padding="longest",
        )
        print("Dry-run successful: model and tokenizer loaded; tokenization ok.")
        return run_dir

    model = _init_model(qlora_cfg["base_model"], qlora_cfg["lora"])

    training_args = TrainingArguments(
        output_dir=str(run_dir / "adapter_model"),
        num_train_epochs=int(qlora_cfg["epochs"]),
        per_device_train_batch_size=int(qlora_cfg["per_device_train_batch_size"]),
        gradient_accumulation_steps=int(qlora_cfg["gradient_accumulation_steps"]),
        learning_rate=float(qlora_cfg["learning_rate"]),
        warmup_ratio=float(qlora_cfg["warmup_ratio"]),
        logging_steps=10,
        save_strategy="epoch",
        bf16=bool(qlora_cfg.get("bf16", False)),
        fp16=bool(qlora_cfg.get("fp16", False)),
        gradient_checkpointing=True,
        report_to=[],
        seed=int(qlora_cfg.get("seed", 42)),
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        dataset_text_field="text",
        packing=False,
        max_seq_length=qlora_cfg["max_seq_length"],
        args=training_args,
    )

    trainer.train()
    trainer.model.save_pretrained(training_args.output_dir)
    tokenizer.save_pretrained(training_args.output_dir)

    _write_json(run_dir / "training_args.json", training_args.to_dict())
    with (run_dir / "config_snapshot.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(
            {"qlora": qlora_cfg, "mix_config": _load_yaml(mix_config)},
            handle,
            sort_keys=False,
        )

    print(f"Training complete. Adapter saved to {training_args.output_dir}")
    return run_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a BLUX-cA QLoRA adapter")
    parser.add_argument(
        "--dataset-dir",
        required=False,
        type=Path,
        default=Path(os.environ["DATASET_DIR"]) if os.environ.get("DATASET_DIR") else None,
        help="Path to dataset repository (or set DATASET_DIR)",
    )
    parser.add_argument("--config", type=Path, default=Path("train/configs/qlora.yaml"), help="QLoRA config path")
    parser.add_argument("--mix-config", type=Path, default=Path("train/configs/dataset_mix.yaml"), help="Dataset mixing config")
    parser.add_argument("--output-root", type=Path, default=Path("runs"), help="Root directory for outputs")
    parser.add_argument("--run-name", type=str, default=os.environ.get("RUN_NAME"), help="Optional run folder name")
    parser.add_argument("--dry-run", action="store_true", help="Load model/tokenizer and tokenize sample without training")
    parser.add_argument("--strict", action="store_true", help="Validate dataset strictly before mixing")
    return parser.parse_args()


if __name__ == "__main__":
    cli_args = parse_args()
    try:
        train(cli_args)
    except (FileNotFoundError, ValueError) as exc:
        print(exc)
        raise SystemExit(1)
