#!/usr/bin/env bash
# Build the wheel, install it into a clean venv outside the source tree, and use it there: cA 2 must build,
# patch and roll back a workspace, and the frozen cA 1.0 engine must find its schemas and policy packs.
set -euo pipefail
PYTHON="${PYTHON:-python3}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

"$PYTHON" -m build --wheel --outdir "$WORK/dist" "$ROOT" >/dev/null
"$PYTHON" -m venv "$WORK/venv"
"$WORK/venv/bin/pip" install -q "$WORK"/dist/*.whl
cd "$WORK"
CA="$WORK/venv/bin/ca"
"$CA" --version
"$CA" schema artifact.construct >/dev/null
cat >build.json <<'JSON'
{"workspace": "w", "blueprint": {"units": [{"task": "build", "files": [
  {"path": "app.py", "content": "a = 1\n"},
  {"path": "conf.toml", "config": {"data": {"name": "demo"}}}]}]}}
JSON
"$CA" construct build.json -o built.json
printf '%s' '{"workspace": "w", "path": "app.py", "diff": "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-a = 1\n+a = 2\n"}' >patch.json
"$CA" code-patch patch.json -o patched.json
grep -qx 'a = 2' w/app.py
ID=$("$WORK/venv/bin/python" -c "import json,sys; print(json.load(open(sys.argv[1]))['changeset']['changeset_id'])" patched.json)
"$CA" rollback "$ID" -w w >/dev/null
grep -qx 'a = 1' w/app.py
set +e; echo '{}' | "$CA" modify - >/dev/null 2>&1; code=$?; set -e
[ "$code" -eq 3 ] || { echo "expected exit 3 for an invalid request, got $code" >&2; exit 1; }
# The frozen 1.0 engine, run outside the checkout: output must equal the checked-in expectation.
"$WORK/venv/bin/blux-ca" run --goal "$ROOT/examples/goal_hello.json" --out "$WORK/legacy"
cmp "$WORK/legacy/artifact.json" "$ROOT/examples/goal_hello.artifact.json"
cmp "$WORK/legacy/verdict.json" "$ROOT/examples/goal_hello.verdict.json"
echo "verify_wheel: OK"
