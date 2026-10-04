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

    def test_verify_page_references_existing_local_assets(self):
        html = (ROOT / "site/verify.html").read_text(encoding="utf-8")
        app_js = (ROOT / "site/assets/app.js").read_text(encoding="utf-8")

        for asset in ("assets/styles.css", "config.js", "assets/app.js?v="):
            self.assertIn(asset, html)

        for asset in (
            "data/demo-bundle.json",
            "data/demo-proof.json",
            "data/demo-issuer-registry.json",
        ):
            self.assertIn(asset, app_js)

        for relative_path in (
            "site/assets/styles.css",
            "site/config.js",
            "site/assets/app.js",
            "site/data/demo-bundle.json",
            "site/data/demo-proof.json",
            "site/data/demo-issuer-registry.json",
        ):
            self.assertTrue((ROOT / relative_path).is_file(), relative_path)

    def test_portable_profile_matches_demo_identity(self):
        profile = read_json(ROOT / "site/data/portable-profile-demo.json")
        identity = next(
            item for item in self.bundle["identities"]
            if item["nothing_id"] == profile["verqivia_id"]
        )
        self.assertEqual(profile["subject"], identity["subject"])
        self.assertEqual(profile["claims"][0]["claim_id"], identity["claims"][0]["claim_id"])
        self.assertEqual(profile["claims"][0]["statement"], identity["claims"][0]["statement"])
        self.assertEqual(profile["claims"][0]["status"], identity["claims"][0]["status"])
        self.assertEqual(profile["claims"][0]["current_event_id"], "VER-000001")

    def test_public_html_has_no_inline_style_attributes(self):
        for html_path in (ROOT / "site").glob("*.html"):
            html = html_path.read_text(encoding="utf-8")
            self.assertNotRegex(
                html,
                r"\bstyle\s*=",
                f"inline style attribute found in {html_path.name}",
            )

    def test_ai_discovery_points_to_machine_endpoint(self):
        discovery = read_json(ROOT / "site/.well-known/verqivia-ai.json")
        self.assertEqual(discovery["document_type"], "VERQIVIA-AI-DISCOVERY")
        self.assertEqual(
            discovery["profile"]["name"],
            "VERQIVIA-PORTABLE-VERIFICATION-PROFILE",
        )
        self.assertEqual(
            discovery["endpoints"]["portable_profile"],
            "/v1/identity/{nothing_id}/profile",
        )
        self.assertTrue(discovery["synthetic_demo"])

    def test_commercial_surface_has_required_pages_and_links(self):
        commercial = (ROOT / "site/commercial.html").read_text(encoding="utf-8")
        terms = (ROOT / "site/terms.html").read_text(encoding="utf-8")
        self.assertIn("Start a controlled pilot", commercial)
        self.assertIn("Contact the project founder", commercial)
        self.assertIn("./terms.html", commercial)
        self.assertIn("Final production terms", terms)
        self.assertIn("./pilot.html", terms)
        self.assertTrue((ROOT / "site/commercial.html").is_file())
        self.assertTrue((ROOT / "site/terms.html").is_file())

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
