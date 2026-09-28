#!/usr/bin/env bash
# From a clean checkout: start DB, migrate, seed fixtures, run verification tests.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHON="${ROOT}/.venv/bin/python"
PIP="${ROOT}/.venv/bin/pip"

if [[ ! -x "${PYTHON}" ]]; then
  echo "Creating Python virtualenv..."
  python3 -m venv .venv
fi

"${PIP}" install -q -e ".[dev]"

"${ROOT}/scripts/reset_db.sh"
"${ROOT}/scripts/seed_data.sh"

echo "Running rubric correctness tests..."
"${PYTHON}" -m pytest tests/test_database_correctness.py -v

echo "Running full test suite..."
"${PYTHON}" -m pytest -q

echo "Bootstrap complete."
