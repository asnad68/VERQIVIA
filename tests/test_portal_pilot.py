import hashlib
import http.client
import json
import os
import tempfile
import threading
import unittest
import uuid
from pathlib import Path

from src.nothing_api import build_server
from src.nothing_pilot import PilotDraftValidationError, parse_pilot_draft
from src.nothing_store import ConflictError, SQLiteNothingStore


def sample_draft():
    return {
        "stage": "PILOT_DRAFT",
        "protocol_version": "0.1",
        "generated_at": "2026-10-09T12:00:00.000Z",
        "registration": {
            "name": "Example Organization",
            "type": "business",
            "website": "https://example.com/",
            "domains": ["example.com"],
            "channels": ["https://www.linkedin.com/company/example"],
            "description": "Synthetic pilot fixture",
        },
        "pilot": {
            "requested_claims": ["official_domain", "official_website"],
            "evidence_boundary": "Public website and DNS can be inspected.\nNo private documents are submitted.",
        },
        "readiness": {
            "production_identity_created": False,
            "server_submission": False,
            "note": "Local planning draft only.",
        },
    }


def parse_sample():
    return parse_pilot_draft(
        json.dumps(sample_draft(), ensure_ascii=False).encode("utf-8"),
        "application/json",
    )


class PilotDraftValidationTests(unittest.TestCase):
    def test_normalizes_and_marks_server_received_draft_without_creating_identity(self):
        parsed = parse_sample()
        self.assertEqual(parsed["stage"], "PILOT_DRAFT")
        self.assertEqual(parsed["registration"]["domains"], ["example.com"])
        self.assertTrue(parsed["readiness"]["server_submission"])
        self.assertFalse(parsed["readiness"]["production_identity_created"])

    def test_rejects_duplicate_json_properties(self):
        body = b'{"stage":"PILOT_DRAFT","stage":"PILOT_DRAFT"}'
        with self.assertRaises(PilotDraftValidationError):
            parse_pilot_draft(body, "application/json")

    def test_rejects_private_ip_and_local_hostname_domains(self):
        for domain in ("127.0.0.1", "localhost", "example.local", "company.internal"):
            with self.subTest(domain=domain):
                payload = sample_draft()
                payload["registration"]["domains"] = [domain]
                with self.assertRaises(PilotDraftValidationError):
                    parse_pilot_draft(json.dumps(payload).encode(), "application/json")

    def test_rejects_malformed_unicode_domain_without_internal_error(self):
        payload = sample_draft()
        payload["registration"]["domains"] = ["\\ud800"]
        with self.assertRaises(PilotDraftValidationError):
            parse_pilot_draft(json.dumps(payload).encode("utf-8"), "application/json")

    def test_rejects_control_characters_in_urls(self):
        payload = sample_draft()
        payload["registration"]["website"] = "https://example.com/\\npath"
        with self.assertRaises(PilotDraftValidationError):
            parse_pilot_draft(json.dumps(payload).encode("utf-8"), "application/json")

    def test_rejects_non_http_url_credentials_and_unsupported_claims(self):
        for bad_website, claims in (
            ("javascript:alert(1)", ["official_website"]),
            ("https://user:pass@example.com/", ["official_website"]),
            ("https://example.com/", ["make_me_verified"]),
        ):
            with self.subTest(website=bad_website, claims=claims):
                payload = sample_draft()
                payload["registration"]["website"] = bad_website
                payload["pilot"]["requested_claims"] = claims
                with self.assertRaises(PilotDraftValidationError):
                    parse_pilot_draft(json.dumps(payload).encode(), "application/json")

    def test_body_size_and_media_type_are_bounded(self):
        with self.assertRaises(OverflowError):
            parse_pilot_draft(b" " * 32769, "application/json")
        with self.assertRaises(TypeError):
            parse_pilot_draft(b"{}", "text/plain")


class SQLitePilotDraftPersistenceTests(unittest.TestCase):
    def test_idempotency_and_actor_scoping(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteNothingStore(Path(tmp) / "pilot.sqlite3")
            try:
                draft = parse_sample()
                fingerprint = hashlib.sha256(
                    json.dumps(draft, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest()
                first = store.submit_pilot_draft(
                    actor="issuer#company-user",
                    draft_id=str(uuid.uuid4()),
                    idempotency_key="pilot-submission-123",
                    request_sha256=fingerprint,
                    payload=draft,
                )
                replay = store.submit_pilot_draft(
                    actor="issuer#company-user",
                    draft_id=str(uuid.uuid4()),
                    idempotency_key="pilot-submission-123",
                    request_sha256=fingerprint,
                    payload=draft,
                )
                self.assertEqual(first["draft_id"], replay["draft_id"])
                self.assertTrue(replay["replayed"])
                self.assertIsNotNone(store.get_pilot_draft(
                    actor="issuer#company-user", draft_id=first["draft_id"]
                ))
                self.assertIsNone(store.get_pilot_draft(
                    actor="someone-else", draft_id=first["draft_id"]
                ))
                with self.assertRaises(ConflictError):
                    store.submit_pilot_draft(
                        actor="issuer#company-user",
                        draft_id=str(uuid.uuid4()),
                        idempotency_key="pilot-submission-123",
                        request_sha256="a" * 64,
                        payload={"changed": True},
                    )
            finally:
                store.close()


class AuthenticatedPilotDraftApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.server = build_server(
            "127.0.0.1",
            0,
            storage_backend="sqlite",
            db_path=Path(cls.temp_dir.name) / "api.sqlite3",
            auth_mode="static-bearer",
            ingestion_token="ingestion-test-token",
            portal_token="pilot-test-token",
        )
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.host, cls.port = cls.server.server_address

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=5)
        cls.server.server_close()
        cls.temp_dir.cleanup()

    def request(self, path, *, method="GET", token=None, payload=None, idempotency_key=None):
        connection = http.client.HTTPConnection(self.host, self.port, timeout=5)
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if token:
            headers["Authorization"] = "Bearer " + token
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        raw = response.read()
        status = response.status
        connection.close()
        return status, json.loads(raw) if raw else None

    def test_submission_requires_authentication(self):
        status, body = self.request(
            "/v1/pilot/drafts",
            method="POST",
            payload=sample_draft(),
            idempotency_key="pilot-auth-check",
        )
        self.assertEqual(status, 401)
        self.assertEqual(body["code"], "UNAUTHORIZED")

    def test_authenticated_submit_replay_and_owner_only_read(self):
        key = "pilot-api-" + uuid.uuid4().hex
        status, body = self.request(
            "/v1/pilot/drafts",
            method="POST",
            token="pilot-test-token",
            payload=sample_draft(),
            idempotency_key=key,
        )
        self.assertEqual(status, 201)
        data = body["data"]
        self.assertEqual(data["status"], "RECEIVED")
        self.assertFalse(data["production_identity_created"])
        status2, body2 = self.request(
            "/v1/pilot/drafts",
            method="POST",
            token="pilot-test-token",
            payload=sample_draft(),
            idempotency_key=key,
        )
        self.assertEqual(status2, 200)
        self.assertEqual(body2["data"]["draft_id"], data["draft_id"])
        self.assertTrue(body2["data"]["replayed"])
        status3, retrieved = self.request(
            "/v1/pilot/drafts/" + data["draft_id"],
            token="pilot-test-token",
        )
        self.assertEqual(status3, 200)
        self.assertEqual(retrieved["data"]["payload"]["registration"]["name"], "Example Organization")
        self.assertFalse(retrieved["data"]["production_identity_created"])

    def test_idempotency_conflict_and_foreign_read_not_found(self):
        key = "pilot-conflict-" + uuid.uuid4().hex
        first = sample_draft()
        status, result = self.request(
            "/v1/pilot/drafts",
            method="POST",
            token="pilot-test-token",
            payload=first,
            idempotency_key=key,
        )
        self.assertEqual(status, 201)
        changed = sample_draft()
        changed["registration"]["name"] = "A different organization"
        conflict_status, conflict = self.request(
            "/v1/pilot/drafts",
            method="POST",
            token="pilot-test-token",
            payload=changed,
            idempotency_key=key,
        )
        self.assertEqual(conflict_status, 409)
        self.assertEqual(conflict["code"], "CONFLICT")

        foreign_token = "not-the-configured-token"
        foreign_status, foreign = self.request(
            "/v1/pilot/drafts/" + result["data"]["draft_id"],
            token=foreign_token,
        )
        self.assertEqual(foreign_status, 401)
        self.assertEqual(foreign["code"], "UNAUTHORIZED")


if __name__ == "__main__":
    unittest.main()
