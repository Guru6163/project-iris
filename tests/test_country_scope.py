"""Country-scoped identifier and relationship rules for iris_core business tables."""

import psycopg
import pytest

from tests.conftest import RESET_CORE_TABLES_SQL

MIN_POLYGON = "ST_Multi(ST_GeomFromText('POLYGON((0 0,1 0,1 1,0 1,0 0))', 4326))"
MIN_POINT = "ST_SetSRID(ST_MakePoint(0.5, 0.5), 4326)"

COUNTRY_SCOPED_TABLES = (
    ("parcel", f"""
        INSERT INTO iris_core.parcel (
            country_code, parcel_id, region_code, geom, source_id, source_date
        ) VALUES (
            %s, %s, 'RG', {MIN_POLYGON}, 'vendor', DATE '2024-01-01'
        );
    """),
    ("substation", f"""
        INSERT INTO iris_core.substation (
            country_code, substation_id, geom, source_id, source_date
        ) VALUES (
            %s, %s, {MIN_POINT}, 'vendor', DATE '2024-01-01'
        );
    """),
    ("peatland", f"""
        INSERT INTO iris_core.peatland (
            country_code, peatland_id, region_code, geom, representation,
            source_id, source_date
        ) VALUES (
            %s, %s, 'RG', {MIN_POLYGON}, 'observed', 'vendor', DATE '2024-01-01'
        );
    """),
    ("screening_layer", f"""
        INSERT INTO iris_core.screening_layer (
            country_code, screening_layer_id, layer_code, geom,
            source_run_id, source_id, source_date
        ) VALUES (
            %s, %s, 'TEST_LAYER', {MIN_POLYGON}, %s, 'vendor', DATE '2024-01-01'
        );
    """),
    ("evidence", """
        INSERT INTO iris_core.evidence (
            country_code, evidence_id, screening_layer_id, entity_type, entity_id,
            source_run_id, source_id, source_date
        ) VALUES (
            %s, %s, %s, 'parcel', %s, %s, 'vendor', DATE '2024-01-01'
        );
    """),
)


@pytest.fixture
def scope_db(migrated_database: str) -> str:
    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            cur.execute(RESET_CORE_TABLES_SQL)
        conn.commit()
    return migrated_database


def test_country_code_cannot_be_null(scope_db: str) -> None:
    with psycopg.connect(scope_db) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO iris_core.source_run (source_id, source_date) "
                "VALUES ('vendor', DATE '2024-01-01') RETURNING source_run_id;"
            )
            source_run_id = cur.fetchone()[0]

            for table, insert_sql in COUNTRY_SCOPED_TABLES:
                with pytest.raises(psycopg.Error):
                    if table == "screening_layer":
                        cur.execute(insert_sql, (None, "ID-1", source_run_id))
                    elif table == "evidence":
                        cur.execute(
                            insert_sql,
                            (None, "EV-1", "SL-1", "P-1", source_run_id),
                        )
                    else:
                        cur.execute(insert_sql, (None, "ID-1"))
        conn.rollback()


def test_same_identifier_allowed_in_different_countries(scope_db: str) -> None:
    shared_id = "SHARED-PARCEL-001"
    with psycopg.connect(scope_db) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO iris_core.parcel (
                    country_code, parcel_id, region_code, geom, source_id, source_date
                ) VALUES
                    ('IN', %s, 'KA', {MIN_POLYGON}, 'vendor', DATE '2024-01-01'),
                    ('US', %s, 'CA', {MIN_POLYGON}, 'vendor', DATE '2024-01-01');
                """,
                (shared_id, shared_id),
            )
            cur.execute(
                """
                SELECT country_code, parcel_id
                FROM iris_core.parcel
                WHERE parcel_id = %s
                ORDER BY country_code;
                """,
                (shared_id,),
            )
            rows = cur.fetchall()
        conn.commit()

    assert rows == [("IN", shared_id), ("US", shared_id)]


def test_duplicate_identifier_rejected_within_country(scope_db: str) -> None:
    with psycopg.connect(scope_db) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO iris_core.parcel (
                    country_code, parcel_id, region_code, geom, source_id, source_date
                ) VALUES ('IN', 'DUP-1', 'KA', {MIN_POLYGON}, 'vendor', DATE '2024-01-01');
                """
            )
            with pytest.raises(psycopg.errors.UniqueViolation):
                cur.execute(
                    f"""
                    INSERT INTO iris_core.parcel (
                        country_code, parcel_id, region_code, geom, source_id, source_date
                    ) VALUES ('IN', 'DUP-1', 'KA', {MIN_POLYGON}, 'vendor', DATE '2024-01-01');
                    """
                )
        conn.rollback()


def _seed_evidence_graph(cur: psycopg.Cursor) -> None:
    cur.execute(
        "INSERT INTO iris_core.source_run (source_id, source_date, status) "
        "VALUES ('vendor', DATE '2024-01-01', 'succeeded') RETURNING source_run_id;"
    )
    source_run_id = cur.fetchone()[0]
    cur.execute(
        f"""
        INSERT INTO iris_core.parcel (
            country_code, parcel_id, region_code, geom, source_id, source_date
        ) VALUES ('DE', 'P-DE-ONLY', 'BE', {MIN_POLYGON}, 'vendor', DATE '2024-01-01');
        """
    )
    cur.execute(
        f"""
        INSERT INTO iris_core.screening_layer (
            country_code, screening_layer_id, layer_code, geom,
            source_run_id, source_id, source_date
        ) VALUES (
            'IN', 'SL-IN-1', 'TEST_LAYER', {MIN_POLYGON}, %s, 'vendor', DATE '2024-01-01'
        );
        """,
        (source_run_id,),
    )


def test_cross_country_screening_layer_fk_rejected(scope_db: str) -> None:
    with psycopg.connect(scope_db) as conn:
        with conn.cursor() as cur:
            _seed_evidence_graph(cur)
            with pytest.raises(psycopg.Error, match="not found for country US"):
                cur.execute(
                    """
                    INSERT INTO iris_core.evidence (
                        country_code, evidence_id, screening_layer_id, entity_type,
                        entity_id, source_run_id, source_id, source_date
                    ) VALUES (
                        'US', 'EV-US-1', 'SL-IN-1', 'parcel', 'P-DE-ONLY',
                        1, 'vendor', DATE '2024-01-01'
                    );
                    """
                )
        conn.rollback()


def test_cross_country_entity_reference_rejected(scope_db: str) -> None:
    with psycopg.connect(scope_db) as conn:
        with conn.cursor() as cur:
            _seed_evidence_graph(cur)
            with pytest.raises(psycopg.Error, match="parcel P-DE-ONLY not found for country IN"):
                cur.execute(
                    """
                    INSERT INTO iris_core.evidence (
                        country_code, evidence_id, screening_layer_id, entity_type,
                        entity_id, source_run_id, source_id, source_date
                    ) VALUES (
                        'IN', 'EV-IN-1', 'SL-IN-1', 'parcel', 'P-DE-ONLY',
                        1, 'vendor', DATE '2024-01-01'
                    );
                    """
                )
        conn.rollback()
