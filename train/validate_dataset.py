"""Dataset validation for BLUX-cA QLoRA pipeline.

Checks that training JSONL files conform to the expected message schema and
contain the BLUX-cA system placeholder.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SYSTEM_PROMPT_PATH = REPO_ROOT / "identity" / "system_prompt.txt"


def load_system_prompt(dataset_dir: Optional[Path] = None) -> str:
    """Load the canonical system prompt from dataset or repo root."""

    candidates = []
    if dataset_dir:
        candidates.append(dataset_dir / "prompts" / "system_core.txt")
    candidates.append(DEFAULT_SYSTEM_PROMPT_PATH)

    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate.read_text(encoding="utf-8").strip()

    raise FileNotFoundError(
        "System prompt not found. Ensure identity/system_prompt.txt exists or dataset includes prompts/system_core.txt."
    )


def run_cli_validator(dataset_dir: Path, files: Optional[List[Path]] = None) -> List[str]:
    """Invoke the dataset repository's validator script via subprocess."""

    validator_path = dataset_dir / "tools" / "validate_jsonl.py"
    if not validator_path.exists():
        return []

    # Dataset validator supports dataset-dir invocation; skip file hints to keep interfaces simple.
    cmd = [sys.executable, str(validator_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=dataset_dir)
    if result.returncode != 0:
        output = (result.stdout + "\n" + result.stderr).strip()
        return [line for line in output.splitlines() if line.strip()] or [
            f"Validator exited with code {result.returncode}",
            f"Re-run manually: python {validator_path}",
        ]
    return []


def _load_external_validator(dataset_dir: Path):
    """Load dataset-provided validator if available.

    Returns a callable with signature List[Path] -> Dict[Path, List[str]]
    mapping file paths to lists of errors. If not available, returns None.
    """

    validator_path = dataset_dir / "tools" / "validate_jsonl.py"
    if not validator_path.exists():
        return None

    spec = importlib.util.spec_from_file_location("blux_ca_dataset_validator", validator_path)
    if not spec or not spec.loader:  # pragma: no cover - defensive
        return None

    module = importlib.util.module_from_spec(spec)
    sys.modules["blux_ca_dataset_validator"] = module
    spec.loader.exec_module(module)

    def validate(files: List[Path]) -> Dict[Path, List[str]]:
        error_map: Dict[Path, List[str]] = {}

        if hasattr(module, "validate_dataset"):
            dataset_errors = getattr(module, "validate_dataset")(dataset_dir)
            if dataset_errors:
                error_map[dataset_dir] = dataset_errors
            return error_map

        for file_path in files:
            errs = getattr(module, "validate_file")(file_path)
            if errs:
                error_map[file_path] = errs
        return error_map

    return validate


def _iter_jsonl(path: Path) -> Tuple[int, Dict]:
    with path.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield idx, json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path} line {idx}: invalid JSON ({exc})") from exc


def _validate_messages(
    messages: List[Dict], path: Path, line_no: int, strict: bool, canonical_prompt: str
) -> List[str]:
    errors: List[str] = []
    if not isinstance(messages, list) or not messages:
        errors.append(f"{path} line {line_no}: 'messages' must be a non-empty list")
        return errors

    roles = [m.get("role") for m in messages if isinstance(m, dict)]
    if roles.count("system") < 1:
        errors.append(f"{path} line {line_no}: missing system role")
    if roles.count("user") < 1:
        errors.append(f"{path} line {line_no}: missing user role")
    if roles.count("assistant") < 1:
        errors.append(f"{path} line {line_no}: missing assistant role")

    system_messages = [m for m in messages if isinstance(m, dict) and m.get("role") == "system"]
    if system_messages:
        system_content = system_messages[0].get("content", "").strip()
        if system_content != canonical_prompt:
            errors.append(
                f"{path} line {line_no}: system content must equal canonical prompt from identity/system_prompt.txt"
            )
    else:
        errors.append(f"{path} line {line_no}: system message missing")

    for m in messages:
        if not isinstance(m, dict):
            errors.append(f"{path} line {line_no}: each message must be an object")
            continue
        if not m.get("role"):
            errors.append(f"{path} line {line_no}: message missing role")
        if not m.get("content"):
            errors.append(f"{path} line {line_no}: message missing content for role {m.get('role')}")
        audit_errors = _validate_audit_notes(m.get("content", ""), path, line_no)
        errors.extend(audit_errors)

    if strict:
        last_role = messages[-1].get("role") if isinstance(messages[-1], dict) else None
        if last_role != "assistant":
            errors.append(f"{path} line {line_no}: strict mode requires assistant as last role")

    return errors


def _validate_audit_notes(content: str, path: Path, line_no: int) -> List[str]:
    if "## Audit Notes" not in content:
        return []
    errors: List[str] = []
    lines = content.splitlines()
    try:
        header_index = lines.index("## Audit Notes")
    except ValueError:
        return errors
    bullets = lines[header_index + 1 :]
    for bullet in bullets:
        if bullet.strip() and not bullet.strip().startswith("- "):
            errors.append(f"{path} line {line_no}: Audit Notes must use '- ' bullets")
    return errors


def validate_file(path: Path, strict: bool, canonical_prompt: str) -> Tuple[int, int, List[str]]:
    total = 0
    errors: List[str] = []
    for line_no, record in _iter_jsonl(path):
        total += 1
        if not isinstance(record, dict):
            errors.append(f"{path} line {line_no}: expected JSON object per line")
            continue
        messages = record.get("messages")
        errors.extend(_validate_messages(messages, path, line_no, strict, canonical_prompt))
    return total, len(errors), errors


def validate_dataset(dataset_dir: Path, files: Optional[str] = None, strict: bool = False) -> Tuple[int, List[str]]:
    if not dataset_dir.exists():
        return 0, [f"Dataset directory not found: {dataset_dir}"]

    data_dir = dataset_dir / "data"
    eval_dir = dataset_dir / "eval"
    canonical_prompt = load_system_prompt(dataset_dir)
    candidates: List[Path]
    if files:
        candidates = [data_dir / f for f in files.split(",")]
    else:
        candidates = sorted(data_dir.glob("*.jsonl"))

    if not candidates:
        return 0, [f"No JSONL files found under {data_dir}"]
    if not eval_dir.exists():
        return 0, [f"Eval probes missing: {eval_dir}"]

    missing_files = [path for path in candidates if not path.exists()]
    if missing_files:
        return 0, [f"Missing file: {path}" for path in missing_files]

    cli_errors = run_cli_validator(dataset_dir, candidates)
    if cli_errors:
        return 0, cli_errors

    external_validator = _load_external_validator(dataset_dir)
    if external_validator:
        print("Using dataset-supplied validator")
        errors_map = external_validator(candidates)
        overall_errors = [f"{path}: {err}" for path, errs in errors_map.items() for err in errs]
        total_lines = sum(1 for path in candidates for _ in _iter_jsonl(path))
        return total_lines, overall_errors

    overall_errors = []
    total_lines = 0
    for path in candidates:
        if not path.exists():
            overall_errors.append(f"Missing file: {path}")
            continue
        count, error_count, errors = validate_file(
            path, strict=strict, canonical_prompt=canonical_prompt
        )
        total_lines += count
        overall_errors.extend(errors)
        print(f"Validated {path} - lines: {count}, errors: {error_count}")

    return total_lines, overall_errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate BLUX-cA JSONL datasets")
    parser.add_argument("--dataset-dir", required=True, type=Path, help="Path to dataset repository")
    parser.add_argument("--files", type=str, default=None, help="Comma-separated list of data/*.jsonl files")
    parser.add_argument("--strict", action="store_true", help="Enable strict ordering and audit checks")
    args = parser.parse_args()

    total_lines, errors = validate_dataset(args.dataset_dir, files=args.files, strict=args.strict)
    if errors:
        print("Validation errors:")
        for err in errors:
            print(f"- {err}")
        return 1

    print(f"Validation passed. Files checked: {total_lines} lines total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
