import os

import psycopg
import pytest

from iris.migrate import apply_migrations


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://iris:iris@localhost:5432/iris",
    )


@pytest.fixture(scope="session")
def database_url() -> str:
    return _database_url()


RESET_CORE_TABLES_SQL = """
TRUNCATE TABLE
    iris_core.evidence,
    iris_core.screening_layer,
    iris_core.peatland,
    iris_core.substation,
    iris_core.parcel,
    iris_core.source_run,
    iris_staging.parcel,
    iris_staging.ingest_run
RESTART IDENTITY CASCADE;
"""


@pytest.fixture(scope="session")
def migrated_database(database_url: str) -> str:
    try:
        apply_migrations(database_url)
    except psycopg.OperationalError as exc:
        pytest.skip(f"database not available: {exc}")
    return database_url
