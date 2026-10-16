# VERQIVIA — Deployment Recovery Path

**Status checked: 2026-10-16**

## Verified blocker

The connected Render workspace `Mehdi's workspace` has no listed API service and no PostgreSQL database. An attempt to create a free PostgreSQL instance returned HTTP 402 with the message: `Payment information is required to complete this request`.

This is an account/provider provisioning barrier, not a code failure. Do not retry the same operation or try to evade a provider's payment/eligibility controls. No new Render resource was created by that failed request.

## Keep the product safe while unblocking infrastructure

Until a real API, persistent database and authentication provider are configured:

- GitHub Pages stays in local-draft mode; `site/portal-config.js` intentionally has blank API/OIDC values.
- Do not add secrets, connection strings, tokens, private keys or passwords to Git.
- Keep billing, official identity issuance, wallet authorization and general enrollment disabled.
- Use only synthetic test records. An intake draft is not an official identity and is not evidence that the submitter represents the named organization.

## Least-change recovery route

Prefer a provider stack that is legally available to the project operator and can run the existing Docker image. Keep the current Python API and PostgreSQL data model rather than rewriting the verification core just to match a hosting vendor.

1. Provision a small API web service from the repository's `Dockerfile` and a persistent PostgreSQL database. A free database tier, if available, is only for synthetic pilot testing when its expiry, backup, networking and usage limits are acceptable. It is not production storage.
2. Configure separate database roles: `nothing_migrator` for schema migrations, least-privileged `nothing_app` for API runtime, and `nothing_payment` to satisfy the existing schema contract while billing remains disabled. Never give the API the migration-owner credential.
3. Configure a managed OIDC provider with the exact contract below. Do not assume the provider's default access tokens are compatible; check a real synthetic login/token before opening the Portal.
4. Set server secrets in the provider's secret manager. Put only public settings into `site/portal-config.js`, commit the non-secret configuration, and let GitHub Pages publish it.
5. Run the repository's live smoke workflow and the negative authorization checks before any external pilot user is invited.

The connected Render workspace is blocked at step 1 today. The Neon and Railway integrations are candidates to assess once explicitly connected; their availability, billing requirements, and suitability must be confirmed before provisioning. Do not treat a suggested integration as connected or as proof that a server is deployed.

## Required public Portal settings

File: `site/portal-config.js`

- `apiBaseUrl`: the deployed API's HTTPS origin.
- `oidcIssuer`: the exact HTTPS issuer used by the API.
- `oidcClientId`: public browser-client ID; not a secret.
- `oidcAudience`: exact API audience.
- `scope`: includes `openid` and `nothing:pilot:write`.

Portal callback URI:
`https://asnad68.github.io/VERQIVIA/portal.html`

Browser origin for API write allowlisting and OIDC token-endpoint CORS:
`https://asnad68.github.io`

## Required server configuration

At minimum, configure these as protected environment variables (not in the repository):

- `NOTHING_POSTGRES_DSN`: runtime connection using `nothing_app`.
- `NOTHING_POSTGRES_MIGRATOR_DSN`: separate migration connection using `nothing_migrator`.
- `NOTHING_AUTH_ISSUER`, `NOTHING_AUTH_AUDIENCE`, `NOTHING_AUTH_JWKS_URI`.
- `NOTHING_PORTAL_REQUIRED_SCOPE=nothing:pilot:write`.
- `NOTHING_AUTH_REQUIRED_SCOPE=nothing:ingest`.
- `NOTHING_WRITE_ALLOWED_ORIGINS=https://asnad68.github.io`.
- `NOTHING_PUBLIC_API_ORIGIN`: the final API origin.
- `NOTHING_BILLING_ENABLED=false`, `NOTHING_ENROLLMENT_ENABLED=false`, `NOTHING_IDENTITY_CONTROL_ENABLED=false`, `NOTHING_WALLET_AUTH_ENABLED=false`.

The access token contract is intentionally strict: RS256, `typ=at+jwt` or `application/at+jwt`, matching issuer and audience, required time/token claims, expected public client ID, and the dedicated `nothing:pilot:write` scope. The browser separately validates the ID token. A mismatch means stop and configure a compatible provider; do not weaken token checks simply to get a green status.

## Acceptance gates

Do not call the pilot server-connected until all are true:

1. `GET /healthz` returns HTTP 200.
2. `GET /readyz` returns HTTP 200 and reports persistent storage ready.
3. A test account can submit a synthetic draft and read it back.
4. A request without a token is rejected; missing scope and unapproved origins are rejected.
5. A second test actor cannot read the first actor's draft.
6. Idempotent retry returns the same draft ID; reusing the key with a different payload is rejected.
7. The release revision is recorded and a backup/restore check has been completed before real business data is accepted.

See `docs/PILOT-SERVER-SMOKE-TEST.md` and `docs/PRODUCTION-DEPLOYMENT.md` for the complete release sequence.
