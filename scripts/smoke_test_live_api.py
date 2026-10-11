#!/usr/bin/env python3
"""Run safe, synthetic-data smoke checks against a deployed VERQIVIA API.

This deliberately avoids credentials and real company data. It verifies public
readiness, the published synthetic identity/profile, CORS boundaries, and that
pilot write access remains unavailable without an authorized token.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from typing import Any, Callable

DEMO_ID = "NTH-000001"
PUBLIC_SITE_ORIGIN = "https://asnad68.github.io"
TIMEOUT_SECONDS = 10


class SmokeTestError(RuntimeError):
    """Raised when the deployed API fails a release-gate smoke check."""


def normalize_api_origin(value: str) -> str:
    """Validate and normalize a bare API origin; never accept a URL path."""
    candidate = str(value or "").strip()
    if not candidate:
        raise ValueError("API origin is required (use --api-origin or VERQIVIA_SMOKE_API_ORIGIN).")
    try:
        parsed = urlsplit(candidate)
        hostname = parsed.hostname
    except ValueError as exc:
        raise ValueError("API origin is malformed.") from exc
    if not parsed.scheme or not parsed.netloc or not hostname:
        raise ValueError("API origin must be an absolute origin such as https://api.example.com.")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("API origin must not contain credentials, query parameters, or a fragment.")
    if parsed.path not in ("", "/"):
        raise ValueError("Use the API origin only; do not include a path prefix.")
    if parsed.scheme != "https":
        local_hosts = {"localhost", "127.0.0.1", "::1"}
        if parsed.scheme != "http" or hostname.lower() not in local_hosts:
            raise ValueError("The API must use HTTPS (HTTP is allowed only for localhost smoke tests).")
    return f"{parsed.scheme.lower()}://{parsed.netloc}".rstrip("/")


def request_api(
    api_origin: str,
    path: str,
    *,
    method: str = "GET",
    browser_origin: str | None = None,
    payload: dict[str, Any] | None = None,
) -> tuple[int, Any, bytes]:
    """Make one bounded HTTP request and preserve HTTP error responses."""
    headers = {"Accept": "application/json"}
    if browser_origin:
        headers["Origin"] = browser_origin
    body = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        if method.upper() == "POST":
            # This script only posts a synthetic pilot draft; use a valid key so
            # a denial cannot be explained by a malformed idempotency header.
            headers["Idempotency-Key"] = "11111111-1111-4111-8111-111111111111"
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    req = Request(f"{api_origin}{path}", data=body, headers=headers, method=method)
    try:
        with urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            return response.status, response.headers, response.read()
    except HTTPError as response:
        return response.code, response.headers, response.read()
    except (URLError, TimeoutError, OSError) as exc:
        raise SmokeTestError(f"{method} {path} could not reach the API: {exc}") from exc


def parse_json(status: int, body: bytes, path: str) -> dict[str, Any]:
    if not body:
        raise SmokeTestError(f"{path} returned HTTP {status} without a JSON body.")
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SmokeTestError(f"{path} returned invalid JSON (HTTP {status}).") from exc
    if not isinstance(payload, dict):
        raise SmokeTestError(f"{path} returned a JSON value other than an object.")
    return payload


def _header(headers: Any, name: str) -> str | None:
    getter = getattr(headers, "get", None)
    if not callable(getter):
        return None
    return getter(name) or getter(name.lower())


def _is_synthetic_record(data: Any) -> bool:
    """Recognize the published demo by its explicit experimental claim marker.

    The production Postgres store sets meta.demo=false even when reading this
    deliberately seeded synthetic record, so metadata alone is not sufficient.
    """
    if not isinstance(data, dict):
        return False
    subject = data.get("subject")
    claims = data.get("claims")
    if not isinstance(subject, dict) or not isinstance(claims, list):
        return False
    return any(
        isinstance(claim, dict)
        and "experimental demonstration" in str(claim.get("statement", "")).lower()
        for claim in claims
    )


def run_smoke_test(
    api_origin: str,
    request: Callable[..., tuple[int, Any, bytes]] = request_api,
) -> list[str]:
    """Execute release-gate checks using only synthetic values; return passed labels."""
    origin = normalize_api_origin(api_origin)
    passed: list[str] = []

    status, _, body = request(origin, "/healthz")
    health = parse_json(status, body, "/healthz")
    if status != 200 or health.get("status") != "ok":
        raise SmokeTestError("/healthz did not return HTTP 200 with status=ok.")
    passed.append("health endpoint")

    status, _, body = request(origin, "/readyz")
    ready = parse_json(status, body, "/readyz")
    if status != 200 or ready.get("status") != "ready":
        raise SmokeTestError("/readyz is not ready; persistence or schema may be unavailable.")
    passed.append("readiness endpoint")

    status, _, body = request(origin, f"/v1/identity/{DEMO_ID}")
    identity = parse_json(status, body, f"/v1/identity/{DEMO_ID}")
    identity_data = identity.get("data")
    if status != 200 or not isinstance(identity_data, dict) or identity_data.get("id") != DEMO_ID:
        raise SmokeTestError("The synthetic public identity endpoint failed or returned the wrong ID.")
    if not _is_synthetic_record(identity_data):
        raise SmokeTestError("The identity response lacks the explicit experimental-demo claim marker.")
    passed.append("synthetic identity read")

    profile_path = f"/v1/identity/{DEMO_ID}/profile"
    status, _, body = request(origin, profile_path)
    profile = parse_json(status, body, profile_path)
    profile_data = profile.get("data")
    if status != 200 or not isinstance(profile_data, dict) or profile_data.get("verqivia_id") != DEMO_ID:
        raise SmokeTestError("The portable verification profile endpoint failed or returned the wrong ID.")
    if not _is_synthetic_record(profile_data):
        raise SmokeTestError("The portable profile lacks the explicit experimental-demo claim marker.")
    passed.append("synthetic portable profile")

    status, headers, _ = request(
        origin, "/v1/pilot/drafts", method="OPTIONS", browser_origin=PUBLIC_SITE_ORIGIN
    )
    if status != 204 or _header(headers, "Access-Control-Allow-Origin") != PUBLIC_SITE_ORIGIN:
        raise SmokeTestError("The approved Portal CORS preflight failed.")
    passed.append("approved Portal CORS")

    status, _, _ = request(
        origin, "/v1/pilot/drafts", method="OPTIONS", browser_origin="https://unapproved.invalid"
    )
    if status != 403:
        raise SmokeTestError("An unapproved browser origin was not rejected with HTTP 403.")
    passed.append("unapproved browser origin rejected")

    # The body is synthetic and contains no credentials. The missing token must
    # result in a denial or an explicit not-configured response, never acceptance.
    fake_draft = {
        "stage": "PILOT_DRAFT",
        "protocol_version": "0.1",
        "generated_at": "2026-10-11T00:00:00Z",
        "registration": {
            "name": "VERQIVIA Synthetic Smoke-Test Example",
            "type": "business",
            "website": "https://example.com",
            "domains": ["example.com"],
            "channels": ["https://www.linkedin.com/company/example"],
            "description": "Synthetic test data only; no real company is represented.",
        },
        "pilot": {
            "requested_claims": ["official_domain", "official_website"],
            "evidence_boundary": "Synthetic smoke test; no real company data.",
        },
        "readiness": {
            "production_identity_created": False,
            "server_submission": False,
            "note": "Synthetic smoke test only.",
        },
    }
    status, _, _ = request(
        origin,
        "/v1/pilot/drafts",
        method="POST",
        browser_origin=PUBLIC_SITE_ORIGIN,
        payload=fake_draft,
    )
    if status not in {401, 503}:
        raise SmokeTestError(
            f"Unauthenticated pilot submission returned HTTP {status}; expected 401 or 503."
        )
    passed.append("unauthenticated pilot write denied")

    return passed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--api-origin",
        default=os.getenv("VERQIVIA_SMOKE_API_ORIGIN", ""),
        help="Bare HTTPS API origin (or set VERQIVIA_SMOKE_API_ORIGIN).",
    )
    args = parser.parse_args()
    try:
        origin = normalize_api_origin(args.api_origin)
        results = run_smoke_test(origin)
    except (ValueError, SmokeTestError) as exc:
        print(f"VERQIVIA LIVE SMOKE TEST: FAILED — {exc}", file=sys.stderr)
        return 1

    print(f"VERQIVIA LIVE SMOKE TEST: PASS — {len(results)} checks")
    for item in results:
        print(f"  PASS  {item}")
    print("Synthetic data only; this does not replace a full production security review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
