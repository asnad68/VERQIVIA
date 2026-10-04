# VERQIVIA Interoperability Boundary

## Purpose

VERQIVIA should interoperate with existing identity, trust and domain ecosystems instead of creating a closed trust island.

This document defines the first interoperability boundary. It is an integration plan, not a claim of standards conformance.

## Verifiable Credentials

The stable external target is the W3C Verifiable Credentials Data Model 2.0 Recommendation. A newer Verifiable Credentials Data Model 2.1 Working Draft exists, so the implementation must pin the exact profile it supports instead of assuming the latest draft is stable.

Planned mapping:

- VERQIVIA Identity -> credential subject / identifier reference
- VERQIVIA Claim -> credential claim
- Evidence -> supporting evidence reference or status metadata, depending on the external profile
- Verification Event -> verifier-side event/audit record
- Revocation -> status mechanism, where a compatible status-list or equivalent profile is selected

VERQIVIA must not silently convert a VERQIVIA verification event into a W3C credential. An explicit issuance profile and issuer authorization are required.

## OpenID for Verifiable Credentials

OpenID for Verifiable Credential Issuance 1.0 is a Final Specification. VERQIVIA should treat it as a transport/issuance integration boundary, not as a replacement for the internal claim/evidence protocol.

The first integration target should be:

registration/authorization -> issuer policy -> credential issuance -> external verifier

The internal record remains authoritative for VERQIVIA lifecycle history.

## LEI / GLEIF

GLEIF provides public API access to LEI reference data and relationships. VERQIVIA can use LEI data as authoritative external evidence when the claim being tested concerns a legal entity.

The integration must preserve:

- LEI identifier
- source URL/API reference
- retrieval timestamp
- matched fields
- matching method
- source limitations

A fuzzy name match must never be treated as proof of legal identity by itself.

## BIMI

BIMI provides a useful domain-controlled brand-indicator ecosystem. It should be treated as an adjacent signal, not as a general business-identity certificate.

Potential VERQIVIA evidence:

- domain publishes BIMI record
- domain has aligned email authentication
- logo indicator is referenced by the domain

VERQIVIA must not infer ownership or trademark validity solely from the presence of a BIMI record.

## Boundary rule

External standards provide evidence, transport or interoperability semantics. VERQIVIA retains its own explicit claim scope, evidence provenance, verification event history and revocation semantics.

No external integration should introduce an implicit universal trust score.
