-- Promote ingest_run_id = 1 staged parcels into iris_core (idempotent on parcel PK).
BEGIN;

WITH new_run AS (
    INSERT INTO iris_core.source_run (
        source_id,
        source_date,
        status,
        started_at,
        completed_at
    )
    SELECT
        ir.source_id,
        ir.source_date,
        'succeeded',
        ir.created_at,
        now()
    FROM iris_staging.ingest_run AS ir
    WHERE ir.ingest_run_id = 1
    RETURNING source_run_id, source_id, source_date
),
inserted AS (
    INSERT INTO iris_core.parcel (
        country_code,
        parcel_id,
        region_code,
        geom,
        source_id,
        source_date
    )
    SELECT
        sp.country_code,
        sp.parcel_id,
        sp.region_code,
        sp.geom,
        nr.source_id,
        nr.source_date
    FROM iris_staging.parcel AS sp
    CROSS JOIN new_run AS nr
    WHERE sp.ingest_run_id = 1
      AND sp.promoted_at IS NULL
    ON CONFLICT (country_code, parcel_id) DO NOTHING
    RETURNING country_code, parcel_id
)
UPDATE iris_staging.parcel AS sp
SET promoted_at = now()
WHERE sp.ingest_run_id = 1
  AND sp.promoted_at IS NULL
  AND EXISTS (SELECT 1 FROM inserted);

COMMIT;
