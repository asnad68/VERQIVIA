# VERQIVIA — Server-connected Pilot Smoke Test

## Current status

The repository contains the authenticated Portal/API flow and automated local HTTP tests. The Render workspace checked on 2026-10-09 had **no API service and no PostgreSQL instance**, so this guide is a runbook for the first deployment; it is not evidence that a live server currently exists.

Do not enter real company data until the privacy, retention, access-control and legal review is complete. Use synthetic data during the first live smoke test. Payments, public identity issuance, wallet authorization and general enrollment must remain disabled.

## Gate 0 — Deployment prerequisites

Before the browser can connect, the operator must provision:

- an HTTPS API service running the production Docker image;
- a durable PostgreSQL database with separate `nothing_migrator` and least-privileged `nothing_app` credentials (and the migration-required `nothing_payment` database role created even though billing is disabled);
- an OIDC provider configured for Authorization Code + PKCE/S256, the exact Portal callback URI below, and the expected signed JWT access-token contract;
- the public, non-secret Portal settings in `site/portal-config.js`.

The OIDC access token must be accepted by both sides: RS256, `typ=at+jwt` or `application/at+jwt`, the configured issuer and API audience, required time/token claims, and `nothing:pilot:write`. Do not assume a provider's default token format meets this contract; test a real token before relying on the provider.

Exact Portal redirect URI:

`https://asnad68.github.io/VERQIVIA/portal.html`

Exact browser origin to allow for pilot writes:

`https://asnad68.github.io`

Configure the API CORS allowlist to that exact origin. Configure OIDC token-endpoint CORS for the same origin. Do not place client secrets, API keys, bearer tokens, database URLs, passwords or private keys in GitHub files. Public browser configuration may contain only the API base URL, OIDC issuer, public client ID, API audience and required scopes.

## Gate 1 — API and storage status

Open the published Portal over HTTPS.

Expected results once configured:

1. `/healthz` returns HTTP 200 with `{"status":"ok"}`.
2. `/readyz` returns HTTP 200 with `{"status":"ready", ...}`.
3. The Portal reports that the API is reachable and storage is ready.
4. If the API is down, its URL/CORS is wrong, or storage is unavailable, the Portal must not report that the server is ready.

A reachable `/healthz` alone is not sufficient; the database readiness gate must pass.

## Gate 2 — Safe test draft

Use a fake organization such as `VERQIVIA Smoke-Test Example`, a reserved/example domain such as `example.com`, and a description stating that all data is synthetic.

1. Build a local draft and inspect the JSON.
2. Connect an authorized pilot account.
3. Submit the draft.
4. Expect HTTP 201 and a `draft_id` with status `RECEIVED`; the UI should explicitly say no official identity was created.
5. Use “Refresh server status” and confirm that the same draft UUID and status are read back.

Do not paste credentials, private documents, recovery phrases, private keys or live personal data into the test.

## Gate 3 — Negative security checks

Verify all of these before inviting an external pilot:

- Submission without a bearer token returns HTTP 401.
- A valid token missing `nothing:pilot:write` returns HTTP 403.
- A browser origin outside the configured allowlist is denied (HTTP 403).
- The submitting actor can read their own draft.
- A second test actor cannot read the first actor's draft (HTTP 404).
- Repeating the same request with the same idempotency key returns the same draft ID.
- Reusing that key for a different payload returns HTTP 409.
- Invalid JSON/schema and wrong content type are rejected (HTTP 400/415).
- Restart/redeploy and database restore tests do not lose acknowledged drafts.

Use separate test accounts for actor-isolation verification. Never send real-user tokens to another person or place them in issue trackers or logs.

## Gate 4 — Decision

**PASS — Controlled test only:** all gates above pass, the deployment revision is recorded, and synthetic test data survives the database and restore check.

**STOP:** any auth, scope, CORS, actor-isolation, persistence or restore test fails. Keep the Portal closed to external submissions until fixed.

Passing this smoke test still does not establish commercial production readiness. Production also requires operational monitoring and alerts, security/gateway controls, key governance, a tested backup/recovery plan, privacy/legal review and clearance of the VERQIVIA name. Payments remain disabled.
