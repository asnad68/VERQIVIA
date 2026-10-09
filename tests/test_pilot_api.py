"""End-to-end HTTP contract tests for the authenticated pilot-intake API."""

from __future__ import annotations

import http.client
import json
import tempfile
import threading
import unittest
import uuid
from pathlib import Path

import src.nothing_api as api_module
from src.nothing_api import build_server
from src.nothing_auth import AuthenticatedPrincipal
from src.nothing_store import SQLiteNothingStore


class TestActorAuthenticator:
    """Deterministic test-only authenticator; never used by a deployment."""

    configured = True

    def authenticate(self, authorization: str | None) -> AuthenticatedPrincipal | None:
        actors = {
            "Bearer pilot-token-a": "test-issuer#actor-a",
            "Bearer pilot-token-b": "test-issuer#actor-b",
        }
        actor = actors.get(authorization or "")
        if actor is None:
            return None
        subject = actor.rsplit("#", 1)[-1]
        return AuthenticatedPrincipal(
            actor=actor,
            subject=subject,
            issuer="https://issuer.test",
            client_id="verqivia-test-client",
            scopes=frozenset({"nothing:pilot:write"}),
            claims={"sub": subject},
        )

    def authorize(self, principal: AuthenticatedPrincipal, action: str) -> bool:
        return action == "nothing:pilot:write" and action in principal.scopes


def make_draft(name: str = "Example Organization") -> dict:
    return {
        "stage": "PILOT_DRAFT",
        "protocol_version": "0.1",
        "generated_at": "2026-10-09T12:00:00Z",
        "registration": {
            "name": name,
            "type": "business",
            "website": "https://example.com",
            "domains": ["example.com"],
            "channels": ["https://www.linkedin.com/company/example"],
            "description": "Synthetic data for automated API tests.",
        },
        "pilot": {
            "requested_claims": ["official_domain", "official_website"],
            "evidence_boundary": "Synthetic test only; no real company data.",
        },
        "readiness": {
            "production_identity_created": False,
            "server_submission": False,
            "note": "Local draft only.",
        },
    }


class AuthenticatedPilotApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tempdir = tempfile.TemporaryDirectory(prefix="verqivia-pilot-api-")
        cls.store = SQLiteNothingStore(Path(cls.tempdir.name) / "pilot.sqlite3")
        cls.authenticator = TestActorAuthenticator()
        cls.old_origins = api_module.WRITE_CORS_ALLOWED_ORIGINS
        api_module.WRITE_CORS_ALLOWED_ORIGINS = ("https://portal.example",)
        cls.server = build_server(
            "127.0.0.1",
            0,
            store=cls.store,
            auth_mode="static-bearer",
            portal_authenticator=cls.authenticator,
        )
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.host, cls.port = cls.server.server_address

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        cls.store.close()
        api_module.WRITE_CORS_ALLOWED_ORIGINS = cls.old_origins
        cls.tempdir.cleanup()

    def request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        origin: str | None = "https://portal.example",
        payload: dict | bytes | None = None,
        idempotency_key: str | None = None,
        content_type: str = "application/json",
    ):
        headers: dict[str, str] = {}
        if token:
            headers["Authorization"] = token
        if origin:
            headers["Origin"] = origin
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        body = None
        if isinstance(payload, dict):
            body = json.dumps(payload).encode("utf-8")
        elif isinstance(payload, bytes):
            body = payload
        if body is not None:
            headers["Content-Type"] = content_type
        connection = http.client.HTTPConnection(self.host, self.port, timeout=5)
        try:
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            raw = response.read()
            return response, raw
        finally:
            connection.close()

    def submit(self, *, token: str = "Bearer pilot-token-a", key: str | None = None, draft: dict | None = None):
        return self.request(
            "POST",
            "/v1/pilot/drafts",
            token=token,
            payload=draft or make_draft(),
            idempotency_key=key or str(uuid.uuid4()),
        )

    def test_unauthenticated_submission_is_rejected(self) -> None:
        response, body = self.request(
            "POST",
            "/v1/pilot/drafts",
            payload=make_draft(),
            idempotency_key=str(uuid.uuid4()),
        )
        self.assertEqual(response.status, 401)
        self.assertEqual(json.loads(body)["code"], "UNAUTHORIZED")

    def test_authenticated_submission_can_be_read_back_by_same_actor(self) -> None:
        response, body = self.submit()
        self.assertEqual(response.status, 201)
        self.assertEqual(response.getheader("Access-Control-Allow-Origin"), "https://portal.example")
        result = json.loads(body)["data"]
        self.assertEqual(result["status"], "RECEIVED")
        self.assertFalse(result["production_identity_created"])
        self.assertIsInstance(result["draft_id"], str)

        read_response, read_body = self.request(
            "GET",
            f"/v1/pilot/drafts/{result['draft_id']}",
            token="Bearer pilot-token-a",
        )
        self.assertEqual(read_response.status, 200)
        data = json.loads(read_body)["data"]
        self.assertEqual(data["draft_id"], result["draft_id"])
        self.assertEqual(data["payload"]["registration"]["name"], "Example Organization")
        self.assertFalse(data["production_identity_created"])

    def test_same_idempotency_key_replays_and_changed_payload_conflicts(self) -> None:
        key = str(uuid.uuid4())
        first, first_body = self.submit(key=key)
        second, second_body = self.submit(key=key)
        first_data = json.loads(first_body)["data"]
        second_data = json.loads(second_body)["data"]
        self.assertEqual(first.status, 201)
        self.assertEqual(second.status, 200)
        self.assertEqual(first_data["draft_id"], second_data["draft_id"])
        self.assertTrue(second_data["replayed"])

        conflict, conflict_body = self.submit(key=key, draft=make_draft("Different Organization"))
        self.assertEqual(conflict.status, 409)
        self.assertEqual(json.loads(conflict_body)["code"], "CONFLICT")

    def test_draft_isolation_hides_another_actors_record(self) -> None:
        response, body = self.submit()
        self.assertEqual(response.status, 201)
        draft_id = json.loads(body)["data"]["draft_id"]

        owner_response, _ = self.request("GET", f"/v1/pilot/drafts/{draft_id}", token="Bearer pilot-token-a")
        other_response, other_body = self.request("GET", f"/v1/pilot/drafts/{draft_id}", token="Bearer pilot-token-b")
        self.assertEqual(owner_response.status, 200)
        self.assertEqual(other_response.status, 404)
        self.assertEqual(json.loads(other_body)["code"], "NOT_FOUND")

    def test_browser_preflight_allows_only_required_portal_headers(self) -> None:
        response, body = self.request(
            "OPTIONS",
            "/v1/pilot/drafts",
            token=None,
            origin="https://portal.example",
        )
        self.assertEqual(response.status, 204)
        self.assertEqual(response.getheader("Access-Control-Allow-Origin"), "https://portal.example")
        self.assertEqual(response.getheader("Access-Control-Allow-Methods"), "POST, OPTIONS")
        self.assertEqual(
            set(response.getheader("Access-Control-Allow-Headers").lower().split(", ")),
            {"authorization", "content-type", "idempotency-key"},
        )
        self.assertEqual(body, b"")

    def test_unapproved_browser_origin_is_rejected(self) -> None:
        response, body = self.request(
            "POST",
            "/v1/pilot/drafts",
            token="Bearer pilot-token-a",
            origin="https://attacker.example",
            payload=make_draft(),
            idempotency_key=str(uuid.uuid4()),
        )
        self.assertEqual(response.status, 403)
        self.assertEqual(json.loads(body)["code"], "ORIGIN_NOT_ALLOWED")

    def test_invalid_draft_shape_is_rejected_without_storage(self) -> None:
        response, body = self.request(
            "POST",
            "/v1/pilot/drafts",
            token="Bearer pilot-token-a",
            payload={},
            idempotency_key=str(uuid.uuid4()),
        )
        self.assertEqual(response.status, 400)
        self.assertEqual(json.loads(body)["code"], "INVALID_PILOT_DRAFT")

    def test_non_json_submission_is_rejected(self) -> None:
        response, body = self.request(
            "POST",
            "/v1/pilot/drafts",
            token="Bearer pilot-token-a",
            payload=b"not-json",
            content_type="text/plain",
            idempotency_key=str(uuid.uuid4()),
        )
        self.assertEqual(response.status, 415)
        self.assertEqual(json.loads(body)["code"], "UNSUPPORTED_MEDIA_TYPE")


if __name__ == "__main__":
    unittest.main()
