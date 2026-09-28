import os

import pytest


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://iris:iris@localhost:5432/iris",
    )


@pytest.fixture(scope="session")
def database_url() -> str:
    return _database_url()
