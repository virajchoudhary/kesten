#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
if [ ! -x .venv/bin/python ]; then
    python3.12 -m venv .venv
fi
.venv/bin/python -m pip install -r backend/requirements-workspace.lock.txt
(cd web && npm ci --no-audit --no-fund)
printf '%s\n' 'Run .venv/bin/python scripts/dev.py to start Cadrisyn.'
