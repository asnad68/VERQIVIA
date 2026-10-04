# VERQIVIA — Final Repository Readiness

## Scope freeze

The identity/verification core is the current product scope. Cryptocurrency payment settlement is intentionally deferred to the final commercial phase and must not be represented as live production functionality in this release.

## Repository-level implementation status

| Area | Status | Notes |
| --- | --- | --- |
| Identity schema | Complete | Versioned v0.1 contract with deterministic validation |
| Evidence model | Complete | Explicit provenance and integrity boundary |
| Verification events | Complete | Immutable event semantics, scope and supersession |
| Procedure registry | Complete | Versioned procedures and result allow-lists |
| Relationship resolver | Complete | Cross-record consistency and lifecycle checks |
| Verify Web | Complete | Human-facing graph/timeline and demo proof panel |
| Cryptographic proof | Complete for v0.1 release scope | SHA-256 binding + Ed25519 detached envelope + durable SQLite/PostgreSQL persistence + API verification |
| Issuer/key registry | Complete for v0.1 prototype | Lifecycle and validity-window checks |
| API contract | Complete | OpenAPI v1 with explicit read/write boundaries |
| Reference API | Complete | Storage-agnostic HTTP implementation |
| SQLite reference persistence | Complete | Transactional, immutable, append-oriented |
| PostgreSQL adapter | Complete | Serializable writes, advisory locking and retries |
| Authenticated ingestion | Complete | Bearer/JWT boundary, idempotency and atomic bundle writes |
| CI | Active | Unit, PostgreSQL integration, container builds and repository preflight |
| Static-site security | Hardened | CSP added to public pages |
| GitHub Pages workflow | Configured | Workflow requests Pages enablement and deploys site/ |
| Payments | Frozen | Existing code retained; no new payment work in this scope |\n| Controlled pilot fixture | Complete | Synthetic lifecycle dataset plus CI validation |\n| Interoperability boundary | Defined | W3C VC, OpenID4VCI, GLEIF/LEI and BIMI integration boundaries documented |
| Commercial packaging | Complete for early access | Commercial offering, terms and reusable proposal framework published; production SaaS remains gated |
| Deployment blueprint | Prepared | Root `render.yaml` defines API + static site + PostgreSQL target; external workspace, authentication and billing gates remain |\n| Operational security | Defined | Authentication, secret, network, data, key, logging and incident gates documented |\n| Backup/restore | Defined | Restore drill and integrity requirements documented |\n| Observability | Defined | Availability, DB, identity, verification and billing signals documented |

## What "complete" means

Repository-level completeness means the code, contracts, tests and operational documentation needed for the current scope are present and internally checked.

It does not mean:

- a production cloud account is provisioned;
- production credentials exist;
- a managed identity provider has been registered;
- a database has been provisioned;
- legal/compliance approval has been obtained;
- a live customer payment service is operating.

## Branding / IP gate

Before filing or spending materially on the **VERQIVIA** brand, the project must complete a professional trademark/name-clearance review in the intended jurisdictions and for the actual goods/services. A current public-source check The current project name is VERQIVIA. A professional clearance is still required before filing or materially expanding commercial use.

Project rule: do not describe VERQIVIA as a registered trademark until an appropriate clearance and filing strategy has been completed.

Tracking issue: #8 — Pre-commercial gate: trademark/name clearance for VERQIVIA.

## Final external launch gates

Before real public production use, the operator still has to complete:

1. managed authentication/authorization registration;
2. production PostgreSQL provisioning and least-privileged secret injection;
3. immutable production image selection;
4. TLS/gateway/WAF and distributed rate limiting;
5. centralized logs, metrics and alerting;
6. encrypted backup/restore testing and measured recovery objectives;
7. database/network isolation verification;
8. issuer governance and signing-key custody procedures;
9. cross-runtime cryptographic interoperability tests;
10. jurisdiction-specific legal, privacy, tax, sanctions and AML/CFT review.

These are intentionally outside the repository because they depend on the real deployment environment and legal entity.

## Commercial delivery surface

The public site now includes a commercial offering page and early-commercial terms page. The repository also contains a reusable sales/pricing framework and proposal template. These support controlled pilot sales without falsely representing an undeployed production service as live.

## Portable verification layer

The repository now includes an additive 0.2-draft portable verification profile, a profile builder, a schema/example, a public discovery pointer and a public ecosystem use-case page. Production endpoints and external conformance testing remain launch gates. The v1 API now exposes the portable profile endpoint, and an AI/machine integration guide plus machine discovery document are published.

## Payment boundary

Crypto settlement remains a future phase. The production payment gate must not be opened merely because the payment code exists in the repository.

The future phase must independently verify:

- exact asset/network configuration;
- receiving-address custody;
- invoice allocation;
- confirmation/finality policy;
- duplicate-event handling;
- reconciliation;
- refunds/disputes;
- accounting;
- monitoring and incident response.

## Release principle

The project should not be called production-ready until the external launch gates are explicitly completed and evidenced.

Current repository position:

**Identity/Verification Core: ready for controlled pilot/review.**

**Public commercial production: blocked on external deployment, governance, security and legal gates.**
