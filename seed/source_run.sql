-- Deterministic sample row for local verification and tests.
INSERT INTO iris_core.source_run (
    source_run_id,
    source_id,
    source_date,
    status,
    started_at,
    completed_at,
    error_message,
    created_at
) VALUES (
    1,
    'fixture_vendor_a',
    DATE '2024-06-15',
    'succeeded',
    TIMESTAMPTZ '2024-06-15 10:00:00+00',
    TIMESTAMPTZ '2024-06-15 10:05:00+00',
    NULL,
    TIMESTAMPTZ '2024-06-15 10:00:00+00'
)
ON CONFLICT (source_run_id) DO NOTHING;

SELECT setval(
    pg_get_serial_sequence('iris_core.source_run', 'source_run_id'),
    (SELECT COALESCE(MAX(source_run_id), 1) FROM iris_core.source_run)
);
