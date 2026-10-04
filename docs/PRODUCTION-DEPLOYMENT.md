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

- `render.yaml` — deployment blueprint for API, static site and PostgreSQL target.
- `Dockerfile` — production API container.
- `.env.example` — configuration contract.
- `api/openapi.json` — public API contract.
- `docs/FINAL-REPOSITORY-READINESS.md` — launch gates.

## 1. Create the production services

Use an authorized Render workspace and apply the root `render.yaml`. The blueprint defines:

- `verqivia-api` — Docker web service;
- `verqivia-postgres` — PostgreSQL target;
- GitHub Pages remains the single canonical public website.

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

## 3. Configure persistent storage

Set:

- `NOTHING_STORAGE_BACKEND=postgres`;
- `NOTHING_POSTGRES_DSN` from the managed database connection;
- bounded pool and statement/lock timeouts from `.env.example`.

Use TLS for the database connection according to the provider's supported configuration. Runtime credentials should have only the privileges required by the application.

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