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

  window.renderV1 = async function() {
    const container = d3.select("#viz-v1-heatmap");
    container.selectAll("*").remove();
    const settings = window.VIZ_SETTINGS ? window.VIZ_SETTINGS.get("v1_sessions_heatmap") : {};
    const objId = window.VIZ.getCurrentObjId();
    if (!objId) return;

    window.VIZ.setStatus("Loading V1: " + objId.slice(0, 8));
    try {
      const days = settings.days || window.VIZ.getCurrentDays();
      const resp = await fetch(`/visualizations/api/sessions_heatmap/${objId}?days=${days}`);
      const data = await resp.json();
      if (data.error || !data.matrix || !data.matrix.length) {
        container.append("div").text(data.error || "No data");
        return;
      }

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
        Object.entries(sessions).forEach(([name, info]) => {
          const x0 = labelW + info.start * cellW;
          const x1 = labelW + info.end * cellW;
          svg.append("rect")
            .attr("x", x0).attr("y", labelH)
            .attr("width", x1 - x0).attr("height", 7 * cellH)
            .attr("fill", info.color).attr("opacity", 0.1)
            .attr("stroke", info.color).attr("stroke-width", 1).attr("stroke-dasharray", "2,2");
        });
      }

      const g = svg.append("g").attr("transform", `translate(${labelW},${labelH})`);

      g.selectAll(".cell")
        .data(data.matrix.flatMap((row, wd) => row.map((v, h) => ({ wd, h, v }))))
        .enter().append("rect")
        .attr("class", "cell")
        .attr("x", d => d.h * cellW)
        .attr("y", d => d.wd * cellH)
        .attr("width", cellW - 1)
        .attr("height", cellH - 1)
        .attr("fill", d => d.v > 0 ? colorFor(settings.color_scheme, d.v / maxVal) : "#1f2937")
        .attr("opacity", d => d.v > 0 ? 0.9 : 0.3)
        .on("mousemove", function(evt, d) {
          window.VIZ.showTooltip(evt, `
            <div class="tt-row"><span class="tt-label">Day:</span><span class="tt-value">${data.weekday_labels[d.wd]}</span></div>
            <div class="tt-row"><span class="tt-label">Hour UTC:</span><span class="tt-value">${d.h}:00</span></div>
            <div class="tt-row"><span class="tt-label">${data.metric}:</span><span class="tt-value">${(d.v * 100).toFixed(2)}%</span></div>
          `);
        })
        .on("mouseleave", window.VIZ.hideTooltip);

      svg.selectAll(".wd-label")
        .data(data.weekday_labels).enter().append("text")
        .attr("x", labelW - 6).attr("y", (_, i) => labelH + i * cellH + cellH / 2 + 3)
        .attr("text-anchor", "end").attr("font-size", "10").attr("fill", "#374151")
        .text(d => d);

      svg.selectAll(".h-label")
        .data(d3.range(0, 24, 3)).enter().append("text")
        .attr("x", d => labelW + d * cellW + cellW / 2)
        .attr("y", labelH - 4)
        .attr("text-anchor", "middle").attr("font-size", "9").attr("fill", "#6b7280")
        .text(d => d);

      if (settings.show_session_labels) {
        Object.entries(sessions).forEach(([name, info]) => {
          const x0 = labelW + info.start * cellW;
          const x1 = labelW + info.end * cellW;
          svg.append("text")
            .attr("x", (x0 + x1) / 2).attr("y", labelH - 4)
            .attr("text-anchor", "middle").attr("font-size", "8").attr("fill", info.color)
            .attr("font-weight", "600").text(name);
        });
      }

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
        .text((maxVal * 100).toFixed(1) + "%");

      window.VIZ.setStatus("V1 loaded · " + data.symbol + " · " + data.candles_count + " candles");
    } catch (e) {
      console.error(e);
      window.VIZ.setStatus("V1 error: " + e.message);
    }
  };
})();
