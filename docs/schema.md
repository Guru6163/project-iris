# IRIS database architecture

Country-scoped business entities use composite primary keys `(country_code, <entity_id>)`. `source_run` is global ingestion metadata (not country-scoped). Staged rows promote into `iris_core.parcel` without a database foreign key.

```mermaid
erDiagram
    iris_staging_ingest_run {
        bigint ingest_run_id PK
        text source_id
        date source_date
    }

    iris_staging_parcel {
        bigint staging_parcel_id PK
        bigint ingest_run_id FK
        char country_code
        text parcel_id
        geometry geom
        timestamptz promoted_at
    }

    iris_core_source_run {
        bigint source_run_id PK
        text source_id
        date source_date
        text status
    }

    iris_core_parcel {
        char country_code PK
        text parcel_id PK
        text region_code
        geometry geom
        text source_id
        date source_date
    }

    iris_core_substation {
        char country_code PK
        text substation_id PK
        geometry geom
        text source_id
        date source_date
    }

    iris_core_peatland {
        char country_code PK
        text peatland_id PK
        text region_code
        geometry geom
        text representation
        text source_id
        date source_date
    }

    iris_core_screening_layer {
        char country_code PK
        text screening_layer_id PK
        text layer_code
        geometry geom
        bigint source_run_id FK
        text source_id
        date source_date
    }

    iris_core_evidence {
        char country_code PK
        text evidence_id PK
        text screening_layer_id FK
        text entity_type
        text entity_id
        bigint source_run_id FK
        text source_id
        date source_date
    }

    iris_staging_ingest_run ||--o{ iris_staging_parcel : "batches"
    iris_core_source_run ||--o{ iris_core_screening_layer : "produces"
    iris_core_source_run ||--o{ iris_core_evidence : "provenance"
    iris_core_screening_layer ||--o{ iris_core_evidence : "country_code + screening_layer_id"

    iris_core_evidence }o..o| iris_core_parcel : "entity_type=parcel (same country_code)"
    iris_core_evidence }o..o| iris_core_peatland : "entity_type=peatland (same country_code)"
    iris_core_evidence }o..o| iris_core_substation : "entity_type=substation (same country_code)"

    iris_staging_parcel }o..o| iris_core_parcel : "promote (application)"
```

**Notes**

- `evidence` → `parcel` / `peatland` / `substation` is enforced by trigger (not a polymorphic FK); joins use `country_code` + `entity_id`.
- `screening_layer` → business entities use spatial predicates at query time; `evidence` stores explainability links.
- All `geom` columns are EPSG:4326 (`MultiPolygon` for area features, `Point` for substations).
