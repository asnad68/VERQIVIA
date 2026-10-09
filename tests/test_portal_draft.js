"use strict";

const assert = require("node:assert/strict");
const { test } = require("node:test");
const { buildPortalDraft } = require("../site/portal-draft.js");

const base = {
  name: "Example Organization",
  type: "business",
  website: "https://example.com/about",
  domain: "Example.COM.",
  channels: "https://www.linkedin.com/company/example\nhttps://www.linkedin.com/company/example\n",
  description: "A synthetic organization for local draft tests.",
  claims: ["official_domain", "official_website", "official_domain"],
  evidenceBoundary: "Public website and DNS TXT check."
};

test("creates a schema-compatible registration payload without implying production creation", () => {
  const draft = buildPortalDraft(base, "2026-10-09T12:00:00Z");
  assert.equal(draft.stage, "PILOT_DRAFT");
  assert.equal(draft.generated_at, "2026-10-09T12:00:00.000Z");
  assert.deepEqual(Object.keys(draft.registration).sort(), [
    "channels", "description", "domains", "name", "type", "website"
  ]);
  assert.deepEqual(draft.registration.domains, ["example.com"]);
  assert.equal(draft.registration.channels.length, 1);
  assert.deepEqual(draft.pilot.requested_claims, ["official_domain", "official_website"]);
  assert.equal(draft.readiness.production_identity_created, false);
  assert.equal(draft.readiness.server_submission, false);
});

test("allows an optional website and domain but requires at least one claim", () => {
  const draft = buildPortalDraft({
    name: "Example",
    type: "brand",
    website: "",
    domain: "",
    channels: "",
    description: "",
    claims: ["business_relationship"],
    evidenceBoundary: ""
  }, "2026-10-09T00:00:00Z");
  assert.equal(draft.registration.website, "");
  assert.deepEqual(draft.registration.domains, []);
  assert.deepEqual(draft.registration.channels, []);
  assert.throws(() => buildPortalDraft({ ...base, claims: [] }), /Select at least one pilot claim/);
});

test("rejects malformed or credential-bearing web addresses", () => {
  assert.throws(() => buildPortalDraft({ ...base, website: "javascript:alert(1)" }), /HTTP\(S\) URL/);
  assert.throws(() => buildPortalDraft({ ...base, website: "https://user:secret@example.com" }), /without credentials/);
  assert.throws(() => buildPortalDraft({ ...base, channels: "https://example.com\nftp://example.com" }), /HTTP\(S\) URL/);
});

test("rejects private and malformed organization domains", () => {
  for (const domain of ["localhost", "127.0.0.1", "printer.local", "service.internal", "example.com/path", "example.com:8080"]) {
    assert.throws(() => buildPortalDraft({ ...base, domain }), /domain|hostname|public organization/i);
  }
});

test("rejects unsupported claim types and limits", () => {
  assert.throws(() => buildPortalDraft({ ...base, claims: ["admin_override"] }), /unsupported pilot claim/);
  assert.throws(() => buildPortalDraft({ ...base, name: "x".repeat(181) }), /180 characters/);
  assert.throws(() => buildPortalDraft({ ...base, description: "x".repeat(2001) }), /2000 characters/);
  assert.throws(() => buildPortalDraft({ ...base, generatedAt: "not-a-date" }, "not-a-date"), /timestamp is invalid/);
});
