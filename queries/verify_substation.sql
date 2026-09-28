-- Country-scoped uniqueness: one row per (country_code, substation_id).
SELECT country_code, substation_id, COUNT(*) AS row_count
FROM iris_core.substation
GROUP BY country_code, substation_id
HAVING COUNT(*) > 1;

-- Spatial filter: substations within ~5 km of the IN fixture parcel (degrees, 4326).
SELECT s.country_code, s.substation_id
FROM iris_core.substation AS s
WHERE s.country_code = 'IN'
  AND ST_DWithin(
      s.geom::geography,
      ST_SetSRID(ST_MakePoint(77.5905, 12.9705), 4326)::geography,
      5000
  );

-- Provenance join to source_run via source_id + source_date.
SELECT
    s.country_code,
    s.substation_id,
    r.source_run_id,
    r.status
FROM iris_core.substation AS s
INNER JOIN iris_core.source_run AS r
    ON r.source_id = s.source_id
   AND r.source_date = s.source_date
ORDER BY s.country_code, s.substation_id;
