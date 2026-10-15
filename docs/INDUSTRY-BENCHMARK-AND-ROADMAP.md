# VERQIVIA — Industry Benchmark, Design Decisions and Integration Roadmap

**Reviewed:** 2026-10-15  
**Scope:** business identity, domain/channel claims, supporting evidence, verification workflows and portable outputs.

This review uses public product documentation and standards to identify patterns that are useful to VERQIVIA. It is not a claim that VERQIVIA is partnered with, certified by, or has integrated any named provider.

## Executive decision

VERQIVIA should be an **evidence-centric, provider-neutral verification layer**. It should not try to replace company registries, identity/KYB providers, trust centers, domain registrars or trademark offices. Instead it should connect evidence from these sources to individual, scoped claims; preserve provenance; publish a machine-readable result; and let a verifier apply its own policy.

The key product distinction is: **a cryptographically valid record proves integrity and issuer attribution, not that every underlying business claim is true.** A claim must retain the issuer, evidence, method, scope, observation time, freshness/expiry, review status and any later dispute/revocation.

## Benchmark: what to adopt, and what not to copy

### 1. Company registries and legal-entity data — OpenCorporates and GLEIF

**Useful pattern:** return structured records with source attribution and support machine-to-machine lookup. OpenCorporates documents a versioned API and records that include provenance; GLEIF's API supports LEI searches and entity/ownership relationship lookups.

**VERQIVIA decision:**
- Keep the registry source and source-record identifier with every result.
- Treat registry data as evidence for the specific proposition it supports (for example, a legal entity name or LEI), not automatic proof of a website, brand, social account or current representative.
- Build a small provider-adapter interface so an official national registry, GLEIF or a licensed data provider can be added/replaced without changing the core claim model.
- Prefer the official source when possible. Use third-party aggregators as attributed sources, respecting their licence, API limits, refresh rules and commercial terms.

**Do not copy:** treating a fuzzy name match as definitive identity; silently merging similar entities; hiding source date; relying on an aggregator where an authoritative registry is available; or assuming worldwide coverage is uniform.

### 2. KYB and business onboarding — specialist verification providers

**Useful pattern:** configurable country coverage, business and owner checks, structured API outcomes and workflow orchestration can shorten onboarding.

**VERQIVIA decision:**
- Keep specialist KYB checks optional and separately scoped. They can provide evidence but must not silently control VERQIVIA's global identity status.
- Store provider, check type, jurisdiction, provider reference, result class, checked-at time, freshness/expiry and allowed redisclosure/use.
- Keep personal/beneficial-owner data out of public profiles unless there is a lawful and explicit need. Prefer a claim such as “required control check completed” over publishing unnecessary personal attributes.
- Before adding a paid provider, confirm coverage for the pilot jurisdiction, lawful basis, retention terms, data location, price and a safe failure mode.

**Do not copy:** a mandatory single-vendor dependency, opaque “pass” results without a reason or source, a single global risk score, or collecting more personal data than the verifier's use case requires.

### 3. Security trust centers and supplier questionnaires — Vanta-style workflows

**Useful pattern:** clear role permissions, evidence requests, private-by-default documents, an auditable review workspace, and selective public/private sharing reduce repeat supplier-review work.

**VERQIVIA decision:**
- Separate public verification claims from confidential evidence and internal reviewer notes.
- Design for resource-level access, least privilege, auditable access/review actions, expiring grants and redaction of sensitive fields.
- Keep “submitted by organization,” “reviewed by VERQIVIA,” and “independently sourced” distinct.
- Reuse approved claim/evidence packages across a customer's integrations, but show when each item was last checked and when it should be renewed.

**Do not copy:** access policies that are hard for a customer to understand, stale trust material presented as current, feature availability tied to one vendor's paid plan, or domain-level invitation rules that grant wider access than the customer intends.

### 4. Signed records and transparency logs — Sigstore-style design

**Useful pattern:** signed entries and independently verifiable append-only logs improve auditability and allow third parties to check whether historical entries were changed.

**VERQIVIA decision:**
- Continue using cryptographic proofs for integrity and issuer/key attribution.
- For the controlled pilot, keep an immutable, database-backed verification-event history and signed proof output; do not claim the system has a publicly witnessed transparency log until one exists.
- Before public transparency logging, define independent monitors/witnesses, key rotation and recovery, consistency proofs, a public incident process and a privacy/redaction policy.
- Prefer public commitments/digests and minimal metadata. Keep confidential evidence outside a public append-only log, with controlled access.

**Do not copy:** assuming an append-only log independently proves the underlying claim; publishing raw personal/company-sensitive evidence; or relying on one log operator without monitoring for inconsistent views.

### 5. Portable credentials and browser authentication — W3C VC and current OAuth/OIDC practice

**Useful pattern:** interoperable credential models and standard authorization-code/PKCE flows make it easier for different systems to exchange and validate claims.

**VERQIVIA decision:**
- Preserve the existing API contract and profile as the source of truth; add a W3C Verifiable Credentials Data Model 2.0 output adapter only after claim semantics, issuer identifiers, revocation/status, key rotation and interoperability tests are defined.
- Validate tokens on the server, restrict tokens to the intended audience and scope, use short lifetimes, protect callback state/nonce and PKCE, and keep browser JavaScript local/self-hosted.
- Treat a credential as verifiable data—not an automatic guarantee that its contents are correct. Each relying party applies its own acceptance policy.

**Do not copy:** custom cryptography when established standards suffice; accepting self-asserted claims as externally verified; broad scopes; long-lived browser tokens; or assuming one issuer is automatically trusted everywhere.

## Recommended VERQIVIA claim contract

Every claim that reaches a real identity should be able to communicate, at minimum:

- `claim_type` and a narrowly scoped `claim_value`;
- `status`: self-claimed, pending review, source-verified, independently verified, disputed, expired or revoked (only statuses implemented by the current protocol may be emitted);
- `evidence_refs` and source/provider identifiers, with visibility and redistribution rules;
- `verification_method` / procedure version, reviewer or issuer identity, and outcome reason;
- `observed_at`, `valid_until` or a defined recheck policy;
- `event_id`, record/proof version and any superseding or revoking event.

This is a target design checklist, not a declaration that each field is already implemented. Existing schemas and OpenAPI remain authoritative until the model is changed with tests and migration compatibility.

## Prioritized roadmap

### P0 — Before the first real pilot (blocking)
1. Deploy the API and PostgreSQL only in an authorized operator workspace; keep runtime DB credentials separate from migration credentials.
2. Configure a managed OIDC provider for the exact GitHub Pages callback and server-validated issuer, audience, algorithm and pilot scope.
3. Run the live smoke workflow, then positive and negative authenticated tests: submission/read-back, missing scope, wrong client/audience, actor isolation, idempotency conflict and disallowed origin.
4. Complete backup/restore and key-custody procedures; use synthetic data until privacy/access/retention decisions are approved.
5. Keep public identity issuance, wallet authority and automated payments disabled for this intake-only pilot.

### P1 — First measurable product advantage
1. Build a **domain-control proof adapter** (DNS TXT and/or an HTTP well-known challenge) that issues a short-lived, single-use challenge and records the evidence, time and exact domain scope. A challenge proves control at that time; it does not prove trademark ownership or the truth of all company claims.
2. **Implemented in repository code:** a read-only GLEIF LEI name-search adapter and public `GET /v1/sources/gleif/search?name=...` API. It uses a fixed HTTPS upstream host, a short network timeout, a bounded response size, short-lived bounded caching, per-client rate limiting, normalized source fields and an explicit warning that a name match is not verification. Still required: CI confirmation and a live smoke test against the official upstream API before declaring it production-validated.
3. Add source freshness and renewal states, user-visible reason codes, and a dispute/correction process.
4. Run independent interoperability tests for the portable profile, API and cryptographic proof.

### P2 — Expand only after pilot evidence
1. Add jurisdiction-specific company-registry adapters and a commercial KYB provider only after coverage, cost, terms and data-protection review.
2. Add role-scoped evidence sharing, expiring grants and an auditable supplier-review workspace.
3. Design an independently monitored transparency log and privacy-preserving public commitments before representing entries as publicly witnessed.
4. Test multi-tenant isolation, rate limiting at the gateway, incident alerts, restore objectives and key rotation before scaling beyond a single-customer pilot.

## Current implementation and external blockers (as of 2026-10-15)

- Repository includes a server-capable pilot intake flow, OIDC/PKCE browser client, API contract, actor-scoped draft reads, idempotency handling and automated tests.
- `site/portal-config.js` intentionally has blank API/OIDC settings.
- The deployment runbook reports that no live API service or PostgreSQL instance was present when checked on 2026-10-15. Therefore the browser-to-server flow is **implemented in code but not yet usable against a live production server**.
- The GLEIF reference lookup is now integrated in repository code and documented in OpenAPI; this is a read-only lookup, not a claim verification procedure. No KYB provider or country-specific company registry is integrated by this review.
- Public identity issuance and payments remain disabled.

Do not mark a gate complete until its evidence exists in CI or the actual deployment environment. A green repository CI run is necessary but does not prove the live service is deployed, configured, secure or commercially ready.

## Public sources

- [OpenCorporates API documentation](https://api.opencorporates.com/documentation/API-Reference) and [OpenCorporates API overview](https://api.opencorporates.com/)
- [GLEIF API](https://www.gleif.org/en/lei-data/gleif-api)
- [W3C Verifiable Credentials Data Model v2.0 (Recommendation)](https://www.w3.org/TR/2025/REC-vc-data-model-2.0-20250515/) and [W3C announcement](https://www.w3.org/news/2025/the-verifiable-credentials-2-0-family-of-specifications-is-now-a-w3c-recommendation/)
- [Vanta Trust Center access and management](https://help.vanta.com/en/articles/11345469-managing-your-trust-center) and [vendor assessments](https://help.vanta.com/en/articles/11345550-conducting-vendor-security-assessments)
- [Persona KYB API integration guide](https://docs.withpersona.com/2026-09-29/integration-guide-kyb-via-api)
- [Sigstore security model](https://docs.sigstore.dev/about/security/) and [Rekor transparency log](https://docs.sigstore.dev/logging/overview/)
- [RFC 10017 — OAuth 2.0 for Browser-Based Applications](https://www.rfc-editor.org/rfc/rfc10017.html), published August 2026; [RFC 9700 — OAuth 2.0 Security Best Current Practice](https://www.rfc-editor.org/rfc/rfc9700.html)
