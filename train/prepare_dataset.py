"""Prepare a weighted, shuffled training set for BLUX-cA QLoRA."""
from __future__ import annotations

import argparse
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from validate_dataset import load_system_prompt, validate_dataset


def _timestamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


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


def prepare_dataset(
    dataset_dir: Path,
    mix_config: Path,
    output_root: Path,
    run_name: Optional[str] = None,
    override_max_samples: Optional[int] = None,
    strict: bool = False,
) -> Path:
    """Create a weighted, deterministic training mix.

    If ``override_max_samples`` is provided it takes precedence over the YAML
    ``max_samples`` value. When ``strict`` is True, data files are validated
    before mixing.
    """

    canonical_prompt = load_system_prompt(dataset_dir)

    if strict:
        _, errors = validate_dataset(dataset_dir, strict=True)
        if errors:
            joined = "\n".join(errors)
            raise ValueError(f"Dataset validation failed before mixing:\n{joined}")

    config = _load_config(mix_config)
    sources = config.get("sources", [])
    shuffle = bool(config.get("shuffle", True))
    max_samples = override_max_samples if override_max_samples is not None else config.get("max_samples")
    seed = int(config.get("seed", 42))

    rng = random.Random(seed)
    total_weight = sum(float(src.get("weight", 1.0)) for src in sources)
    if total_weight <= 0:
        raise ValueError("Total weight must be positive")

    collected: List[Dict] = []

    for src in sources:
        raw_path = Path(src["file"])
        if raw_path.is_absolute():
            file_path = raw_path
        elif raw_path.parts and raw_path.parts[0] == "data":
            file_path = dataset_dir / raw_path
        else:
            file_path = dataset_dir / "data" / raw_path
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

    folder_name = _timestamp() if not run_name else f"{_timestamp()}_{run_name}"
    run_dir = output_root / folder_name
    run_dir.mkdir(parents=True, exist_ok=True)
    output_path = run_dir / "prepared_train.jsonl"
    with output_path.open("w", encoding="utf-8") as handle:
        for record in collected:
            if "messages" in record:
                system_msgs = [m for m in record["messages"] if m.get("role") == "system"]
                if system_msgs:
                    system_msgs[0]["content"] = canonical_prompt
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    resolved_mix_path = run_dir / "mix_config_resolved.yaml"
    with resolved_mix_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(
            {
                **config,
                "max_samples": max_samples,
                "seed": seed,
                "dataset_dir": str(dataset_dir),
            },
            handle,
            sort_keys=False,
        )

    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare weighted training data for QLoRA")
    parser.add_argument("--dataset-dir", required=True, type=Path, help="Path to dataset repository")
    parser.add_argument("--mix-config", type=Path, default=Path("train/configs/dataset_mix.yaml"), help="Mixing config YAML")
    parser.add_argument("--output-root", type=Path, default=Path("runs"), help="Root directory for run outputs")
    parser.add_argument("--run-name", type=str, default=None, help="Optional run folder name (otherwise timestamp)")
    parser.add_argument("--max-samples", type=int, default=None, help="Override max_samples in config for quick smoke runs")
    parser.add_argument("--strict", action="store_true", help="Validate input files strictly before mixing")
    args = parser.parse_args()

    if not args.dataset_dir.exists():
        print(f"Dataset directory not found: {args.dataset_dir}")
        return 1

    output_path = prepare_dataset(
        args.dataset_dir,
        args.mix_config,
        args.output_root,
        run_name=args.run_name,
        override_max_samples=args.max_samples,
        strict=args.strict,
    )
    print(f"Prepared dataset written to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
