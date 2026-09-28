-- Peatland footprints: IN overlaps parcel; DE/US in separate regions/sites.
INSERT INTO iris_core.peatland (
    country_code, peatland_id, region_code, geom, representation,
    source_id, source_date, created_at
) VALUES
    (
        'IN', 'PL-FIXTURE-IN-001', 'KA',
        ST_Multi(ST_GeomFromText(
            'POLYGON((77.5895 12.9695, 77.5915 12.9695, 77.5915 12.9715, 77.5895 12.9715, 77.5895 12.9695))', 4326)),
        'inferred',
        'fixture_vendor_a', DATE '2024-06-15', TIMESTAMPTZ '2024-06-15 10:05:00+00'
    ),
    (
        'DE', 'PL-FIXTURE-DE-001', 'BY',
        ST_Multi(ST_GeomFromText(
            'POLYGON((11.5700 48.1300, 11.5800 48.1300, 11.5800 48.1400, 11.5700 48.1400, 11.5700 48.1300))', 4326)),
        'observed',
        'fixture_vendor_a', DATE '2024-06-15', TIMESTAMPTZ '2024-06-15 10:05:00+00'
    ),
    (
        'US', 'PL-FIXTURE-US-001', 'VA',
        ST_Multi(ST_GeomFromText(
            'POLYGON((-77.0390 38.8960, -77.0340 38.8960, -77.0340 38.8995, -77.0390 38.8995, -77.0390 38.8960))', 4326)),
        'observed',
        'fixture_vendor_a', DATE '2024-06-15', TIMESTAMPTZ '2024-06-15 10:05:00+00'
    )
ON CONFLICT (country_code, peatland_id) DO NOTHING;
