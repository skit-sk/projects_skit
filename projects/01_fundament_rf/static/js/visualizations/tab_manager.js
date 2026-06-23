(function() {
  "use strict";

  const state = {
    activeTab: "v2",
    currentObjId: null,
    currentDays: 30,
    objects: window.VIZ_OBJECTS || [],
  };

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

  function activateTab(tabName) {
    state.activeTab = tabName;
    document.querySelectorAll(".viz-tab").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.tab === tabName);
    });
    document.querySelectorAll(".viz-tab-pane").forEach(pane => {
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
    if (renderFn && window[renderFn]) {
      try { window[renderFn](); } catch (e) { console.error(e); VIZ.setStatus("Error: " + e.message); }
    }
  }

  document.addEventListener("DOMContentLoaded", function() {
    state.currentObjId = VIZ.getCurrentObjId();
    state.currentDays = VIZ.getCurrentDays();

    document.querySelectorAll(".viz-tab").forEach(btn => {
      btn.addEventListener("click", function() { activateTab(this.dataset.tab); });
    });

    document.getElementById("viz-symbol").addEventListener("change", function() {
      state.currentObjId = this.value;
      VIZ.setStatus("Symbol: " + this.options[this.selectedIndex].dataset.symbol);
      activateTab(state.activeTab);
    });

    document.getElementById("viz-range").addEventListener("change", function() {
      state.currentDays = parseInt(this.value, 10);
      VIZ.setStatus("Range: " + state.currentDays + " days");
      activateTab(state.activeTab);
    });

    activateTab("v2");
  });
})();
