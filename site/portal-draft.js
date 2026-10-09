(function attachPortalDraft(root, factory) {
  "use strict";
  const api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.VERQIVIA_PORTAL_DRAFT = api;
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function createPortalDraftApi() {
  "use strict";

  const ALLOWED_TYPES = new Set(["business", "brand", "digital_channel"]);
  const ALLOWED_CLAIMS = new Set([
    "official_domain",
    "official_website",
    "authorized_representative",
    "business_relationship"
  ]);

  function cleanText(value, field, maxLength) {
    const text = value == null ? "" : String(value).trim();
    if (text.length > maxLength) {
      throw new Error(field + " must be no longer than " + maxLength + " characters.");
    }
    return text;
  }

  function uniqueLines(value, field, maxCount, maxLength) {
    const raw = Array.isArray(value) ? value : String(value == null ? "" : value).split(/\r?\n/);
    const result = [];
    for (const item of raw) {
      if (typeof item !== "string") {
        throw new Error(field + " must contain text values only.");
      }
      const entry = item.trim();
      if (!entry) continue;
      if (entry.length > maxLength) {
        throw new Error(field + " entries must be no longer than " + maxLength + " characters.");
      }
      if (!result.includes(entry)) result.push(entry);
    }
    if (result.length > maxCount) {
      throw new Error(field + " cannot contain more than " + maxCount + " entries.");
    }
    return result;
  }

  function validateHttpUrl(value, field) {
    const text = cleanText(value, field, 500);
    if (!text) return "";
    let parsed;
    try {
      parsed = new URL(text);
    } catch (_error) {
      throw new Error(field + " must be an absolute HTTP(S) URL.");
    }
    if (!["http:", "https:"].includes(parsed.protocol) ||
        !parsed.hostname ||
        parsed.username ||
        parsed.password) {
      throw new Error(field + " must be an absolute HTTP(S) URL without credentials.");
    }
    return parsed.href;
  }

  function validateDomain(value) {
    const text = cleanText(value, "Official domain", 253);
    if (!text) return "";
    if (/[\s/@?#:]/.test(text) || text.includes("://") || text.includes("/")) {
      throw new Error("Official domain must be a hostname only, such as example.com.");
    }
    let hostname;
    try {
      const parsed = new URL("https://" + text.replace(/\.$/, ""));
      if (parsed.pathname !== "/" || parsed.search || parsed.hash || parsed.port) {
        throw new Error("invalid hostname");
      }
      hostname = parsed.hostname.toLowerCase();
    } catch (_error) {
      throw new Error("Official domain is not a valid hostname.");
    }
    if (!hostname.includes(".") ||
        hostname === "localhost" ||
        hostname.endsWith(".local") ||
        hostname.endsWith(".internal") ||
        hostname.endsWith(".lan") ||
        hostname.endsWith(".home.arpa") ||
        /^\d{1,3}(\.\d{1,3}){3}$/.test(hostname)) {
      throw new Error("Use a public organization domain, not an IP address or local hostname.");
    }
    const labels = hostname.split(".");
    if (labels.some(label =>
      !label || label.length > 63 ||
      !/^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/i.test(label)
    )) {
      throw new Error("Official domain is not a valid hostname.");
    }
    return hostname;
  }

  function buildPortalDraft(input, generatedAt) {
    const source = input || {};
    const name = cleanText(source.name, "Business / brand name", 180);
    if (!name) throw new Error("Business / brand name is required.");
    const type = cleanText(source.type || "business", "Type", 30);
    if (!ALLOWED_TYPES.has(type)) throw new Error("Select a supported business type.");

    const website = validateHttpUrl(source.website, "Official website");
    const domain = validateDomain(source.domain);
    const description = cleanText(source.description, "Public description", 2000);
    const channels = uniqueLines(source.channels, "Official digital channels", 50, 500)
      .map(channel => validateHttpUrl(channel, "Each digital channel"));
    const claims = uniqueLines(source.claims, "Pilot claims", 4, 80);
    if (!claims.length) throw new Error("Select at least one pilot claim.");
    if (claims.some(claim => !ALLOWED_CLAIMS.has(claim))) {
      throw new Error("The draft contains an unsupported pilot claim.");
    }
    const evidenceBoundary = cleanText(source.evidenceBoundary, "Evidence boundary", 3000);
    const timestamp = generatedAt === undefined ? new Date() : new Date(generatedAt);
    if (Number.isNaN(timestamp.getTime())) throw new Error("Draft timestamp is invalid.");

    const registration = {
      name,
      type,
      website,
      domains: domain ? [domain] : [],
      channels,
      description
    };

    return {
      stage: "PILOT_DRAFT",
      protocol_version: "0.1",
      generated_at: timestamp.toISOString(),
      registration,
      pilot: {
        requested_claims: claims,
        evidence_boundary: evidenceBoundary
      },
      readiness: {
        production_identity_created: false,
        server_submission: false,
        note: "Local planning draft only; production authorization and server-side validation are still required."
      }
    };
  }

  return { buildPortalDraft };
});
