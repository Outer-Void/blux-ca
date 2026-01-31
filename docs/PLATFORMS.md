# Platform Setup

This repository is a Python project. Follow the steps below for your platform.

## Termux (native)

```sh
./cA_mux.sh run --goal examples/goal_hello.json --out out/
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
./cA_proot.sh run --goal examples/goal_hello.json --out out/
```

## Debian / Ubuntu

```sh
./cA.sh run --goal examples/goal_hello.json --out out/
```

## macOS

```sh
./cA.sh run --goal examples/goal_hello.json --out out/
```

## Windows (PowerShell)

```powershell
.\cA.ps1 run --goal examples/goal_hello.json --out out/
```

## Cross-platform smoke commands

Use these commands after the setup above. They create outputs and validate them against the schema.

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
