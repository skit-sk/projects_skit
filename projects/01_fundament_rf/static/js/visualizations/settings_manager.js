(function() {
  "use strict";

  const STORAGE_KEY = "viz_settings_v1";
  const DEFAULTS = {
    v1_sessions_heatmap: {
      days: 30, metric: "body_pct", color_scheme: "viridis",
      show_session_borders: true, show_session_labels: true,
    },
    v2_liquidation_risk: {
      show_10x: true, show_5x: true, show_2x: true,
      timeline_range: "30d", color_scheme: "default",
    },
    v3_fibonacci_tool: {
      mode: "retracement", show_level_labels: true, show_price_markers: true,
      level_0: true, level_236: true, level_382: true, level_5: true,
      level_618: true, level_786: true, level_1: true, level_1618: true,
    },
    v4_multi_equity: {
      normalize: true, show_absolute: false, y_scale: "linear",
      color_per_symbol: "auto", show_drawdown_zones: false,
    },
    v5_session_volatility: {
      lookback_days: 90, metric: "body_pct", plot_type: "violin",
      show_outliers: true, show_mean_line: true,
    },
  };

  let settings = JSON.parse(JSON.stringify(DEFAULTS));

  function load() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        Object.keys(DEFAULTS).forEach(k => {
          if (parsed[k]) settings[k] = Object.assign({}, DEFAULTS[k], parsed[k]);
        });
      }
    } catch (e) { console.warn("Settings load failed", e); }
  }

  function save() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(settings)); } catch (e) {}
  }

  function reset() { settings = JSON.parse(JSON.stringify(DEFAULTS)); }

  function get(module) { return settings[module] || DEFAULTS[module]; }

  function buildControlRow(key, def, value) {
    const wrap = document.createElement("div");
    wrap.className = "viz-settings-row";
    const label = document.createElement("label");
    label.textContent = key;
    wrap.appendChild(label);

    if (def.type === "bool") {
      const input = document.createElement("input");
      input.type = "checkbox";
      input.checked = !!value;
      input.dataset.setting = key;
      input.dataset.module = "";
      wrap.appendChild(input);
    } else if (def.type === "int") {
      const input = document.createElement("input");
      input.type = "number";
      input.value = value;
      input.min = 1;
      input.className = "viz-input-sm";
      input.dataset.setting = key;
      wrap.appendChild(input);
    } else if (def.type === "select") {
      const sel = document.createElement("select");
      sel.className = "viz-select";
      sel.dataset.setting = key;
      (def.options || []).forEach(opt => {
        const o = document.createElement("option");
        o.value = String(opt);
        o.textContent = String(opt);
        if (String(opt) === String(value)) o.selected = true;
        sel.appendChild(o);
      });
      wrap.appendChild(sel);
    } else {
      const input = document.createElement("input");
      input.type = "text";
      input.value = value;
      input.className = "viz-input";
      input.dataset.setting = key;
      wrap.appendChild(input);
    }
    return wrap;
  }

  function render() {
    const container = document.getElementById("viz-settings-modules");
    if (!container) return;
    container.innerHTML = "";

    const moduleNames = {
      v1_sessions_heatmap: "V1 · Sessions Heatmap",
      v2_liquidation_risk: "V2 · Liquidation Risk",
      v3_fibonacci_tool:   "V3 · Fibonacci Tool",
      v4_multi_equity:     "V4 · Multi-Equity",
      v5_session_volatility: "V5 · Session Volatility",
    };

    const schema = {
      v1_sessions_heatmap: {
        days: { type: "select", options: [7, 30, 90, 180] },
        metric: { type: "select", options: ["body_pct", "total_range", "volatility", "volume"] },
        color_scheme: { type: "select", options: ["viridis", "plasma", "RdYlGn", "custom"] },
        show_session_borders: { type: "bool" },
        show_session_labels: { type: "bool" },
      },
      v2_liquidation_risk: {
        show_10x: { type: "bool" }, show_5x: { type: "bool" }, show_2x: { type: "bool" },
        timeline_range: { type: "select", options: ["7d", "30d", "90d", "all"] },
        color_scheme: { type: "select", options: ["default", "colorblind", "mono"] },
      },
      v3_fibonacci_tool: {
        mode: { type: "select", options: ["retracement", "extension"] },
        show_level_labels: { type: "bool" },
        show_price_markers: { type: "bool" },
        level_0:   { type: "bool" }, level_236: { type: "bool" },
        level_382: { type: "bool" }, level_5:   { type: "bool" },
        level_618: { type: "bool" }, level_786: { type: "bool" },
        level_1:   { type: "bool" }, level_1618:{ type: "bool" },
      },
      v4_multi_equity: {
        normalize: { type: "bool" }, show_absolute: { type: "bool" },
        y_scale: { type: "select", options: ["linear", "log"] },
        color_per_symbol: { type: "select", options: ["auto", "custom"] },
        show_drawdown_zones: { type: "bool" },
      },
      v5_session_volatility: {
        lookback_days: { type: "int" },
        metric: { type: "select", options: ["body_pct", "total_range", "volatility", "volume"] },
        plot_type: { type: "select", options: ["violin", "box", "both"] },
        show_outliers: { type: "bool" }, show_mean_line: { type: "bool" },
      },
    };

    Object.keys(moduleNames).forEach(mod => {
      const card = document.createElement("div");
      card.className = "viz-settings-module";
      const h = document.createElement("h3");
      h.textContent = moduleNames[mod];
      card.appendChild(h);

      const sch = schema[mod] || {};
      Object.keys(sch).forEach(key => {
        const row = buildControlRow(key, sch[key], settings[mod][key]);
        const input = row.querySelector("[data-setting]");
        if (input) input.dataset.module = mod;
        card.appendChild(row);
      });

      container.appendChild(card);
    });
  }

  function collectFromUI() {
    const container = document.getElementById("viz-settings-modules");
    if (!container) return;
    container.querySelectorAll("[data-setting]").forEach(el => {
      const mod = el.dataset.module;
      const key = el.dataset.setting;
      if (!mod || !key) return;
      if (el.type === "checkbox") settings[mod][key] = el.checked;
      else if (el.type === "number") settings[mod][key] = parseInt(el.value, 10) || 0;
      else settings[mod][key] = el.value;
    });
  }

  function applyAndRerender() {
    collectFromUI();
    save();
    const tab = window.VIZ ? window.VIZ.state.activeTab : "v2";
    if (tab !== "settings" && window.VIZ) {
      const renderFn = {
        v1: "renderV1", v2: "renderV2", v3: "renderV3",
        v4: "renderV4", v5: "renderV5",
      }[tab];
      if (renderFn && window[renderFn]) window[renderFn]();
    }
  }

  load();

  document.addEventListener("DOMContentLoaded", function() {
    const applyBtn = document.getElementById("viz-settings-apply");
    const resetBtn = document.getElementById("viz-settings-reset");
    const saveBtn  = document.getElementById("viz-settings-save");
    if (applyBtn) applyBtn.addEventListener("click", applyAndRerender);
    if (resetBtn) resetBtn.addEventListener("click", function() { reset(); render(); applyAndRerender(); });
    if (saveBtn)  saveBtn.addEventListener("click", function() { collectFromUI(); save(); window.VIZ && window.VIZ.setStatus("Defaults saved"); });
  });

  window.VIZ_SETTINGS = { get, render, applyAndRerender, DEFAULTS };
})();
