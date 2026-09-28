-- Traceability from screening outputs back to source runs and input entities.

CREATE TABLE iris_core.evidence (
    country_code CHAR(2) NOT NULL,
    evidence_id TEXT NOT NULL,
    screening_layer_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    source_run_id BIGINT NOT NULL,
    source_id TEXT NOT NULL,
    source_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT evidence_pkey PRIMARY KEY (country_code, evidence_id),
    CONSTRAINT evidence_country_code_format_check
        CHECK (country_code ~ '^[A-Z]{2}$'),
    CONSTRAINT evidence_entity_type_check
        CHECK (entity_type IN ('parcel', 'peatland', 'substation')),
    CONSTRAINT evidence_screening_layer_fkey
        FOREIGN KEY (country_code, screening_layer_id)
        REFERENCES iris_core.screening_layer (country_code, screening_layer_id),
    CONSTRAINT evidence_source_run_fkey
        FOREIGN KEY (source_run_id)
        REFERENCES iris_core.source_run (source_run_id)
);

CREATE INDEX evidence_screening_layer_idx
    ON iris_core.evidence (country_code, screening_layer_id);
CREATE INDEX evidence_entity_idx
    ON iris_core.evidence (country_code, entity_type, entity_id);
CREATE INDEX evidence_source_run_idx ON iris_core.evidence (source_run_id);

COMMENT ON TABLE iris_core.evidence IS
    'Links a screening layer to country-scoped input entities for explainable results.';
COMMENT ON COLUMN iris_core.evidence.entity_type IS
    'Business entity kind; entity_id is interpreted with country_code (parcel_id, peatland_id, or substation_id).';
COMMENT ON COLUMN iris_core.evidence.source_run_id IS
    'Source run that produced the screening outcome recorded by this evidence row.';
