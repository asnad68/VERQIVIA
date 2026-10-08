import unittest

from src import nothing_enrollment_gateway as gateway
from src.nothing_enrollment import RegistrationDraft


class FakeStore:
    def __init__(self, challenge):
        self.challenge = challenge

    def get_auth_challenge(self, challenge_id):
        if challenge_id != self.challenge["challenge_id"]:
            raise AssertionError("unexpected challenge id")
        return self.challenge


class EnrollmentGatewayTests(unittest.TestCase):
    def test_gateway_imports_and_google_authorization_binding(self):
        draft = RegistrationDraft.from_mapping(
            {
                "name": "Apple",
                "website": "https://www.apple.com",
                "domains": ["apple.com"],
            }
        )
        challenge = {
            "challenge_id": "google-1",
            "purpose": "google_oidc",
            "authorization_status": "AUTHORIZED",
            "registration_consumed_at": None,
            "wallet_address": None,
            "expires_at": "2999-01-01T00:00:00+00:00",
            "authorization": {
                "registration_digest": draft.digest(),
                "domain": "apple.com",
                "authorization_method": "google_oidc+dns_txt",
            },
        }
        authorization = gateway._registration_authorization(
            FakeStore(challenge),
            "google-1",
            "0x1111111111111111111111111111111111111111",
            draft,
        )
        self.assertEqual(authorization["domain"], "apple.com")

    def test_rate_limiter_bounds_unique_key_memory(self):
        limiter = gateway.RateLimiter(max_keys=2)
        self.assertTrue(limiter.allow("a"))
        self.assertTrue(limiter.allow("b"))
        self.assertFalse(limiter.allow("c"))

    def test_safe_json_rejects_duplicate_keys(self):
        body = b'{"registration":{"name":"Example"},"registration":{"name":"Attacker"}}'
        with self.assertRaises(gateway.EnrollmentValidationError):
            gateway._safe_json(body)

    def test_google_authorization_rejects_changed_registration(self):
        draft = RegistrationDraft.from_mapping(
            {"name": "Apple", "domains": ["apple.com"]}
        )
        changed = RegistrationDraft.from_mapping(
            {"name": "Apple", "domains": ["example.com"]}
        )
        challenge = {
            "challenge_id": "google-2",
            "purpose": "google_oidc",
            "authorization_status": "AUTHORIZED",
            "registration_consumed_at": None,
            "wallet_address": None,
            "expires_at": "2999-01-01T00:00:00+00:00",
            "authorization": {
                "registration_digest": draft.digest(),
                "domain": "apple.com",
            },
        }
        with self.assertRaises(Exception):
            gateway._registration_authorization(
                FakeStore(challenge),
                "google-2",
                "0x1111111111111111111111111111111111111111",
                changed,
            )


if __name__ == "__main__":
    unittest.main()
