"""Apply ordered SQL migrations from the migrations/ directory."""

from __future__ import annotations

import os
from pathlib import Path

import psycopg

MIGRATIONS_TABLE = "iris_migrations"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MIGRATIONS_DIR = PROJECT_ROOT / "migrations"


def database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://iris:iris@localhost:5432/iris",
    )


def _migration_versions(migrations_dir: Path) -> list[tuple[str, Path]]:
    files = sorted(migrations_dir.glob("*.sql"))
    return [(path.stem, path) for path in files]


def _ensure_migrations_table(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS public.{MIGRATIONS_TABLE} (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            """
        )


def _applied_versions(conn: psycopg.Connection) -> set[str]:
    with conn.cursor() as cur:
        cur.execute(f"SELECT version FROM public.{MIGRATIONS_TABLE};")
        return {row[0] for row in cur.fetchall()}


def apply_migrations(
    url: str | None = None,
    *,
    migrations_dir: Path | None = None,
) -> list[str]:
    """Run pending migrations in filename order. Returns newly applied versions."""
    db_url = url or database_url()
    directory = migrations_dir or DEFAULT_MIGRATIONS_DIR
    if not directory.is_dir():
        raise FileNotFoundError(f"migrations directory not found: {directory}")

    pending = _migration_versions(directory)
    if not pending:
        return []

    applied_now: list[str] = []

    with psycopg.connect(db_url, connect_timeout=10) as conn:
        conn.autocommit = True
        _ensure_migrations_table(conn)
        already_applied = _applied_versions(conn)

        for version, path in pending:
            if version in already_applied:
                continue

            sql = path.read_text(encoding="utf-8")
            with conn.cursor() as cur:
                cur.execute(sql)
                cur.execute(
                    f"INSERT INTO public.{MIGRATIONS_TABLE} (version) VALUES (%s);",
                    (version,),
                )
            applied_now.append(version)

    return applied_now


def main() -> int:
    applied = apply_migrations()
    if applied:
        print("Applied migrations:", ", ".join(applied))
    else:
        print("Database is up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
