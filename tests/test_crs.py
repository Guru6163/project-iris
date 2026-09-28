import psycopg

CRS_ROUND_TRIP_SQL = """
WITH fixture AS (
    SELECT ST_Multi(
        ST_GeomFromText(
            'POLYGON((77.5900 12.9700, 77.5910 12.9700, 77.5910 12.9710, 77.5900 12.9710, 77.5900 12.9700))',
            4326
        )
    ) AS geom
),
metric AS (
    SELECT
        ST_SRID(geom) AS stored_srid,
        ST_SRID(ST_Transform(geom, 32643)) AS projected_srid,
        ST_Area(geom::geography) AS area_sq_m,
        ST_DWithin(
            ST_SetSRID(ST_MakePoint(77.5905, 12.9705), 4326)::geography,
            geom::geography,
            1000
        ) AS within_1km
    FROM fixture
)
SELECT stored_srid, projected_srid, area_sq_m, within_1km FROM metric;
"""


def test_crs_round_trip_and_metric_calculation(migrated_database: str) -> None:
    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            cur.execute(CRS_ROUND_TRIP_SQL)
            stored_srid, projected_srid, area_sq_m, within_1km = cur.fetchone()

            cur.execute(
                """
                SELECT conname
                FROM pg_constraint
                WHERE conrelid = 'iris_core.parcel'::regclass
                  AND conname = 'parcel_geom_srid_check';
                """
            )
            constraint = cur.fetchone()

    assert stored_srid == 4326
    assert projected_srid == 32643
    assert area_sq_m > 0
    assert within_1km is True
    assert constraint is not None
