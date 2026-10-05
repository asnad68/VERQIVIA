# VERQIVIA — First Customer Production Readiness

## Release objective

Deliver VERQIVIA to the first real customer as a controlled production engagement without overstating what the system has independently verified or what infrastructure is actually live.

## Release decision

**Current decision: Release Candidate / controlled pilot only.**

Repository and product surfaces are substantially prepared. Public production remains blocked until the external deployment and governance gates below are evidenced.

## Gate matrix

| Gate | Current state | Required evidence | Blocking? |
| --- | --- | --- | --- |
| Identity / claim / evidence core | READY | Repository tests + schemas + resolver | No |
| Verify Web | READY FOR PILOT | Public demo returns expected record and cryptographic proof | No |
| Cryptographic proof | READY FOR PILOT | Valid Ed25519 demo proof + registry lifecycle checks | No |
| Portable profile | READY FOR PILOT | Schema/OpenAPI/profile parity | No |
| API contract | READY FOR PILOT | OpenAPI + reference implementation + tests | No |
| Production API | NOT DEPLOYED | Live HTTPS endpoint + health/readiness + smoke tests | Yes |
| PostgreSQL production | NOT PROVISIONED | Managed database + migration + readiness + access controls | Yes |
| Production authentication | NOT CONFIGURED | OIDC issuer/audience/JWKS + positive/negative auth tests | Yes |
| Gateway / abuse controls | NOT EVIDENCED | HTTPS, rate limits, WAF/firewall policy and logs | Yes |
| Monitoring / alerting | NOT EVIDENCED | Live alerts for 5xx, readiness, DB/auth failures | Yes |
| Backup / restore | NOT DRILLED | Successful restore drill with recorded RPO/RTO | Yes |
| Signing-key governance | NOT FINALIZED | Custody, rotation, revocation and recovery procedure | Yes for real signed records |
| Privacy / legal | NOT FINALIZED | Operating entity review, privacy terms and applicable legal analysis | Yes |
| Name / trademark clearance | NOT COMPLETED | Professional clearance in target jurisdictions | Yes before material brand expansion |
| Commercial proposal | READY | Scope / fee / responsibilities / acceptance template | No |
| Payment automation | DEFERRED | Approved settlement design + reconciliation + monitoring | No for manual pilot contract; Yes for automated SaaS billing |

## Recommended first-customer path

### Stage A — Controlled pilot

Use one customer, one VERQIVIA identity and a small number of claims. Agree evidence sources and verification scope in writing.

### Stage B — Production verification service

After the deployment gates are complete, expose the customer record through the production API and public verification origin. Keep the service single-tenant until tenant isolation is separately engineered and tested.

### Stage C — Expanded integration

Only after the first customer demonstrates utility should the project add higher-volume API usage, additional verification procedures, ecosystem adapters, custom domains and broader enterprise controls.

## What the first customer should receive

- one canonical VERQIVIA identity;
- a human verification URL;
- claim-level verification records with scope;
- evidence references appropriate to the agreed visibility;
- lifecycle/history where relevant;
- portable machine-readable profile;
- API integration guidance where required;
- a written scope and acceptance definition.

## What the first customer should not be promised yet

- universal trust or safety certification;
- trademark registration or government registration;
- indefinite truth of a verified claim;
- guaranteed regulatory approval;
- automatic crypto settlement unless separately activated and tested;
- multi-tenant isolation;
- enterprise uptime SLA unless explicitly contracted and supported by the actual infrastructure.

## Exit criteria for Production

The release can be called **Production — First Customer** only when every blocking gate above has documented evidence and a real end-to-end smoke test succeeds against the deployed service.

Until then, public language should remain **Early Access / Controlled Pilot**.