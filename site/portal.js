(() => {
  "use strict";

  const byId = (id) => document.getElementById(id);
  const config = window.VERQIVIA_PORTAL_CONFIG || {};
  const authApi = window.VERQIVIA_PORTAL_AUTH;
  const client = authApi ? authApi.createClient(config, window) : null;

  let currentDraft = null;
  let currentIdempotencyKey = null;
  let submittedDraftId = null;

  function selectedClaims() {
    return Array.from(
      document.querySelectorAll('input[type="checkbox"][value]')
    ).filter((input) => input.checked).map((input) => input.value);
  }

  function buildDraft() {
    const builder = window.VERQIVIA_PORTAL_DRAFT;
    if (!builder || typeof builder.buildPortalDraft !== "function") {
      throw new Error("The local draft validator is unavailable. Reload the page and try again.");
    }
    return builder.buildPortalDraft({
      name: byId("company-name").value,
      type: byId("company-type").value,
      website: byId("official-website").value,
      domain: byId("official-domain").value,
      channels: byId("official-channels").value,
      description: byId("public-description").value,
      claims: selectedClaims(),
      evidenceBoundary: byId("evidence-notes").value
    });
  }

  function setStatus(message, ok) {
    const el = byId("portal-status");
    el.textContent = message;
    el.className = "status portal-status " + (ok ? "status-ok" : "status-neutral");
  }

  function setServerStatus(message, kind) {
    const el = byId("server-status");
    el.textContent = message;
    el.className = "status portal-status " + (
      kind === "ok" ? "status-ok" : kind === "bad" ? "status-bad" : "status-neutral"
    );
  }

  function renderDraft(draft) {
    byId("portal-preview").textContent = JSON.stringify(draft, null, 2);
  }

  function connected() {
    return Boolean(client && client.getToken());
  }

  function refreshControls() {
    const configured = Boolean(authApi && client && !authApi.validateConfig(config, window.location));
    const hasDraft = Boolean(currentDraft);
    const hasToken = configured && connected();
    byId("connect-account").disabled = !configured || hasToken;
    byId("disconnect-account").disabled = !hasToken;
    byId("submit-server-draft").disabled = !hasToken || !hasDraft;
    byId("refresh-server-draft").disabled = !hasToken || !submittedDraftId;
    if (!configured) {
      byId("connect-account").textContent = "Connection not configured";
    } else {
      byId("connect-account").textContent = hasToken ? "Account connected" : "Connect pilot account";
    }
    if (hasToken) {
      byId("auth-status").textContent = "Authenticated session active in this browser tab.";
      byId("auth-status").className = "status portal-status status-ok";
    } else {
      byId("auth-status").textContent = configured
        ? "Not connected. Connect an authorized pilot account before server submission."
        : authApi
          ? authApi.validateConfig(config, window.location)
          : "Secure authentication module is unavailable.";
      byId("auth-status").className = "status portal-status status-neutral";
    }
  }

  function newIdempotencyKey() {
    if (window.crypto && typeof window.crypto.randomUUID === "function") {
      return window.crypto.randomUUID();
    }
    const bytes = new Uint8Array(24);
    window.crypto.getRandomValues(bytes);
    return Array.from(bytes, (value) => value.toString(16).padStart(2, "0")).join("");
  }

  byId("portal-form").addEventListener("submit", (event) => {
    event.preventDefault();
    try {
      currentDraft = buildDraft();
      currentIdempotencyKey = newIdempotencyKey();
      submittedDraftId = null;
      renderDraft(currentDraft);
      setStatus("Pilot draft created locally. Submit it separately to the authenticated server intake.", true);
      setServerStatus("Local draft ready. No server submission has occurred yet.", "neutral");
      refreshControls();
    } catch (error) {
      currentDraft = null;
      currentIdempotencyKey = null;
      refreshControls();
      setStatus(error.message || "The draft could not be created.", false);
    }
  });

  byId("clear-draft").addEventListener("click", () => {
    byId("portal-form").reset();
    currentDraft = null;
    currentIdempotencyKey = null;
    submittedDraftId = null;
    byId("portal-preview").textContent = JSON.stringify({
      stage: "PILOT_DRAFT",
      registration: null,
      pilot: null,
      readiness: {
        production_identity_created: false,
        server_submission: false
      }
    }, null, 2);
    setStatus("Draft cleared. Nothing was sent to a server.", false);
    setServerStatus("No server draft selected.", "neutral");
    refreshControls();
  });

  byId("copy-draft").addEventListener("click", async () => {
    const text = byId("portal-preview").textContent;
    try {
      await navigator.clipboard.writeText(text);
      setStatus("JSON copied to the clipboard.", true);
    } catch (_error) {
      setStatus("Clipboard access is unavailable in this browser.", false);
    }
  });

  byId("download-draft").addEventListener("click", () => {
    const blob = new Blob(
      [byId("portal-preview").textContent + "\n"],
      { type: "application/json" }
    );
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "verqivia-pilot-draft.json";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    setStatus("Pilot draft prepared for local download.", true);
  });

  byId("connect-account").addEventListener("click", async () => {
    try {
      setServerStatus("Connecting to the configured identity provider…", "neutral");
      await client.login();
    } catch (error) {
      setServerStatus(error.message || "Account connection could not start.", "bad");
      refreshControls();
    }
  });

  byId("disconnect-account").addEventListener("click", () => {
    try {
      client.logout();
      setServerStatus("Local browser session cleared. The identity provider may still maintain its own sign-in session.", "neutral");
    } catch (error) {
      setServerStatus(error.message || "Could not clear this browser session.", "bad");
    }
    refreshControls();
  });

  byId("submit-server-draft").addEventListener("click", async () => {
    if (!currentDraft || !currentIdempotencyKey) {
      setServerStatus("Build a valid pilot draft first.", "bad");
      return;
    }
    if (!connected()) {
      setServerStatus("Connect an authorized account first.", "bad");
      refreshControls();
      return;
    }
    byId("submit-server-draft").disabled = true;
    try {
      setServerStatus("Submitting to the authenticated pilot intake…", "neutral");
      const result = await client.submitDraft(currentDraft, currentIdempotencyKey);
      const data = result && result.data;
      if (!data || typeof data.draft_id !== "string" || data.production_identity_created !== false) {
        throw new Error("The server response did not match the pilot-intake contract.");
      }
      submittedDraftId = data.draft_id;
      setServerStatus(
        "Server accepted pilot intake " + data.draft_id + " · " + data.status +
        (data.replayed ? " · safe retry" : "") +
        ". No official identity was created.",
        "ok"
      );
    } catch (error) {
      setServerStatus(error.message || "Server submission failed. Retry the same draft to preserve idempotency.", "bad");
    } finally {
      refreshControls();
    }
  });

  byId("refresh-server-draft").addEventListener("click", async () => {
    if (!submittedDraftId || !connected()) {
      setServerStatus("A connected session and previously submitted draft are required.", "bad");
      refreshControls();
      return;
    }
    try {
      setServerStatus("Reading the private server draft…", "neutral");
      const result = await client.readDraft(submittedDraftId);
      const data = result && result.data;
      if (!data || data.draft_id !== submittedDraftId || data.production_identity_created !== false) {
        throw new Error("The server response did not match the pilot-intake contract.");
      }
      setServerStatus(
        "Server record confirmed · " + data.draft_id + " · " + data.status +
        ". This remains an intake draft, not an official identity.",
        "ok"
      );
    } catch (error) {
      setServerStatus(error.message || "Could not retrieve the server draft.", "bad");
    } finally {
      refreshControls();
    }
  });

  async function initialize() {
    if (!authApi || !client) {
      setServerStatus("Secure authentication module is unavailable.", "bad");
      refreshControls();
      return;
    }
    const configProblem = authApi.validateConfig(config, window.location);
    if (configProblem) {
      setServerStatus(configProblem + " The API and OIDC provider have not yet been provisioned and configured.", "neutral");
      refreshControls();
      return;
    }
    let authCallbackError = "";
    try {
      // Consume and remove OIDC callback parameters before making any other network request.
      await client.finishCallback();
    } catch (error) {
      authCallbackError = error.message || "Sign-in could not be completed.";
    }

    try {
      const state = await client.checkServer();
      if (state.health.status === "ok" && state.readiness.status === "ready") {
        setServerStatus("API reachable and storage ready. Connect an authorized pilot account to submit a draft.", "ok");
      } else {
        setServerStatus("API is reachable, but storage is not ready yet. Server submission remains unavailable.", "bad");
      }
    } catch (error) {
      setServerStatus(error.message || "Could not reach the configured API. Check its URL, availability and read-only CORS settings.", "bad");
    }

    refreshControls();
    if (authCallbackError) {
      byId("auth-status").textContent = authCallbackError;
      byId("auth-status").className = "status portal-status status-bad";
    }
  }

  refreshControls();
  initialize();
})();
