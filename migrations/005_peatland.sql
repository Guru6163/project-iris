-- Peatland polygons for inference / overlap screening (WGS 84).

CREATE TABLE iris_core.peatland (
    country_code CHAR(2) NOT NULL,
    peatland_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    geom geometry(MultiPolygon, 4326) NOT NULL,
    representation TEXT NOT NULL,
    source_id TEXT NOT NULL,
    source_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT peatland_pkey PRIMARY KEY (country_code, peatland_id),
    CONSTRAINT peatland_country_code_format_check
        CHECK (country_code ~ '^[A-Z]{2}$'),
    CONSTRAINT peatland_geom_srid_check
        CHECK (ST_SRID(geom) = 4326),
    CONSTRAINT peatland_representation_check
        CHECK (representation IN ('observed', 'inferred'))
);

CREATE INDEX peatland_geom_gix ON iris_core.peatland USING GIST (geom);

COMMENT ON TABLE iris_core.peatland IS
    'Country-scoped peatland footprints; geom stored in EPSG:4326 (WGS 84).';
COMMENT ON COLUMN iris_core.peatland.geom IS
    'Peatland extent as MultiPolygon, SRID 4326 (degrees).';
COMMENT ON COLUMN iris_core.peatland.representation IS
    'Whether the footprint is directly observed or model-inferred; supports screening without storing scientific uncertainty metrics.';
