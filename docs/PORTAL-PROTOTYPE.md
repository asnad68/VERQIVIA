# VERQIVIA Portal Prototype

## Purpose

`site/portal.html` is the company-facing front door for the future VERQIVIA organization portal. The current implementation is a **browser-only draft tool**, not a hosted organization workspace.

## Current working behavior

- Collects a business/brand name, type, website, domain, public description, channels, pilot claims and evidence boundary.
- Validates draft fields locally, including URL schemes, URL credentials, hostname shape, field sizes and supported claim types.
- Produces a JSON envelope with a `registration` object matching the shape in `schema/registration-draft.schema.json`, plus separate pilot-planning metadata.
- Lets the user copy or download that JSON.
- Does not call the API, create a server record, authenticate an organization, verify domain control or persist drafts in browser storage.

The client-side checks improve draft quality only. They are not a security boundary; any future server endpoint must repeat validation and apply authorization itself. Do not enter passwords, seed phrases, private keys or confidential evidence into this public prototype.

## Intended production workflow

`Company → authenticated workspace → identity → claims → evidence → verification → public record/API`

The production portal still needs:

- managed company authentication and organization-controlled registration;
- server-side draft submission and durable persistence;
- tenant isolation and authorization tests;
- claim management, evidence references and visibility controls;
- verification requests, status and lifecycle/audit history;
- API credentials and machine-integration controls.

## Deployment boundary

The public prototype remains suitable for preparing a synthetic or non-confidential pilot draft. It does not represent a production multi-tenant SaaS application.

Production activation remains gated by managed authentication, PostgreSQL provisioning, gateway/rate limiting, observability, backup/restore, signing-key governance and legal/privacy review. Payments remain separately frozen.

## Product rule

GitHub is the engineering/backstage surface. The organization portal is the intended company-facing surface. Public Verify remains the human-facing inspection surface.
