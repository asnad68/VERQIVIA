# VERQIVIA Portable Verification Profile

## Status

This document defines an experimental **0.2-draft** exchange profile for VERQIVIA.

It is a profile and adapter format, not a claim of conformance with W3C, OpenID Foundation, GLEIF, BIMI or GS1 specifications.

## Why the profile exists

The same business identity should be usable by a human verifier and by software.

A portable profile carries the minimum structured information needed to:

- identify the subject;
- expose selected identifiers and domains;
- enumerate claims;
- link each claim to current verification state;
- express relationships;
- provide canonical verification/discovery links;
- preserve a clear boundary between verification and legal ownership.

## Core shape

```json
{
  "profile_type": "VERQIVIA-PORTABLE-VERIFICATION-PROFILE",
  "profile_version": "0.2-draft",
  "verqivia_id": "NTH-000001",
  "subject": {
    "name": "Example Corporation",
    "type": "business",
    "website": "https://example.com"
  },
  "status": "ACTIVE",
  "identifiers": [],
  "domains": [],
  "claims": [],
  "relationships": [],
  "links": {
    "verify": "https://.../verify.html?id=NTH-000001"
  }
}
```

## Claim semantics

A claim is not considered globally true merely because it appears in a profile.

Each claim should expose:

- the statement;
- the current VERQIVIA status;
- the current verification event when available;
- evidence references;
- verification scope and timing.

This preserves the core VERQIVIA rule:

> **Verify the claim, not the reputation of the whole company.**

## Relationships

The profile can express relationships such as:

- official domain;
- brand association;
- authorized agent;
- authorized partner;
- marketplace merchant account;
- digital channel.

Relationship records must carry an explicit status and scope. A relationship does not imply ownership unless the underlying claim and evidence actually establish that specific proposition.

## Interoperability boundaries

### W3C Verifiable Credentials

W3C Verifiable Credentials Data Model 2.0 is a W3C Recommendation. VERQIVIA can expose a future adapter that maps selected VERQIVIA claims into VC-compatible credentials or presentations.

That adapter must keep issuer, holder and verifier semantics explicit and must not label the current VERQIVIA profile itself as a W3C credential.

### OpenID for Verifiable Credential Issuance

OpenID for Verifiable Credential Issuance 1.0 is a Final Specification. A future VERQIVIA integration may use OpenID4VCI transport and issuance flows for credentials derived from verified VERQIVIA claims.

VERQIVIA should not invent a proprietary credential-issuance flow when an established interoperability path is available.

### GLEIF / LEI

GLEIF provides a public API for searching LEI and related organizational data. The profile therefore permits an LEI identifier to be attached to an organization without treating the LEI as a universal trust score.

A future implementation can resolve the LEI against the GLEIF ecosystem and retain the external source plus timestamp as evidence.

### BIMI

BIMI is a useful domain-level signal around authenticated email and brand indicators. VERQIVIA may reference a BIMI record as evidence or a domain signal.

A BIMI record must not be treated as proof of all corporate or trademark claims.

### GS1 Digital Link

GS1 Digital Link provides a standardized URI approach for connecting identifiers to web information. VERQIVIA can use similar resolver-oriented design patterns for its own identifiers while remaining a separate system.

## Discovery

A participating domain may publish a small discovery document at:

```text
https://example.com/.well-known/verqivia.json
```

The document should point to the canonical VERQIVIA identity and verification endpoint.

The discovery document is a pointer, not proof by itself. Domain control must still be evaluated by the configured VERQIVIA procedure.

## Security requirements

Portable profiles must be:

- immutable once published as a versioned artifact;
- bound to a specific VERQIVIA identity;
- explicit about issuer/signing information when cryptographic proof is present;
- safe to consume without executing remote code;
- free of credentials, seed phrases and private keys;
- explicit about revocation and supersession;
- clear about the difference between evidence integrity and evidence truth.

## Privacy requirements

A profile should expose only the information needed for the declared verification purpose.

Avoid collecting:

- passport scans;
- seed phrases;
- private keys;
- unnecessary personal data;
- unrelated banking information.

## Compatibility strategy

The v0.2 profile is intentionally additive.

Existing v0.1 identifiers and protocol contracts remain unchanged:

- `NTH-*` identity IDs;
- `NOTHING_*` environment variables;
- existing procedure IDs;
- existing cryptographic envelope identifiers.

A future protocol version can migrate those identifiers deliberately rather than breaking existing records.
