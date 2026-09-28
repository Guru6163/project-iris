from pathlib import Path

import psycopg
import pytest

from tests.conftest import RESET_CORE_TABLES_SQL

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_RUN_SEED = PROJECT_ROOT / "seed" / "source_run.sql"
PARCEL_SEED = PROJECT_ROOT / "seed" / "parcel.sql"
PEATLAND_SEED = PROJECT_ROOT / "seed" / "peatland.sql"
VERIFY_QUERIES = PROJECT_ROOT / "queries" / "verify_peatland.sql"


@pytest.fixture
def seeded_peatland(migrated_database: str) -> str:
    source_sql = SOURCE_RUN_SEED.read_text(encoding="utf-8")
    parcel_sql = PARCEL_SEED.read_text(encoding="utf-8")
    peatland_sql = PEATLAND_SEED.read_text(encoding="utf-8")
    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            cur.execute(RESET_CORE_TABLES_SQL)
            cur.execute(source_sql)
            cur.execute(parcel_sql)
            cur.execute(peatland_sql)
        conn.commit()
    return migrated_database


def test_peatland_table_columns(migrated_database: str) -> None:
    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'iris_core'
                  AND table_name = 'peatland'
                ORDER BY ordinal_position;
                """
            )
            columns = [row[0] for row in cur.fetchall()]

    assert columns == [
        "country_code",
        "peatland_id",
        "region_code",
        "geom",
        "representation",
        "source_id",
        "source_date",
        "created_at",
    ]


def test_peatland_fixture_rows(seeded_peatland: str) -> None:
    with psycopg.connect(seeded_peatland) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT country_code, peatland_id, region_code, representation
                FROM iris_core.peatland
                ORDER BY country_code, peatland_id;
                """
            )
            rows = cur.fetchall()

    assert rows == [
        ("DE", "PL-FIXTURE-DE-001", "BY", "observed"),
        ("IN", "PL-FIXTURE-IN-001", "KA", "inferred"),
        ("US", "PL-FIXTURE-US-001", "VA", "observed"),
    ]


def test_verify_peatland_queries(seeded_peatland: str) -> None:
    assert VERIFY_QUERIES.is_file()

    with psycopg.connect(seeded_peatland) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT country_code, peatland_id, COUNT(*) AS row_count
                FROM iris_core.peatland
                GROUP BY country_code, peatland_id
                HAVING COUNT(*) > 1;
                """
            )
            assert cur.fetchall() == []

            cur.execute(
                """
                SELECT pl.country_code, pl.peatland_id, p.parcel_id
                FROM iris_core.peatland AS pl
                INNER JOIN iris_core.parcel AS p
                    ON p.country_code = pl.country_code
                   AND ST_Intersects(pl.geom, p.geom)
                WHERE pl.country_code = 'IN'
                ORDER BY pl.peatland_id, p.parcel_id;
                """
            )
            overlaps = cur.fetchall()

            cur.execute(
                """
                SELECT pl.country_code, pl.peatland_id, pl.representation,
                       r.source_run_id, r.status
                FROM iris_core.peatland AS pl
                INNER JOIN iris_core.source_run AS r
                    ON r.source_id = pl.source_id
                   AND r.source_date = pl.source_date
                ORDER BY pl.country_code, pl.peatland_id;
                """
            )
            provenance = cur.fetchall()

    assert overlaps == [("IN", "PL-FIXTURE-IN-001", "P-FIXTURE-IN-001")]
    assert len(provenance) == 3
    assert all(row[3] == 1 and row[4] == "succeeded" for row in provenance)
