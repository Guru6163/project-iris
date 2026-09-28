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

`iris_core.substation` stores country-scoped substation sites (`PRIMARY KEY (country_code, substation_id)`) for proximity screening. Load after `source_run` seed:

```bash
docker compose exec -T db psql -U iris -d iris -f - < seed/substation.sql
docker compose exec -T db psql -U iris -d iris < queries/verify_substation.sql
```

`iris_core.peatland` stores country-scoped peatland footprints (`PRIMARY KEY (country_code, peatland_id)`). `representation` is `observed` or `inferred` so screening can distinguish mapped vs modelled extents without storing numeric uncertainty. Load after `source_run` (and `parcel` if using overlap checks):

```bash
docker compose exec -T db psql -U iris -d iris -f - < seed/peatland.sql
docker compose exec -T db psql -U iris -d iris < queries/verify_peatland.sql
```

`iris_core.screening_layer` holds derived screening footprints. Load after `source_run` (and `parcel` for overlap checks):

```bash
docker compose exec -T db psql -U iris -d iris -f - < seed/screening_layer.sql
docker compose exec -T db psql -U iris -d iris < queries/verify_screening_layer.sql
```

`iris_core.evidence` records which country-scoped entities contributed to a screening layer. Load after `source_run`, business seeds, and `screening_layer`:

```bash
docker compose exec -T db psql -U iris -d iris -f - < seed/evidence.sql
docker compose exec -T db psql -U iris -d iris < queries/verify_evidence.sql
```

### Staging → core flow

Raw parcel loads land in `iris_staging.ingest_run` (source metadata) and `iris_staging.parcel` (geometry + country-scoped ids). Promotion creates a `iris_core.source_run` and upserts into `iris_core.parcel`, then sets `promoted_at` on staged rows.

Load staging fixture:

```bash
docker compose exec -T db psql -U iris -d iris -f - < seed/staging_parcel.sql
```

Promote (Python):

```bash
python -m iris.promote 1
```

Or run the SQL example:

```bash
docker compose exec -T db psql -U iris -d iris < queries/promote_staging_parcel.sql
```

### Schema (iris_core)

| Table | Role |
| --- | --- |
| `source_run` | Ingestion run metadata and status |
| `parcel` | Country-scoped land parcels (`country_code`, `parcel_id`) |
| `substation` | Country-scoped substation sites (`country_code`, `substation_id`) |
| `peatland` | Country-scoped peatland footprints (`country_code`, `peatland_id`) |
| `screening_layer` | Derived screening geometry per run (`source_run_id`, `layer_code`, `geom`) |
| `evidence` | Links a screening layer to input entities (`entity_type`, `entity_id`) and `source_run_id` |

### Schema (iris_staging)

| Table | Role |
| --- | --- |
| `ingest_run` | Staged batch metadata (`source_id`, `source_date`, `record_format`) |
| `parcel` | Parcel rows awaiting promotion (`promoted_at` NULL until promoted) |

Provenance fields (`source_id`, `source_date`, `created_at`) appear on business and derived tables. `source_run` is ingestion metadata and is not country-scoped (runs may feed multiple countries). All other `iris_core` entity tables require `country_code NOT NULL` with primary keys on `(country_code, <entity_id>)`. `evidence` foreign-keys `screening_layer` on `(country_code, screening_layer_id)`; a trigger enforces that `entity_id` resolves to an entity in the same `country_code` and that `source_run_id` matches the linked screening layer.

### Screening layers (design)

`screening_layer` is a **generic derived geometry** table: it stores the output of a screening job as `geom` plus a `layer_code` label (for example `PEATLAND_PARCEL_OVERLAP`), not foreign keys to `parcel`, `peatland`, or `substation`. That avoids duplicating business attributes and keeps one table for multiple pilot screens. Provenance is anchored with `source_run_id` (and the usual `source_id` / `source_date` fields). **`evidence`** stores explainability links from a layer to the country-scoped entities that informed the screen; spatial predicates can still validate those links.

### CRS policy

| Topic | Policy |
| --- | --- |
| **Storage SRID** | **EPSG:4326 (WGS 84)** on every `geom` column (`geometry(..., 4326)` + `ST_SRID(geom) = 4326` checks) |
| **Why 4326** | One global storage CRS for a multi-country pilot; matches common feeds (GeoJSON, lat/lon APIs) and avoids maintaining per-country tables in mixed SRIDs |
| **When to transform** | Keep 4326 in the database. Transform **at query time** (e.g. `ST_Transform(geom, <local_epsg>)`) when a country-specific projected CRS is required for engineering-grade planimetric work |
| **Distance / area** | Use **`geography`** casts for geodesic distance and area in **metres** (`ST_DWithin`, `ST_Area`, `ST_Length` on `geom::geography`). For regional workflows, transform to an appropriate projected UTM / national CRS and use geometry functions in that CRS’s **metre** units |
| **Unit interpretation** | EPSG:4326 coordinates are **degrees** (lon/lat). `geography` results are **metres**. Projected CRS results use that CRS’s axis units (typically metres) |

Geometry types: parcels, peatland, and screening layers are `MultiPolygon`; substations are `Point`.

CRS round-trip verification (insert via WKT, read SRID, transform to UTM zone 43N for the fixture locale, geodesic area / distance):

```bash
docker compose exec -T db psql -U iris -d iris < queries/verify_crs.sql
```

### Spatial indexes (GiST)

| Table | Index | Pilot use |
| --- | --- | --- |
| `iris_core.substation` | `substation_geom_gix` | **BESS:** bbox `&&` on `geom`, then `ST_DWithin` (geography) for distance |
| `iris_core.peatland` | `peatland_geom_gix` | **Peatland:** `ST_Intersects` with parcels |
| `iris_core.parcel` | `parcel_geom_gix` | **Both:** parcel side of intersect / proximity joins |
| `iris_core.screening_layer` | `screening_layer_geom_gix` | Derived footprint ↔ parcel checks (not on hot ingest path) |
| `iris_staging.parcel` | *(none)* | Promotion is keyed load, not spatial search |

Verify plans (loads pilot seeds, forces index use for demonstration on small fixtures):

```bash
python scripts/verify_spatial_indexes.py
```

SQL equivalents:

```bash
docker compose exec -T db psql -U iris -d iris -f - < seed/parcel.sql  # plus other seeds as needed
docker compose exec -T db psql -U iris -d iris -v ON_ERROR_STOP=1 < queries/explain_spatial_pilot.sql
docker compose exec -T db psql -U iris -d iris < queries/verify_crs.sql
```

## Python & tests

Requires Python 3.12+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Database-related tests expect Docker to be running and migrations applied (`./scripts/rebuild_db.sh` or `python -m iris.migrate`).
