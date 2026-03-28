#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
export PYTHONPATH="$(pwd)/src${PYTHONPATH:+:$PYTHONPATH}"

if command -v python3 >/dev/null 2>&1; then
  python3 -m codex_accmgr "$@"
elif command -v python >/dev/null 2>&1; then
  python -m codex_accmgr "$@"
else
  echo "Python 3 not found. Please install Python 3.10+ and retry."
  exit 1
fi
