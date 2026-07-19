// Pulse AI docs — shared chrome:
//   • mobile sidebar toggle
//   • Langflow settings modal (localStorage persistence)
//   • Briefing overlay modal
//   • Credential-aware Streamlit iframe loader (on pages that have #pulse-frame)

(function () {
  var STORAGE_KEY = "pulseai.langflow.settings.v1";

  // ── localStorage helpers ────────────────────────────────────────────────
  function readSettings() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : { url: "", portfolioUrl: "", key: "", streamlitUrl: "" };
    } catch (e) {
      return { url: "", portfolioUrl: "", key: "", streamlitUrl: "" };
    }
  }
  function writeSettings(s) { localStorage.setItem(STORAGE_KEY, JSON.stringify(s)); }
  function clearSettings()  { localStorage.removeItem(STORAGE_KEY); }

  // Exposed for inline scripts
  window.PulseSettings = { read: readSettings, write: writeSettings, clear: clearSettings };

  // ── Streamlit base URL ───────────────────────────────────────────────────
  // Priority: streamlitUrl saved by start.bat → localhost fallback
  function getStreamlitBase() {
    var lf = readSettings();
    if (lf && lf.streamlitUrl) return lf.streamlitUrl;
    return "http://localhost:8501";
  }

  // ── Streamlit URL builder ────────────────────────────────────────────────
  function buildStreamlitUrl(lf) {
    var base = getStreamlitBase();
    var p = [];
    if (lf && lf.url)          p.push("lf_url="      + encodeURIComponent(lf.url));
    if (lf && lf.key)          p.push("lf_key="       + encodeURIComponent(lf.key));
    if (lf && lf.portfolioUrl) p.push("lf_portfolio=" + encodeURIComponent(lf.portfolioUrl));
    return p.length ? base + "?" + p.join("&") : base;
  }

  // ── Iframe loader ────────────────────────────────────────────────────────
  // Runs only on pages that contain a #pulse-frame element (product-briefing.html).
  function showSetupCard(loader) {
    loader.innerHTML = [
      '<div class="loader-setup-card">',
      '  <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#C9A24B"',
      '       stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"',
      '       style="display:block;margin:0 auto 14px;">',
      '    <circle cx="12" cy="12" r="3"/>',
      '    <path d="M19.4 13.5a1.7 1.7 0 0 0 .34 1.87l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.7 1.7 0 0 0-1.87-.34 1.7 1.7 0 0 0-1 1.56V19.6a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.56 1.7 1.7 0 0 0-1.87.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.7 1.7 0 0 0 .34-1.87 1.7 1.7 0 0 0-1.56-1H4.4a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.56-1.1 1.7 1.7 0 0 0-.34-1.87l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.7 1.7 0 0 0 1.87.34H10a1.7 1.7 0 0 0 1-1.56V4.4a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.56 1.7 1.7 0 0 0 1.87-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.7 1.7 0 0 0-.34 1.87V10a1.7 1.7 0 0 0 1.56 1h.1a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.56 1Z"/>',
      '  </svg>',
      '  <h3>Connect Langflow to load the demo</h3>',
      '  <p>Enter your Langflow URLs and API key &mdash; saved in your browser, takes 30 seconds.</p>',
      '  <button class="btn primary" id="loader-connect-btn" type="button"',
      '          style="display:inline-flex;margin:0 auto;">',
      '    Connect Langflow',
      '  </button>',
      '</div>'
    ].join("\n");
    // Bind after innerHTML is set — the button is now in the DOM
    var connectBtn = document.getElementById("loader-connect-btn");
    if (connectBtn) {
      connectBtn.addEventListener("click", function () {
        window.dispatchEvent(new CustomEvent("pulse-open-settings"));
      });
    }
  }

  function loadFrame(frame, loader, src) {
    // FIX: attach the load listener BEFORE setting src so we never miss the event.
    // Also guard against the initial about:blank firing by checking src matches.
    function onLoad() {
      if (frame.src === "about:blank") return; // spurious blank load — ignore
      frame.removeEventListener("load", onLoad);
      frame.classList.add("is-loaded");
      if (loader) loader.classList.add("is-hidden");
    }
    frame.addEventListener("load", onLoad);
    frame.src = src;
  }

  function initIframe() {
    var frame  = document.getElementById("pulse-frame");
    var loader = document.getElementById("iframe-loader");
    if (!frame) return; // not on a page with an iframe — skip

    var lf    = readSettings();
    var hasLf = lf && (lf.url || lf.key || lf.portfolioUrl);

    if (!hasLf) {
      showSetupCard(loader);
      return;
    }

    loadFrame(frame, loader, buildStreamlitUrl(lf));
  }

  // ── Reload iframe with fresh credentials after Save ─────────────────────
  function reloadIframe() {
    var frame = document.getElementById("pulse-frame");
    if (!frame) return;
    var loader = document.getElementById("iframe-loader");
    if (loader) {
      loader.classList.remove("is-hidden");
      loader.innerHTML = [
        '<div class="dot-pulse-row">',
        '  <div class="dot-pulse"></div>',
        '  <div class="dot-pulse"></div>',
        '  <div class="dot-pulse"></div>',
        '</div>',
        '<p class="step-label" id="loader-label">Reloading with new settings\u2026</p>',
        '<p class="loader-hint" id="loader-hint"></p>'
      ].join("\n");
    }
    frame.classList.remove("is-loaded");
    loadFrame(frame, loader, buildStreamlitUrl(readSettings()));
  }

  document.addEventListener("DOMContentLoaded", function () {

    // ── Mobile sidebar toggle ──────────────────────────────────────────────
    var toggleBtns = document.querySelectorAll("[data-sidebar-toggle]");
    var sidebar    = document.querySelector(".sidebar");
    toggleBtns.forEach(function (btn) {
      btn.addEventListener("click", function () {
        if (sidebar) sidebar.classList.toggle("is-open");
      });
    });
    document.addEventListener("click", function (e) {
      if (!sidebar || !sidebar.classList.contains("is-open")) return;
      if (sidebar.contains(e.target) || e.target.closest("[data-sidebar-toggle]")) return;
      sidebar.classList.remove("is-open");
    });

    // ── Briefing overlay modal ────────────────────────────────────────────
    var briefingOverlay = document.getElementById("briefing-overlay");
    if (briefingOverlay) {
      function openBriefing()  { briefingOverlay.classList.add("is-open"); document.body.style.overflow = "hidden"; }
      function closeBriefing() { briefingOverlay.classList.remove("is-open"); document.body.style.overflow = ""; }

      document.querySelectorAll("[data-briefing-open]").forEach(function (b) {
        b.addEventListener("click", openBriefing);
      });
      document.querySelectorAll("[data-briefing-close]").forEach(function (b) {
        b.addEventListener("click", closeBriefing);
      });
      briefingOverlay.addEventListener("click", function (e) {
        if (e.target === briefingOverlay) closeBriefing();
      });
      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && briefingOverlay.classList.contains("is-open")) closeBriefing();
      });
    }

    // ── Langflow settings modal ───────────────────────────────────────────
    var settingsOverlay = document.getElementById("settings-overlay");
    if (!settingsOverlay) return;

    var openBtns      = document.querySelectorAll("[data-settings-open]");
    var closeBtns     = settingsOverlay.querySelectorAll("[data-settings-close]");
    var urlField       = document.getElementById("set-lf-url");
    var portfolioField = document.getElementById("set-lf-portfolio-url");
    var keyField       = document.getElementById("set-lf-key");
    var stField        = document.getElementById("set-st-url");
    var statusEl      = document.getElementById("settings-modal-status");
    var saveBtn       = document.getElementById("settings-save");
    var clearBtn      = document.getElementById("settings-clear");

    function populate() {
      var s = readSettings();
      if (urlField)       urlField.value       = s.url          || "";
      if (portfolioField) portfolioField.value = s.portfolioUrl || "";
      if (keyField)       keyField.value       = s.key          || "";
      if (stField)        stField.value        = s.streamlitUrl || "";
      if (statusEl) {
        statusEl.textContent = (s.url || s.portfolioUrl || s.key)
          ? "Connected to your Langflow instance."
          : "Not connected — the demo will show the app shell only.";
        statusEl.classList.toggle("ok", !!(s.url || s.portfolioUrl || s.key));
      }
    }

    function openSettings()  { populate(); settingsOverlay.classList.add("is-open"); }
    function closeSettings() { settingsOverlay.classList.remove("is-open"); }

    openBtns.forEach(function  (b) { b.addEventListener("click", openSettings);  });
    closeBtns.forEach(function (b) { b.addEventListener("click", closeSettings); });
    settingsOverlay.addEventListener("click", function (e) {
      if (e.target === settingsOverlay) closeSettings();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && settingsOverlay.classList.contains("is-open")) closeSettings();
    });

    // Listen for the event fired by dynamically-injected open buttons
    window.addEventListener("pulse-open-settings", openSettings);

    if (saveBtn) {
      saveBtn.addEventListener("click", function () {
        writeSettings({
          url:          (urlField       && urlField.value.trim())       || "",
          portfolioUrl: (portfolioField && portfolioField.value.trim()) || "",
          key:          (keyField       && keyField.value.trim())       || "",
          streamlitUrl: (stField        && stField.value.trim())        || "",
        });
        if (statusEl) {
          statusEl.textContent = "Saved.";
          statusEl.classList.add("ok");
        }
        closeSettings();
        reloadIframe();
        window.dispatchEvent(new CustomEvent("pulse-settings-saved"));
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener("click", function () {
        clearSettings();
        if (urlField)       urlField.value       = "";
        if (portfolioField) portfolioField.value = "";
        if (keyField)       keyField.value       = "";
        if (stField)        stField.value        = "";
        if (statusEl) {
          statusEl.textContent = "Cleared.";
          statusEl.classList.remove("ok");
        }
        window.dispatchEvent(new CustomEvent("pulse-settings-saved"));
      });
    }

    // ── Boot the iframe (no-op on pages without one) ──────────────────────
    initIframe();
  });
})();
