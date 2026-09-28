from pathlib import Path

import psycopg
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_RUN_SEED = PROJECT_ROOT / "seed" / "source_run.sql"
VERIFY_QUERIES = PROJECT_ROOT / "queries" / "verify_source_run.sql"


@pytest.fixture
def seeded_source_run(migrated_database: str) -> str:
    sql = SOURCE_RUN_SEED.read_text(encoding="utf-8")
    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE iris_core.source_run RESTART IDENTITY;")
            cur.execute(sql)
        conn.commit()
    return migrated_database


def test_source_run_table_columns(migrated_database: str) -> None:
    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'iris_core'
                  AND table_name = 'source_run'
                ORDER BY ordinal_position;
                """
            )
            columns = [row[0] for row in cur.fetchall()]

    assert columns == [
        "source_run_id",
        "source_id",
        "source_date",
        "status",
        "started_at",
        "completed_at",
        "error_message",
        "created_at",
    ]


def test_source_run_fixture_row(seeded_source_run: str) -> None:
    with psycopg.connect(seeded_source_run) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT source_run_id, source_id, source_date::text, status
                FROM iris_core.source_run
                WHERE source_run_id = 1;
                """
            )
            row = cur.fetchone()

    assert row == (1, "fixture_vendor_a", "2024-06-15", "succeeded")


def test_verify_source_run_queries(seeded_source_run: str) -> None:
    assert VERIFY_QUERIES.is_file()

    with psycopg.connect(seeded_source_run) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (source_id)
                    source_run_id,
                    source_id,
                    source_date,
                    status,
                    completed_at
                FROM iris_core.source_run
                WHERE status = 'succeeded'
                ORDER BY source_id, source_date DESC, source_run_id DESC;
                """
            )
            latest = cur.fetchall()
            cur.execute(
                """
                SELECT status, COUNT(*) AS run_count
                FROM iris_core.source_run
                GROUP BY status
                ORDER BY status;
                """
            )
            counts = cur.fetchall()

    assert len(latest) == 1
    assert latest[0][1] == "fixture_vendor_a"
    assert counts == [("succeeded", 1)]
