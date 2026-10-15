"""Read-only GLEIF LEI search adapter.

Only the official GLEIF API host is contacted. Results are normalized to a small,
provenance-rich shape and are never treated as proof of domain control, trademark
ownership, or authority to represent an organization.
"""
from __future__ import annotations

import json
import re
import threading
import time
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

SOURCE_NAME = "GLEIF Global LEI Index"
SOURCE_URL = "https://api.gleif.org/api/v1/lei-records"
MAX_QUERY_LENGTH = 180
MAX_RESULTS = 5
MAX_RESPONSE_BYTES = 262_144
UPSTREAM_TIMEOUT_SECONDS = 3.0
CACHE_TTL_SECONDS = 900
CACHE_MAX_ENTRIES = 256
_LEI_RE = re.compile(r"^[A-Z0-9]{20}$")
_CACHE: OrderedDict[str, tuple[float, dict[str, Any]]] = OrderedDict()
_CACHE_LOCK = threading.Lock()


class GleifQueryError(ValueError):
    """The supplied lookup term is invalid."""


class GleifSourceUnavailable(RuntimeError):
    """GLEIF could not provide a trustworthy response."""


class _SameHostHttpsRedirects(HTTPRedirectHandler):
    """Prevent a fixed upstream request from redirecting to an arbitrary host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlsplit(newurl)
        if (
            parsed.scheme != "https"
            or parsed.hostname != "api.gleif.org"
            or parsed.username
            or parsed.password
            or parsed.port not in (None, 443)
        ):
            raise URLError("GLEIF redirected outside its approved HTTPS origin")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _fetch_json(url: str, timeout: float = UPSTREAM_TIMEOUT_SECONDS) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.api+json, application/json",
            "User-Agent": "VERQIVIA-Reference-Resolver/0.1",
        },
        method="GET",
    )
    opener = build_opener(_SameHostHttpsRedirects())
    try:
        with opener.open(request, timeout=timeout) as response:
            if getattr(response, "status", 200) != 200:
                raise GleifSourceUnavailable("GLEIF returned an unsuccessful response")
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise GleifSourceUnavailable("GLEIF reference data is temporarily unavailable") from exc
    if len(body) > MAX_RESPONSE_BYTES:
        raise GleifSourceUnavailable("GLEIF response exceeded the allowed size")
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GleifSourceUnavailable("GLEIF returned invalid JSON") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise GleifSourceUnavailable("GLEIF response does not match the expected API contract")
    return payload


def _clean_string(value: Any, max_length: int = 300) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value or len(value) > max_length:
        return None
    return value


def _normalize_record(record: Any) -> dict[str, Any] | None:
    if not isinstance(record, dict):
        return None
    lei = record.get("id")
    if not isinstance(lei, str) or not _LEI_RE.fullmatch(lei):
        return None
    attrs = record.get("attributes")
    if not isinstance(attrs, dict):
        return None
    entity = attrs.get("entity")
    registration = attrs.get("registration")
    if not isinstance(entity, dict):
        entity = {}
    if not isinstance(registration, dict):
        registration = {}
    legal_name = entity.get("legalName")
    if isinstance(legal_name, dict):
        legal_name = legal_name.get("name")
    name = _clean_string(legal_name)
    if not name:
        return None
    address = entity.get("legalAddress")
    country = address.get("country") if isinstance(address, dict) else None
    country = country.upper() if isinstance(country, str) and re.fullmatch(r"[A-Za-z]{2}", country) else None
    return {
        "lei": lei,
        "legal_name": name,
        "country": country,
        "entity_status": _clean_string(entity.get("status"), 80),
        "registration_status": _clean_string(registration.get("status"), 80),
        "last_updated": _clean_string(registration.get("lastUpdateDate"), 80),
        "next_renewal_date": _clean_string(registration.get("nextRenewalDate"), 80),
        "source_record_url": f"{SOURCE_URL}/{lei}",
    }


def search_gleif_entities(name: str, *, now: float | None = None) -> dict[str, Any]:
    """Search GLEIF by legal name and return an explicitly non-decisive evidence result."""
    if not isinstance(name, str):
        raise GleifQueryError("name must be text")
    query = name.strip()
    if len(query) < 2 or len(query) > MAX_QUERY_LENGTH or any(ord(c) < 32 for c in query):
        raise GleifQueryError(f"name must be between 2 and {MAX_QUERY_LENGTH} printable characters")

    current = time.monotonic() if now is None else now
    cache_key = query.casefold()
    with _CACHE_LOCK:
        cached = _CACHE.get(cache_key)
        if cached and current - cached[0] < CACHE_TTL_SECONDS:
            _CACHE.move_to_end(cache_key)
            response = dict(cached[1])
            response["query"] = query
            response["cache_hit"] = True
            return response
        if cached:
            _CACHE.pop(cache_key, None)

    params = urlencode({"filter[entity.legalName]": query, "page[size]": str(MAX_RESULTS)})
    url = f"{SOURCE_URL}?{params}"
    payload = _fetch_json(url)
    records = []
    for raw in payload["data"][:MAX_RESULTS]:
        normalized = _normalize_record(raw)
        if normalized is not None:
            records.append(normalized)

    result: dict[str, Any] = {
        "source": SOURCE_NAME,
        "source_url": SOURCE_URL,
        "query": query,
        "observed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "result_count": len(records),
        "results": records,
        "cache_hit": False,
        "interpretation": (
            "Reference data only. A name match does not prove website/domain control, "
            "trademark ownership, authority to represent the entity, or general trustworthiness."
        ),
    }
    with _CACHE_LOCK:
        _CACHE[cache_key] = (current, dict(result))
        _CACHE.move_to_end(cache_key)
        while len(_CACHE) > CACHE_MAX_ENTRIES:
            _CACHE.popitem(last=False)
    return result


def clear_gleif_cache() -> None:
    """Clear cached results; exposed for deterministic tests and maintenance."""
    with _CACHE_LOCK:
        _CACHE.clear()
