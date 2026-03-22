# Platform Setup

This repository is a Python project. Use `python -m pip`, not raw `pip`.

## Termux (native)

```sh
pkg install python3 git
python -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .[dev]
./cA_mux.sh run --goal examples/goal_hello.json --out out/
```

## Termux (proot-distro Debian)

Host Termux:

```sh
pkg install proot-distro git
proot-distro install debian
proot-distro login debian
```

Inside Debian:

```sh
sudo apt update && sudo apt install -y python3 python3-venv python3-pip git
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .[dev]
./cA_proot.sh run --goal examples/goal_hello.json --out out/
```

## Debian / Ubuntu

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .[dev]
./cA.sh run --goal examples/goal_hello.json --out out/
```

## macOS

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .[dev]
./cA.sh run --goal examples/goal_hello.json --out out/
```

## Windows (PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python -m pip install -U pip
.\.venv\Scripts\python -m pip install -e .[dev]
.\cA.ps1 run --goal examples/goal_hello.json --out out/
```

## Cross-platform smoke checks

After setup, validate the generated outputs:

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
