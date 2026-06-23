(function() {
  "use strict";

  const SCHEMES = {
    viridis: ["#440154", "#482878", "#3e4a89", "#31688e", "#26828e", "#1f9d8a", "#35b779", "#6cce5a", "#b3de69", "#fde725"],
    plasma:  ["#0d0887", "#41049d", "#6a00a8", "#8f0da4", "#b12a90", "#cc4778", "#e16462", "#f1844b", "#fca636", "#fcce25"],
    RdYlGn:  ["#a50026", "#d73027", "#f46d43", "#fdae61", "#fee08b", "#ffffbf", "#d9ef8b", "#a6d96a", "#66bd63", "#1a9850", "#006837"],
    custom:  ["#1e3a8a", "#3b82f6", "#60a5fa", "#93c5fd", "#dbeafe", "#fef3c7", "#fde68a", "#f59e0b", "#dc2626", "#7f1d1d"],
  };

  function colorFor(scheme, t) {
    const colors = SCHEMES[scheme] || SCHEMES.viridis;
    const idx = Math.max(0, Math.min(colors.length - 1, Math.floor(t * (colors.length - 1))));
    return colors[idx];
  }

  let currentMode = "heatmap";
  let currentData = null;

  function getMetricName(data) {
    if (data.metric_label) return data.metric_label;
    const map = {
      body_pct: "волатильность (body_pct, %)",
      total_range: "диапазон (total_range, %)",
      volatility: "волатильность (position_metrics)",
      volume: "объём (volume)",
    };
    return map[data.metric] || data.metric;
  }

  function renderHeatmap(container, data, settings) {
    container.selectAll("*").remove();
    const cellW = 28, cellH = 22;
    const labelW = 50, labelH = 24;
    const width = labelW + 24 * cellW + 20;
    const height = labelH + 7 * cellH + 60;

    const svg = container.append("svg")
      .attr("width", width).attr("height", height)
      .attr("viewBox", `0 0 ${width} ${height}`);

    const maxVal = data.max_value || 1;
    const sessions = data.sessions_overlay || {};

    if (settings.show_session_borders) {
      Object.entries(sessions).forEach(function(entry) {
        const info = entry[1];
        const x0 = labelW + info.start * cellW;
        const x1 = labelW + info.end * cellW;
        svg.append("rect")
          .attr("x", x0).attr("y", labelH)
          .attr("width", x1 - x0).attr("height", 7 * cellH)
          .attr("fill", info.color).attr("opacity", 0.08)
          .attr("stroke", info.color).attr("stroke-width", 1).attr("stroke-dasharray", "2,2");
      });
    }

    const g = svg.append("g").attr("transform", "translate(" + labelW + "," + labelH + ")");

    g.selectAll(".cell")
      .data(data.matrix.flatMap(function(row, wd) { return row.map(function(v, h) { return { wd: wd, h: h, v: v }; }); }))
      .enter().append("rect")
      .attr("class", "cell")
      .attr("x", function(d) { return d.h * cellW; })
      .attr("y", function(d) { return d.wd * cellH; })
      .attr("width", cellW - 1)
      .attr("height", cellH - 1)
      .attr("fill", function(d) { return d.v > 0 ? colorFor(settings.color_scheme, d.v / maxVal) : "#1f2937"; })
      .attr("opacity", function(d) { return d.v > 0 ? 0.9 : 0.25; })
      .on("mousemove", function(evt, d) {
        const n = (data.counts && data.counts[d.wd] && data.counts[d.wd][d.h]) || 0;
        const valStr = d.v > 0 ? (d.v * 100).toFixed(2) + "%" : "No data";
        const cntStr = n > 0 ? n + " " + (n === 1 ? "свеча" : (n < 5 ? "свечи" : "свечей")) : "0 свечей";
        window.VIZ.showTooltip(evt, `
          <div class="tt-row"><span class="tt-label">День:</span><span class="tt-value">${data.weekday_labels[d.wd]}</span></div>
          <div class="tt-row"><span class="tt-label">Час (UTC${data.timezone_offset >= 0 ? "+" : ""}${data.timezone_offset}):</span><span class="tt-value">${String(d.h).padStart(2, "0")}:00</span></div>
          <div class="tt-row"><span class="tt-label">${data.metric}:</span><span class="tt-value">${valStr}</span></div>
          <div class="tt-row"><span class="tt-label">Свечей в ячейке:</span><span class="tt-value">${cntStr}</span></div>
        `);
      })
      .on("mouseleave", window.VIZ.hideTooltip);

    svg.selectAll(".wd-label")
      .data(data.weekday_labels).enter().append("text")
      .attr("class", "wd-label")
      .attr("x", labelW - 6).attr("y", function(_, i) { return labelH + i * cellH + cellH / 2 + 3; })
      .attr("text-anchor", "end").attr("font-size", "10").attr("fill", "#374151")
      .text(function(d) { return d; });

    svg.selectAll(".h-label")
      .data(d3.range(0, 24, 3)).enter().append("text")
      .attr("class", "h-label")
      .attr("x", function(d) { return labelW + d * cellW + cellW / 2; })
      .attr("y", labelH - 4)
      .attr("text-anchor", "middle").attr("font-size", "9").attr("fill", "#6b7280")
      .text(function(d) { return d; });

    const legendY = labelH + 7 * cellH + 16;
    const legendSteps = 20;
    const legendW = 200;
    for (let i = 0; i < legendSteps; i++) {
      svg.append("rect")
        .attr("x", labelW + (i * legendW / legendSteps))
        .attr("y", legendY)
        .attr("width", legendW / legendSteps)
        .attr("height", 10)
        .attr("fill", colorFor(settings.color_scheme, i / (legendSteps - 1)));
    }
    svg.append("text").attr("x", labelW).attr("y", legendY - 3)
      .attr("font-size", "10").attr("fill", "#6b7280").text("0%");
    svg.append("text").attr("x", labelW + legendW).attr("y", legendY - 3)
      .attr("text-anchor", "end").attr("font-size", "10").attr("fill", "#6b7280")
      .text((maxVal * 100).toFixed(2) + "%");
    svg.append("text").attr("x", labelW).attr("y", legendY + 22)
      .attr("font-size", "10").attr("fill", "#6b7280").text("низкая");
    svg.append("text").attr("x", labelW + legendW).attr("y", legendY + 22)
      .attr("text-anchor", "end").attr("font-size", "10").attr("fill", "#6b7280").text("высокая");
  }

  function renderByDay(container, data) {
    container.selectAll("*").remove();
    const aggregated = data.matrix.map(function(row, wd) {
      const nonZero = row.filter(function(v) { return v > 0; });
      return {
        weekday: wd,
        avg: nonZero.length ? nonZero.reduce(function(a, b) { return a + b; }, 0) / nonZero.length : 0,
        max: nonZero.length ? Math.max.apply(null, nonZero) : 0,
        count: nonZero.length,
      };
    });
    const maxAvg = Math.max.apply(null, aggregated.map(function(d) { return d.avg; }).concat([0.001]));

    const width = 700, height = 280;
    const margin = { top: 20, right: 20, bottom: 40, left: 50 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;
    const svg = container.append("svg").attr("width", width).attr("height", height)
      .attr("viewBox", "0 0 " + width + " " + height);
    const g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");
    const x = d3.scaleBand().domain(aggregated.map(function(d) { return d.weekday; })).range([0, innerW]).padding(0.2);
    const y = d3.scaleLinear().domain([0, maxAvg * 1.1]).range([innerH, 0]).nice();

    g.append("g").attr("transform", "translate(0," + innerH + ")")
      .call(d3.axisBottom(x).tickFormat(function(i) { return data.weekday_labels[i]; }));
    g.append("g").call(d3.axisLeft(y).ticks(6).tickFormat(function(d) { return (d * 100).toFixed(1) + "%"; }));

    g.selectAll(".bar")
      .data(aggregated).enter().append("rect")
      .attr("class", "bar")
      .attr("x", function(d) { return x(d.weekday); })
      .attr("y", function(d) { return y(d.avg); })
      .attr("width", x.bandwidth())
      .attr("height", function(d) { return innerH - y(d.avg); })
      .attr("fill", "#2563eb")
      .attr("opacity", 0.8)
      .on("mousemove", function(evt, d) {
        window.VIZ.showTooltip(evt, `
          <div class="tt-row"><span class="tt-label">День:</span><span class="tt-value">${data.weekday_labels[d.weekday]}</span></div>
          <div class="tt-row"><span class="tt-label">Avg ${data.metric}:</span><span class="tt-value">${(d.avg * 100).toFixed(2)}%</span></div>
          <div class="tt-row"><span class="tt-label">Max:</span><span class="tt-value">${(d.max * 100).toFixed(2)}%</span></div>
          <div class="tt-row"><span class="tt-label">Активных часов:</span><span class="tt-value">${d.count} / 24</span></div>
        `);
      })
      .on("mouseleave", window.VIZ.hideTooltip);

    g.selectAll(".bar-label")
      .data(aggregated).enter().append("text")
      .attr("class", "bar-label")
      .attr("x", function(d) { return x(d.weekday) + x.bandwidth() / 2; })
      .attr("y", function(d) { return y(d.avg) - 4; })
      .attr("text-anchor", "middle").attr("font-size", "10").attr("fill", "#1f2937")
      .text(function(d) { return d.avg > 0 ? (d.avg * 100).toFixed(1) + "%" : "—"; });
  }

  function renderByHour(container, data) {
    container.selectAll("*").remove();
    const aggregated = [];
    for (let h = 0; h < 24; h++) {
      const vals = data.matrix.map(function(row) { return row[h]; }).filter(function(v) { return v > 0; });
      aggregated.push({
        hour: h,
        avg: vals.length ? vals.reduce(function(a, b) { return a + b; }, 0) / vals.length : 0,
        count: vals.length,
      });
    }
    const maxAvg = Math.max.apply(null, aggregated.map(function(d) { return d.avg; }).concat([0.001]));

    const sessions = data.sessions_overlay || {};
    const sessionColors = {
      sydney: "#3b82f6", tokyo: "#ef4444", frankfurt: "#f59e0b",
      london: "#10b981", new_york: "#8b5cf6",
    };
    function colorForHour(h) {
      for (const name in sessions) {
        const s = sessions[name];
        if (h >= s.start && h < s.end) return sessionColors[name] || "#6b7280";
      }
      return "#9ca3af";
    }

    const width = 800, height = 280;
    const margin = { top: 20, right: 20, bottom: 40, left: 50 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;
    const svg = container.append("svg").attr("width", width).attr("height", height)
      .attr("viewBox", "0 0 " + width + " " + height);
    const g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");
    const x = d3.scaleBand().domain(d3.range(24)).range([0, innerW]).padding(0.1);
    const y = d3.scaleLinear().domain([0, maxAvg * 1.1]).range([innerH, 0]).nice();

    g.append("g").attr("transform", "translate(0," + innerH + ")")
      .call(d3.axisBottom(x).tickFormat(function(d) { return String(d).padStart(2, "0"); }));
    g.append("g").call(d3.axisLeft(y).ticks(6).tickFormat(function(d) { return (d * 100).toFixed(1) + "%"; }));

    g.selectAll(".bar")
      .data(aggregated).enter().append("rect")
      .attr("class", "bar")
      .attr("x", function(d) { return x(d.hour); })
      .attr("y", function(d) { return y(d.avg); })
      .attr("width", x.bandwidth())
      .attr("height", function(d) { return innerH - y(d.avg); })
      .attr("fill", function(d) { return colorForHour(d.hour); })
      .attr("opacity", 0.85)
      .on("mousemove", function(evt, d) {
        window.VIZ.showTooltip(evt, `
          <div class="tt-row"><span class="tt-label">Час (UTC${data.timezone_offset >= 0 ? "+" : ""}${data.timezone_offset}):</span><span class="tt-value">${String(d.hour).padStart(2, "0")}:00</span></div>
          <div class="tt-row"><span class="tt-label">Avg ${data.metric}:</span><span class="tt-value">${(d.avg * 100).toFixed(2)}%</span></div>
          <div class="tt-row"><span class="tt-label">Активных дней:</span><span class="tt-value">${d.count} / 7</span></div>
        `);
      })
      .on("mouseleave", window.VIZ.hideTooltip);
  }

  function renderStats(container, data) {
    container.selectAll("*").remove();
    if (!data || !data.summary) return;
    const s = data.summary;
    const wd = data.weekday_labels;
    function fmtCell(x) {
      if (!x) return "—";
      return wd[x.weekday] + " " + String(x.hour).padStart(2, "0") + ":00 (" +
             (x.value * 100).toFixed(2) + "%, n=" + x.count + ")";
    }
    const rows = [
      ["🔥 Max", fmtCell(s.max)],
      ["❄ Min", fmtCell(s.min)],
      ["📊 Avg", (s.avg * 100).toFixed(2) + "%"],
      ["📅 Ячеек с данными", s.total_cells + " / 168"],
    ];
    rows.forEach(function(row) {
      const r = container.append("div").attr("class", "stat-row");
      r.append("span").attr("class", "stat-label").text(row[0]);
      r.append("span").attr("class", "stat-value").text(row[1]);
    });
    if (s.top5 && s.top5.length) {
      const wrap = container.append("div").attr("class", "stat-row");
      wrap.append("span").attr("class", "stat-label").text("🏆 Top 5");
      const val = wrap.append("span").attr("class", "stat-value");
      s.top5.forEach(function(x, i) {
        if (i > 0) val.append("span").text(" · ");
        val.append("span").text(wd[x.weekday] + " " + String(x.hour).padStart(2, "0") + " (" + (x.value * 100).toFixed(1) + "%)");
      });
    }
  }

  window.renderV1 = async function() {
    const container = d3.select("#viz-v1-heatmap");
    const statsContainer = d3.select("#viz-v1-stats");
    const settings = window.VIZ_SETTINGS ? window.VIZ_SETTINGS.get("v1_sessions_heatmap") : {};
    const objId = window.VIZ.getCurrentObjId();
    if (!objId) return;

    const days = settings.days || window.VIZ.getCurrentDays();
    const metric = settings.metric || "body_pct";
    const tzSel = document.getElementById("viz-v1-tz");
    const tz = tzSel ? parseInt(tzSel.value, 10) : 3;

    const metricNameEl = document.getElementById("viz-v1-metric-name");
    const metricMap = {
      body_pct: "волатильность (body_pct, %)",
      total_range: "диапазон (total_range, %)",
      volatility: "волатильность (position_metrics)",
      volume: "объём (volume)",
    };
    if (metricNameEl) metricNameEl.textContent = metricMap[metric] || metric;

    window.VIZ.setStatus("Loading V1: " + objId.slice(0, 8));
    try {
      const resp = await fetch("/visualizations/api/sessions_heatmap/" + objId +
        "?days=" + days + "&metric=" + metric + "&tz=" + tz);
      const data = await resp.json();
      if (data.error || !data.matrix || !data.matrix.length) {
        container.append("div").text(data.error || "No data");
        return;
      }
      currentData = data;
      if (currentMode === "heatmap")      renderHeatmap(container, data, settings);
      else if (currentMode === "by_day")  renderByDay(container, data);
      else if (currentMode === "by_hour") renderByHour(container, data);
      renderStats(statsContainer, data);
      const modeLabel = { heatmap: "Heatmap", by_day: "By Day", by_hour: "By Hour" }[currentMode];
      window.VIZ.setStatus("V1 · " + modeLabel + " · " + data.symbol + " · " +
        data.candles_count + " candles · UTC" + (tz >= 0 ? "+" : "") + tz);
    } catch (e) {
      console.error(e);
      window.VIZ.setStatus("V1 error: " + e.message);
    }
  };

  document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll(".viz-mode-btn").forEach(function(btn) {
      btn.addEventListener("click", function() {
        document.querySelectorAll(".viz-mode-btn").forEach(function(b) { b.classList.remove("active"); });
        btn.classList.add("active");
        currentMode = btn.dataset.mode;
        if (currentData) {
          const container = d3.select("#viz-v1-heatmap");
          const settings = window.VIZ_SETTINGS ? window.VIZ_SETTINGS.get("v1_sessions_heatmap") : {};
          if (currentMode === "heatmap")      renderHeatmap(container, currentData, settings);
          else if (currentMode === "by_day")  renderByDay(container, currentData);
          else if (currentMode === "by_hour") renderByHour(container, currentData);
        } else {
          window.renderV1();
        }
      });
    });
  });
})();
