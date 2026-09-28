-- Core parcel entity (country-scoped identifier, WGS 84 geometry).

CREATE TABLE iris_core.parcel (
    country_code CHAR(2) NOT NULL,
    parcel_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    geom geometry(MultiPolygon, 4326) NOT NULL,
    source_id TEXT NOT NULL,
    source_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT parcel_pkey PRIMARY KEY (country_code, parcel_id),
    CONSTRAINT parcel_country_code_format_check
        CHECK (country_code ~ '^[A-Z]{2}$'),
    CONSTRAINT parcel_geom_srid_check
        CHECK (ST_SRID(geom) = 4326)
);

CREATE INDEX parcel_geom_gix ON iris_core.parcel USING GIST (geom);

COMMENT ON TABLE iris_core.parcel IS
    'Country-scoped land parcels; geom stored in EPSG:4326 (WGS 84).';
COMMENT ON COLUMN iris_core.parcel.geom IS
    'Parcel boundary as MultiPolygon, SRID 4326 (degrees).';
