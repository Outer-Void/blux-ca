#!/bin/sh

if [ "$#" -eq 0 ]; then
  echo "Usage: ./cA_proot.sh <command> [args...]"
  echo "Example: ./cA_proot.sh run --goal examples/goal_hello.json --out out/"
  exit 0
fi

if [ ! -d ".venv" ]; then
  sudo apt update && sudo apt install -y python3 python3-venv python3-pip git
  python3 -m venv .venv
fi

. ./.venv/bin/activate

python -m pip install -e ".[dev]"

python -m blux_ca "$@"
