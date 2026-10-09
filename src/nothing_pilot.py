"""Server-side validation for authenticated VERQIVIA pilot-draft submissions.

A pilot draft is an intake record only: accepting it never creates an official
identity, verifies a claim, or signs a cryptographic proof.
"""
from __future__ import annotations

import ipaddress
import json
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit
from typing import Any

PILOT_DRAFT_MAX_BODY_BYTES = 32_768
ALLOWED_TYPES = {"business", "brand", "digital_channel"}
ALLOWED_CLAIMS = {
    "official_domain",
    "official_website",
    "authorized_representative",
    "business_relationship",
}
TOP_LEVEL_FIELDS = {"stage", "protocol_version", "generated_at", "registration", "pilot", "readiness"}


class PilotDraftValidationError(ValueError):
    """The submitted pilot draft violates the server-side contract."""


def _text(value: Any, field: str, limit: int, *, required: bool = False) -> str:
    if not isinstance(value, str):
        raise PilotDraftValidationError(f"{field} must be a string")
    result = value.strip()
    if len(result) > limit:
        raise PilotDraftValidationError(f"{field} exceeds its length limit")
    if required and not result:
        raise PilotDraftValidationError(f"{field} is required")
    if any(ord(char) < 32 and char not in "\t\n\r" for char in result):
        raise PilotDraftValidationError(f"{field} contains control characters")
    return result


def _http_url(value: Any, field: str, *, required: bool = False, limit: int = 500) -> str:
    text = _text(value, field, limit, required=required)
    if not text:
        return ""
    if any(ord(char) < 32 for char in text):
        raise PilotDraftValidationError(f"{field} contains control characters")
    try:
        parsed = urlsplit(text)
        hostname = parsed.hostname
        # Accessing .port also validates a supplied port.
        _ = parsed.port
    except ValueError as exc:
        raise PilotDraftValidationError(f"{field} must be an absolute HTTP(S) URL") from exc
    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
        or not parsed.netloc
    ):
        raise PilotDraftValidationError(f"{field} must be an absolute HTTP(S) URL without credentials")
    return urlunsplit((parsed.scheme.lower(), parsed.netloc, parsed.path or "", parsed.query, parsed.fragment))


def _domain(value: Any) -> str:
    text = _text(value, "domain", 253)
    if not text:
        return ""
    if any(char in text for char in "/@?#:\\\\") or any(char.isspace() for char in text):
        raise PilotDraftValidationError("domain must contain a hostname only")
    text = text.rstrip(".").lower()
    try:
        ascii_domain = text.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise PilotDraftValidationError("domain is not a valid public hostname") from exc
    try:
        ipaddress.ip_address(ascii_domain)
    except ValueError:
        pass
    else:
        raise PilotDraftValidationError("IP addresses are not accepted as organization domains")
    if "." not in ascii_domain or ascii_domain == "localhost" or ascii_domain.endswith(
        (".local", ".internal", ".lan", ".home.arpa", ".localhost", ".test", ".invalid")
    ):
        raise PilotDraftValidationError("domain must be a public organization hostname")
    labels = ascii_domain.split(".")
    if any(
        not label
        or len(label) > 63
        or label.startswith("-")
        or label.endswith("-")
        or not all(char.isascii() and (char.isalnum() or char == "-") for char in label)
        for label in labels
    ):
        raise PilotDraftValidationError("domain is not a valid hostname")
    return ascii_domain


def _lines(value: Any, field: str, maximum: int, item_limit: int) -> list[str]:
    if not isinstance(value, list):
        raise PilotDraftValidationError(f"{field} must be a list")
    result: list[str] = []
    for item in value:
        entry = _text(item, field, item_limit, required=True)
        if entry not in result:
            result.append(entry)
        if len(result) > maximum:
            raise PilotDraftValidationError(f"{field} has too many entries")
    return result


def parse_pilot_draft(body: bytes, content_type: str | None) -> dict[str, Any]:
    if len(body) > PILOT_DRAFT_MAX_BODY_BYTES:
        raise OverflowError("pilot draft exceeds the configured body-size limit")
    media_type = (content_type or "").split(";", 1)[0].strip().lower()
    if media_type != "application/json":
        raise TypeError("Content-Type must be application/json")

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise PilotDraftValidationError("duplicate JSON property")
            result[key] = value
        return result

    try:
        payload = json.loads(body.decode("utf-8"), object_pairs_hook=reject_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PilotDraftValidationError("body must contain valid UTF-8 JSON") from exc
    if not isinstance(payload, dict) or set(payload) != TOP_LEVEL_FIELDS:
        raise PilotDraftValidationError("pilot draft has an invalid top-level shape")
    if payload.get("stage") != "PILOT_DRAFT" or payload.get("protocol_version") != "0.1":
        raise PilotDraftValidationError("unsupported pilot draft stage or protocol version")

    generated_at = _text(payload.get("generated_at"), "generated_at", 80, required=True)
    try:
        parsed_time = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
        if parsed_time.tzinfo is None or parsed_time.utcoffset() is None:
            raise ValueError("timezone missing")
    except ValueError as exc:
        raise PilotDraftValidationError("generated_at must be an ISO-8601 timestamp with timezone") from exc

    registration = payload.get("registration")
    pilot = payload.get("pilot")
    readiness = payload.get("readiness")
    if not isinstance(registration, dict) or set(registration) != {
        "name", "type", "website", "domains", "channels", "description"
    }:
        raise PilotDraftValidationError("registration has an invalid shape")
    if not isinstance(pilot, dict) or set(pilot) != {"requested_claims", "evidence_boundary"}:
        raise PilotDraftValidationError("pilot has an invalid shape")
    if not isinstance(readiness, dict) or set(readiness) != {
        "production_identity_created", "server_submission", "note"
    }:
        raise PilotDraftValidationError("readiness has an invalid shape")
    if readiness.get("production_identity_created") is not False:
        raise PilotDraftValidationError("a pilot draft cannot create a production identity")
    if readiness.get("server_submission") is not False:
        raise PilotDraftValidationError("the client cannot assert that a draft was already submitted")

    name = _text(registration.get("name"), "name", 180, required=True)
    business_type = _text(registration.get("type"), "type", 30, required=True)
    if business_type not in ALLOWED_TYPES:
        raise PilotDraftValidationError("unsupported business type")
    website = _http_url(registration.get("website"), "website")
    domains = _lines(registration.get("domains"), "domains", 50, 253)
    domains = list(dict.fromkeys(_domain(item) for item in domains if item))
    channels = _lines(registration.get("channels"), "channels", 50, 500)
    channels = list(dict.fromkeys(_http_url(item, "channel", required=True) for item in channels))
    description = _text(registration.get("description"), "description", 2000)
    claims = _lines(pilot.get("requested_claims"), "requested_claims", 4, 80)
    if not claims or any(claim not in ALLOWED_CLAIMS for claim in claims):
        raise PilotDraftValidationError("at least one supported pilot claim is required")
    evidence_boundary = _text(pilot.get("evidence_boundary"), "evidence_boundary", 3000)
    note = _text(readiness.get("note"), "readiness note", 500)

    return {
        "stage": "PILOT_DRAFT",
        "protocol_version": "0.1",
        "generated_at": parsed_time.isoformat().replace("+00:00", "Z"),
        "registration": {
            "name": name,
            "type": business_type,
            "website": website,
            "domains": domains,
            "channels": channels,
            "description": description,
        },
        "pilot": {
            "requested_claims": claims,
            "evidence_boundary": evidence_boundary,
        },
        "readiness": {
            "production_identity_created": False,
            "server_submission": True,
            "note": "Received for controlled pilot review only. No official identity or verification was created.",
        },
    }
