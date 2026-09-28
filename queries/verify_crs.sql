-- CRS round-trip and metric checks (EPSG:4326 storage; on-the-fly transform / geography).
\set ON_ERROR_STOP on

WITH fixture AS (
    SELECT ST_Multi(
        ST_GeomFromText(
            'POLYGON((77.5900 12.9700, 77.5910 12.9700, 77.5910 12.9710, 77.5900 12.9710, 77.5900 12.9700))',
            4326
        )
    ) AS geom
),
round_trip AS (
    SELECT
        geom,
        ST_SRID(geom) AS stored_srid,
        ST_AsEWKT(geom) AS stored_ewkt
    FROM fixture
),
metric AS (
    SELECT
        rt.geom,
        rt.stored_srid,
        ST_Transform(rt.geom, 32643) AS geom_utm43n,
        ST_SRID(ST_Transform(rt.geom, 32643)) AS projected_srid,
        ST_Area(rt.geom::geography) AS area_sq_m_geography,
        ST_DWithin(
            ST_SetSRID(ST_MakePoint(77.5905, 12.9705), 4326)::geography,
            rt.geom::geography,
            1000
        ) AS site_point_within_1km
    FROM round_trip AS rt
)
SELECT
    stored_srid,
    stored_srid = 4326 AS storage_srid_ok,
    projected_srid,
    projected_srid = 32643 AS transform_srid_ok,
    area_sq_m_geography > 0 AS area_positive,
    site_point_within_1km
FROM metric;
