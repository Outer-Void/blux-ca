# Platform Setup

This repository is a Python project. Use `python -m pip`, not raw `pip`.
The package requires **Python 3.11+**.

## Termux (native)

```sh
pkg install python3
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .[dev]
./cA_mux.sh run --goal examples/goal_hello.json --out out/
```

## Termux (proot-distro Debian)

Host Termux:

```sh
pkg install proot-distro
proot-distro install debian
proot-distro login debian
```

Inside Debian:

```sh
sudo apt update && sudo apt install python3 python3-venv python3-pip git
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .[dev]
./cA_proot.sh run --goal examples/goal_hello.json --out out/
```

## Debian / Ubuntu

Install Python 3.11+ first, then:

```sh
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .[dev]
./cA.sh run --goal examples/goal_hello.json --out out/
```

If your `python3` already resolves to 3.11+, you may substitute `python3`.

## macOS

Install Python 3.11+ first, then:

```sh
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .[dev]
./cA.sh run --goal examples/goal_hello.json --out out/
```

If your `python3` already resolves to 3.11+, you may substitute `python3`.

## Windows (PowerShell)

```powershell
py -3.11 -m venv .venv
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
