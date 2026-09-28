-- Deterministic sample parcel (matches seed/source_run.sql provenance).
INSERT INTO iris_core.parcel (
    country_code,
    parcel_id,
    region_code,
    geom,
    source_id,
    source_date,
    created_at
) VALUES (
    'IN',
    'P-FIXTURE-001',
    'KA',
    ST_Multi(
        ST_GeomFromText(
            'POLYGON((77.5900 12.9700, 77.5910 12.9700, 77.5910 12.9710, 77.5900 12.9710, 77.5900 12.9700))',
            4326
        )
    ),
    'fixture_vendor_a',
    DATE '2024-06-15',
    TIMESTAMPTZ '2024-06-15 10:05:00+00'
)
ON CONFLICT (country_code, parcel_id) DO NOTHING;
