# Project IRIS

Technical assessment scaffold: PostgreSQL 16 with PostGIS for geospatial data, SQL migrations, and pytest.

## Local database (Docker)

Prerequisites: [Docker](https://docs.docker.com/get-docker/) with Compose.

1. Copy environment defaults:

   ```bash
   cp .env.example .env
   ```

2. Start PostgreSQL + PostGIS:

   ```bash
   docker compose up -d
   ```

3. Confirm the container is healthy:

   ```bash
   docker compose ps
   ```

4. Optional — open a SQL shell:

   ```bash
   docker compose exec db psql -U "${POSTGRES_USER:-iris}" -d "${POSTGRES_DB:-iris}"
   ```

5. Stop when finished:

   ```bash
   docker compose down
   ```

## Python & tests

Requires Python 3.12+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Database-related tests expect the Docker service from `.env.example` to be running.
