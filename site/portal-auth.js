(function attachPortalAuth(root, factory) {
  "use strict";
  const api = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.VERQIVIA_PORTAL_AUTH = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function createPortalAuthApi() {
  "use strict";

  const REQUIRED_SCOPE = "nothing:pilot:write";
  const TRANSACTION_KEY = "verqivia.portal.oidc.transaction.v1";
  const SESSION_KEY = "verqivia.portal.oidc.session.v1";
  const CALLBACK_MAX_AGE_MS = 10 * 60 * 1000;
  const CLOCK_SKEW_MS = 30 * 1000;

  function normalizedIssuer(value) {
    return String(value || "").trim().replace(/\/+$/, "");
  }

  function httpsUrl(value, field, { allowPath = true } = {}) {
    let parsed;
    try { parsed = new URL(String(value || "")); }
    catch (_error) { throw new Error(field + " must be a configured absolute HTTPS URL."); }
    if (parsed.protocol !== "https:" || !parsed.hostname || parsed.username || parsed.password ||
        parsed.search || parsed.hash || (!allowPath && parsed.pathname !== "/")) {
      throw new Error(field + " must be a valid HTTPS URL without credentials, query or fragment.");
    }
    return parsed;
  }

  function validateConfig(config, pageLocation) {
    if (!config || typeof config !== "object") return "Public OIDC/API configuration is missing.";
    const required = ["apiBaseUrl", "oidcIssuer", "oidcClientId", "oidcAudience"];
    if (required.some((key) => typeof config[key] !== "string" || !config[key].trim())) {
      return "The operator must configure the API URL, OIDC issuer, public client ID and API audience first.";
    }
    try {
      const api = httpsUrl(config.apiBaseUrl, "API URL");
      const issuer = httpsUrl(config.oidcIssuer, "OIDC issuer");
      if (api.origin === issuer.origin && api.pathname.replace(/\/$/, "") === issuer.pathname.replace(/\/$/, "")) {
        return "The API URL and OIDC issuer must identify their respective configured endpoints.";
      }
      if (pageLocation && pageLocation.protocol !== "https:" && pageLocation.hostname !== "localhost") {
        return "The Portal must be opened over HTTPS.";
      }
      const scopes = new Set(String(config.scope || "").split(/\s+/).filter(Boolean));
      if (!scopes.has("openid") || !scopes.has(REQUIRED_SCOPE)) {
        return "OIDC scope must include openid and " + REQUIRED_SCOPE + ".";
      }
    } catch (error) {
      return error.message || "The public OIDC/API configuration is invalid.";
    }
    return "";
  }

  function base64Url(bytes) {
    let binary = "";
    for (let i = 0; i < bytes.length; i += 1) binary += String.fromCharCode(bytes[i]);
    const encoded = typeof btoa === "function"
      ? btoa(binary)
      : Buffer.from(bytes).toString("base64");
    return encoded.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
  }

  function decodeBase64UrlJson(segment) {
    const normalized = String(segment || "").replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized + "=".repeat((4 - normalized.length % 4) % 4);
    let text;
    if (typeof atob === "function") {
      const binary = atob(padded);
      const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
      text = new TextDecoder().decode(bytes);
    } else {
      text = Buffer.from(padded, "base64").toString("utf8");
    }
    return JSON.parse(text);
  }

  function parseJwt(token) {
    if (typeof token !== "string") throw new Error("The identity provider did not return a JWT access token.");
    const parts = token.split(".");
    if (parts.length !== 3) throw new Error("The identity provider returned an opaque token; a signed JWT access token is required.");
    return { header: decodeBase64UrlJson(parts[0]), claims: decodeBase64UrlJson(parts[1]) };
  }

  function validateAccessToken(token, config, nowSeconds) {
    const parsed = parseJwt(token);
    const header = parsed.header;
    const claims = parsed.claims;
    if (!["at+jwt", "application/at+jwt"].includes(header.typ)) {
      throw new Error("The provider's access-token type is incompatible with the VERQIVIA resource server.");
    }
    if (header.alg !== "RS256") {
      throw new Error("The provider must issue RS256-signed access tokens for this deployment.");
    }
    const iss = normalizedIssuer(claims.iss);
    if (iss !== normalizedIssuer(config.oidcIssuer)) throw new Error("Access-token issuer does not match the configured issuer.");
    const aud = Array.isArray(claims.aud) ? claims.aud : [claims.aud];
    if (!aud.includes(config.oidcAudience)) throw new Error("Access-token audience does not match the VERQIVIA API.");
    for (const key of ["sub", "jti", "client_id"]) {
      if (typeof claims[key] !== "string" || !claims[key]) throw new Error("The access token is missing required claim: " + key + ".");
    }
    if (!Number.isFinite(claims.exp) || !Number.isFinite(claims.iat)) {
      throw new Error("Access token must include numeric exp and iat claims.");
    }
    if (claims.exp <= nowSeconds || claims.iat > nowSeconds + 60) throw new Error("The access token is expired or not yet valid.");
    if (typeof claims.scope !== "string" || !claims.scope.split(/\s+/).includes(REQUIRED_SCOPE)) {
      throw new Error("Access token does not include the " + REQUIRED_SCOPE + " permission.");
    }
    return claims;
  }

  function createClient(config, env) {
    const browser = env || (typeof window !== "undefined" ? window : null);
    let metadata = null;

    function mustHaveBrowser() {
      if (!browser || !browser.location || !browser.sessionStorage || !browser.crypto || !browser.fetch) {
        throw new Error("This secure portal requires a modern HTTPS browser.");
      }
    }

    function redirectUri() {
      const url = new URL(browser.location.href);
      url.search = "";
      url.hash = "";
      return url.href;
    }

    function ensureConfig() {
      mustHaveBrowser();
      const problem = validateConfig(config, browser.location);
      if (problem) throw new Error(problem);
    }

    function randomString(length) {
      const bytes = new Uint8Array(length);
      browser.crypto.getRandomValues(bytes);
      return base64Url(bytes);
    }

    async function sha256Base64Url(text) {
      const bytes = new TextEncoder().encode(text);
      return base64Url(new Uint8Array(await browser.crypto.subtle.digest("SHA-256", bytes)));
    }

    async function discover() {
      ensureConfig();
      if (metadata) return metadata;
      const issuer = normalizedIssuer(config.oidcIssuer);
      const response = await browser.fetch(issuer + "/.well-known/openid-configuration", {
        method: "GET", credentials: "omit", cache: "no-store", redirect: "error",
        headers: { Accept: "application/json" }
      });
      if (!response.ok) throw new Error("Could not load the configured OIDC provider metadata.");
      const document = await response.json();
      if (!document || normalizedIssuer(document.issuer) !== issuer) {
        throw new Error("OIDC discovery issuer does not match the configured issuer.");
      }
      for (const key of ["authorization_endpoint", "token_endpoint", "jwks_uri"]) {
        const endpoint = httpsUrl(document[key], "OIDC " + key);
        if (!endpoint.hostname) throw new Error("OIDC metadata contains an invalid endpoint.");
      }
      if (!Array.isArray(document.response_types_supported) ||
          !document.response_types_supported.includes("code")) {
        throw new Error("OIDC provider does not advertise authorization-code flow.");
      }
      if (Array.isArray(document.code_challenge_methods_supported) &&
          !document.code_challenge_methods_supported.includes("S256")) {
        throw new Error("OIDC provider does not support PKCE with S256.");
      }
      metadata = document;
      return metadata;
    }

    async function login() {
      ensureConfig();
      const document = await discover();
      const verifier = randomString(32);
      const state = randomString(32);
      const nonce = randomString(32);
      const uri = redirectUri();
      const transaction = { verifier, state, nonce, redirectUri: uri, createdAt: Date.now() };
      browser.sessionStorage.setItem(TRANSACTION_KEY, JSON.stringify(transaction));
      const challenge = await sha256Base64Url(verifier);
      const target = new URL(document.authorization_endpoint);
      const scopes = new Set(String(config.scope).split(/\s+/).filter(Boolean));
      scopes.add("openid");
      scopes.add(REQUIRED_SCOPE);
      target.searchParams.set("response_type", "code");
      target.searchParams.set("client_id", config.oidcClientId.trim());
      target.searchParams.set("redirect_uri", uri);
      target.searchParams.set("scope", Array.from(scopes).join(" "));
      target.searchParams.set("state", state);
      target.searchParams.set("nonce", nonce);
      target.searchParams.set("code_challenge", challenge);
      target.searchParams.set("code_challenge_method", "S256");
      if (String(config.oidcAudience || "").trim()) target.searchParams.set("audience", config.oidcAudience.trim());
      browser.location.assign(target.href);
    }

    async function finishCallback() {
      mustHaveBrowser();
      const url = new URL(browser.location.href);
      const code = url.searchParams.get("code");
      const state = url.searchParams.get("state");
      const providerError = url.searchParams.get("error");
      if (!code && !providerError) return { handled: false };
      const txRaw = browser.sessionStorage.getItem(TRANSACTION_KEY);
      browser.history.replaceState({}, "", redirectUri());
      if (!txRaw) throw new Error("The sign-in transaction is missing. Start account connection again.");
      let tx;
      try { tx = JSON.parse(txRaw); }
      catch (_error) { browser.sessionStorage.removeItem(TRANSACTION_KEY); throw new Error("The sign-in transaction is invalid. Start again."); }
      if (!state || state !== tx.state || Date.now() - tx.createdAt > CALLBACK_MAX_AGE_MS ||
          tx.redirectUri !== redirectUri()) {
        browser.sessionStorage.removeItem(TRANSACTION_KEY);
        throw new Error("Sign-in state did not match or the request expired. Start again.");
      }
      if (providerError) {
        browser.sessionStorage.removeItem(TRANSACTION_KEY);
        throw new Error("The identity provider declined sign-in (" + providerError + ").");
      }
      ensureConfig();
      const document = await discover();
      const form = new URLSearchParams({
        grant_type: "authorization_code",
        client_id: config.oidcClientId.trim(),
        code,
        redirect_uri: tx.redirectUri,
        code_verifier: tx.verifier
      });
      let response;
      try {
        response = await browser.fetch(document.token_endpoint, {
          method: "POST",
          credentials: "omit",
          cache: "no-store",
          redirect: "error",
          referrerPolicy: "no-referrer",
          headers: { "Content-Type": "application/x-www-form-urlencoded", Accept: "application/json" },
          body: form.toString()
        });
      } finally {
        browser.sessionStorage.removeItem(TRANSACTION_KEY);
      }
      const tokenData = await response.json().catch(() => null);
      if (!response.ok || !tokenData) throw new Error("The token exchange failed; check provider CORS, callback and client configuration.");
      if (typeof tokenData.access_token !== "string" || tokenData.token_type?.toLowerCase() !== "bearer") {
        throw new Error("The provider did not return a Bearer access token.");
      }
      if (typeof tokenData.id_token !== "string") throw new Error("The OIDC response did not include an ID token for nonce binding.");
      const idToken = parseJwt(tokenData.id_token);
      if (idToken.claims.nonce !== tx.nonce) throw new Error("ID-token nonce did not match the sign-in request.");
      const claims = validateAccessToken(tokenData.access_token, config, Math.floor(Date.now() / 1000));
      const lifetime = Number(tokenData.expires_in);
      if (!Number.isFinite(lifetime) || lifetime < 60 || lifetime > 86400) {
        throw new Error("The access-token lifetime is missing or outside the accepted range.");
      }
      browser.sessionStorage.setItem(SESSION_KEY, JSON.stringify({
        accessToken: tokenData.access_token,
        expiresAt: Date.now() + lifetime * 1000,
        actor: claims.sub,
        issuer: normalizedIssuer(claims.iss),
        clientId: claims.client_id,
        audience: config.oidcAudience
      }));
      return { handled: true, actor: claims.sub };
    }

    function getToken() {
      mustHaveBrowser();
      const raw = browser.sessionStorage.getItem(SESSION_KEY);
      if (!raw) return null;
      try {
        const session = JSON.parse(raw);
        if (typeof session.accessToken !== "string" || session.expiresAt <= Date.now() + CLOCK_SKEW_MS ||
            session.issuer !== normalizedIssuer(config.oidcIssuer) || session.audience !== config.oidcAudience) {
          browser.sessionStorage.removeItem(SESSION_KEY);
          return null;
        }
        return session.accessToken;
      } catch (_error) {
        browser.sessionStorage.removeItem(SESSION_KEY);
        return null;
      }
    }

    function logout() {
      mustHaveBrowser();
      browser.sessionStorage.removeItem(SESSION_KEY);
      browser.sessionStorage.removeItem(TRANSACTION_KEY);
    }

    async function apiRequest(path, options) {
      ensureConfig();
      if (!/^\/v1\/pilot\/drafts(?:\/[0-9a-f-]{36})?$/.test(path)) throw new Error("The portal client may only call the pilot-draft API.");
      const token = getToken();
      if (!token) throw new Error("Connect an authorized pilot account before sending or reading a server draft.");
      const response = await browser.fetch(normalizedIssuer(config.apiBaseUrl) + path, {
        ...(options || {}),
        credentials: "omit",
        cache: "no-store",
        redirect: "error",
        headers: {
          ...((options && options.headers) || {}),
          Authorization: "Bearer " + token,
          Accept: "application/json"
        }
      });
      const body = await response.json().catch(() => null);
      if (!response.ok) {
        const message = body && body.detail ? body.detail : "Server request failed (HTTP " + response.status + ").";
        if (response.status === 401) browser.sessionStorage.removeItem(SESSION_KEY);
        throw new Error(message);
      }
      return body;
    }

    async function submitDraft(draft, idempotencyKey) {
      if (!/^[\x21-\x7E]{1,255}$/.test(idempotencyKey || "")) throw new Error("Invalid submission idempotency key.");
      return apiRequest("/v1/pilot/drafts", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Idempotency-Key": idempotencyKey },
        body: JSON.stringify(draft)
      });
    }

    async function readDraft(draftId) {
      if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(draftId || "")) {
        throw new Error("The server returned an invalid draft identifier.");
      }
      return apiRequest("/v1/pilot/drafts/" + draftId, { method: "GET" });
    }

    return { discover, login, finishCallback, getToken, logout, submitDraft, readDraft };
  }

  return {
    REQUIRED_SCOPE,
    validateConfig,
    parseJwt,
    validateAccessToken,
    createClient
  };
});
