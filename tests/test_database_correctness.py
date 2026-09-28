"""
High-risk database correctness checks (evaluation rubric).

Maps to: schemas, tables, geom/SRID, country_code, uniqueness, relationships,
spatial results, GiST indexes, and idempotent seeds.
"""

import psycopg
import pytest

from iris.seed_data import load_seeds
from tests.conftest import RESET_CORE_TABLES_SQL

IRIS_SCHEMAS = ("iris_core", "iris_staging")

CORE_TABLES = (
    "source_run",
    "parcel",
    "substation",
    "peatland",
    "screening_layer",
    "evidence",
)

STAGING_TABLES = ("ingest_run", "parcel")

COUNTRY_SCOPED_TABLES = (
    "parcel",
    "substation",
    "peatland",
    "screening_layer",
    "evidence",
)

GEOM_EXPECTATIONS = {
    "parcel": ("MULTIPOLYGON", 4326),
    "substation": ("POINT", 4326),
    "peatland": ("MULTIPOLYGON", 4326),
    "screening_layer": ("MULTIPOLYGON", 4326),
}

GIST_INDEXES = {
    "parcel_geom_gix",
    "substation_geom_gix",
    "peatland_geom_gix",
    "screening_layer_geom_gix",
}

MIN_POLYGON = "ST_Multi(ST_GeomFromText('POLYGON((0 0,1 0,1 1,0 1,0 0))', 4326))"


@pytest.fixture
def seeded_core(migrated_database: str) -> str:
    load_seeds(migrated_database, include_staging=False)
    return migrated_database


def test_rubric_01_schemas_exist(migrated_database: str) -> None:
    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name = ANY(%s)
                ORDER BY schema_name;
                """,
                (list(IRIS_SCHEMAS),),
            )
            names = [row[0] for row in cur.fetchall()]
    assert names == list(IRIS_SCHEMAS)


def test_rubric_02_required_tables_exist(migrated_database: str) -> None:
    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema IN ('iris_core', 'iris_staging')
                  AND table_type = 'BASE TABLE'
                ORDER BY table_schema, table_name;
                """
            )
            rows = {(schema, table) for schema, table in cur.fetchall()}

    for table in CORE_TABLES:
        assert ("iris_core", table) in rows
    for table in STAGING_TABLES:
        assert ("iris_staging", table) in rows


def test_rubric_03_geom_type_and_srid(migrated_database: str) -> None:
    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    f_table_name,
                    type,
                    srid
                FROM geometry_columns
                WHERE f_table_schema = 'iris_core'
                  AND f_geometry_column = 'geom'
                ORDER BY f_table_name;
                """
            )
            actual = {name: (geom_type, srid) for name, geom_type, srid in cur.fetchall()}

    assert actual == GEOM_EXPECTATIONS


def test_rubric_04_country_code_not_null(migrated_database: str) -> None:
    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            for table in COUNTRY_SCOPED_TABLES:
                cur.execute(
                    """
                    SELECT is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'iris_core'
                      AND table_name = %s
                      AND column_name = 'country_code';
                    """,
                    (table,),
                )
                row = cur.fetchone()
                assert row is not None
                assert row[0] == "NO"


def test_rubric_05_country_scoped_uniqueness(migrated_database: str) -> None:
    shared_id = "RUBRIC-SHARED-PARCEL"
    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            cur.execute(RESET_CORE_TABLES_SQL)
            cur.execute(
                f"""
                INSERT INTO iris_core.parcel (
                    country_code, parcel_id, region_code, geom, source_id, source_date
                ) VALUES
                    ('IN', %s, 'KA', {MIN_POLYGON}, 'vendor', DATE '2024-01-01'),
                    ('US', %s, 'VA', {MIN_POLYGON}, 'vendor', DATE '2024-01-01');
                """,
                (shared_id, shared_id),
            )
            with pytest.raises(psycopg.errors.UniqueViolation):
                cur.execute(
                    f"""
                    INSERT INTO iris_core.parcel (
                        country_code, parcel_id, region_code, geom, source_id, source_date
                    ) VALUES ('IN', %s, 'KA', {MIN_POLYGON}, 'vendor', DATE '2024-01-01');
                    """,
                    (shared_id,),
                )
        conn.rollback()


def test_rubric_06_country_scoped_relationships(migrated_database: str) -> None:
    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            cur.execute(RESET_CORE_TABLES_SQL)
            cur.execute(
                "INSERT INTO iris_core.source_run (source_id, source_date, status) "
                "VALUES ('vendor', DATE '2024-01-01', 'succeeded') RETURNING source_run_id;"
            )
            run_id = cur.fetchone()[0]
            cur.execute(
                f"""
                INSERT INTO iris_core.screening_layer (
                    country_code, screening_layer_id, layer_code, geom,
                    source_run_id, source_id, source_date
                ) VALUES (
                    'IN', 'SL-RUBRIC', 'TEST', {MIN_POLYGON}, %s, 'vendor', DATE '2024-01-01'
                );
                """,
                (run_id,),
            )
            with pytest.raises(psycopg.Error, match="parcel .* not found for country IN"):
                cur.execute(
                    """
                    INSERT INTO iris_core.evidence (
                        country_code, evidence_id, screening_layer_id, entity_type,
                        entity_id, source_run_id, source_id, source_date
                    ) VALUES (
                        'IN', 'EV-RUBRIC', 'SL-RUBRIC', 'parcel', 'MISSING-PARCEL',
                        %s, 'vendor', DATE '2024-01-01'
                    );
                    """,
                    (run_id,),
                )
        conn.rollback()


def test_rubric_07_spatial_queries_return_fixture_records(seeded_core: str) -> None:
    with psycopg.connect(seeded_core) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT p.parcel_id
                FROM iris_core.peatland AS pl
                INNER JOIN iris_core.parcel AS p
                    ON p.country_code = pl.country_code
                   AND ST_Intersects(pl.geom, p.geom)
                WHERE pl.country_code = 'IN' AND pl.peatland_id = 'PL-FIXTURE-IN-001';
                """
            )
            peat_hits = cur.fetchall()

            cur.execute(
                """
                SELECT s.substation_id
                FROM iris_core.substation AS s
                WHERE s.country_code = 'IN'
                  AND s.geom && ST_Expand(ST_SetSRID(ST_MakePoint(77.5905, 12.9705), 4326), 0.045)
                  AND ST_DWithin(
                      s.geom::geography,
                      ST_SetSRID(ST_MakePoint(77.5905, 12.9705), 4326)::geography,
                      5000
                  );
                """
            )
            bess_hits = cur.fetchall()

    assert peat_hits == [("P-FIXTURE-IN-001",)]
    assert bess_hits == [("S-FIXTURE-IN-001",)]


def test_rubric_08_spatial_gist_indexes_exist(migrated_database: str) -> None:
    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = 'iris_core'
                  AND indexdef ILIKE '%USING gist%';
                """
            )
            names = {row[0] for row in cur.fetchall()}
    assert GIST_INDEXES <= names


def test_rubric_09_seed_load_idempotent(migrated_database: str) -> None:
    load_seeds(migrated_database, include_staging=True)
    first = _core_counts(migrated_database)
    load_seeds(migrated_database, include_staging=True)
    second = _core_counts(migrated_database)
    assert first == second
    assert first["parcel"] == 3
    assert first["evidence"] == 7


def _core_counts(database_url: str) -> dict[str, int]:
    sql = {
        "parcel": "SELECT COUNT(*) FROM iris_core.parcel",
        "substation": "SELECT COUNT(*) FROM iris_core.substation",
        "peatland": "SELECT COUNT(*) FROM iris_core.peatland",
        "screening_layer": "SELECT COUNT(*) FROM iris_core.screening_layer",
        "evidence": "SELECT COUNT(*) FROM iris_core.evidence",
        "source_run": "SELECT COUNT(*) FROM iris_core.source_run",
    }
    counts: dict[str, int] = {}
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            for key, query in sql.items():
                cur.execute(query)
                counts[key] = cur.fetchone()[0]
    return counts
