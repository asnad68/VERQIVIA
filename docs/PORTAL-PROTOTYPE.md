# VERQIVIA Portal — Controlled Pilot Intake

## Purpose

`site/portal.html` is the company-facing entry point for preparing a pilot request. It now supports a server-backed intake flow when the API and a compatible managed OpenID Connect provider are configured. It is not yet a general-purpose multi-tenant organization workspace.

## Current implementation

- Collects a business/brand name, type, website, domain, public description, channels, pilot claims and evidence boundary.
- Validates draft fields in the browser and repeats validation on the server.
- Preserves local JSON copy/download for review.
- Supports OIDC Authorization Code with PKCE (S256), a short-lived access token in `sessionStorage`, and no embedded client secret or long-lived refresh token.
- Sends a draft to `POST /v1/pilot/drafts` with the separate `nothing:pilot:write` scope and an `Idempotency-Key`.
- Stores accepted drafts in PostgreSQL or the SQLite reference backend; returns a draft UUID and a `RECEIVED` status.
- Allows the authenticated submitting actor to retrieve only their own draft with `GET /v1/pilot/drafts/{draft_id}`.
- Performs unauthenticated `/healthz` and `/readyz` probes once public API configuration is present, so the page can distinguish API reachability from database readiness before submission.
- Treats exact retries as idempotent and rejects reuse of a key with a different payload.
- Adds HTTP integration tests for authentication, actor isolation, idempotent retry/conflict, invalid payloads, origin allowlisting and the browser preflight headers.

A successful HTTP response means only that a draft was received for controlled pilot review. It does **not** create an official VERQIVIA identity, prove that a user represents the company, confirm domain ownership, verify claims, or issue a cryptographic proof.

## Browser configuration (public values only)

`site/portal-config.js` contains intentionally blank operator settings:

- `apiBaseUrl`: deployed API origin, for example `https://api.example.org`;
- `oidcIssuer`: exact HTTPS OIDC issuer configured on the API;
- `oidcClientId`: public browser client identifier, not a secret;
- `oidcAudience`: exact audience expected by the API resource server;
- `scope`: must include `openid` and `nothing:pilot:write`.

Do not put a client secret, access token, API key, wallet recovery phrase or private key in a website file or Git commit. The exact redirect URI for the current GitHub Pages path is:

`https://asnad68.github.io/VERQIVIA/portal.html`

The identity-provider client must be configured as a public client using Authorization Code + PKCE/S256, with the redirect URI above, and the token endpoint must permit CORS for `https://asnad68.github.io`. It must issue a signed RS256 JWT access token with `typ=at+jwt` (or `application/at+jwt`), the configured API audience, `iss`, `sub`, `exp`, `iat`, `jti`, `client_id`, and a `scope` containing `nothing:pilot:write`. The API validates the token signature against the configured HTTPS JWKS URI; client-side checks do not replace server validation.

Configuration stays blank and the connection controls stay disabled until these public deployment values are supplied. The Portal should not be described as server-connected in the live site until a deployment test confirms it end to end.

## API and data boundary

`POST /v1/pilot/drafts` requires an authenticated principal, the dedicated pilot scope, JSON content type, a bounded request body and an idempotency key. The server rejects unsupported fields and malformed domains/URLs. `GET /v1/pilot/drafts/{uuid}` is actor-scoped; a record belonging to another actor is indistinguishable from a missing record.

Drafts may contain business-contact information. Use synthetic data in early testing and do not submit confidential documents or personal data until privacy notice, retention policy, deletion workflow and jurisdiction-specific review have been approved. The pilot endpoint is not an upload endpoint for evidence documents.

## Deployment boundary and remaining work

The client, API route and deployment contract are in the repository's main branch. The connected flow is **not live yet**: the Render workspace currently has no API service or PostgreSQL instance, and `site/portal-config.js` intentionally contains no live API/OIDC values. The page remains safe in local-draft mode until those external services are configured. Before real external users can submit drafts, an operator must:

1. Provision the API and PostgreSQL, including separate migration-owner and least-privileged application database credentials.
2. Configure the OIDC issuer, API audience, JWKS URI, public client and exact callback/CORS settings.
3. Put only the matching non-secret API/issuer/client/audience values in `site/portal-config.js`, publish the Pages site, and set exact origin allowlisting on the API.
4. Run the production deployment smoke tests and verify the actor-isolation, retry, audit, backup and restore behavior.
5. Complete privacy/security/legal review before collecting real company information.

The current data model and production gateway remain single-tenant at the identity-resource layer. That means this intake is not permission to open general identity registration to the public. Official registration, organization-controlled ownership checks, tenant isolation, production verification governance, observability and backup/restore remain separate gates. Payments remain frozen.

## Product rule

GitHub is the engineering/backstage surface. The Portal is the controlled pilot intake. Public Verify remains the human-facing inspection surface.
