const test = require("node:test");
const assert = require("node:assert/strict");
const { generateKeyPairSync, sign, webcrypto } = require("node:crypto");
const {
  validateConfig,
  validateAccessToken,
  validateIdToken,
  parseJwt
} = require("../site/portal-auth.js");

const config = {
  apiBaseUrl: "https://api.verqivia.example",
  oidcIssuer: "https://identity.verqivia.example/",
  oidcClientId: "verqivia-public-client",
  oidcAudience: "https://api.verqivia.example",
  scope: "openid profile email nothing:pilot:write"
};

function encodeJson(value) {
  return Buffer.from(JSON.stringify(value)).toString("base64url");
}

function fakeJwt(header, claims) {
  return encodeJson(header) + "." + encodeJson(claims) + ".not-a-real-signature";
}

const testKeys = generateKeyPairSync("rsa", { modulusLength: 2048 });
const publicJwk = {
  ...testKeys.publicKey.export({ format: "jwk" }),
  kid: "portal-auth-test-key",
  use: "sig",
  alg: "RS256"
};

function signedJwt(header, claims, privateKey = testKeys.privateKey) {
  const input = encodeJson(header) + "." + encodeJson(claims);
  return input + "." + sign("RSA-SHA256", Buffer.from(input), privateKey).toString("base64url");
}

function validIdClaims(nonce = "expected-nonce") {
  return {
    iss: "https://identity.verqivia.example",
    sub: "pilot-user-123",
    aud: "verqivia-public-client",
    exp: 1_800_000_900,
    iat: 1_800_000_000,
    nonce
  };
}

function validClaims() {
  return {
    iss: "https://identity.verqivia.example",
    aud: "https://api.verqivia.example",
    sub: "pilot-user-123",
    jti: "token-unique-id",
    client_id: "verqivia-public-client",
    scope: "openid nothing:pilot:write",
    iat: 1_800_000_000,
    exp: 1_800_000_900
  };
}

test("portal requires explicit HTTPS API and OIDC configuration", () => {
  assert.match(validateConfig({}, { protocol: "https:", hostname: "asnad68.github.io" }), /configure/i);
  assert.equal(validateConfig(config, { protocol: "https:", hostname: "asnad68.github.io" }), "");
  assert.match(validateConfig({ ...config, apiBaseUrl: "http://api.example" }, { protocol: "https:", hostname: "asnad68.github.io" }), /HTTPS/i);
});

test("portal config requires the narrowly-scoped pilot permission", () => {
  assert.match(
    validateConfig({ ...config, scope: "openid profile" }, { protocol: "https:", hostname: "asnad68.github.io" }),
    /nothing:pilot:write/
  );
});

test("JWT parser reads well-formed token JSON only", () => {
  const token = fakeJwt({ typ: "at+jwt", alg: "RS256" }, validClaims());
  assert.equal(parseJwt(token).header.typ, "at+jwt");
  assert.throws(() => parseJwt("opaque-access-token"), /JWT access token/);
  assert.throws(() => parseJwt("a.b.c"), /InvalidCharacter|JSON|position|property/i);
});

test("access-token contract rejects wrong token type, audience and scope", () => {
  const now = 1_800_000_100;
  const goodHeader = { typ: "at+jwt", alg: "RS256" };
  assert.equal(
    validateAccessToken(fakeJwt(goodHeader, validClaims()), config, now).sub,
    "pilot-user-123"
  );
  assert.throws(
    () => validateAccessToken(fakeJwt({ ...goodHeader, typ: "JWT" }, validClaims()), config, now),
    /token type/i
  );
  assert.throws(
    () => validateAccessToken(fakeJwt(goodHeader, { ...validClaims(), aud: "https://wrong.example" }), config, now),
    /audience/i
  );
  assert.throws(
    () => validateAccessToken(fakeJwt(goodHeader, { ...validClaims(), scope: "openid" }), config, now),
    /permission/i
  );
  assert.throws(
    () => validateAccessToken(fakeJwt(goodHeader, { ...validClaims(), client_id: "another-client" }), config, now),
    /client_id/i
  );
});


test("ID token requires a valid RS256 signature and all OIDC transaction bindings", async () => {
  const token = signedJwt(
    { alg: "RS256", kid: "portal-auth-test-key", typ: "JWT" },
    validIdClaims()
  );
  const claims = await validateIdToken(
    token,
    config,
    "expected-nonce",
    { keys: [publicJwk] },
    webcrypto,
    1_800_000_100
  );
  assert.equal(claims.sub, "pilot-user-123");

  await assert.rejects(
    validateIdToken(token, config, "wrong-nonce", { keys: [publicJwk] }, webcrypto, 1_800_000_100),
    /nonce/i
  );
  await assert.rejects(
    validateIdToken(
      signedJwt({ alg: "RS256", kid: "portal-auth-test-key" }, { ...validIdClaims(), aud: "wrong-client" }),
      config,
      "expected-nonce",
      { keys: [publicJwk] },
      webcrypto,
      1_800_000_100
    ),
    /audience/i
  );
  await assert.rejects(
    validateIdToken(
      token.slice(0, token.lastIndexOf(".") + 1) + Buffer.from("tampered").toString("base64url"),
      config,
      "expected-nonce",
      { keys: [publicJwk] },
      webcrypto,
      1_800_000_100
    ),
    /signature/i
  );
});

test("ID token rejects duplicate or invalid authorized-party bindings", async () => {
  const token = signedJwt(
    { alg: "RS256", kid: "portal-auth-test-key" },
    { ...validIdClaims(), aud: ["verqivia-public-client", "another-client"], azp: "another-client" }
  );
  await assert.rejects(
    validateIdToken(token, config, "expected-nonce", { keys: [publicJwk] }, webcrypto, 1_800_000_100),
    /authorized party/i
  );
});

test("server status probe checks health and storage readiness without sending credentials", async () => {
  const calls = [];
  const browser = {
    location: { protocol: "https:", hostname: "asnad68.github.io" },
    sessionStorage: { getItem: () => null, setItem: () => {}, removeItem: () => {} },
    crypto: {},
    fetch: async (url, options) => {
      calls.push({ url, options });
      if (url.endsWith("/healthz")) {
        return { ok: true, status: 200, json: async () => ({ status: "ok" }) };
      }
      return { ok: false, status: 503, json: async () => ({ status: "not_ready" }) };
    }
  };
  const state = await require("../site/portal-auth.js").createClient(config, browser).checkServer();
  assert.deepEqual(state, {
    health: { httpStatus: 200, status: "ok" },
    readiness: { httpStatus: 503, status: "not_ready" }
  });
  assert.equal(calls.length, 2);
  assert.equal(calls[0].url, "https://api.verqivia.example/healthz");
  assert.equal(calls[1].url, "https://api.verqivia.example/readyz");
  for (const call of calls) {
    assert.equal(call.options.credentials, "omit");
    assert.equal(call.options.redirect, "error");
    assert.equal(call.options.referrerPolicy, "no-referrer");
    assert.equal("Authorization" in (call.options.headers || {}), false);
  }
});

test("access-token contract rejects expired tokens and incomplete server claims", () => {
  const header = { typ: "at+jwt", alg: "RS256" };
  assert.throws(
    () => validateAccessToken(fakeJwt(header, { ...validClaims(), exp: 1_800_000_010 }), config, 1_800_000_020),
    /expired/i
  );
  const claims = validClaims();
  delete claims.jti;
  assert.throws(
    () => validateAccessToken(fakeJwt(header, claims), config, 1_800_000_100),
    /jti/i
  );
});
