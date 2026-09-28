-- Derived screening footprints (source_run_id = 1).
INSERT INTO iris_core.screening_layer (
    country_code, screening_layer_id, layer_code, geom,
    source_run_id, source_id, source_date, created_at
) VALUES
    (
        'IN', 'SL-FIXTURE-IN-PEAT-001', 'PEATLAND_PARCEL_OVERLAP',
        ST_Multi(ST_GeomFromText(
            'POLYGON((77.5900 12.9700, 77.5910 12.9700, 77.5910 12.9710, 77.5900 12.9710, 77.5900 12.9700))', 4326)),
        1, 'fixture_vendor_a', DATE '2024-06-15', TIMESTAMPTZ '2024-06-15 10:06:00+00'
    ),
    (
        'IN', 'SL-FIXTURE-IN-BESS-001', 'SUBSTATION_PROXIMITY',
        ST_Multi(ST_GeomFromText(
            'POLYGON((77.5908 12.9702, 77.5912 12.9702, 77.5912 12.9708, 77.5908 12.9708, 77.5908 12.9702))', 4326)),
        1, 'fixture_vendor_a', DATE '2024-06-15', TIMESTAMPTZ '2024-06-15 10:06:00+00'
    ),
    (
        'DE', 'SL-FIXTURE-DE-BESS-001', 'SUBSTATION_PROXIMITY',
        ST_Multi(ST_GeomFromText(
            'POLYGON((13.4045 52.5195, 13.4055 52.5195, 13.4055 52.5205, 13.4045 52.5205, 13.4045 52.5195))', 4326)),
        1, 'fixture_vendor_a', DATE '2024-06-15', TIMESTAMPTZ '2024-06-15 10:06:00+00'
    ),
    (
        'US', 'SL-FIXTURE-US-PEAT-001', 'PEATLAND_PARCEL_OVERLAP',
        ST_Multi(ST_GeomFromText(
            'POLYGON((-77.0380 38.8965, -77.0350 38.8965, -77.0350 38.8990, -77.0380 38.8990, -77.0380 38.8965))', 4326)),
        1, 'fixture_vendor_a', DATE '2024-06-15', TIMESTAMPTZ '2024-06-15 10:06:00+00'
    )
ON CONFLICT (country_code, screening_layer_id) DO NOTHING;
