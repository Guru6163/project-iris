-- Enforce country-scoped evidence links to business entities and screening layers.

CREATE OR REPLACE FUNCTION iris_core.evidence_country_scope_checks()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    layer_source_run_id BIGINT;
BEGIN
    SELECT sl.source_run_id
    INTO layer_source_run_id
    FROM iris_core.screening_layer AS sl
    WHERE sl.country_code = NEW.country_code
      AND sl.screening_layer_id = NEW.screening_layer_id;

    IF layer_source_run_id IS NULL THEN
        RAISE EXCEPTION
            'screening_layer % not found for country %',
            NEW.screening_layer_id,
            NEW.country_code;
    END IF;

    IF NEW.source_run_id IS DISTINCT FROM layer_source_run_id THEN
        RAISE EXCEPTION
            'evidence source_run_id % does not match screening layer run %',
            NEW.source_run_id,
            layer_source_run_id;
    END IF;

    IF NEW.entity_type = 'parcel' THEN
        IF NOT EXISTS (
            SELECT 1
            FROM iris_core.parcel AS p
            WHERE p.country_code = NEW.country_code
              AND p.parcel_id = NEW.entity_id
        ) THEN
            RAISE EXCEPTION
                'parcel % not found for country %',
                NEW.entity_id,
                NEW.country_code;
        END IF;
    ELSIF NEW.entity_type = 'peatland' THEN
        IF NOT EXISTS (
            SELECT 1
            FROM iris_core.peatland AS pl
            WHERE pl.country_code = NEW.country_code
              AND pl.peatland_id = NEW.entity_id
        ) THEN
            RAISE EXCEPTION
                'peatland % not found for country %',
                NEW.entity_id,
                NEW.country_code;
        END IF;
    ELSIF NEW.entity_type = 'substation' THEN
        IF NOT EXISTS (
            SELECT 1
            FROM iris_core.substation AS s
            WHERE s.country_code = NEW.country_code
              AND s.substation_id = NEW.entity_id
        ) THEN
            RAISE EXCEPTION
                'substation % not found for country %',
                NEW.entity_id,
                NEW.country_code;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER evidence_country_scope_trg
    BEFORE INSERT OR UPDATE ON iris_core.evidence
    FOR EACH ROW
    EXECUTE FUNCTION iris_core.evidence_country_scope_checks();

COMMENT ON FUNCTION iris_core.evidence_country_scope_checks() IS
    'Ensures evidence entity_id resolves within country_code and source_run_id matches the screening layer.';
