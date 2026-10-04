# VERQIVIA Backup and Restore Runbook

## Scope

This runbook applies to production PostgreSQL and any associated object storage used by VERQIVIA.

## Minimum backup policy

- Backups must be encrypted at rest.
- Backup credentials must be separate from application credentials.
- Retention must be documented.
- At least one backup copy must be isolated from the primary runtime environment.
- Backup success must be monitored rather than assumed.

## Restore test

A restore drill must:

1. provision an isolated recovery database;
2. restore the selected backup;
3. run schema/migration checks;
4. verify identity, evidence and verification-event counts;
5. verify audit-log continuity;
6. verify cryptographic proof records and issuer-registry state;
7. run the repository preflight and relevant integration tests;
8. record the recovery timestamp and observed duration.

## Integrity checks

After restore, verify:

- foreign-key and uniqueness constraints;
- append-only/audit invariants;
- idempotency records;
- latest verification-event resolution;
- issuer/key registry integrity;
- payment checkpoint monotonicity where billing data is included.

## Recovery objectives

Before production, the operator must record explicit:

- RPO (maximum tolerable data loss)
- RTO (maximum tolerable recovery time)

No production-readiness claim should be made without measured restore evidence.
