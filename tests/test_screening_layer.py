from pathlib import Path

import psycopg
import pytest

from tests.conftest import RESET_CORE_TABLES_SQL

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_RUN_SEED = PROJECT_ROOT / "seed" / "source_run.sql"
PARCEL_SEED = PROJECT_ROOT / "seed" / "parcel.sql"
SCREENING_SEED = PROJECT_ROOT / "seed" / "screening_layer.sql"
VERIFY_QUERIES = PROJECT_ROOT / "queries" / "verify_screening_layer.sql"


@pytest.fixture
def seeded_screening_layer(migrated_database: str) -> str:
    source_sql = SOURCE_RUN_SEED.read_text(encoding="utf-8")
    parcel_sql = PARCEL_SEED.read_text(encoding="utf-8")
    screening_sql = SCREENING_SEED.read_text(encoding="utf-8")
    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            cur.execute(RESET_CORE_TABLES_SQL)
            cur.execute(source_sql)
            cur.execute(parcel_sql)
            cur.execute(screening_sql)
        conn.commit()
    return migrated_database


def test_screening_layer_table_columns(migrated_database: str) -> None:
    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'iris_core'
                  AND table_name = 'screening_layer'
                ORDER BY ordinal_position;
                """
            )
            columns = [row[0] for row in cur.fetchall()]

    assert columns == [
        "country_code",
        "screening_layer_id",
        "layer_code",
        "geom",
        "source_run_id",
        "source_id",
        "source_date",
        "created_at",
    ]


def test_screening_layer_fixture_rows(seeded_screening_layer: str) -> None:
    with psycopg.connect(seeded_screening_layer) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT country_code, screening_layer_id, layer_code, source_run_id
                FROM iris_core.screening_layer
                ORDER BY screening_layer_id;
                """
            )
            rows = cur.fetchall()

    assert rows == [
        ("IN", "SL-FIXTURE-IN-BESS-001", "SUBSTATION_PROXIMITY", 1),
        ("IN", "SL-FIXTURE-IN-PEAT-001", "PEATLAND_PARCEL_OVERLAP", 1),
    ]


def test_verify_screening_layer_queries(seeded_screening_layer: str) -> None:
    assert VERIFY_QUERIES.is_file()

    with psycopg.connect(seeded_screening_layer) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT sl.screening_layer_id, sl.layer_code, r.source_run_id, r.status
                FROM iris_core.screening_layer AS sl
                INNER JOIN iris_core.source_run AS r
                    ON r.source_run_id = sl.source_run_id
                ORDER BY sl.screening_layer_id;
                """
            )
            runs = cur.fetchall()

            cur.execute(
                """
                SELECT sl.screening_layer_id, p.parcel_id
                FROM iris_core.screening_layer AS sl
                INNER JOIN iris_core.parcel AS p
                    ON p.country_code = sl.country_code
                   AND ST_Intersects(sl.geom, p.geom)
                WHERE sl.layer_code = 'PEATLAND_PARCEL_OVERLAP'
                ORDER BY sl.screening_layer_id, p.parcel_id;
                """
            )
            spatial = cur.fetchall()

    assert runs == [
        ("SL-FIXTURE-IN-BESS-001", "SUBSTATION_PROXIMITY", 1, "succeeded"),
        ("SL-FIXTURE-IN-PEAT-001", "PEATLAND_PARCEL_OVERLAP", 1, "succeeded"),
    ]
    assert spatial == [("SL-FIXTURE-IN-PEAT-001", "P-FIXTURE-001")]
