#!/data/data/com.termux/files/usr/bin/sh

if [ "$#" -eq 0 ]; then
  echo "Usage: ./cA_mux.sh <command> [args...]"
  echo "Example: ./cA_mux.sh run --goal examples/goal_hello.json --out out/"
  exit 0
fi

if [ ! -d ".venv" ]; then
  pkg install -y python3
  python -m venv .venv
fi

. ./.venv/bin/activate

python -m pip install -e ".[dev]"

python -m blux_ca "$@"
