"""Deterministic seed bundle loading."""

import psycopg

from iris.seed_data import load_seeds


def test_seed_bundle_idempotent(migrated_database: str) -> None:
    load_seeds(migrated_database, include_staging=True)
    counts_first = _table_counts(migrated_database)
    load_seeds(migrated_database, include_staging=True)
    counts_second = _table_counts(migrated_database)
    assert counts_first == counts_second
    assert counts_first["parcel"] == 3
    assert counts_first["substation"] == 3
    assert counts_first["peatland"] == 3
    assert counts_first["screening_layer"] == 4
    assert counts_first["evidence"] == 7
    assert counts_first["source_run"] == 1


def _table_counts(database_url: str) -> dict[str, int]:
    queries = {
        "source_run": "SELECT COUNT(*) FROM iris_core.source_run",
        "parcel": "SELECT COUNT(*) FROM iris_core.parcel",
        "substation": "SELECT COUNT(*) FROM iris_core.substation",
        "peatland": "SELECT COUNT(*) FROM iris_core.peatland",
        "screening_layer": "SELECT COUNT(*) FROM iris_core.screening_layer",
        "evidence": "SELECT COUNT(*) FROM iris_core.evidence",
        "staging_parcel": (
            "SELECT COUNT(*) FROM iris_staging.parcel WHERE promoted_at IS NULL"
        ),
    }
    counts: dict[str, int] = {}
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            for name, sql in queries.items():
                cur.execute(sql)
                counts[name] = cur.fetchone()[0]
    return counts
