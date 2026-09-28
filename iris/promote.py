"""Promote staged parcel rows into iris_core."""

from __future__ import annotations

import os
import sys

import psycopg

from iris.migrate import database_url

PROMOTE_PARCELS_SQL = """
WITH new_run AS (
    INSERT INTO iris_core.source_run (
        source_id,
        source_date,
        status,
        started_at,
        completed_at
    )
    SELECT
        ir.source_id,
        ir.source_date,
        'succeeded',
        ir.created_at,
        now()
    FROM iris_staging.ingest_run AS ir
    WHERE ir.ingest_run_id = %(ingest_run_id)s
    RETURNING source_id, source_date
),
inserted AS (
    INSERT INTO iris_core.parcel (
        country_code,
        parcel_id,
        region_code,
        geom,
        source_id,
        source_date
    )
    SELECT
        sp.country_code,
        sp.parcel_id,
        sp.region_code,
        sp.geom,
        nr.source_id,
        nr.source_date
    FROM iris_staging.parcel AS sp
    CROSS JOIN new_run AS nr
    WHERE sp.ingest_run_id = %(ingest_run_id)s
      AND sp.promoted_at IS NULL
    ON CONFLICT (country_code, parcel_id) DO NOTHING
    RETURNING country_code, parcel_id
)
UPDATE iris_staging.parcel AS sp
SET promoted_at = now()
WHERE sp.ingest_run_id = %(ingest_run_id)s
  AND sp.promoted_at IS NULL
  AND EXISTS (SELECT 1 FROM inserted)
RETURNING sp.staging_parcel_id;
"""


def promote_parcels(ingest_run_id: int, url: str | None = None) -> int:
    """Promote unpromoted staged parcels for one ingest run. Returns rows marked promoted."""
    db_url = url or database_url()
    with psycopg.connect(db_url) as conn:
        conn.autocommit = False
        with conn.cursor() as cur:
            cur.execute(PROMOTE_PARCELS_SQL, {"ingest_run_id": ingest_run_id})
            promoted_ids = [row[0] for row in cur.fetchall()]
        conn.commit()
    return len(promoted_ids)


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print("Usage: python -m iris.promote <ingest_run_id>", file=sys.stderr)
        return 2

    ingest_run_id = int(args[0])
    count = promote_parcels(ingest_run_id)
    print(f"Promoted {count} staged parcel row(s) for ingest_run_id={ingest_run_id}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
