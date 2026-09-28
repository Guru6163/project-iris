from pathlib import Path

import psycopg
import pytest

from tests.conftest import RESET_CORE_TABLES_SQL

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_RUN_SEED = PROJECT_ROOT / "seed" / "source_run.sql"
PARCEL_SEED = PROJECT_ROOT / "seed" / "parcel.sql"
PEATLAND_SEED = PROJECT_ROOT / "seed" / "peatland.sql"
SUBSTATION_SEED = PROJECT_ROOT / "seed" / "substation.sql"
SCREENING_SEED = PROJECT_ROOT / "seed" / "screening_layer.sql"
EVIDENCE_SEED = PROJECT_ROOT / "seed" / "evidence.sql"
VERIFY_QUERIES = PROJECT_ROOT / "queries" / "verify_evidence.sql"


@pytest.fixture
def seeded_evidence(migrated_database: str) -> str:
    seeds = (
        SOURCE_RUN_SEED,
        PARCEL_SEED,
        PEATLAND_SEED,
        SUBSTATION_SEED,
        SCREENING_SEED,
        EVIDENCE_SEED,
    )
    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            cur.execute(RESET_CORE_TABLES_SQL)
            for path in seeds:
                cur.execute(path.read_text(encoding="utf-8"))
        conn.commit()
    return migrated_database


def test_evidence_table_columns(migrated_database: str) -> None:
    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'iris_core'
                  AND table_name = 'evidence'
                ORDER BY ordinal_position;
                """
            )
            columns = [row[0] for row in cur.fetchall()]

    assert columns == [
        "country_code",
        "evidence_id",
        "screening_layer_id",
        "entity_type",
        "entity_id",
        "source_run_id",
        "source_id",
        "source_date",
        "created_at",
    ]


def test_evidence_fixture_rows(seeded_evidence: str) -> None:
    with psycopg.connect(seeded_evidence) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT evidence_id, screening_layer_id, entity_type, entity_id
                FROM iris_core.evidence
                ORDER BY evidence_id;
                """
            )
            rows = cur.fetchall()

    assert len(rows) == 7


def test_verify_evidence_traceability(seeded_evidence: str) -> None:
    assert VERIFY_QUERIES.is_file()

    with psycopg.connect(seeded_evidence) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT e.evidence_id, r.source_run_id, r.source_id, r.status
                FROM iris_core.evidence AS e
                INNER JOIN iris_core.source_run AS r
                    ON r.source_run_id = e.source_run_id
                ORDER BY e.evidence_id;
                """
            )
            source_trace = cur.fetchall()

            cur.execute(
                """
                SELECT e.evidence_id, sl.layer_code
                FROM iris_core.evidence AS e
                INNER JOIN iris_core.screening_layer AS sl
                    ON sl.country_code = e.country_code
                   AND sl.screening_layer_id = e.screening_layer_id
                ORDER BY e.evidence_id;
                """
            )
            layer_trace = cur.fetchall()

            cur.execute(
                """
                SELECT e.evidence_id, p.parcel_id
                FROM iris_core.evidence AS e
                INNER JOIN iris_core.parcel AS p
                    ON p.country_code = e.country_code
                   AND p.parcel_id = e.entity_id
                WHERE e.entity_type = 'parcel'
                ORDER BY e.evidence_id;
                """
            )
            parcel_trace = cur.fetchall()

    assert len(source_trace) == 7
    assert all(row[1] == 1 and row[3] == "succeeded" for row in source_trace)
    assert len(layer_trace) == 7
    assert len(parcel_trace) == 3
