"""Pilot spatial queries and EXPLAIN helpers for GiST verification."""

from __future__ import annotations

import psycopg

BESS_QUERY = """
SELECT s.country_code, s.substation_id
FROM iris_core.substation AS s
WHERE s.country_code = 'IN'
  AND s.geom && ST_Expand(ST_SetSRID(ST_MakePoint(77.5905, 12.9705), 4326), 0.045)
  AND ST_DWithin(
      s.geom::geography,
      ST_SetSRID(ST_MakePoint(77.5905, 12.9705), 4326)::geography,
      5000
  );
"""

PEATLAND_QUERY = """
SELECT pl.peatland_id, p.parcel_id
FROM iris_core.peatland AS pl
INNER JOIN iris_core.parcel AS p
    ON p.country_code = pl.country_code
   AND ST_Intersects(pl.geom, p.geom)
WHERE pl.country_code = 'IN';
"""


def explain_plan(cur: psycopg.Cursor, sql: str) -> str:
    cur.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) " + sql)
    return "\n".join(row[0] for row in cur.fetchall())


def plan_uses_gist(plan: str, index_name: str) -> bool:
    return index_name in plan and "Index" in plan
