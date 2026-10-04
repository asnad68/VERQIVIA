import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from src.nothing_proof import verify_envelope


ROOT = Path(__file__).resolve().parents[1]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class VerifyWebAssetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bundle = read_json(ROOT / "site/data/demo-bundle.json")
        self.proof = read_json(ROOT / "site/data/demo-proof.json")
        self.registry = read_json(ROOT / "site/data/demo-issuer-registry.json")

    def test_public_demo_assets_are_json_and_have_matching_identity(self):
        identity_ids = {
            item["nothing_id"] for item in self.bundle.get("identities", [])
        }
        self.assertIn(self.proof["resource_id"], identity_ids)
        self.assertEqual(self.proof["resource_type"], "identity")

    def test_public_demo_proof_is_cryptographically_valid(self):
        identity = next(
            item for item in self.bundle["identities"]
            if item["nothing_id"] == self.proof["resource_id"]
        )
        result = verify_envelope(
            self.proof,
            identity,
            self.registry,
            at_time=self.proof["proof"]["created"],
        )
        self.assertTrue(result["valid"])
        self.assertTrue(all(result["checks"].values()))

    def test_public_demo_assets_match_json_schemas(self):
        proof_schema = read_json(ROOT / "schema/proof.schema.json")
        registry_schema = read_json(ROOT / "schema/issuer-registry.schema.json")
        proof_errors = list(
            Draft202012Validator(
                proof_schema, format_checker=FormatChecker()
            ).iter_errors(self.proof)
        )
        registry_errors = list(
            Draft202012Validator(
                registry_schema, format_checker=FormatChecker()
            ).iter_errors(self.registry)
        )
        self.assertEqual(proof_errors, [])
        self.assertEqual(registry_errors, [])

    def test_discovery_pointer_is_explicitly_synthetic(self):
        discovery = read_json(ROOT / "site/.well-known/verqivia.json")
        self.assertTrue(discovery["synthetic"])
        self.assertEqual(
            discovery["verqivia_id"],
            self.proof["resource_id"],
        )
        self.assertEqual(
            discovery["verification_profile"],
            "VERQIVIA-PORTABLE-VERIFICATION-PROFILE",
        )


if __name__ == "__main__":
    unittest.main()
