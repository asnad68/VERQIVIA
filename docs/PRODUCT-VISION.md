# VERQIVIA Product Vision

## Product definition

VERQIVIA is a portable verification layer for organizations, brands, digital domains, authorized relationships and machine-readable business claims.

The product is not a trademark office and does not replace government registration, domain registration, legal certification or a company's own security controls.

The commercial question is:

> Can a business publish a structured identity once, attach evidence and verification history to specific claims, and let people and software verify the result wherever that identity is used?

## Who uses it

### Organizations and brands
Publish a canonical identity record and the claims they want others to verify.

### Procurement and compliance teams
Check a supplier identity, official domain, claimed relationship or authorized contact before onboarding or purchasing.

### Marketplaces
Resolve seller and merchant identities, inspect verification status, and distinguish self-claims from independently supported claims.

### Business software
Resolve a VERQIVIA ID through an API and use structured verification results inside workflows.

### Security and trust teams
Check domain-control evidence, reported identities and revocation/supersession history.

### AI agents
Before relying on a business identity, an agent can inspect a structured record instead of treating an unverified name, domain or message as authoritative.

## The core workflow

```text
Organization
    ↓
Identity
    ↓
Claims
    ↓
Evidence
    ↓
Verification Procedure
    ↓
Verification Event
    ↓
Portable Profile
    ↓
Human / API / Software / Agent verification
```

The important design choice is that VERQIVIA verifies **claims with scope**, not a person or company with one universal green light.

## Example: a global brand

Illustrative scenario only; it is not a claim of partnership with Apple or any other named company.

A global brand could publish:

- its legal organization identity
- official domains
- brand associations
- selected business identifiers such as an LEI
- approved digital channels
- selected authorized-agent or partner relationships
- verification procedures and evidence for specific claims
- current and historical verification events

A procurement system receiving a supplier's claimed relationship could resolve the supplier's VERQIVIA profile and inspect:

1. who the subject is;
2. which domain is associated with it;
3. which claim is being evaluated;
4. what evidence was used;
5. which procedure was used;
6. when the result was produced;
7. whether a later event superseded it;
8. whether the organization or claim has been revoked.

VERQIVIA therefore creates value by making verification **portable and inspectable**, not by granting legal ownership of a name.

## Product surface

The project should expose the same identity through four compatible surfaces:

1. **Verify Web** — for humans.
2. **Portable Verification Profile** — for machine-readable exchange.
3. **API** — for business software and marketplaces.
4. **Verification marker** — a visual entry point that opens the authoritative record.

These surfaces should resolve to the same underlying identity and lifecycle data.

## Commercial value hypothesis

The strongest commercial value is not "registration of a brand".

It is reducing uncertainty and verification work at the boundary between:

- companies and suppliers;
- brands and digital channels;
- marketplaces and sellers;
- organizations and partners;
- software and external business identities;
- users and business-facing AI agents.

Potential paid services, only after real pilot validation, include enterprise onboarding, managed verification procedures, API usage, audit exports, policy integrations and higher-assurance verification services.

## Non-goals

VERQIVIA must not claim that it:

- grants trademark rights;
- proves every fact about an organization;
- guarantees a company is trustworthy;
- replaces government or registry authorities;
- replaces TLS, email authentication, domain registration or corporate security;
- turns an external source into truth merely because it was referenced.

## Success criteria

A commercially useful release should let:

- a normal user understand a result in seconds;
- a business publish and update a portable identity;
- software resolve the same identity without screen scraping;
- a verifier see evidence and scope rather than an unexplained badge;
- a later revocation or superseding event change the current result without deleting history;
- external standards be integrated without making unsupported conformance claims.
