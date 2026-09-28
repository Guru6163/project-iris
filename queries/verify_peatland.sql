-- Country-scoped uniqueness.
SELECT country_code, peatland_id, COUNT(*) AS row_count
FROM iris_core.peatland
GROUP BY country_code, peatland_id
HAVING COUNT(*) > 1;

-- Spatial overlap: peatland intersecting the IN fixture parcel (when parcel seed is loaded).
SELECT
    pl.country_code,
    pl.peatland_id,
    p.parcel_id
FROM iris_core.peatland AS pl
INNER JOIN iris_core.parcel AS p
    ON p.country_code = pl.country_code
   AND ST_Intersects(pl.geom, p.geom)
WHERE pl.country_code = 'IN'
ORDER BY pl.peatland_id, p.parcel_id;

-- Provenance join to source_run via source_id + source_date.
SELECT
    pl.country_code,
    pl.peatland_id,
    pl.representation,
    r.source_run_id,
    r.status
FROM iris_core.peatland AS pl
INNER JOIN iris_core.source_run AS r
    ON r.source_id = pl.source_id
   AND r.source_date = pl.source_date
ORDER BY pl.country_code, pl.peatland_id;
