# VERQIVIA Operational Security Requirements

## Scope

These controls are required before real customer or production data is processed. They are deployment requirements, not merely application-code requirements.

## Authentication and authorization

- Use a managed OIDC identity provider for operator/admin access.
- Validate issuer, audience, expiry, token type and signing algorithm.
- Enforce least-privilege scopes.
- Separate customer authentication from operator administration.
- Do not use a long-lived shared bearer token for human administration.
- Keep official organization authorization separate from login.

## Secrets

- Store secrets only in the deployment secret manager.
- Rotate signing, database and domain-challenge secrets according to a documented schedule.
- Never place private keys or real credentials in Git.
- Keep runtime database credentials distinct from migration credentials.

## Network

- Put the API behind HTTPS.
- Restrict database access to the application network.
- Keep PostgreSQL private.
- Apply gateway/WAF rate limiting in addition to application-level limits.
- Do not expose administrative database endpoints publicly.

## Data

- Store the minimum data required for each claim.
- Treat submitted business information and authentication metadata as sensitive operational data.
- Define retention and deletion periods before the pilot.
- Do not collect seed phrases, private keys or unnecessary identity documents.

## Key management

- Production issuer keys must be separate from demo keys.
- Record key activation, rotation and revocation events.
- Never reuse demo signing keys in production.
- Publish only public verification material.

## Logging and monitoring

At minimum monitor:

- authentication failures
- authorization denials
- ingestion failures
- idempotency conflicts
- proof verification failures
- database errors
- queue/worker lag
- backup failures
- unusual request volume

Logs must avoid secrets and unnecessary personal data.

## Incident response

The production runbook must define:

1. credential compromise response;
2. signing-key compromise response;
3. database restore procedure;
4. payment/entitlement isolation;
5. verification-record integrity investigation;
6. public communication boundaries.

## Deployment gate

Production activation is blocked until these requirements have an owner, evidence and a tested procedure.
