#!/usr/bin/env bash
# Load deterministic core (+ staging) fixtures. Safe to run repeatedly.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHON="${ROOT}/.venv/bin/python"
if [[ ! -x "${PYTHON}" ]]; then
  PYTHON="python3"
fi

"${PYTHON}" -m iris.seed_data "$@"
