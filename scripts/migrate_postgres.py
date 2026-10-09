#!/usr/bin/env python3
"""Apply PostgreSQL migrations using the separate schema-owner connection.

The public API container runs with NOTHING_POSTGRES_DSN and the least-privileged
nothing_app role. The pre-deploy migration phase must use
NOTHING_POSTGRES_MIGRATOR_DSN. Never silently run schema migrations as the API
runtime identity.
"""
from __future__ import annotations

import os

from src.nothing_postgres import PostgreSQLNothingStore


def main() -> int:
    migrator_dsn = os.getenv("NOTHING_POSTGRES_MIGRATOR_DSN", "").strip()
    runtime_dsn = os.getenv("NOTHING_POSTGRES_DSN", "").strip()
    if not migrator_dsn:
        raise SystemExit(
            "NOTHING_POSTGRES_MIGRATOR_DSN is required for schema migrations; "
            "configure a separate migration-owner connection."
        )
    if runtime_dsn and migrator_dsn == runtime_dsn:
        raise SystemExit(
            "NOTHING_POSTGRES_MIGRATOR_DSN must differ from the application runtime DSN."
        )

    os.environ["NOTHING_POSTGRES_DSN"] = migrator_dsn
    os.environ["NOTHING_POSTGRES_AUTO_MIGRATE"] = "true"
    store = PostgreSQLNothingStore.from_environment()
    try:
        if not store.health():
            raise SystemExit(
                "PostgreSQL migration finished but schema is not at the expected version."
            )
    finally:
        store.close()
    print("VERQIVIA PostgreSQL migrations: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
