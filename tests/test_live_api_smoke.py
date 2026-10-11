from __future__ import annotations

import json
import unittest

from scripts.smoke_test_live_api import (
    SmokeTestError,
    normalize_api_origin,
    run_smoke_test,
)


class LiveSmokeOriginValidationTests(unittest.TestCase):
    def test_accepts_https_origin_and_normalizes_trailing_slash(self):
        self.assertEqual(
            normalize_api_origin("  https://api.example.com/  "),
            "https://api.example.com",
        )

    def test_accepts_local_http_for_local_testing_only(self):
        self.assertEqual(normalize_api_origin("http://localhost:8080"), "http://localhost:8080")

    def test_rejects_path_query_credentials_and_non_local_http(self):
        for value in (
            "https://api.example.com/api",
            "https://api.example.com?debug=true",
            "https://user:secret@api.example.com",
            "http://api.example.com",
        ):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_api_origin(value)


class LiveSmokeBehaviorTests(unittest.TestCase):
    def fake_api(self, *, unauthenticated_write_status=503, blocked_origin_status=403):
        def request(origin, path, *, method="GET", browser_origin=None, payload=None):
            if path == "/healthz":
                return 200, {}, b'{"status":"ok"}'
            if path == "/readyz":
                return 200, {}, b'{"status":"ready","api_version":"1"}'
            if path == "/v1/identity/NTH-000001":
                return 200, {}, b'{"data":{"id":"NTH-000001"},"meta":{"demo":true}}'
            if path == "/v1/identity/NTH-000001/profile":
                return 200, {}, b'{"data":{"id":"NTH-000001","profile_version":"0.2"},"meta":{"demo":true}}'
            if path == "/v1/pilot/drafts" and method == "OPTIONS":
                if browser_origin == "https://unapproved.invalid":
                    return blocked_origin_status, {}, b'{"status":403}'
                return 204, {"Access-Control-Allow-Origin": "https://asnad68.github.io"}, b""
            if path == "/v1/pilot/drafts" and method == "POST":
                self.assertIsNotNone(payload)
                self.assertNotIn("Authorization", {})  # The test request is deliberately unauthenticated.
                return unauthenticated_write_status, {}, b'{"status":"denied"}'
            raise AssertionError(f"Unexpected smoke-test request: {method} {path}")

        return request

    def test_smoke_passes_with_synthetic_reads_and_closed_write_boundary(self):
        checks = run_smoke_test(
            "https://api.example.com",
            request=self.fake_api(),
        )
        self.assertEqual(len(checks), 7)
        self.assertIn("unapproved browser origin rejected", checks)
        self.assertIn("unauthenticated pilot write denied", checks)

    def test_smoke_fails_if_unauthenticated_write_is_accepted(self):
        with self.assertRaises(SmokeTestError):
            run_smoke_test(
                "https://api.example.com",
                request=self.fake_api(unauthenticated_write_status=201),
            )

    def test_smoke_fails_if_demo_endpoint_is_not_marked_synthetic(self):
        request = self.fake_api()

        def altered(origin, path, *, method="GET", browser_origin=None, payload=None):
            status, headers, body = request(
                origin, path, method=method, browser_origin=browser_origin, payload=payload
            )
            if path == "/v1/identity/NTH-000001":
                return status, headers, json.dumps({
                    "data": {"id": "NTH-000001"},
                    "meta": {"demo": False},
                }).encode()
            return status, headers, body

        with self.assertRaises(SmokeTestError):
            run_smoke_test("https://api.example.com", request=altered)

    def test_smoke_fails_if_unapproved_origin_is_not_rejected(self):
        with self.assertRaises(SmokeTestError):
            run_smoke_test(
                "https://api.example.com",
                request=self.fake_api(blocked_origin_status=204),
            )


if __name__ == "__main__":
    unittest.main()
