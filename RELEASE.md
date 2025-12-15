# BLUX-cA Release Checklist

## Pre-flight
1. Ensure dataset path is set:
```bash
export DATASET_DIR=/absolute/path/to/blux-ca-dataset
```
2. Validate dataset:
```bash
python tools/validate_jsonl.py
```

## Codebase checks
```bash
python -m compileall .
python ca.py --help
python ca.py doctor --dataset-dir "$DATASET_DIR"
```

## Training lane
- Dry-run adapter training:
```bash
python train/train_qlora.py --dataset-dir "$DATASET_DIR" --dry-run
```
- Smoke run (small sample):
```bash
python train/train_qlora.py --dataset-dir "$DATASET_DIR" --max-samples 200 --run-name smoke
```
- Full run (as needed):
```bash
python train/train_qlora.py --dataset-dir "$DATASET_DIR" --run-name full
```

Prepared data and artifacts are stored under `runs/<timestamp_or_name>/`.

## Evaluation gate
Run the evaluation suite against a prepared run directory:
```bash
python train/run_eval.py --dataset-dir "$DATASET_DIR" --run runs/<timestamp_or_name> --strict
```

## Publish
1. Push code repo (no binaries):
```bash
git push origin <branch>
```
2. Push dataset repo from `/workspace/blux-ca-dataset`:
```bash
git push origin <branch>
```
3. Upload adapter-only artifacts (from `runs/<timestamp>/adapter/`) to a dedicated Hugging Face repo.
