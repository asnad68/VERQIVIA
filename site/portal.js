(() => {
  "use strict";

  const byId = (id) => document.getElementById(id);

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

  function renderDraft(draft) {
    byId("portal-preview").textContent = JSON.stringify(draft, null, 2);
  }

  byId("portal-form").addEventListener("submit", (event) => {
    event.preventDefault();
    try {
      const draft = buildDraft();
      renderDraft(draft);
      setStatus("Pilot draft created locally. Nothing was sent to a server.", true);
    } catch (error) {
      setStatus(error.message || "The draft could not be created.", false);
    }
  });

  byId("clear-draft").addEventListener("click", () => {
    byId("portal-form").reset();
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
})();