"""Build an additive VERQIVIA Portable Verification Profile.

The profile is an exchange representation layered on top of the v0.1 protocol.
It does not change the v0.1 contracts and does not claim legal ownership or
universal trust.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.nothing_protocol import resolve_claim_relationships
from src.nothing_verify import (
    validate_evidence,
    validate_identity,
    validate_verification_event,
)

PROFILE_TYPE = "VERQIVIA-PORTABLE-VERIFICATION-PROFILE"
PROFILE_VERSION = "0.2-draft"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _clean_optional_str(value: Any, field: str) -> str | None:
    if value is None:
        return None
    _require(isinstance(value, str) and value.strip(), f"{field} must be a non-empty string")
    return value.strip()


def build_portable_profile(
    identity: Mapping[str, Any],
    *,
    verification_events: list[Mapping[str, Any]] | None = None,
    evidence_records: list[Mapping[str, Any]] | None = None,
    procedure_registry: Mapping[str, Any] | None = None,
    identifiers: list[Mapping[str, Any]] | None = None,
    domains: list[Mapping[str, Any]] | None = None,
    relationships: list[Mapping[str, Any]] | None = None,
    public_verify_url: str | None = None,
    api_url: str | None = None,
    discovery_url: str | None = None,
    interop: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Build a deterministic exchange profile from a validated v0.1 bundle."""
    validate_identity(identity)

    events = verification_events or []
    evidence = evidence_records or []
    if events or evidence:
        _require(
            verification_events is not None
            and evidence_records is not None
            and procedure_registry is not None,
            "verification_events, evidence_records and procedure_registry are required together",
        )
        for record in evidence:
            validate_evidence(record)
        for event in events:
            validate_verification_event(event)
        resolution = resolve_claim_relationships(
            identity, evidence, events, procedure_registry
        )
    else:
        resolution = {
            "resolution_version": "none",
            "verification_event_count": 0,
            "evidence_count": 0,
            "claims": {},
        }

    claims_report = resolution["claims"]
    profile_claims: list[dict[str, Any]] = []
    for claim in identity["claims"]:
        report = claims_report.get(claim["claim_id"], {})
        current_status = report.get("current_status")
        item: dict[str, Any] = {
            "claim_id": claim["claim_id"],
            "statement": claim["statement"],
            "status": current_status or claim["status"],
        }
        if report.get("current_event_id"):
            item["current_event_id"] = report["current_event_id"]
        if report.get("evidence_ids"):
            item["evidence_ids"] = report["evidence_ids"]
        profile_claims.append(item)

    subject = {
        "name": identity["subject"]["name"],
        "type": identity["subject"]["type"],
    }
    website = identity["subject"].get("website")
    if website is not None:
        subject["website"] = website

    profile: dict[str, Any] = {
        "profile_type": PROFILE_TYPE,
        "profile_version": PROFILE_VERSION,
        "verqivia_id": identity["nothing_id"],
        "subject": subject,
        "status": (
            "REVOKED"
            if identity.get("revocation", {}).get("status") == "REVOKED"
            else "ACTIVE"
        ),
        "identifiers": identifiers or [],
        "domains": domains or [],
        "claims": profile_claims,
        "relationships": relationships or [],
        "verification": {
            "resolution_version": resolution.get("resolution_version", "none"),
            "verification_event_count": resolution.get("verification_event_count", 0),
            "evidence_count": resolution.get("evidence_count", 0),
        },
        "links": {
            "verify": _clean_optional_str(public_verify_url, "public_verify_url")
            or f"/verify.html?id={identity['nothing_id']}"
        },
        "interop": {
            "w3c_vc": "adapter_planned",
            "openid4vci": "adapter_planned",
            "gleif_lei": "not_present",
            "bimi": "not_present",
            "gs1_digital_link": "adapter_planned",
        },
        "disclaimer": (
            "Experimental VERQIVIA profile. It is not a trademark registration, "
            "legal certification or universal trust score."
        ),
    }

    if api_url:
        profile["links"]["api"] = _clean_optional_str(api_url, "api_url")
    if discovery_url:
        profile["links"]["discovery"] = _clean_optional_str(
            discovery_url, "discovery_url"
        )
    if interop:
        for key, value in interop.items():
            if key in profile["interop"]:
                profile["interop"][key] = value

    return profile
