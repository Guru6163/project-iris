from pathlib import Path

import psycopg
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_RUN_SEED = PROJECT_ROOT / "seed" / "source_run.sql"
PARCEL_SEED = PROJECT_ROOT / "seed" / "parcel.sql"
VERIFY_QUERIES = PROJECT_ROOT / "queries" / "verify_parcel.sql"


@pytest.fixture
def seeded_parcel(migrated_database: str) -> str:
    source_sql = SOURCE_RUN_SEED.read_text(encoding="utf-8")
    parcel_sql = PARCEL_SEED.read_text(encoding="utf-8")
    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE iris_core.parcel;")
            cur.execute("TRUNCATE iris_core.source_run RESTART IDENTITY;")
            cur.execute(source_sql)
            cur.execute(parcel_sql)
        conn.commit()
    return migrated_database


def test_parcel_table_columns(migrated_database: str) -> None:
    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'iris_core'
                  AND table_name = 'parcel'
                ORDER BY ordinal_position;
                """
            )
            columns = [row[0] for row in cur.fetchall()]

    assert columns == [
        "country_code",
        "parcel_id",
        "region_code",
        "geom",
        "source_id",
        "source_date",
        "created_at",
    ]


def test_parcel_fixture_row(seeded_parcel: str) -> None:
    with psycopg.connect(seeded_parcel) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT country_code, parcel_id, region_code, source_id, source_date::text
                FROM iris_core.parcel
                WHERE country_code = 'IN' AND parcel_id = 'P-FIXTURE-001';
                """
            )
            row = cur.fetchone()

    assert row == ("IN", "P-FIXTURE-001", "KA", "fixture_vendor_a", "2024-06-15")


def test_parcel_country_code_not_null(seeded_parcel: str) -> None:
    with psycopg.connect(seeded_parcel) as conn:
        with conn.cursor() as cur:
            with pytest.raises(psycopg.Error):
                cur.execute(
                    """
                    INSERT INTO iris_core.parcel (
                        country_code, parcel_id, region_code, geom,
                        source_id, source_date
                    ) VALUES (
                        NULL, 'bad', 'KA',
                        ST_Multi(ST_GeomFromText('POLYGON((0 0,1 0,1 1,0 1,0 0))', 4326)),
                        'fixture_vendor_a', DATE '2024-06-15'
                    );
                    """
                )


def test_verify_parcel_queries(seeded_parcel: str) -> None:
    assert VERIFY_QUERIES.is_file()

    with psycopg.connect(seeded_parcel) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM iris_core.parcel;")
            assert cur.fetchone()[0] == 1

            cur.execute(
                "SELECT COUNT(*) FROM iris_core.parcel WHERE country_code IS NULL;"
            )
            assert cur.fetchone()[0] == 0

            cur.execute(
                """
                SELECT country_code, parcel_id
                FROM iris_core.parcel
                WHERE ST_Contains(
                    geom,
                    ST_SetSRID(ST_MakePoint(77.5905, 12.9705), 4326)
                );
                """
            )
            spatial = cur.fetchall()

    assert spatial == [("IN", "P-FIXTURE-001")]
