# BLUX-cA Adapter Training Pipeline

This folder contains a reproducible adapter (LoRA/QLoRA) pipeline for BLUX-cA using the external dataset repository. The dataset must live **outside** this repository; set `DATASET_DIR` to its absolute path (for example `/workspace/blux-ca-dataset`).

## Prerequisites
- Python 3.10+
- Recommended: NVIDIA GPU with recent CUDA drivers
- Sufficient disk space/memory for the base model (default: `Qwen/Qwen2.5-7B-Instruct`)

## Environment setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r train/requirements.txt
```

## Dataset layout
The dataset directory should contain:
```
prompts/system_core.txt
data/*.jsonl
eval/*.jsonl
```
Each training JSONL line must include a `messages` array containing `system`, `user`, and `assistant` roles. The system content must equal `<SYSTEM_PROMPT_FROM_BLUX_CA>`.

## Commands (copy/paste)
Set the dataset location once per shell:
```bash
export DATASET_DIR=/absolute/path/to/blux-ca-dataset
```

Validate dataset strictly (always invokes the dataset repo validator first):
```bash
python train/validate_dataset.py --dataset-dir "$DATASET_DIR" --strict
```

Dry-run (loads base model, prepares 5 samples, tokenizes). On CPU-only hosts the base model automatically falls back to
`Qwen/Qwen2.5-1.5B-Instruct` unless you override `BASE_MODEL`:
```bash
python train/train_adapter.py --dataset-dir "$DATASET_DIR" --dry-run
```

Smoke train (adapter, capped mix):
```bash
python train/train_adapter.py --dataset-dir "$DATASET_DIR" --max-samples 200 --run-name smoke
```

Full train:
```bash
python train/train_adapter.py --dataset-dir "$DATASET_DIR" --run-name full
```

Eval gate (strict). Use `--use-stub` when running without a trained adapter or when offline:
```bash
python train/run_eval.py --dataset-dir "$DATASET_DIR" --run runs/<timestamp_or_name> --strict --use-stub
```

GPU is recommended for smoke/full runs. On CPU-only environments, set `BASE_MODEL=Qwen/Qwen2.5-1.5B-Instruct` for the dry-run to conserve memory.

## Outputs
- Runs are created under `runs/YYYYMMDD_HHMMSS_<optional_name>/`
- Prepared dataset + resolved mix: `runs/<timestamp>/prepared_train.jsonl` and `runs/<timestamp>/mix_config_resolved.yaml`
- Training artifacts: `runs/<timestamp>/adapter/` plus `runs/<timestamp>/training_args.json` and `config_snapshot.yaml`
- Evaluation report: `runs/<timestamp>/eval_report.md`

## Release checklist
- Dataset validated (`python train/validate_dataset.py --dataset-dir ... --strict`)
- Prepared dataset generated and referenced by run folder
- Evaluation run passes in strict mode
- Adapter artifacts present under `runs/<timestamp>/adapter/`
- Model card/README updated before publishing adapter (adapter-only, no base weights)

## Uploading adapter to Hugging Face Hub
```bash
git lfs track "*.safetensors"
cd runs/<timestamp>/adapter
# add README/model card as needed
```
Only upload the adapter weights—do not upload base model weights.
