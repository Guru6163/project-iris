-- 1) Parcel records exist.
SELECT COUNT(*) AS parcel_count
FROM iris_core.parcel;

-- 2) country_code is enforced NOT NULL (no rows may have a null country_code).
SELECT COUNT(*) AS null_country_code_rows
FROM iris_core.parcel
WHERE country_code IS NULL;

-- 3) Basic spatial query: parcels containing a point in the fixture area.
SELECT country_code, parcel_id
FROM iris_core.parcel
WHERE ST_Contains(
    geom,
    ST_SetSRID(ST_MakePoint(77.5905, 12.9705), 4326)
);
