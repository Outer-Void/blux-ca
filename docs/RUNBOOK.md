# Runbook

This runbook describes deterministic, offline execution for all supported platforms.

## 1. Install dependencies

Follow the platform setup steps in `docs/PLATFORMS.md`.

## 2. Create a virtual environment

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
```

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python -m pip install -U pip
```

## 3. Install the package

```sh
python -m pip install -e .
```

Windows PowerShell:

```powershell
py -3 -m pip install -e .
```

## 4. Run the engine

```sh
python -m blux_ca run --goal examples/goal_hello.json --out out/
```

Windows PowerShell:

```powershell
py -3 -m blux_ca run --goal examples/goal_hello.json --out out/
```

## 5. Run the acceptance harness

```sh
python -m blux_ca accept --fixtures examples --out out/
```

Windows PowerShell:

```powershell
py -3 -m blux_ca accept --fixtures examples --out out/
```

## 6. Validate outputs

```sh
python - <<'PY'
import json
from jsonschema import validate
from pathlib import Path

schemas = Path("schemas")
artifact = json.loads(Path("out/artifact.json").read_text(encoding="utf-8"))
verdict = json.loads(Path("out/verdict.json").read_text(encoding="utf-8"))
validate(instance=artifact, schema=json.loads((schemas / "artifact.schema.json").read_text()))
validate(instance=verdict, schema=json.loads((schemas / "verdict.schema.json").read_text()))
print("validated")
PY
```

Windows PowerShell:

```powershell
py -3 - <<'PY'
import json
from jsonschema import validate
from pathlib import Path

schemas = Path("schemas")
artifact = json.loads(Path("out/artifact.json").read_text(encoding="utf-8"))
verdict = json.loads(Path("out/verdict.json").read_text(encoding="utf-8"))
validate(instance=artifact, schema=json.loads((schemas / "artifact.schema.json").read_text()))
validate(instance=verdict, schema=json.loads((schemas / "verdict.schema.json").read_text()))
print("validated")
PY
```
