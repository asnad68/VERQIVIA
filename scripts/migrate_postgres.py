#!/usr/bin/env python3
"""Run PostgreSQL migrations as a deployment-time operation.

The API container itself starts with auto-migration disabled. The deployment
platform should run this command once during the pre-deploy phase so schema
changes are applied before the new application instance receives traffic.
"""

from __future__ import annotations

from src.nothing_postgres import PostgreSQLNothingStore


def main() -> int:
    store = PostgreSQLNothingStore.from_environment()
    try:
        if not store.health():
            # The health check is intentionally strict: an empty or partially
            # migrated database is not considered ready.
            raise SystemExit(
                "PostgreSQL migration finished but schema is not at the expected version."
            )
    finally:
        store.close()
    print("VERQIVIA PostgreSQL migrations: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
