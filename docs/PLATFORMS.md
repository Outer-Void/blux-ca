# Platform Setup

This repository is a Python project. Follow the steps below for your platform.

## Termux (native)

```sh
pkg update && pkg upgrade
pkg install python3 git
python -m venv .venv
python -m pip install -U pip
```

## Termux (proot-distro Debian)

Host (Termux):

```sh
pkg install proot-distro git
proot-distro install debian
proot-distro login debian
```

Inside Debian:

```sh
sudo apt update && sudo apt install -y python3 python3-venv python3-pip git
python3 -m venv .venv
python -m pip install -U pip
```

## Debian / Ubuntu

```sh
sudo apt update && sudo apt install -y python3 python3-venv python3-pip git
python3 -m venv .venv
python -m pip install -U pip
```

## macOS

```sh
brew install python git
python3 -m venv .venv
python -m pip install -U pip
```

## Windows (PowerShell)

```powershell
winget install -e --id Python.Python.3
winget install -e --id Git.Git
py -3 -m venv .venv
.\.venv\Scripts\python -m pip install -U pip
```

## Cross-platform smoke commands

Use these commands after the setup above. They create outputs and validate them against the schema.

### Termux (native)

```sh
python -m pip install -e .
python -m blux_ca run --goal examples/goal_hello.json --out out/
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

### Termux (proot-distro Debian)

```sh
python -m pip install -e .
python -m blux_ca run --goal examples/goal_hello.json --out out/
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

### Debian / Ubuntu

```sh
python -m pip install -e .
python -m blux_ca run --goal examples/goal_hello.json --out out/
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

### macOS

```sh
python -m pip install -e .
python -m blux_ca run --goal examples/goal_hello.json --out out/
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

### Windows (PowerShell)

```powershell
py -3 -m pip install -e .
py -3 -m blux_ca run --goal examples/goal_hello.json --out out/
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
