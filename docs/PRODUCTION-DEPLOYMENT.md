# VERQIVIA — Production Deployment Runbook

## Purpose

This runbook turns the repository's production boundary into an explicit deployment sequence. It is intentionally deployment-oriented: the repository may be complete while the real environment still requires operator-controlled credentials, services and legal approval.

## Target topology

```text
Public Internet
    ↓
Managed DNS / TLS / WAF / rate limiting
    ↓
VERQIVIA API
    ↓
Private PostgreSQL

GitHub Pages (public documentation + demo)
    ↓
Machine-readable discovery/profile
```

## Repository deployment assets

- `render.yaml` — deployment blueprint for the API service and PostgreSQL target. It does **not** create the GitHub Pages static site.
- `Dockerfile` — production API container.
- `.env.example` — configuration contract.
- `api/openapi.json` — public API contract.
- `docs/FINAL-REPOSITORY-READINESS.md` — launch gates.

## 1. Create the production services

Use an authorized Render workspace and apply the root `render.yaml`. The blueprint defines:

- `verqivia-api` — Docker web service;
- `verqivia-postgres` — PostgreSQL target.

The migration SQL expects distinct PostgreSQL roles `nothing_migrator`, `nothing_app` and `nothing_payment`. The Blueprint reserves the default managed credential for `nothing_migrator`; create/configure the other role credentials before applying migrations (the billing migrations require `nothing_payment` to exist even while payment remains disabled). Configure:

- `NOTHING_POSTGRES_MIGRATOR_DSN`: internal connection string for the `nothing_migrator` role;
- `NOTHING_POSTGRES_DSN`: internal connection string for the least-privileged `nothing_app` runtime role;
- a separate `nothing_payment` connection for a future payment worker, only if that component is deliberately activated.

The migration script checks `current_user = nothing_migrator` before applying any schema change and refuses to migrate as the API runtime identity. Record each managed connection string when creating the credential; do not point both variables at the same account. If the provider cannot give the roles the permissions and ownership required by the migration scripts, stop and resolve that database design before deploying.

GitHub Pages remains the separate canonical public website. The Portal now has a code path for authenticated pilot-intake submission; it remains disabled until API/OIDC public configuration is supplied and the server is deployed.

Do not expose the database publicly. Keep the service topology single-tenant for the current release.

## 2. Configure authentication

Production writes use OIDC/JWT. Configure a managed identity provider and record:

- `NOTHING_AUTH_ISSUER` — fixed HTTPS issuer;
- `NOTHING_AUTH_AUDIENCE` — API audience;
- `NOTHING_AUTH_JWKS_URI` — fixed HTTPS JWKS endpoint;
- `NOTHING_AUTH_REQUIRED_SCOPE=nothing:ingest`;
- `NOTHING_AUTH_ALLOWED_ALGORITHMS=RS256`.

The API validates issuer, audience, expiry, token type, signing algorithm and required scope.

Do not use the reference static-bearer mode for public production.

### Portal intake authorization

The private pilot intake has a separate scope: `NOTHING_PORTAL_REQUIRED_SCOPE=nothing:pilot:write`. Configure the OIDC public client for Authorization Code + PKCE (S256), the exact callback URI `https://asnad68.github.io/VERQIVIA/portal.html`, and token-endpoint CORS for `https://asnad68.github.io`. The browser configuration file `site/portal-config.js` contains public values only; it must never contain a client secret or bearer token.

The access token must be a signed RS256 JWT with `typ=at+jwt` (or `application/at+jwt`) and the exact configured API audience. The claims must include issuer, subject, `exp`, `iat`, `jti`, `client_id` and the dedicated pilot scope. The API validates the signature and scope independently; a client-side token check is only a compatibility check.

The Portal can only be connected after the API and IdP are deployed. A successful pilot-draft response records an intake request; it does not register an official identity or verify a company.

## 3. Configure persistent storage

Set:

- `NOTHING_STORAGE_BACKEND=postgres`;
- `NOTHING_POSTGRES_DSN` as the least-privileged `nothing_app` runtime connection;
- `NOTHING_POSTGRES_MIGRATOR_DSN` as a separate migration connection with the documented DDL/ownership privileges; the pre-deploy migration command fails closed if it is not configured;
- bounded pool and statement/lock timeouts from `.env.example`.

Use TLS for the database connection according to the provider's supported configuration. Runtime credentials should have only the privileges required by the application.

## 3a. Runtime and migration credential separation

In the Render dashboard, configure both DSNs explicitly from the database credential manager. `NOTHING_POSTGRES_DSN` is marked `sync: false` by design: a Blueprint-managed default connection string could otherwise silently change when a database credential is rotated. Use the database's internal URL, not an exposed public URL. The migration pre-deploy command requires its own connection and checks the SQL role name before running.

## 4. Configure canonical machine URLs

After the API service receives its public HTTPS hostname, set:

- `NOTHING_PUBLIC_SITE_ORIGIN` to the canonical public verification site;
- `NOTHING_PUBLIC_API_ORIGIN` to the canonical API origin.

The Portable Verification Profile then exposes canonical links to the human verification page, API and cryptographic proof endpoint.

## 5. Security gateway

Place the API behind the deployment provider's managed TLS and abuse-control boundary.

Required controls before public production:

- HTTPS only;
- distributed rate limiting;
- WAF/abuse controls;
- request-size limits;
- upstream health checks;
- no public database access;
- access/error logs without credentials or token contents;
- direct application access disabled when proxy headers are trusted.

Set `NOTHING_TRUST_PROXY_HEADERS=true` only when the upstream gateway overwrites forwarding headers and direct access to the application is blocked.

## 6. Signing keys

Cryptographic proof issuance requires explicit issuer/key governance.

Before real identities are signed, establish:

- key generation and custody;
- role separation;
- rotation policy;
- revocation procedure;
- validity windows;
- backup/recovery handling;
- independent verification tests across supported runtimes.

Never store an issuer private key in the repository.

## 7. Backups and restore

Before launch, perform a restore drill in an isolated environment and verify:

- schema and migrations;
- representative identity resolution;
- verification history;
- cryptographic proof verification;
- authenticated ingestion;
- idempotent retry behavior;
- audit history;
- measured recovery objectives.

Record the drill date and observed RPO/RTO outside the application repository.

## 8. Release verification

Release only an exact source/image revision that has passed the repository test suite and container build.

Smoke-test at minimum:

- `/healthz`;
- `/readyz`;
- `GET /v1/identity/{nothing_id}`;
- `GET /v1/identity/{nothing_id}/profile`;
- `GET /v1/proofs/{envelope_id}`;
- authenticated ingestion with a test credential;
- negative authorization test;
- idempotent replay test.

## 9. Commercial activation

Do not call the service production-ready merely because the Docker image starts.

Commercial production requires all external launch gates to be evidenced, including infrastructure, authentication, key governance, security controls, backups, observability and jurisdiction-specific legal/privacy/tax review.

Crypto settlement remains separately gated. It must not be enabled merely because payment code exists in the repository.

## 10. Current boundary

At repository level, VERQIVIA is suitable for controlled pilot/review and early commercial discussions.

Public production remains blocked until the real deployment environment, managed authentication, persistent storage, security controls, operational recovery and legal/compliance requirements are completed.