# Runbook

This runbook describes deterministic offline execution for the frozen `cA-1.0-pro` repo.
Use Python 3.11+ for all commands below.

## 1. Create a virtual environment

```sh
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python -m pip install -U pip
```

## 2. Install the package

```sh
python -m pip install -e .[dev]
```

Windows PowerShell:

```powershell
py -3.11 -m pip install -e .[dev]
```

## 3. Run the engine

```sh
blux-ca run --goal examples/goal_hello.json --out out/
```

Windows PowerShell:

```powershell
py -3.11 -m blux_ca run --goal examples/goal_hello.json --out out/
```

## 4. Run the acceptance harness

```sh
blux-ca accept --fixtures examples --out out/
blux-ca accept --fixtures examples --out out-cpu/ --profile cpu
```

Windows PowerShell:

```powershell
py -3.11 -m blux_ca accept --fixtures examples --out out/
```

## 5. Validate outputs

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

## 6. Verify acceptance expectations

```sh
python - <<'PY'
import json
from pathlib import Path

report = json.loads(Path("out/report.json").read_text(encoding="utf-8"))
for row in report["fixtures"]:
    assert row["expected_artifact"] == "MATCH", row
    assert row["expected_verdict"] == "MATCH", row
print("acceptance expectations matched")
PY
```
