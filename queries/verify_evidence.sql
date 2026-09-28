-- Evidence to producing source run.
SELECT
    e.evidence_id,
    e.entity_type,
    e.entity_id,
    r.source_run_id,
    r.source_id,
    r.source_date,
    r.status
FROM iris_core.evidence AS e
INNER JOIN iris_core.source_run AS r
    ON r.source_run_id = e.source_run_id
ORDER BY e.evidence_id;

-- Evidence to screening layer and layer code.
SELECT
    e.evidence_id,
    sl.screening_layer_id,
    sl.layer_code
FROM iris_core.evidence AS e
INNER JOIN iris_core.screening_layer AS sl
    ON sl.country_code = e.country_code
   AND sl.screening_layer_id = e.screening_layer_id
ORDER BY e.evidence_id;

-- Country-scoped link from evidence to parcel input (when entity_type = parcel).
SELECT
    e.evidence_id,
    p.country_code,
    p.parcel_id,
    p.source_id AS parcel_source_id,
    p.source_date AS parcel_source_date
FROM iris_core.evidence AS e
INNER JOIN iris_core.parcel AS p
    ON p.country_code = e.country_code
   AND p.parcel_id = e.entity_id
WHERE e.entity_type = 'parcel'
ORDER BY e.evidence_id;
