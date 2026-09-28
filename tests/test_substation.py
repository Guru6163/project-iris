from pathlib import Path

import psycopg
import pytest

from tests.conftest import RESET_CORE_TABLES_SQL

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_RUN_SEED = PROJECT_ROOT / "seed" / "source_run.sql"
SUBSTATION_SEED = PROJECT_ROOT / "seed" / "substation.sql"
VERIFY_QUERIES = PROJECT_ROOT / "queries" / "verify_substation.sql"


@pytest.fixture
def seeded_substation(migrated_database: str) -> str:
    source_sql = SOURCE_RUN_SEED.read_text(encoding="utf-8")
    substation_sql = SUBSTATION_SEED.read_text(encoding="utf-8")
    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            cur.execute(RESET_CORE_TABLES_SQL)
            cur.execute(source_sql)
            cur.execute(substation_sql)
        conn.commit()
    return migrated_database


def test_substation_table_columns(migrated_database: str) -> None:
    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'iris_core'
                  AND table_name = 'substation'
                ORDER BY ordinal_position;
                """
            )
            columns = [row[0] for row in cur.fetchall()]

    assert columns == [
        "country_code",
        "substation_id",
        "geom",
        "source_id",
        "source_date",
        "created_at",
    ]


def test_substation_fixture_countries(seeded_substation: str) -> None:
    with psycopg.connect(seeded_substation) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT country_code, substation_id
                FROM iris_core.substation
                ORDER BY country_code, substation_id;
                """
            )
            rows = cur.fetchall()

    assert rows == [
        ("DE", "S-FIXTURE-DE-001"),
        ("IN", "S-FIXTURE-IN-001"),
        ("US", "S-FIXTURE-US-001"),
    ]


def test_substation_country_scoped_uniqueness(seeded_substation: str) -> None:
    with psycopg.connect(seeded_substation) as conn:
        with conn.cursor() as cur:
            with pytest.raises(psycopg.errors.UniqueViolation):
                cur.execute(
                    """
                    INSERT INTO iris_core.substation (
                        country_code, substation_id, geom, source_id, source_date
                    ) VALUES (
                        'IN', 'S-FIXTURE-IN-001',
                        ST_SetSRID(ST_MakePoint(0, 0), 4326),
                        'fixture_vendor_a', DATE '2024-06-15'
                    );
                    """
                )


def test_verify_substation_queries(seeded_substation: str) -> None:
    assert VERIFY_QUERIES.is_file()

    with psycopg.connect(seeded_substation) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT country_code, substation_id, COUNT(*) AS row_count
                FROM iris_core.substation
                GROUP BY country_code, substation_id
                HAVING COUNT(*) > 1;
                """
            )
            assert cur.fetchall() == []

            cur.execute(
                """
                SELECT s.country_code, s.substation_id
                FROM iris_core.substation AS s
                WHERE s.country_code = 'IN'
                  AND ST_DWithin(
                      s.geom::geography,
                      ST_SetSRID(ST_MakePoint(77.5905, 12.9705), 4326)::geography,
                      5000
                  );
                """
            )
            nearby = cur.fetchall()

            cur.execute(
                """
                SELECT s.country_code, s.substation_id, r.source_run_id, r.status
                FROM iris_core.substation AS s
                INNER JOIN iris_core.source_run AS r
                    ON r.source_id = s.source_id
                   AND r.source_date = s.source_date
                ORDER BY s.country_code, s.substation_id;
                """
            )
            provenance = cur.fetchall()

    assert nearby == [("IN", "S-FIXTURE-IN-001")]
    assert len(provenance) == 3
    assert all(row[2] == 1 and row[3] == "succeeded" for row in provenance)
