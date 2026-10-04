# VERQIVIA Controlled Pilot Runbook

## Purpose

This runbook turns the repository's Phase 5 pilot requirements into a repeatable synthetic test before any real organization data is processed.

The fixture at `pilot/controlled-dataset.json` is **synthetic**. It does not represent a customer, partner, certification, legal entity, or real verification result.

## Pilot sequence

1. Register one business identity as a self-claim.
2. Attach one or more evidence records to a specific claim.
3. Record a versioned verification event with explicit scope.
4. Add a later event that supersedes the earlier event.
5. Confirm the resolver exposes the latest event as current while retaining the earlier event in history.
6. Test identity-level revocation as a separate state transition.
7. Confirm that revocation does not rewrite historical verification events.
8. Test procedure lifecycle changes without silently reinterpreting historical events.
9. Record the pilot result, failures and operational friction.

## Acceptance criteria

A pilot passes only when:

- every identity, evidence record and verification event validates against the v0.1 schemas;
- all event references resolve;
- the supersession chain is linear and acyclic;
- the current verification event is deterministic;
- evidence remains traceable to the event that used it;
- revocation is explicit and does not erase history;
- a failed or unsupported check is represented by a bounded result rather than a universal trust score;
- no real personal or confidential data is required for the synthetic test.

## Real-world pilot gate

Before replacing the synthetic fixture with real data, the operator must obtain written pilot scope and data-handling terms, define the legal entity and authorized contact, configure production identity controls, and complete the applicable privacy/security/legal review.
