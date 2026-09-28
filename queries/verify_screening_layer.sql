-- Link each screening layer to its producing source run.
SELECT
    sl.country_code,
    sl.screening_layer_id,
    sl.layer_code,
    r.source_run_id,
    r.status
FROM iris_core.screening_layer AS sl
INNER JOIN iris_core.source_run AS r
    ON r.source_run_id = sl.source_run_id
ORDER BY sl.country_code, sl.screening_layer_id;

-- Spatial check: peatland overlap layer intersects the IN fixture parcel (when parcel seed is loaded).
SELECT sl.screening_layer_id, p.parcel_id
FROM iris_core.screening_layer AS sl
INNER JOIN iris_core.parcel AS p
    ON p.country_code = sl.country_code
   AND ST_Intersects(sl.geom, p.geom)
WHERE sl.layer_code = 'PEATLAND_PARCEL_OVERLAP'
ORDER BY sl.screening_layer_id, p.parcel_id;
