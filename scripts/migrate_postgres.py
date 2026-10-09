#!/usr/bin/env python3
"""Apply PostgreSQL migrations using the dedicated schema-owner connection."""
from __future__ import annotations

import os

from src.nothing_postgres import PostgreSQLNothingStore


def main() -> int:
    migrator_dsn = os.getenv("NOTHING_POSTGRES_MIGRATOR_DSN", "").strip()
    runtime_dsn = os.getenv("NOTHING_POSTGRES_DSN", "").strip()
    if not migrator_dsn:
        raise SystemExit(
            "NOTHING_POSTGRES_MIGRATOR_DSN is required; configure the dedicated "
            "nothing_migrator database credential."
        )
    if runtime_dsn and migrator_dsn == runtime_dsn:
        raise SystemExit(
            "NOTHING_POSTGRES_MIGRATOR_DSN must differ from the API runtime DSN."
        )

    # Check identity before any DDL is applied. Never auto-migrate as the app role.
    os.environ["NOTHING_POSTGRES_DSN"] = migrator_dsn
    os.environ["NOTHING_POSTGRES_AUTO_MIGRATE"] = "false"
    store = PostgreSQLNothingStore.from_environment()
    try:
        with store._pool.connection() as connection:
            row = connection.execute("SELECT current_user AS role_name").fetchone()
        if row is None or row["role_name"] != "nothing_migrator":
            raise SystemExit(
                "Migration connection must authenticate as exactly 'nothing_migrator'; "
                "no schema changes were applied."
            )
        store._migrate()
        if not store.health():
            raise SystemExit(
                "PostgreSQL migration finished but schema is not at the expected version."
            )
    finally:
        store.close()
    print("VERQIVIA PostgreSQL migrations: OK (nothing_migrator)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
