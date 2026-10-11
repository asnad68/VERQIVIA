#!/usr/bin/env python3
"""Seed exactly the published synthetic VERQIVIA demo into PostgreSQL.

The seed is safe to re-run for an identical fixture. It refuses to overwrite a
record with the same ID but different content, and it requires the dedicated
schema-owner database role. This is not a customer-registration mechanism.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.nothing_postgres import PostgreSQLNothingStore
from src.nothing_proof import verify_envelope
from src.nothing_store import NotFoundError


SEED_ACTOR = "verqivia-synthetic-demo-seed"
DEMO_ID = "NTH-000001"
DEMO_NAME = "VERQIVIA Experimental Identity"


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read required synthetic fixture {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"Expected a JSON object in {path}.")
    return value


def ensure_absent_or_identical(
    label: str,
    getter: Callable[[], Any],
    expected: dict[str, Any],
) -> None:
    try:
        stored = getter()
    except NotFoundError:
        return
    if getattr(stored, "record", None) != expected:
        raise SystemExit(
            f"Refusing to seed: {label} already exists with different content. "
            "No seed writes have been made."
        )


def main() -> int:
    migrator_dsn = os.getenv("NOTHING_POSTGRES_MIGRATOR_DSN", "").strip()
    runtime_dsn = os.getenv("NOTHING_POSTGRES_DSN", "").strip()
    if not migrator_dsn:
        raise SystemExit("NOTHING_POSTGRES_MIGRATOR_DSN is required for the synthetic seed.")
    if not runtime_dsn or migrator_dsn == runtime_dsn:
        raise SystemExit(
            "Configure a separate NOTHING_POSTGRES_DSN runtime role and "
            "NOTHING_POSTGRES_MIGRATOR_DSN schema-owner role before seeding."
        )

    bundle = read_json(ROOT / "site" / "data" / "demo-bundle.json")
    proof = read_json(ROOT / "site" / "data" / "demo-proof.json")
    trusted_issuers = read_json(ROOT / "trust" / "issuer-registry.json")

    if bundle.get("demo") is not True:
        raise SystemExit("Refusing to seed a bundle not explicitly marked as demo data.")
    identities = bundle.get("identities")
    evidence_items = bundle.get("evidence")
    events = bundle.get("verification_events")
    procedure_registry = bundle.get("procedure_registry")
    if not all(isinstance(items, list) for items in (identities, evidence_items, events)):
        raise SystemExit("The demo bundle has an invalid fixture structure.")
    if not isinstance(procedure_registry, dict) or not isinstance(procedure_registry.get("procedures"), list):
        raise SystemExit("The demo procedure registry is invalid.")

    matches = [item for item in identities if isinstance(item, dict) and item.get("nothing_id") == DEMO_ID]
    if len(matches) != 1:
        raise SystemExit(f"The bundle must contain exactly one {DEMO_ID} identity.")
    identity = matches[0]
    if identity.get("subject", {}).get("name") != DEMO_NAME:
        raise SystemExit("The reserved demo ID does not match the expected VERQIVIA demo identity.")
    claims = identity.get("claims")
    if not isinstance(claims, list) or not any(
        isinstance(claim, dict)
        and "experimental demonstration of the VERQIVIA identity model" in str(claim.get("statement", ""))
        for claim in claims
    ):
        raise SystemExit("The reserved demo identity lacks its explicit synthetic claim marker.")

    if proof.get("resource_type") != "identity" or proof.get("resource_id") != DEMO_ID:
        raise SystemExit("The public demo proof does not reference the reserved demo identity.")
    result = verify_envelope(
        proof,
        identity,
        trusted_issuers,
        at_time=proof.get("proof", {}).get("created"),
    )
    if not result.get("valid"):
        raise SystemExit(f"The public demo proof is not trusted by the API registry: {result.get('reason')}")

    evidence_ids = {item.get("evidence_id") for item in evidence_items if isinstance(item, dict)}
    procedure_keys = {
        (item.get("id"), item.get("version"))
        for item in procedure_registry["procedures"]
        if isinstance(item, dict)
    }
    matching_events = [
        item for item in events
        if isinstance(item, dict) and item.get("subject") == DEMO_ID
    ]
    if not matching_events or not evidence_ids:
        raise SystemExit("The synthetic demo bundle is missing its evidence or verification event.")
    for event in matching_events:
        if not set(event.get("evidence", [])) <= evidence_ids:
            raise SystemExit("A synthetic verification event references evidence absent from the bundle.")
        procedure = event.get("procedure", {})
        if (procedure.get("id"), procedure.get("version")) not in procedure_keys:
            raise SystemExit("A synthetic verification event references an unknown procedure.")

    store = PostgreSQLNothingStore(migrator_dsn, auto_migrate=False)
    try:
        with store._pool.connection() as connection:
            row = connection.execute("SELECT current_user AS role_name").fetchone()
        if row is None or row["role_name"] != "nothing_migrator":
            raise SystemExit("Seed connection must authenticate as exactly 'nothing_migrator'.")
        if not store.health():
            raise SystemExit("PostgreSQL schema is not ready; no seed writes were attempted.")

        # Check every fixture ID before making the first write. The store's
        # immutable/idempotent writers then make identical redeploys safe.
        checks: list[tuple[str, Callable[[], Any], dict[str, Any]]] = []
        for procedure in procedure_registry["procedures"]:
            checks.append((
                f"procedure {procedure['id']} v{procedure['version']}",
                lambda p=procedure: store.get_procedure(p["id"], p["version"]),
                procedure,
            ))
        checks.append((f"identity {DEMO_ID}", lambda: store.get_identity(DEMO_ID), identity))
        for evidence in evidence_items:
            checks.append((
                f"evidence {evidence['evidence_id']}",
                lambda e=evidence: store.get_evidence(e["evidence_id"]),
                evidence,
            ))
        for event in matching_events:
            checks.append((
                f"verification event {event['event_id']}",
                lambda e=event: store.get_event(e["event_id"]),
                event,
            ))
        checks.append((
            f"proof {proof['envelope_id']}",
            lambda: store.get_proof(proof["envelope_id"]),
            proof,
        ))
        for label, getter, expected in checks:
            ensure_absent_or_identical(label, getter, expected)

        for procedure in procedure_registry["procedures"]:
            store.put_procedure(procedure, actor=SEED_ACTOR)
        store.put_identity(identity, actor=SEED_ACTOR)
        for evidence in evidence_items:
            store.put_evidence(evidence, actor=SEED_ACTOR)
        for event in matching_events:
            store.put_event(event, actor=SEED_ACTOR)
        store.put_proof(proof, actor=SEED_ACTOR)
    finally:
        store.close()

    print("VERQIVIA synthetic demo seed: OK")
    print(f"Reserved demo identity available: {DEMO_ID} ({DEMO_NAME})")
    print("Only repository-published synthetic records were seeded; no customer records were created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
