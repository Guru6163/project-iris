# IRIS technical assessment — scope map

This repository implements the IRIS geospatial data model and pilot workflow. The original assignment brief is not stored here; this document records what the codebase delivers and documents intentional design choices called out in review.

## Delivered capabilities

| Area | Location |
| --- | --- |
| PostGIS foundation, schemas `iris_staging` / `iris_core` | `migrations/001_foundation.sql` |
| Ingestion provenance (`source_run`) | `migrations/002_source_run.sql`, `seed/source_run.sql` |
| Country-scoped parcels, substations, peatland | `migrations/003`–`005`, `seed/*.sql` |
| Screening layers and evidence | `migrations/006`–`007`, `seed/screening_layer.sql`, `seed/evidence.sql` |
| Cross-table country / run integrity | `migrations/008_country_scope_integrity.sql` |
| Staging ingest + parcel promotion | `migrations/009_staging.sql`, `iris/promote.py`, `queries/promote_staging_parcel.sql` |
| Spatial index documentation | `migrations/010_spatial_index_notes.sql`, `iris/spatial_indexes.py` |
| Deterministic multi-country fixtures | `seed/`, `iris/seed_data.py` |
| Correctness rubric + full pytest suite | `tests/test_database_correctness.py`, `tests/` |
| ER diagram | [schema.md](schema.md) |

## Intentional partials (not bugs)

- **`source_run` is global** — ingestion runs are not keyed by `country_code`; a single run may feed multiple countries. Business tables remain country-scoped.
- **Staging promotes parcels only** — the pilot path is `iris_staging.parcel` → `iris_core.parcel`. Other entity types are loaded into core via seeds or future ingest pipelines.
- **Evidence → entity links use a trigger** — `entity_type` + `entity_id` is polymorphic; PostgreSQL cannot express one declarative FK. The trigger `iris_core.evidence_country_scope_checks()` enforces same-country entity resolution and matching `source_run_id` on the screening layer. See [schema.md](schema.md).

## Reproducibility

From a clean checkout with Docker and Python 3.12+:

```bash
./scripts/bootstrap.sh
```

That resets the database, applies migrations, loads seeds, and runs pytest.
