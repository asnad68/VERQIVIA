# VERQIVIA Live API Smoke Test

This repeatable smoke test is a **release gate**, not evidence that any server is already deployed. It uses the public synthetic record `NTH-000001`, no bearer token, and a fabricated company draft. Never enter a real brand, customer information, credential, private key, or document into this test.

## Run after an API is deployed

From the repository root, with Python 3.12 or a compatible modern Python:

```bash
python scripts/smoke_test_live_api.py --api-origin https://YOUR-API-HOST
```

You can instead set `VERQIVIA_SMOKE_API_ORIGIN` and omit the argument. Use the origin only, with no path, query, credentials, or fragment. HTTPS is required except when testing a local service on `localhost`.

The script checks:

1. `/healthz` returns HTTP 200 and `status=ok`.
2. `/readyz` returns HTTP 200 and `status=ready`.
3. `NTH-000001` is readable and contains the explicit experimental-demo claim marker. This works with both the file-system demo store and PostgreSQL, whose response metadata correctly reports demo=false.
4. The portable profile endpoint works and marks its data as synthetic.
5. The published Portal origin passes CORS preflight.
6. An unapproved browser origin is rejected.
7. A pilot-draft POST without credentials is denied (401), or explicitly unavailable (503) while pilot authentication is not configured.

A failure means **stop the release** and fix the deployment/configuration before inviting a pilot. This script does not test real OIDC login, database durability, backup/restore, tenant isolation, key custody, external-source truth, or legal/privacy compliance; those remain separate required gates in `PILOT-SERVER-SMOKE-TEST.md`.

## Run the offline unit tests

```bash
python -m unittest tests.test_live_api_smoke -v
```

The offline tests use mock responses and make no network calls. They validate failure behavior, including a write that is unexpectedly accepted and an unapproved origin that is not rejected.

## Current limitation

The connected Render workspace currently has no VERQIVIA API/database. A no-cost Render service creation attempt was rejected because Render required payment information. Therefore, the live smoke test cannot currently be executed against a production-like server. A verified eligible host and its account-controlled deployment are still required; do not bypass provider billing or eligibility checks.
