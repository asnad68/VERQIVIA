# VERQIVIA — Release Notes

## 2026-10-05 — First Customer Release Candidate

This release moves VERQIVIA from a prototype-only presentation toward an early commercial / controlled-production candidate.

### Product surface

- Commercial offering page
- Early-commercial Terms page
- Developer / AI integration page
- Reusable sales/pricing framework
- Reusable commercial proposal template
- First-customer readiness gate matrix
- Production deployment runbook

### Verification infrastructure

- Public cryptographic proof verification with Ed25519
- Detailed browser-side proof checks
- Portable verification profile with claim scope
- Portable profile cryptographic proof references
- OpenAPI contract parity
- Machine-readable AI integration guidance
- Shareable verification links

### Security and operations

- Strict CSP without inline styles
- Local HTML link integrity tests
- Python compilation gate in CI
- `security.txt` responsible-disclosure entry point
- Paid Render production baseline
- Pre-deploy PostgreSQL migration command
- Health/readiness checks
- Canonical public API origin support
- Single-tenant production boundary

### Explicit limitations

This release is **not** a declaration of fully live global production.

The remaining external launch gates are:

- production Render workspace authorization;
- live OIDC identity-provider configuration;
- live PostgreSQL provisioning;
- production gateway/security configuration;
- backup/restore drill;
- signing-key governance for real customer records;
- privacy/legal review by the operating entity;
- professional VERQIVIA trademark/name clearance;
- any automated cryptocurrency payment activation.

The public GitHub Pages demo continues to use synthetic data only.

### Release principle

> **Production is a deployment state, not a repository label.**

The project should only be called **Production — First Customer** after the blocking gates are evidenced and an end-to-end smoke test succeeds against the live service.