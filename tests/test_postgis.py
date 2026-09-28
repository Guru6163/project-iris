import psycopg
import pytest


def test_postgresql_connects(database_url: str) -> None:
    try:
        with psycopg.connect(database_url, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                row = cur.fetchone()
    except psycopg.OperationalError as exc:
        pytest.skip(f"database not available: {exc}")

    assert row is not None
    assert "PostgreSQL" in row[0]


def test_postgis_extension_available(database_url: str) -> None:
    try:
        with psycopg.connect(database_url, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT PostGIS_Version();")
                row = cur.fetchone()
    except psycopg.OperationalError as exc:
        pytest.skip(f"database not available: {exc}")

    assert row is not None
    assert row[0]
