/*
 * Public, non-secret configuration for the VERQIVIA browser pilot.
 *
 * The API URL, OIDC issuer, client ID and audience are intentionally blank
 * until the operator has provisioned the matching server and identity provider.
 * Never put a client secret, bearer token, API key or private key in this file.
 */
window.VERQIVIA_PORTAL_CONFIG = Object.freeze({
  apiBaseUrl: "",
  oidcIssuer: "",
  oidcClientId: "",
  oidcAudience: "",
  scope: "openid profile email nothing:pilot:write"
});
