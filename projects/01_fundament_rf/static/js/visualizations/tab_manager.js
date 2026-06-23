(function() {
  "use strict";

  const state = {
    activeTab: "v2",
    currentObjId: null,
    currentDays: 30,
    objects: window.VIZ_OBJECTS || [],
  };

  const MODULE_LOADERS = {
    v1: "/static/js/visualizations/d3_v1_sessions_heatmap.js",
    v2: "/static/js/visualizations/d3_v2_liquidation_risk.js",
    v3: "/static/js/visualizations/d3_v3_fibonacci_tool.js",
    v4: "/static/js/visualizations/d3_v4_multi_equity.js",
    v5: "/static/js/visualizations/d3_v5_session_volatility.js",
  };
  const _loaded = { v1: false, v2: false, v3: false, v4: false, v5: false };
  const _loading = {};

  const VIZ = {
    state: state,
    setStatus: function(msg) {
      const el = document.getElementById("viz-status");
      if (el) el.textContent = msg;
    },
    getCurrentObjId: function() {
      const sel = document.getElementById("viz-symbol");
      return sel ? sel.value : null;
    },
    getCurrentDays: function() {
      const sel = document.getElementById("viz-range");
      return sel ? parseInt(sel.value, 10) : 30;
    },
    showTooltip: function(evt, html) {
      let tip = document.getElementById("viz-tooltip");
      if (!tip) {
        tip = document.createElement("div");
        tip.id = "viz-tooltip";
        tip.className = "viz-tooltip";
        document.body.appendChild(tip);
      }
      tip.innerHTML = html;
      tip.style.display = "block";
      tip.style.left = (evt.pageX + 12) + "px";
      tip.style.top  = (evt.pageY - 12) + "px";
    },
    hideTooltip: function() {
      const tip = document.getElementById("viz-tooltip");
      if (tip) tip.style.display = "none";
    },
    clearContainer: function(id) {
      const el = document.getElementById(id);
      if (el) el.innerHTML = "";
    },
  };
  window.VIZ = VIZ;

  function loadModule(name) {
    if (_loaded[name]) return Promise.resolve();
    if (_loading[name]) return _loading[name];
    const url = MODULE_LOADERS[name];
    if (!url) return Promise.reject(new Error("Unknown module: " + name));
    VIZ.setStatus("Loading " + name + "…");
    _loading[name] = new Promise(function(resolve, reject) {
      const s = document.createElement("script");
      s.src = url;
      s.async = false;
      s.onload = function() {
        _loaded[name] = true;
        delete _loading[name];
        resolve();
      };
      s.onerror = function() {
        delete _loading[name];
        reject(new Error("Failed to load " + url));
      };
      document.head.appendChild(s);
    });
    return _loading[name];
  }

  async function activateTab(tabName) {
    state.activeTab = tabName;
    document.querySelectorAll(".viz-tab").forEach(function(btn) {
      btn.classList.toggle("active", btn.dataset.tab === tabName);
    });
    document.querySelectorAll(".viz-tab-pane").forEach(function(pane) {
      pane.classList.toggle("active", pane.dataset.tabContent === tabName);
    });
    VIZ.setStatus("Tab: " + tabName);
    if (tabName === "settings") {
      if (window.VIZ_SETTINGS) window.VIZ_SETTINGS.render();
      return;
    }
    const renderFn = {
      v1: "renderV1",
      v2: "renderV2",
      v3: "renderV3",
      v4: "renderV4",
      v5: "renderV5",
    }[tabName];
    if (!renderFn) return;
    try {
      await loadModule(tabName);
      if (typeof window[renderFn] !== "function") {
        throw new Error(renderFn + " not registered after load");
      }
      await window[renderFn]();
    } catch (e) {
      console.error("[VIZ]", tabName, e);
      VIZ.setStatus("Error in " + tabName + ": " + e.message);
    }
  }

  function waitForD3AndActivate(retries) {
    retries = retries == null ? 60 : retries;
    if (typeof window.d3 !== "undefined") {
      activateTab("v2");
      return;
    }
    if (retries <= 0) {
      VIZ.setStatus("ERROR: d3.js not loaded");
      return;
    }
    setTimeout(function() { waitForD3AndActivate(retries - 1); }, 50);
  }

  document.addEventListener("DOMContentLoaded", function() {
    state.currentObjId = VIZ.getCurrentObjId();
    state.currentDays = VIZ.getCurrentDays();

    document.querySelectorAll(".viz-tab").forEach(function(btn) {
      btn.addEventListener("click", function() { activateTab(this.dataset.tab); });
    });

    document.getElementById("viz-symbol").addEventListener("change", function() {
      state.currentObjId = this.value;
      var lbl = this.options[this.selectedIndex] && this.options[this.selectedIndex].dataset.symbol;
      VIZ.setStatus("Symbol: " + lbl);
      activateTab(state.activeTab);
    });

    document.getElementById("viz-range").addEventListener("change", function() {
      state.currentDays = parseInt(this.value, 10);
      VIZ.setStatus("Range: " + state.currentDays + " days");
      activateTab(state.activeTab);
    });

    waitForD3AndActivate();
  });
})();
