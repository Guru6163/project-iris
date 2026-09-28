from pathlib import Path

import psycopg
import pytest

from iris.spatial_indexes import BESS_QUERY, PEATLAND_QUERY, explain_plan, plan_uses_gist

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SEED_FILES = (
    PROJECT_ROOT / "seed" / "source_run.sql",
    PROJECT_ROOT / "seed" / "parcel.sql",
    PROJECT_ROOT / "seed" / "substation.sql",
    PROJECT_ROOT / "seed" / "peatland.sql",
)


@pytest.fixture
def pilot_seeded_db(migrated_database: str) -> str:
    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            for path in SEED_FILES:
                cur.execute(path.read_text(encoding="utf-8"))
        conn.commit()
    return migrated_database


def test_core_gist_indexes_exist(migrated_database: str) -> None:
    expected = {
        "parcel_geom_gix",
        "substation_geom_gix",
        "peatland_geom_gix",
        "screening_layer_geom_gix",
    }
    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = 'iris_core'
                  AND indexname LIKE '%_geom_gix';
                """
            )
            names = {row[0] for row in cur.fetchall()}
    assert expected <= names


def test_staging_parcel_has_no_spatial_index(migrated_database: str) -> None:
    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM pg_indexes
                WHERE schemaname = 'iris_staging'
                  AND tablename = 'parcel'
                  AND indexdef ILIKE '%USING gist%';
                """
            )
            count = cur.fetchone()[0]
    assert count == 0


def test_pilot_queries_use_gist_indexes(pilot_seeded_db: str) -> None:
    with psycopg.connect(pilot_seeded_db) as conn:
        with conn.cursor() as cur:
            cur.execute("SET enable_seqscan = off")
            bess_plan = explain_plan(cur, BESS_QUERY)
            peat_plan = explain_plan(cur, PEATLAND_QUERY)

    assert plan_uses_gist(bess_plan, "substation_geom_gix")
    assert plan_uses_gist(peat_plan, "peatland_geom_gix") or plan_uses_gist(
        peat_plan, "parcel_geom_gix"
    )
