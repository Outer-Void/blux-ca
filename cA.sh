#!/bin/sh

if [ "$#" -eq 0 ]; then
  echo "Usage: ./cA.sh <command> [args...]"
  echo "Example: ./cA.sh run --goal examples/goal_hello.json --out out/"
  exit 0
fi

if [ ! -d ".venv" ]; then
  python3 -m venv .venv 2>/dev/null || python -m venv .venv
fi

. ./.venv/bin/activate

python -m pip install -e ".[dev]"

python -m blux_ca "$@"
