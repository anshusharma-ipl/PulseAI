// Pulse AI docs — shared chrome: mobile sidebar toggle + Settings modal.
// Settings are stored in localStorage so they persist across visits and
// across every page, and are read by app/stlite-runtime.html when it launches.

(function () {
  const STORAGE_KEY = "pulseai.langflow.settings.v1";

  function readSettings() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : { url: "", portfolioUrl: "", key: "" };
    } catch (e) {
      return { url: "", portfolioUrl: "", key: "" };
    }
  }

  function writeSettings(settings) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  }

  function clearSettings() {
    localStorage.removeItem(STORAGE_KEY);
  }

  // Exposed for app/stlite-runtime.html (via localStorage) and the settings modal
  window.PulseSettings = { read: readSettings, write: writeSettings, clear: clearSettings };

  document.addEventListener("DOMContentLoaded", function () {
    // ---- mobile sidebar toggle ----
    const toggleBtns = document.querySelectorAll("[data-sidebar-toggle]");
    const sidebar = document.querySelector(".sidebar");
    toggleBtns.forEach((btn) => {
      btn.addEventListener("click", () => sidebar && sidebar.classList.toggle("is-open"));
    });
    document.addEventListener("click", (e) => {
      if (!sidebar || !sidebar.classList.contains("is-open")) return;
      if (sidebar.contains(e.target) || e.target.closest("[data-sidebar-toggle]")) return;
      sidebar.classList.remove("is-open");
    });

    // ---- settings modal ----
    const overlay = document.getElementById("settings-overlay");
    if (!overlay) return;
    const openBtns = document.querySelectorAll("[data-settings-open]");
    const closeBtns = overlay.querySelectorAll("[data-settings-close]");
    const urlField = document.getElementById("set-lf-url");
    const portfolioField = document.getElementById("set-lf-portfolio-url");
    const keyField = document.getElementById("set-lf-key");
    const statusEl = document.getElementById("settings-modal-status");
    const saveBtn = document.getElementById("settings-save");
    const clearBtn = document.getElementById("settings-clear");

    function populate() {
      const s = readSettings();
      if (urlField) urlField.value = s.url || "";
      if (portfolioField) portfolioField.value = s.portfolioUrl || "";
      if (keyField) keyField.value = s.key || "";
      if (statusEl) {
        statusEl.textContent = s.url || s.portfolioUrl || s.key
          ? "Connected to your Langflow instance."
          : "Not connected — the demo will show the app shell only.";
        statusEl.classList.toggle("ok", !!(s.url || s.portfolioUrl || s.key));
      }
    }

    function open() {
      populate();
      overlay.classList.add("is-open");
    }
    function close() {
      overlay.classList.remove("is-open");
    }

    openBtns.forEach((b) => b.addEventListener("click", open));
    closeBtns.forEach((b) => b.addEventListener("click", close));
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) close();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") close();
    });

    if (saveBtn) {
      saveBtn.addEventListener("click", () => {
        writeSettings({
          url: (urlField && urlField.value.trim()) || "",
          portfolioUrl: (portfolioField && portfolioField.value.trim()) || "",
          key: (keyField && keyField.value.trim()) || "",
        });
        if (statusEl) {
          statusEl.textContent = "Saved. This applies next time the demo loads.";
          statusEl.classList.add("ok");
        }
        window.dispatchEvent(new CustomEvent("pulse-settings-saved"));
      });
    }
    if (clearBtn) {
      clearBtn.addEventListener("click", () => {
        clearSettings();
        if (urlField) urlField.value = "";
        if (portfolioField) portfolioField.value = "";
        if (keyField) keyField.value = "";
        if (statusEl) {
          statusEl.textContent = "Cleared — reset to the default (unconfigured) state.";
          statusEl.classList.remove("ok");
        }
        window.dispatchEvent(new CustomEvent("pulse-settings-saved"));
      });
    }
  });
})();
