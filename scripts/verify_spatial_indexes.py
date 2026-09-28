#!/usr/bin/env python3
"""Run pilot spatial queries with EXPLAIN and confirm GiST index use."""

from __future__ import annotations

import sys
from pathlib import Path

import psycopg

from iris.migrate import database_url
from iris.spatial_indexes import BESS_QUERY, PEATLAND_QUERY, explain_plan, plan_uses_gist

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SEED_FILES = (
    PROJECT_ROOT / "seed" / "source_run.sql",
    PROJECT_ROOT / "seed" / "parcel.sql",
    PROJECT_ROOT / "seed" / "substation.sql",
    PROJECT_ROOT / "seed" / "peatland.sql",
)


def main() -> int:
    url = database_url()
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            for path in SEED_FILES:
                cur.execute(path.read_text(encoding="utf-8"))
            conn.commit()

            cur.execute("SET enable_seqscan = off")
            bess_plan = explain_plan(cur, BESS_QUERY)
            peat_plan = explain_plan(cur, PEATLAND_QUERY)

    print("=== BESS screening (substation ST_DWithin) ===")
    print(bess_plan)
    print()
    print("=== Peatland inference (ST_Intersects peatland ↔ parcel) ===")
    print(peat_plan)
    print()

    bess_ok = plan_uses_gist(bess_plan, "substation_geom_gix")
    peat_ok = plan_uses_gist(peat_plan, "peatland_geom_gix") or plan_uses_gist(
        peat_plan, "parcel_geom_gix"
    )

    if not bess_ok or not peat_ok:
        print("GiST index not detected in plan (expected with enable_seqscan=off).", file=sys.stderr)
        return 1

    print("GiST indexes referenced in both pilot query plans.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
