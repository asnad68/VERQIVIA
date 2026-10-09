const test = require("node:test");
const assert = require("node:assert/strict");
const {
  validateConfig,
  validateAccessToken,
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
  assert.throws(() => parseJwt("a.b.c"), /JSON|position|property/i);
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
