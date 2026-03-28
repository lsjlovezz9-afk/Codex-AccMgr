#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if command -v python3 >/dev/null 2>&1; then
  python3 codex.py "$@"
elif command -v python >/dev/null 2>&1; then
  python codex.py "$@"
else
  echo "Python 3 not found. Please install Python 3.10+ and retry."
  exit 1
fi
