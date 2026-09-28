# Assessment scope (supplement)

The canonical submission guide is the [README](../README.md) (overview, setup, commands, CRS policy, architectural decisions, and deliberate simplifications).

This file is a quick map from assessment themes to repository locations:

| Theme | Where |
| --- | --- |
| Schemas and PostGIS | `migrations/001_foundation.sql` |
| Provenance | `migrations/002_source_run.sql`, `seed/source_run.sql` |
| Country-scoped entities | `migrations/003`–`005`, `seed/*.sql` |
| Screening + evidence | `migrations/006`–`007`, `migrations/008_country_scope_integrity.sql` |
| Staging + promotion | `migrations/009_staging.sql`, `iris/promote.py` |
| Spatial indexes | `migrations/010_spatial_index_notes.sql`, `tests/test_spatial_indexes.py` |
| Correctness rubric | `tests/test_database_correctness.py` |
| ER diagram | [schema.md](schema.md) |
