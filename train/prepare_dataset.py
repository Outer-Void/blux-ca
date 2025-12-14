"""Prepare a weighted, shuffled training set for BLUX-cA QLoRA."""
from __future__ import annotations

import argparse
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from validate_dataset import SYSTEM_PLACEHOLDER, validate_dataset


def _timestamp() -> str:
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def _load_config(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _load_jsonl(path: Path) -> List[Dict]:
    records: List[Dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def _sample_records(records: List[Dict], target: int, rng: random.Random) -> List[Dict]:
    if not records:
        return []
    if target <= len(records):
        return rng.sample(records, target)
    return [rng.choice(records) for _ in range(target)]


def prepare_dataset(dataset_dir: Path, mix_config: Path, output_root: Path, run_name: Optional[str] = None) -> Path:
    config = _load_config(mix_config)
    sources = config.get("sources", [])
    shuffle = bool(config.get("shuffle", True))
    max_samples = config.get("max_samples")
    seed = int(config.get("seed", 42))

    rng = random.Random(seed)
    total_weight = sum(float(src.get("weight", 1.0)) for src in sources)
    if total_weight <= 0:
        raise ValueError("Total weight must be positive")

    data_dir = dataset_dir / "data"
    collected: List[Dict] = []

    for src in sources:
        file_path = data_dir / src["file"]
        if not file_path.exists():
            raise FileNotFoundError(f"Missing dataset file: {file_path}")
        weight = float(src.get("weight", 1.0))
        records = _load_jsonl(file_path)
        if max_samples is None:
            target = max(len(records), 0)
        else:
            target = max(1, round((weight / total_weight) * max_samples))
        sampled = _sample_records(records, target, rng)
        collected.extend(sampled)

    if not collected:
        raise ValueError("No samples collected from provided sources")

    if shuffle:
        rng.shuffle(collected)

    run_dir = output_root / (run_name or _timestamp())
    run_dir.mkdir(parents=True, exist_ok=True)
    output_path = run_dir / "prepared_train.jsonl"
    with output_path.open("w", encoding="utf-8") as handle:
        for record in collected:
            if "messages" in record:
                system_msgs = [m for m in record["messages"] if m.get("role") == "system"]
                if system_msgs:
                    system_msgs[0]["content"] = SYSTEM_PLACEHOLDER
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare weighted training data for QLoRA")
    parser.add_argument("--dataset-dir", required=True, type=Path, help="Path to dataset repository")
    parser.add_argument("--mix-config", type=Path, default=Path("train/configs/dataset_mix.yaml"), help="Mixing config YAML")
    parser.add_argument("--output-root", type=Path, default=Path("runs"), help="Root directory for run outputs")
    parser.add_argument("--run-name", type=str, default=None, help="Optional run folder name (otherwise timestamp)")
    parser.add_argument("--strict", action="store_true", help="Validate input files strictly before mixing")
    args = parser.parse_args()

    if not args.dataset_dir.exists():
        print(f"Dataset directory not found: {args.dataset_dir}")
        return 1

    if args.strict:
        _, errors = validate_dataset(args.dataset_dir, strict=True)
        if errors:
            print("Validation errors:")
            for err in errors:
                print(f"- {err}")
            return 1
        print("Strict validation passed")

    output_path = prepare_dataset(args.dataset_dir, args.mix_config, args.output_root, run_name=args.run_name)
    print(f"Prepared dataset written to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
