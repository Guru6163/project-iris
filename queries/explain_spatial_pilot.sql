-- Pilot spatial plans (run after core seeds). Tiny tables may seq-scan unless enable_seqscan is off.
\set ON_ERROR_STOP on

-- BESS screening: substations within 5 km of a candidate parcel point (uses substation_geom_gix).
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT s.country_code, s.substation_id
FROM iris_core.substation AS s
WHERE s.country_code = 'IN'
  AND s.geom && ST_Expand(ST_SetSRID(ST_MakePoint(77.5905, 12.9705), 4326), 0.045)
  AND ST_DWithin(
      s.geom::geography,
      ST_SetSRID(ST_MakePoint(77.5905, 12.9705), 4326)::geography,
      5000
  );

-- Peatland inference: peatland polygons intersecting parcels in-country (uses peatland/parcel GiST).
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT pl.peatland_id, p.parcel_id
FROM iris_core.peatland AS pl
INNER JOIN iris_core.parcel AS p
    ON p.country_code = pl.country_code
   AND ST_Intersects(pl.geom, p.geom)
WHERE pl.country_code = 'IN';
