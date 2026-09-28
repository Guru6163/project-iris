#!/usr/bin/env bash
# Reset the local iris database: ensure Docker Postgres is up, drop/create DB, run migrations.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

POSTGRES_USER="${POSTGRES_USER:-iris}"
POSTGRES_DB="${POSTGRES_DB:-iris}"

echo "Starting PostgreSQL/PostGIS (Docker)..."
docker compose up -d

echo "Waiting for database..."
for _ in $(seq 1 60); do
  if docker compose exec -T db pg_isready -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! docker compose exec -T db pg_isready -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" >/dev/null 2>&1; then
  echo "Database did not become ready in time." >&2
  exit 1
fi

"${ROOT}/scripts/rebuild_db.sh"
echo "Reset complete: empty database with migrations applied."
