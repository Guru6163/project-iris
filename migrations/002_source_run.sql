-- Track ingestion runs in core. Staging tables will reference source_run_id when added.

CREATE TABLE iris_core.source_run (
    source_run_id BIGSERIAL PRIMARY KEY,
    source_id TEXT NOT NULL,
    source_date DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT source_run_status_check
        CHECK (status IN ('pending', 'running', 'succeeded', 'failed')),
    CONSTRAINT source_run_completed_after_started
        CHECK (completed_at IS NULL OR completed_at >= started_at)
);

CREATE INDEX source_run_source_lookup_idx
    ON iris_core.source_run (source_id, source_date DESC);

COMMENT ON TABLE iris_core.source_run IS
    'One row per source ingestion run (provenance and execution outcome).';
