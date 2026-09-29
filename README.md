# Project IRIS

PostgreSQL 16 + PostGIS 3.4 technical assessment: country-scoped geospatial entities, screening layers, evidence links, staging-to-core parcel promotion, SQL migrations, and pytest verification.

## 1. Project overview

IRIS models renewable-energy site screening data across multiple countries. Business geometry and attributes live in `iris_core`; raw parcel batches land in `iris_staging` before promotion. The repo is self-contained: Docker Compose for PostGIS, versioned SQL migrations, deterministic seeds (India, Germany, United States fixtures), and automated tests including a rubric-focused correctness suite.

**Clean checkout (recommended for reviewers):**

```bash
./scripts/bootstrap.sh
```

That creates `.env` from `.env.example` if missing, installs Python dependencies, resets the database, loads seeds, and runs the full test suite.

## 2. Architecture

| Layer | Purpose |
| --- | --- |
| **`iris_staging`** | Ingest metadata (`ingest_run`) and staged parcels awaiting promotion |
| **`iris_core`** | Provenance (`source_run`), country-scoped entities (parcel, substation, peatland), derived `screening_layer`, and `evidence` |
| **`migrations/`** | Ordered DDL; applied versions recorded in `public.iris_migrations` |
| **`iris/`** | `migrate`, `seed_data`, `promote`, spatial index helpers |
| **`seed/`** | Idempotent SQL fixtures |
| **`queries/`** | Verification and example promotion / EXPLAIN scripts |
| **`tests/`** | Pytest (schema, scope integrity, CRS, staging, rubric) |

Entity-relationship diagram: [docs/schema.md](docs/schema.md).

**Data flow (pilot):** external parcel files → `iris_staging` → promotion → `iris_core.parcel` + new `source_run`. Other entity types load directly into `iris_core` via seeds or future ingest jobs. Screening jobs write `screening_layer` geometries and optional `evidence` rows explaining which entities informed each layer.

## 3. Requirements

- [Docker](https://docs.docker.com/get-docker/) with Compose (PostGIS image `postgis/postgis:16-3.4`)
- Python **3.12+**
- macOS, Linux, or Windows with WSL2 (commands assume a POSIX shell)
- **Docker daemon running** before `./scripts/bootstrap.sh`, `./scripts/reset_db.sh`, `./scripts/rebuild_db.sh`, or any `docker compose` command

No cloud accounts or API keys are required. Default database credentials are local-dev placeholders in `.env.example` only.

## 4. Setup

```bash
git clone <repository-url>
cd project-iris
cp .env.example .env          # optional; bootstrap creates this if absent
python3 -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

`DATABASE_URL` in `.env` must match Docker Postgres (default `postgresql://iris:iris@localhost:5432/iris`).

**Do not commit `.env`** — it is listed in `.gitignore`. Only `.env.example` is tracked.

## 5. Database startup

```bash
docker compose up -d
docker compose ps              # wait until db is healthy
```

Optional SQL shell:

```bash
docker compose exec db psql -U "${POSTGRES_USER:-iris}" -d "${POSTGRES_DB:-iris}"
```

Stop containers:

```bash
docker compose down
```

## 6. Migration command

Apply all pending migrations (safe on an existing database):

```bash
python -m iris.migrate
```

Rebuild from an **empty** database (drop/create `iris` DB inside the container, then migrate):

```bash
./scripts/rebuild_db.sh
```

Requires Docker running and `docker compose` targeting the project `db` service.

## 7. Seed command

Load deterministic core + staging fixtures (idempotent — `ON CONFLICT DO NOTHING`):

```bash
./scripts/seed_data.sh
```

or:

```bash
python -m iris.seed_data
```

Core tables only (no staging batch):

```bash
python -m iris.seed_data --core-only
```

Fixture geography: **IN/KA**, **DE/BE+BY**, **US/VA**. File order and contents: [seed/README.md](seed/README.md).

## 8. Test command

Full suite (requires a reachable Postgres with PostGIS; start Docker with `docker compose up -d`, apply migrations, or use `./scripts/bootstrap.sh` which does both and runs tests):

```bash
pytest
```

Rubric / database correctness tests:

```bash
pytest tests/test_database_correctness.py -v
```

CI runs the same flow: migrate → seed → `pytest` (see `.github/workflows/ci.yml`).

## 9. Verification commands

After `./scripts/seed_data.sh`, optional SQL checks:

```bash
docker compose exec -T db psql -U iris -d iris < queries/verify_source_run.sql
docker compose exec -T db psql -U iris -d iris < queries/verify_parcel.sql
docker compose exec -T db psql -U iris -d iris < queries/verify_substation.sql
docker compose exec -T db psql -U iris -d iris < queries/verify_peatland.sql
docker compose exec -T db psql -U iris -d iris < queries/verify_screening_layer.sql
docker compose exec -T db psql -U iris -d iris < queries/verify_evidence.sql
```

CRS round-trip (WGS 84 storage, transform, geodesic measures):

```bash
docker compose exec -T db psql -U iris -d iris < queries/verify_crs.sql
```

Spatial index plans (pilot BESS / peatland queries; expects seeds loaded):

```bash
python scripts/verify_spatial_indexes.py
docker compose exec -T db psql -U iris -d iris -v ON_ERROR_STOP=1 < queries/explain_spatial_pilot.sql
```

**Staging promotion** (after seeds include `staging_parcel.sql`):

```bash
python -m iris.promote 1
```

or:

```bash
docker compose exec -T db psql -U iris -d iris -v ingest_run_id=1 -f queries/promote_staging_parcel.sql
```

## 10. Reset command

Drop and recreate the application database, re-apply all migrations (Docker volume retained):

```bash
./scripts/reset_db.sh
```

End-to-end reset + seed + tests:

```bash
./scripts/bootstrap.sh
```

## 11. CRS / geometry policy

| Topic | Policy |
| --- | --- |
| **Storage SRID** | **EPSG:4326 (WGS 84)** on every `geom` column, with checks that `ST_SRID(geom) = 4326` |
| **Why 4326** | Single global storage CRS for a multi-country pilot; aligns with GeoJSON and lat/lon APIs |
| **Transforms** | Keep 4326 in the database; use `ST_Transform` at query time when a national/projected CRS is needed |
| **Distance / area** | Use **`geography`** for geodesic distance and area in **metres** (`ST_DWithin`, `ST_Area` on `geom::geography`); or transform to a suitable projected CRS for regional work |
| **Units** | 4326 coordinates are **degrees**; `geography` results are **metres** |

**Geometry types:** parcels, peatland, and screening layers use `MultiPolygon`; substations use `Point`.

**GiST indexes** (see `migrations/010_spatial_index_notes.sql`): `parcel_geom_gix`, `substation_geom_gix`, `peatland_geom_gix`, `screening_layer_geom_gix`. Staging parcels are not spatially indexed (keyed promotion, not spatial search).

## 12. Key architectural decisions

- **Country-scoped composite primary keys** — `(country_code, entity_id)` on parcel, substation, peatland, screening_layer, and evidence so the same logical id cannot collide across countries.
- **Global `source_run`** — ingestion run metadata is not country-scoped; one run may feed multiple countries. Business rows still require `country_code`.
- **Generic `screening_layer`** — derived footprints keyed by `layer_code` and `source_run_id`, not per-entity-type tables. Spatial relationships to parcels/peatland/substations are evaluated in SQL; `evidence` holds explainability links.
- **Evidence integrity via trigger** — `evidence` FKs `screening_layer` on `(country_code, screening_layer_id)`. A trigger ensures `entity_id` resolves to parcel, peatland, or substation in the same country and that `source_run_id` matches the layer (polymorphic `entity_type` cannot be a single declarative FK).
- **Staging vs core** — staging holds pre-promotion parcels; promotion creates a core `source_run` and upserts `iris_core.parcel`, then sets `promoted_at`.
- **Migrations as source of truth** — no ORM schema; `iris.migrate` applies `migrations/*.sql` in sorted order.

## 13. Deliberate simplifications

- **Parcel-only staging path** — substation, peatland, and screening data are seeded or loaded directly into `iris_core`; only parcels demonstrate staging → promotion.
- **Pilot-scale fixtures** — small hand-authored geometries to exercise overlaps and GiST plans, not production data volume.
- **Trigger-based evidence links** — chosen over multiple nullable FK columns or an entity super-table.
- **Local Docker credentials** — default user/password `iris` in `.env.example` for assessment convenience, not production security.
- **No assignment PDF in-repo** — requirements are reflected in schema, seeds, tests, and this README.

## 14. How the design could evolve for production

- **Per-entity staging tables** and unified ingest orchestration with row-level validation before promotion.
- **Partitioning** by `country_code` or time for large parcel and screening tables; read replicas for analytics.
- **Stronger provenance** — immutable audit log, checksums on source files, lineage from `ingest_run` through `source_run` to derived layers.
- **Materialized views or tile services** for hot screening layers; job queue for heavy spatial joins instead of ad hoc SQL.
- **Secrets management** — managed Postgres, TLS, role separation; remove default passwords.
- **CI parity** — extend GitHub Actions with `bootstrap.sh`-style Docker rebuild if full drop/create testing is required in CI.
- **Optional declarative constraints** — split `evidence` into typed link tables if polymorphic `entity_type` becomes a maintenance burden.

## Repository layout

```
project-iris/
├── docker-compose.yml
├── migrations/          # 001–010 SQL migrations
├── iris/                # Python package (migrate, seed, promote)
├── seed/                # Fixture SQL
├── queries/             # verify_*, promote, EXPLAIN examples
├── scripts/             # bootstrap, reset, rebuild, seed, spatial verify
├── tests/
└── docs/schema.md       # Mermaid ER diagram
```

## Submission checklist (maintainers)

- [ ] `.env` not committed (only `.env.example`)
- [ ] `docker compose up -d` healthy
- [ ] `./scripts/bootstrap.sh` exits 0
- [ ] No local `.venv/`, `.pytest_cache/`, or Docker volume data in git
