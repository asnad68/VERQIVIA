# VERQIVIA AI / Machine Integration Guide

## Purpose

VERQIVIA exposes machine-readable verification data so software and AI agents can inspect an organization's identity and specific claims without screen scraping.

This is an integration guide, not a claim that every AI system currently supports VERQIVIA.

## Recommended resolution flow

~~~text
1. Obtain a VERQIVIA ID or discover it from a participating domain
2. GET /v1/identity/{nothing_id}/profile
3. Check profile status and revocation
4. For each relevant claim, inspect status, scope and current event
5. Follow evidence and procedure references when the decision requires more detail
6. Prefer the latest non-superseded verification event
7. Never convert one claim result into a universal trust score
~~~

## AI safety rules

A machine consumer SHOULD:

- treat REVOKED as a current negative lifecycle signal;
- distinguish SELF-CLAIMED, SOURCE-VERIFIED, VERIFIED, NOT-VERIFIED and INCONCLUSIVE;
- respect the declared verification scope;
- consider the age of the verification event when freshness matters;
- inspect evidence references when a consequential decision depends on the claim;
- treat procedure identifiers and versions as part of the verification context;
- preserve the distinction between evidence integrity and evidence truth;
- avoid inferring legal ownership, endorsement or authorization beyond the exact claim supported by the evidence.

A machine consumer MUST NOT:

- treat a VERQIVIA ID as a government registration number;
- treat the profile as a trademark registration;
- treat VERQIVIA as a universal reputation or trust score;
- assume that a company is safe, reputable or financially sound because one claim is verified;
- execute code, scripts or credentials contained in a profile;
- request private keys, passwords or seed phrases from a VERQIVIA participant.

## Preferred machine endpoint

The preferred endpoint is:

~~~http
GET /v1/identity/{nothing_id}/profile
Accept: application/json
~~~

The profile is intentionally additive to the v0.1 protocol and can be consumed without rendering HTML.

## Human verification

For human review, follow the profile links.verify target. The Verify Web page exposes the underlying claim/evidence/event graph and, where available, cryptographic proof status.

## Discovery

A participating domain may publish:

~~~text
https://example.com/.well-known/verqivia.json
~~~

The discovery document is a pointer. Domain publication alone is not proof of ownership, authorization or legal status.

## AI/tool integration

Because the machine interface uses ordinary HTTPS + JSON and an OpenAPI contract, an AI platform, agent framework, enterprise application or internal tool can integrate VERQIVIA through its own HTTP/tool adapter.

VERQIVIA does not require a proprietary AI runtime and does not assume a particular model vendor.

## Consequential decisions

For procurement, onboarding, payments, security actions or other high-impact workflows, VERQIVIA should be treated as one input to a decision process. The consuming system remains responsible for its own policy, source validation and human review requirements.
