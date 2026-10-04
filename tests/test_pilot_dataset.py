import copy
import json
import unittest
from pathlib import Path

from src.nothing_protocol import RelationshipError, resolve_claim_relationships
from src.nothing_verify import (
    ValidationError,
    validate_evidence,
    validate_identity,
    validate_verification_event,
    load_json,
    validation_result,
)

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "pilot" / "controlled-dataset.json"


class ControlledPilotDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = json.loads(PILOT.read_text(encoding="utf-8"))
        cls.registry = load_json(ROOT / "procedures/registry.json")

    def test_dataset_is_explicitly_synthetic(self):
        self.assertTrue(self.dataset["synthetic"])
        self.assertTrue(self.dataset["dataset_id"].startswith("VERQIVIA-PILOT-SYNTHETIC-"))

    def test_identity_evidence_and_events_validate(self):
        identity = self.dataset["identities"][0]
        evidence = self.dataset["evidence"]
        events = self.dataset["verification_events"]

        validate_identity(identity)
        for item in evidence:
            validate_evidence(item)
        for event in events:
            validate_verification_event(event)

        resolved = resolve_claim_relationships(identity, evidence, events, self.registry)
        claim = resolved["claims"]["CLM-010001"]
        self.assertEqual(claim["current_event_id"], "VER-010002")
        self.assertEqual(claim["current_status"], "SOURCE-VERIFIED")
        self.assertEqual(claim["verification_event_ids"], ["VER-010001", "VER-010002"])
        self.assertEqual(claim["status_consistency"], "CONSISTENT")

    def test_supersession_keeps_history_and_changes_current_event(self):
        identity = self.dataset["identities"][0]
        result = resolve_claim_relationships(
            identity,
            self.dataset["evidence"],
            self.dataset["verification_events"],
            self.registry,
        )
        self.assertEqual(result["verification_event_count"], 2)
        self.assertEqual(result["unreferenced_evidence"], [])

    def test_identity_revocation_is_explicit_and_non_destructive(self):
        identity = copy.deepcopy(self.dataset["identities"][0])
        identity["revocation"] = {
            "status": "REVOKED",
            "reason": "Synthetic revocation test",
            "revoked_at": "2026-10-04T00:10:00Z",
        }
        validate_identity(identity)
        result = resolve_claim_relationships(
            identity,
            self.dataset["evidence"],
            self.dataset["verification_events"],
            self.registry,
        )
        self.assertEqual(result["nothing_id"], "NTH-010001")
        self.assertEqual(
            result["claims"]["CLM-010001"]["verification_event_ids"],
            ["VER-010001", "VER-010002"],
        )

    def test_parallel_supersession_is_rejected(self):
        events = copy.deepcopy(self.dataset["verification_events"])
        third = copy.deepcopy(events[1])
        third["event_id"] = "VER-010003"
        third["occurred_at"] = "2026-10-04T00:06:00Z"
        events.append(third)
        with self.assertRaises(RelationshipError):
            resolve_claim_relationships(
                self.dataset["identities"][0],
                self.dataset["evidence"],
                events,
                self.registry,
            )

    def test_invalid_pilot_identity_is_rejected(self):
        identity = copy.deepcopy(self.dataset["identities"][0])
        identity["nothing_id"] = "BAD-ID"
        self.assertFalse(validation_result(identity)["valid"])


if __name__ == "__main__":
    unittest.main()
