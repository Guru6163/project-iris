-- Staged parcel load (not yet in iris_core until promotion).
INSERT INTO iris_staging.ingest_run (
    ingest_run_id,
    source_id,
    source_date,
    record_format,
    created_at
) VALUES (
    1,
    'staging_vendor_b',
    DATE '2024-07-01',
    'parcel_v1',
    TIMESTAMPTZ '2024-07-01 09:00:00+00'
)
ON CONFLICT (ingest_run_id) DO NOTHING;

SELECT setval(
    pg_get_serial_sequence('iris_staging.ingest_run', 'ingest_run_id'),
    (SELECT COALESCE(MAX(ingest_run_id), 1) FROM iris_staging.ingest_run)
);

INSERT INTO iris_staging.parcel (
    ingest_run_id,
    country_code,
    parcel_id,
    region_code,
    geom,
    promoted_at,
    created_at
) VALUES (
    1,
    'IN',
    'P-STAGING-001',
    'KA',
    ST_Multi(
        ST_GeomFromText(
            'POLYGON((77.5920 12.9720, 77.5930 12.9720, 77.5930 12.9730, 77.5920 12.9730, 77.5920 12.9720))',
            4326
        )
    ),
    NULL,
    TIMESTAMPTZ '2024-07-01 09:00:00+00'
)
ON CONFLICT (ingest_run_id, country_code, parcel_id) DO NOTHING;
