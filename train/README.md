# BLUX-cA QLoRA Training Pipeline

This folder contains a GPU-friendly QLoRA pipeline for finetuning a BLUX-cA adapter on domain-mixed JSONL chat data. The dataset must live outside this repository; provide its path via `--dataset-dir` or the `DATASET_DIR` environment variable.

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
accelerate config
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
Validate dataset strictly:
```bash
python train/validate_dataset.py --dataset-dir /path/to/blux-ca-dataset --strict
```
Dry-run model/tokenizer loading and tokenization:
```bash
python train/train_qlora.py --dataset-dir /path/to/blux-ca-dataset --dry-run
```
Train a QLoRA adapter:
```bash
python train/train_qlora.py --dataset-dir /path/to/blux-ca-dataset
```
Run evaluation against probes:
```bash
python train/run_eval.py --dataset-dir /path/to/blux-ca-dataset --run runs/<timestamp> --strict
```

## Outputs
- Prepared dataset: `runs/<timestamp>/prepared_train.jsonl`
- Training artifacts: `runs/<timestamp>/adapter_model/` plus `runs/<timestamp>/training_args.json` and `config_snapshot.yaml`
- Evaluation report: `runs/<timestamp>/eval_report.md`

## Release checklist
- Dataset validated (`python train/validate_dataset.py --dataset-dir ... --strict`)
- Prepared dataset generated and referenced by run folder
- Evaluation run passes in strict mode
- Adapter artifacts present under `runs/<timestamp>/adapter_model/`
- Model card/README updated before publishing adapter (adapter-only, no base weights)

## Uploading adapter to Hugging Face Hub
```bash
git lfs track "*.safetensors"
cd runs/<timestamp>/adapter_model
# add README/model card as needed
```
Only upload the adapter weights—do not upload base model weights.
