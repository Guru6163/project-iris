-- Electrical substations for proximity / BESS screening (WGS 84 point locations).

CREATE TABLE iris_core.substation (
    country_code CHAR(2) NOT NULL,
    substation_id TEXT NOT NULL,
    geom geometry(Point, 4326) NOT NULL,
    source_id TEXT NOT NULL,
    source_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT substation_pkey PRIMARY KEY (country_code, substation_id),
    CONSTRAINT substation_country_code_format_check
        CHECK (country_code ~ '^[A-Z]{2}$'),
    CONSTRAINT substation_geom_srid_check
        CHECK (ST_SRID(geom) = 4326)
);

CREATE INDEX substation_geom_gix ON iris_core.substation USING GIST (geom);

COMMENT ON TABLE iris_core.substation IS
    'Country-scoped substation locations; geom stored in EPSG:4326 (WGS 84).';
COMMENT ON COLUMN iris_core.substation.geom IS
    'Substation site as Point, SRID 4326 (degrees).';
