-- Derived screening geometries produced by a source run (WGS 84).

CREATE TABLE iris_core.screening_layer (
    country_code CHAR(2) NOT NULL,
    screening_layer_id TEXT NOT NULL,
    layer_code TEXT NOT NULL,
    geom geometry(MultiPolygon, 4326) NOT NULL,
    source_run_id BIGINT NOT NULL,
    source_id TEXT NOT NULL,
    source_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT screening_layer_pkey PRIMARY KEY (country_code, screening_layer_id),
    CONSTRAINT screening_layer_country_code_format_check
        CHECK (country_code ~ '^[A-Z]{2}$'),
    CONSTRAINT screening_layer_geom_srid_check
        CHECK (ST_SRID(geom) = 4326),
    CONSTRAINT screening_layer_source_run_fkey
        FOREIGN KEY (source_run_id)
        REFERENCES iris_core.source_run (source_run_id)
);

CREATE INDEX screening_layer_geom_gix ON iris_core.screening_layer USING GIST (geom);
CREATE INDEX screening_layer_source_run_idx ON iris_core.screening_layer (source_run_id);

COMMENT ON TABLE iris_core.screening_layer IS
    'Derived screening footprints from a source run; geom in EPSG:4326 (WGS 84).';
COMMENT ON COLUMN iris_core.screening_layer.layer_code IS
    'Screening rule/output label (e.g. peatland overlap); not a foreign key to business entities.';
COMMENT ON COLUMN iris_core.screening_layer.source_run_id IS
    'Run that produced this layer; source_id/source_date mirror the run for IRIS provenance.';
