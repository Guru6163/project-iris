-- Staging ingest metadata and parcel loads before promotion to iris_core.

CREATE TABLE iris_staging.ingest_run (
    ingest_run_id BIGSERIAL PRIMARY KEY,
    source_id TEXT NOT NULL,
    source_date DATE NOT NULL,
    record_format TEXT NOT NULL DEFAULT 'parcel_v1',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE iris_staging.parcel (
    staging_parcel_id BIGSERIAL PRIMARY KEY,
    ingest_run_id BIGINT NOT NULL,
    country_code CHAR(2) NOT NULL,
    parcel_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    geom geometry(MultiPolygon, 4326) NOT NULL,
    promoted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT staging_parcel_ingest_run_fkey
        FOREIGN KEY (ingest_run_id)
        REFERENCES iris_staging.ingest_run (ingest_run_id),
    CONSTRAINT staging_parcel_country_code_format_check
        CHECK (country_code ~ '^[A-Z]{2}$'),
    CONSTRAINT staging_parcel_geom_srid_check
        CHECK (ST_SRID(geom) = 4326),
    CONSTRAINT staging_parcel_ingest_country_id_uniq
        UNIQUE (ingest_run_id, country_code, parcel_id)
);

CREATE INDEX staging_parcel_ingest_run_idx
    ON iris_staging.parcel (ingest_run_id);
CREATE INDEX staging_parcel_unpromoted_idx
    ON iris_staging.parcel (ingest_run_id)
    WHERE promoted_at IS NULL;

COMMENT ON TABLE iris_staging.ingest_run IS
    'Batch metadata for a raw load into staging before core promotion.';
COMMENT ON TABLE iris_staging.parcel IS
    'Staged parcel rows; promoted into iris_core.parcel once validated.';
