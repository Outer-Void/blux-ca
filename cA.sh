#!/bin/sh

if [ "$#" -eq 0 ]; then
  echo "Usage: ./cA.sh <command> [args...]"
  echo "Examples:"
  echo "  ./cA.sh run --goal examples/goal_hello.json --out out/"
  echo "  ./cA.sh accept --fixtures examples --out out/"
  exit 0
fi

select_python() {
  if command -v python3.11 >/dev/null 2>&1 && python3.11 --version >/dev/null 2>&1; then
    echo python3.11
    return
  fi
  if command -v pyenv >/dev/null 2>&1; then
    PYENV_311=$(pyenv versions --bare | grep '^3\.11' | head -n 1)
    if [ -n "$PYENV_311" ]; then
      echo "PYENV_VERSION=$PYENV_311 pyenv exec python"
      return
    fi
  fi
  if command -v python3 >/dev/null 2>&1; then
    echo python3
    return
  fi
  echo python
}

PYTHON_CMD=$(select_python)

if [ ! -d ".venv" ]; then
  sh -c "$PYTHON_CMD -m venv .venv"
fi

. ./.venv/bin/activate

python -m pip install -e ".[dev]"
python -m blux_ca "$@"
