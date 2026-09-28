-- Evidence rows for fixture screening layers (source_run_id = 1).
INSERT INTO iris_core.evidence (
    country_code,
    evidence_id,
    screening_layer_id,
    entity_type,
    entity_id,
    source_run_id,
    source_id,
    source_date,
    created_at
) VALUES
    (
        'IN',
        'EV-FIXTURE-IN-001',
        'SL-FIXTURE-IN-PEAT-001',
        'parcel',
        'P-FIXTURE-001',
        1,
        'fixture_vendor_a',
        DATE '2024-06-15',
        TIMESTAMPTZ '2024-06-15 10:07:00+00'
    ),
    (
        'IN',
        'EV-FIXTURE-IN-002',
        'SL-FIXTURE-IN-PEAT-001',
        'peatland',
        'PL-FIXTURE-IN-001',
        1,
        'fixture_vendor_a',
        DATE '2024-06-15',
        TIMESTAMPTZ '2024-06-15 10:07:00+00'
    ),
    (
        'IN',
        'EV-FIXTURE-IN-003',
        'SL-FIXTURE-IN-BESS-001',
        'substation',
        'S-FIXTURE-IN-001',
        1,
        'fixture_vendor_a',
        DATE '2024-06-15',
        TIMESTAMPTZ '2024-06-15 10:07:00+00'
    )
ON CONFLICT (country_code, evidence_id) DO NOTHING;
