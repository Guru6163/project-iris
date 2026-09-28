-- Deterministic substations across countries (matches seed/source_run.sql provenance).
INSERT INTO iris_core.substation (
    country_code,
    substation_id,
    geom,
    source_id,
    source_date,
    created_at
) VALUES
    (
        'IN',
        'S-FIXTURE-IN-001',
        ST_SetSRID(ST_MakePoint(77.5910, 12.9705), 4326),
        'fixture_vendor_a',
        DATE '2024-06-15',
        TIMESTAMPTZ '2024-06-15 10:05:00+00'
    ),
    (
        'DE',
        'S-FIXTURE-DE-001',
        ST_SetSRID(ST_MakePoint(13.4050, 52.5200), 4326),
        'fixture_vendor_a',
        DATE '2024-06-15',
        TIMESTAMPTZ '2024-06-15 10:05:00+00'
    ),
    (
        'US',
        'S-FIXTURE-US-001',
        ST_SetSRID(ST_MakePoint(-77.0365, 38.8977), 4326),
        'fixture_vendor_a',
        DATE '2024-06-15',
        TIMESTAMPTZ '2024-06-15 10:05:00+00'
    )
ON CONFLICT (country_code, substation_id) DO NOTHING;
