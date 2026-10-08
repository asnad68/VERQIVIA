# VERQIVIA Portal Prototype

## Purpose

`site/portal.html` is the public front door for the future VERQIVIA organization portal.

It deliberately does **not** pretend to be a production multi-tenant SaaS application. The current prototype keeps customer credentials, private records, production authentication and production persistence outside the GitHub Pages surface.

## Intended production workflow

`Company → authenticated workspace → identity → claims → evidence → verification → public record/API`

The future portal should provide:

- authenticated company workspace;
- organization-controlled identities;
- claim management;
- evidence references and visibility controls;
- verification requests and status;
- lifecycle/audit history;
- API credentials and machine-integration controls;
- tenant isolation.

## Current prototype boundary

The static portal only routes a prospective pilot participant to the existing public surfaces:

- Register
- Verify
- Pilot
- Security
- Integrate

Production activation remains gated by managed authentication, PostgreSQL provisioning, gateway/rate limiting, observability, backup/restore, signing-key governance and legal/privacy review.

## Product rule

GitHub is the engineering/backstage surface. The organization portal is the intended company-facing surface. Public Verify remains the human-facing inspection surface.
