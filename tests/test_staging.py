from pathlib import Path

import psycopg

from iris.promote import promote_parcels
from tests.conftest import RESET_CORE_TABLES_SQL

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STAGING_SEED = PROJECT_ROOT / "seed" / "staging_parcel.sql"


def test_staging_parcel_promotion_to_core(migrated_database: str) -> None:
    staging_sql = STAGING_SEED.read_text(encoding="utf-8")
    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            cur.execute(RESET_CORE_TABLES_SQL)
            cur.execute("TRUNCATE iris_staging.parcel, iris_staging.ingest_run RESTART IDENTITY;")
            cur.execute(staging_sql)
        conn.commit()

    promoted = promote_parcels(1, migrated_database)
    assert promoted == 1

    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT country_code, parcel_id, source_id, source_date::text
                FROM iris_core.parcel
                WHERE country_code = 'IN' AND parcel_id = 'P-STAGING-001';
                """
            )
            core_row = cur.fetchone()

            cur.execute(
                """
                SELECT promoted_at IS NOT NULL
                FROM iris_staging.parcel
                WHERE ingest_run_id = 1 AND parcel_id = 'P-STAGING-001';
                """
            )
            staged_promoted = cur.fetchone()[0]

            cur.execute(
                """
                SELECT source_id, source_date::text, status
                FROM iris_core.source_run
                WHERE source_id = 'staging_vendor_b';
                """
            )
            run_row = cur.fetchone()

    assert core_row == ("IN", "P-STAGING-001", "staging_vendor_b", "2024-07-01")
    assert staged_promoted is True
    assert run_row == ("staging_vendor_b", "2024-07-01", "succeeded")
