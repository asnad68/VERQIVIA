# VERQIVIA Observability Requirements

## Required signals

### Availability
- HTTP health status
- readiness status
- request error rate
- latency by endpoint class

### Database
- connection-pool saturation
- query/transaction failures
- serialization retries
- lock timeouts
- migration failures

### Identity and verification
- invalid identity submissions
- unresolved evidence references
- verification procedure conflicts
- cryptographic proof failures
- supersession conflicts
- revocation events

### Billing boundary

Billing remains separately monitored:

- invoice creation failures
- payment observation failures
- duplicate observations
- unmatched payments
- reconciliation actions
- entitlement activation/expiration

## Alert principles

Alerts should focus on actionable conditions. Do not alert on expected user validation errors at incident severity.

Security-sensitive events must include enough context for investigation without logging credentials or unnecessary personal information.

## Audit linkage

Operational incidents involving identity or billing records must be traceable to the relevant audit record, ingestion identifier, verification event, payment event or other stable object identifier.

## Production gate

Before production use, alerts must be tested with a controlled failure rather than merely configured.
