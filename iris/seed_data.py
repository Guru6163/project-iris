"""Load deterministic SQL seed files in order."""

from __future__ import annotations

from pathlib import Path

import psycopg

from iris.migrate import database_url

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SEED_DIR = PROJECT_ROOT / "seed"

CORE_SEED_FILES = (
    "source_run.sql",
    "parcel.sql",
    "substation.sql",
    "peatland.sql",
    "screening_layer.sql",
    "evidence.sql",
)

STAGING_SEED_FILE = "staging_parcel.sql"


def load_seeds(
    url: str | None = None,
    *,
    include_staging: bool = True,
) -> list[str]:
    """Execute seed SQL files. Idempotent (ON CONFLICT). Returns files loaded."""
    files = list(CORE_SEED_FILES)
    if include_staging:
        files.append(STAGING_SEED_FILE)

    db_url = url or database_url()
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            for name in files:
                cur.execute((SEED_DIR / name).read_text(encoding="utf-8"))
        conn.commit()
    return files


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Load deterministic IRIS seed SQL files.")
    parser.add_argument(
        "--core-only",
        action="store_true",
        help="Load iris_core fixtures only (skip iris_staging).",
    )
    args = parser.parse_args()
    loaded = load_seeds(include_staging=not args.core_only)
    print("Loaded seed files:", ", ".join(loaded))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
