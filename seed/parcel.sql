-- Country-scoped parcels (Bangalore, Berlin, northern Virginia).
INSERT INTO iris_core.parcel (
    country_code, parcel_id, region_code, geom, source_id, source_date, created_at
) VALUES
    (
        'IN', 'P-FIXTURE-IN-001', 'KA',
        ST_Multi(ST_GeomFromText(
            'POLYGON((77.5900 12.9700, 77.5910 12.9700, 77.5910 12.9710, 77.5900 12.9710, 77.5900 12.9700))', 4326)),
        'fixture_vendor_a', DATE '2024-06-15', TIMESTAMPTZ '2024-06-15 10:05:00+00'
    ),
    (
        'DE', 'P-FIXTURE-DE-001', 'BE',
        ST_Multi(ST_GeomFromText(
            'POLYGON((13.4040 52.5190, 13.4060 52.5190, 13.4060 52.5210, 13.4040 52.5210, 13.4040 52.5190))', 4326)),
        'fixture_vendor_a', DATE '2024-06-15', TIMESTAMPTZ '2024-06-15 10:05:00+00'
    ),
    (
        'US', 'P-FIXTURE-US-001', 'VA',
        ST_Multi(ST_GeomFromText(
            'POLYGON((-77.0380 38.8965, -77.0350 38.8965, -77.0350 38.8990, -77.0380 38.8990, -77.0380 38.8965))', 4326)),
        'fixture_vendor_a', DATE '2024-06-15', TIMESTAMPTZ '2024-06-15 10:05:00+00'
    )
ON CONFLICT (country_code, parcel_id) DO NOTHING;
