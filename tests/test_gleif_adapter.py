"""Unit tests for the read-only GLEIF reference-data adapter."""
from __future__ import annotations

import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from src import nothing_gleif as gleif


VALID_LEI = "5493001KJTIIGC8Y1R12"


def payload():
    return {
        "data": [
            {
                "id": VALID_LEI,
                "attributes": {
                    "entity": {
                        "legalName": {"name": "Example Holdings Limited"},
                        "legalAddress": {"country": "gb"},
                        "status": "ACTIVE",
                    },
                    "registration": {
                        "status": "ISSUED",
                        "lastUpdateDate": "2026-09-01T10:00:00Z",
                        "nextRenewalDate": "2027-09-01",
                    },
                },
            },
            {"id": "bad-id", "attributes": {"entity": {"legalName": {"name": "Spoof"}}}},
            {"id": VALID_LEI, "attributes": {"entity": {}}},
        ]
    }


class GleifAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        gleif.clear_gleif_cache()

    def tearDown(self) -> None:
        gleif.clear_gleif_cache()

    def test_normalizes_minimal_provenance_aware_legal_entity_data(self) -> None:
        with patch.object(gleif, "_fetch_json", return_value=payload()) as fetch:
            result = gleif.search_gleif_entities(" Example Holdings ", now=100.0)

        self.assertEqual(result["source"], "GLEIF Global LEI Index")
        self.assertEqual(result["query"], "Example Holdings")
        self.assertEqual(result["result_count"], 1)
        self.assertFalse(result["cache_hit"])
        record = result["results"][0]
        self.assertEqual(record["lei"], VALID_LEI)
        self.assertEqual(record["legal_name"], "Example Holdings Limited")
        self.assertEqual(record["country"], "GB")
        self.assertEqual(record["registration_status"], "ISSUED")
        self.assertEqual(record["source_record_url"], f"{gleif.SOURCE_URL}/{VALID_LEI}")
        self.assertIn("does not prove", result["interpretation"])
        fetch.assert_called_once()

        requested_url = fetch.call_args.args[0]
        query = parse_qs(urlsplit(requested_url).query)
        self.assertEqual(query["filter[entity.legalName]"], ["Example Holdings"])
        self.assertEqual(query["page[size]"], ["5"])

    def test_rejects_blank_short_non_text_and_oversized_queries(self) -> None:
        for bad in ("", "x", "  ", "x" * (gleif.MAX_QUERY_LENGTH + 1), "a\nmalicious"):
            with self.subTest(value=repr(bad)):
                with self.assertRaises(gleif.GleifQueryError):
                    gleif.search_gleif_entities(bad)
        with self.assertRaises(gleif.GleifQueryError):
            gleif.search_gleif_entities(None)  # type: ignore[arg-type]

    def test_cache_is_bounded_by_ttl_and_does_not_repeat_upstream_call(self) -> None:
        with patch.object(gleif, "_fetch_json", return_value=payload()) as fetch:
            first = gleif.search_gleif_entities("Example Holdings", now=100.0)
            second = gleif.search_gleif_entities("example holdings", now=101.0)

        self.assertFalse(first["cache_hit"])
        self.assertTrue(second["cache_hit"])
        self.assertEqual(second["query"], "example holdings")
        fetch.assert_called_once()

    def test_expired_cache_refreshes(self) -> None:
        with patch.object(gleif, "_fetch_json", return_value=payload()) as fetch:
            gleif.search_gleif_entities("Example Holdings", now=100.0)
            result = gleif.search_gleif_entities(
                "Example Holdings", now=100.0 + gleif.CACHE_TTL_SECONDS + 1
            )
        self.assertFalse(result["cache_hit"])
        self.assertEqual(fetch.call_count, 2)

    def test_upstream_failure_is_not_misrepresented_as_no_matches(self) -> None:
        with patch.object(
            gleif,
            "_fetch_json",
            side_effect=gleif.GleifSourceUnavailable("source down"),
        ):
            with self.assertRaises(gleif.GleifSourceUnavailable):
                gleif.search_gleif_entities("Example Holdings")

    def test_invalid_upstream_records_are_skipped(self) -> None:
        malformed = {"data": [None, {"id": VALID_LEI}, {"id": "invalid", "attributes": {}}]}
        with patch.object(gleif, "_fetch_json", return_value=malformed):
            result = gleif.search_gleif_entities("Example Holdings", now=100.0)
        self.assertEqual(result["results"], [])
        self.assertEqual(result["result_count"], 0)


if __name__ == "__main__":
    unittest.main()
