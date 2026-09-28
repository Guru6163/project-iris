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

## Database migrations

SQL files live in `migrations/` and run in sorted filename order. Applied versions are tracked in `public.iris_migrations`.

**Initialize or rebuild from an empty database** (drops and recreates the `iris` database, then applies all migrations):

```bash
./scripts/rebuild_db.sh
```

Apply pending migrations only (safe on an already-initialized database):

```bash
python -m iris.migrate
```

`iris_core.source_run` records provenance and execution for each ingestion (`source_id`, `source_date`, `created_at`, run status/timestamps). Load the deterministic sample row:

```bash
docker compose exec -T db psql -U iris -d iris -f - < seed/source_run.sql
```

Example checks (after loading the seed):

```bash
docker compose exec -T db psql -U iris -d iris < queries/verify_source_run.sql
```

`iris_core.parcel` stores country-scoped parcels (`PRIMARY KEY (country_code, parcel_id)`). Load sample data after `source_run` seed:

```bash
docker compose exec -T db psql -U iris -d iris -f - < seed/parcel.sql
docker compose exec -T db psql -U iris -d iris < queries/verify_parcel.sql
```

### Geometry / CRS

Parcel boundaries use `geom geometry(MultiPolygon, 4326)` — **EPSG:4326 (WGS 84)**. Longitude/latitude in degrees is a practical default for a multi-country pilot, interoperates with common feeds, and keeps one CRS across regions until a country needs a local projected SRID for metric work.

## Python & tests

Requires Python 3.12+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Database-related tests expect Docker to be running and migrations applied (`./scripts/rebuild_db.sh` or `python -m iris.migrate`).
