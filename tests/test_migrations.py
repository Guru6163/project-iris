import psycopg
import pytest

from iris.migrate import apply_migrations


@pytest.fixture(scope="session")
def migrated_database(database_url: str) -> str:
    try:
        apply_migrations(database_url)
    except psycopg.OperationalError as exc:
        pytest.skip(f"database not available: {exc}")
    return database_url


def test_foundation_schemas_exist(migrated_database: str) -> None:
    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name IN ('iris_staging', 'iris_core')
                ORDER BY schema_name;
                """
            )
            names = [row[0] for row in cur.fetchall()]

    assert names == ["iris_core", "iris_staging"]


def test_foundation_migration_recorded(migrated_database: str) -> None:
    with psycopg.connect(migrated_database) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT version FROM public.iris_migrations ORDER BY version;"
            )
            versions = [row[0] for row in cur.fetchall()]

    assert "001_foundation" in versions
