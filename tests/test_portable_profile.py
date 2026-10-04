import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from src.verqivia_profile import (
    PROFILE_TYPE,
    PROFILE_VERSION,
    build_portable_profile,
)


ROOT = Path(__file__).resolve().parents[1]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class PortableProfileTests(unittest.TestCase):
    def setUp(self):
        self.identity = read_json(ROOT / "examples/NTH-000001.json")
        self.evidence = [read_json(ROOT / "examples/EVD-000001.json")]
        self.events = [read_json(ROOT / "examples/VER-000001.json")]
        self.registry = read_json(ROOT / "procedures/registry.json")
        self.schema = read_json(ROOT / "schema/portable-verification-profile.schema.json")

    def test_profile_is_schema_valid(self):
        profile = build_portable_profile(
            self.identity,
            verification_events=self.events,
            evidence_records=self.evidence,
            procedure_registry=self.registry,
            public_verify_url="https://example.test/verify.html?id=NTH-000001",
        )
        errors = list(
            Draft202012Validator(
                self.schema, format_checker=FormatChecker()
            ).iter_errors(profile)
        )
        self.assertEqual(errors, [])

    def test_profile_is_additive_and_non_destructive(self):
        profile = build_portable_profile(
            self.identity,
            verification_events=self.events,
            evidence_records=self.evidence,
            procedure_registry=self.registry,
        )
        self.assertEqual(profile["profile_type"], PROFILE_TYPE)
        self.assertEqual(profile["profile_version"], PROFILE_VERSION)
        self.assertEqual(profile["verqivia_id"], self.identity["nothing_id"])
        self.assertNotIn("cryptographic_proof", profile)

    def test_claims_follow_resolved_status(self):
        identity = json.loads(json.dumps(self.identity))
        identity["claims"][0]["status"] = "SELF-CLAIMED"
        profile = build_portable_profile(
            identity,
            verification_events=self.events,
            evidence_records=self.evidence,
            procedure_registry=self.registry,
        )
        self.assertEqual(profile["claims"][0]["status"], "SOURCE-VERIFIED")
        self.assertEqual(profile["claims"][0]["current_event_id"], "VER-000001")

    def test_revoked_identity_maps_to_revoked_profile(self):
        identity = json.loads(json.dumps(self.identity))
        identity["revocation"] = {
            "status": "REVOKED",
            "reason": "Synthetic test only",
            "revoked_at": "2026-09-25T00:00:00Z",
        }
        profile = build_portable_profile(identity)
        self.assertEqual(profile["status"], "REVOKED")

    def test_partial_verification_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            build_portable_profile(
                self.identity,
                verification_events=self.events,
                evidence_records=self.evidence,
            )


if __name__ == "__main__":
    unittest.main()
