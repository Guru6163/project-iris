-- Deterministic peatland fixtures (matches seed/source_run.sql provenance).
INSERT INTO iris_core.peatland (
    country_code,
    peatland_id,
    region_code,
    geom,
    representation,
    source_id,
    source_date,
    created_at
) VALUES
    (
        'IN',
        'PL-FIXTURE-IN-001',
        'KA',
        ST_Multi(
            ST_GeomFromText(
                'POLYGON((77.5895 12.9695, 77.5915 12.9695, 77.5915 12.9715, 77.5895 12.9715, 77.5895 12.9695))',
                4326
            )
        ),
        'inferred',
        'fixture_vendor_a',
        DATE '2024-06-15',
        TIMESTAMPTZ '2024-06-15 10:05:00+00'
    ),
    (
        'FI',
        'PL-FIXTURE-FI-001',
        '19',
        ST_Multi(
            ST_GeomFromText(
                'POLYGON((24.9350 60.1690, 24.9450 60.1690, 24.9450 60.1750, 24.9350 60.1750, 24.9350 60.1690))',
                4326
            )
        ),
        'observed',
        'fixture_vendor_a',
        DATE '2024-06-15',
        TIMESTAMPTZ '2024-06-15 10:05:00+00'
    )
ON CONFLICT (country_code, peatland_id) DO NOTHING;
