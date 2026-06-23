(function() {
  "use strict";

  const PALETTE = ["#2563eb", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16"];

  function renderLegend(containerId, series) {
    const container = d3.select("#" + containerId);
    container.selectAll("*").remove();
    series.forEach((s, i) => {
      const item = container.append("div").attr("class", "viz-legend-item");
      item.append("div").attr("class", "viz-legend-color").style("background", s.color);
      item.append("span").text(s.symbol + (s.total_pnl !== undefined ? " (P&L: " + s.total_pnl.toFixed(2) + ")" : ""));
    });
  }

  window.renderV4 = async function() {
    const container = d3.select("#viz-v4-chart");
    container.selectAll("*").remove();
    const settings = window.VIZ_SETTINGS ? window.VIZ_SETTINGS.get("v4_multi_equity") : {};

    const symbolsInput = document.getElementById("viz-v4-symbols");
    const symbols = symbolsInput.value.split(",").map(s => s.trim()).filter(Boolean);
    if (!symbols.length) return;

    window.VIZ.setStatus("Loading V4: " + symbols.join(", "));
    try {
      const resp = await fetch(`/visualizations/api/multi_equity?symbols=${encodeURIComponent(symbols.join(","))}&normalize=${settings.normalize}`);
      const data = await resp.json();
      if (data.error) { container.append("div").text(data.error); return; }

      const series = data.series.map((s, i) => Object.assign({}, s, { color: PALETTE[i % PALETTE.length] }));
      renderLegend("viz-v4-legend", series);

      const width = 800, height = 360;
      const margin = { top: 20, right: 100, bottom: 30, left: 60 };
      const innerW = width - margin.left - margin.right;
      const innerH = height - margin.top - margin.bottom;

      const svg = container.append("svg")
        .attr("width", width).attr("height", height)
        .attr("viewBox", `0 0 ${width} ${height}`);
      const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

      const allPoints = series.flatMap(s => s.points || []);
      if (!allPoints.length) {
        container.append("div").text("No data points");
        return;
      }

      const yMin = d3.min(allPoints, d => d.pnl_usdt);
      const yMax = d3.max(allPoints, d => d.pnl_usdt);
      const x = d3.scalePoint().domain(data.dates).range([0, innerW]);
      const y = settings.y_scale === "log"
        ? d3.scaleLog().domain([Math.max(0.01, Math.abs(yMin) || 1), Math.max(1, Math.abs(yMax) || 10)]).range([innerH, 0])
        : d3.scaleLinear().domain([yMin, yMax]).range([innerH, 0]).nice();

      g.append("g").attr("transform", `translate(0,${innerH})`)
        .call(d3.axisBottom(x).tickValues(x.domain().filter((_, i) => i % Math.ceil(data.dates.length / 10) === 0)));
      g.append("g").call(d3.axisLeft(y).ticks(6));

      if (settings.normalize) {
        g.append("line").attr("x1", 0).attr("x2", innerW)
          .attr("y1", y(0)).attr("y2", y(0))
          .attr("stroke", "#9ca3af").attr("stroke-dasharray", "4,4");
      }

      const line = d3.line()
        .x(d => x(d.date))
        .y(d => y(d.pnl_usdt))
        .defined(d => d.pnl_usdt !== null && d.pnl_usdt !== undefined)
        .curve(d3.curveMonotoneX);

      series.forEach(s => {
        if (!s.points || !s.points.length) return;
        g.append("path")
          .datum(s.points)
          .attr("fill", "none")
          .attr("stroke", s.color)
          .attr("stroke-width", 2)
          .attr("d", line);

        g.selectAll(`.dot-${s.symbol}`)
          .data(s.points).enter().append("circle")
          .attr("class", `dot-${s.symbol}`)
          .attr("cx", d => x(d.date))
          .attr("cy", d => y(d.pnl_usdt))
          .attr("r", 2.5)
          .attr("fill", s.color)
          .on("mousemove", function(evt, d) {
            window.VIZ.showTooltip(evt, `
              <div class="tt-row"><span class="tt-label">Symbol:</span><span class="tt-value">${s.symbol}</span></div>
              <div class="tt-row"><span class="tt-label">Date:</span><span class="tt-value">${d.date}</span></div>
              <div class="tt-row"><span class="tt-label">P&L:</span><span class="tt-value">${d.pnl_usdt.toFixed(2)}</span></div>
            `);
          })
          .on("mouseleave", window.VIZ.hideTooltip);

        g.append("text")
          .attr("x", innerW + 6)
          .attr("y", y(s.points[s.points.length - 1].pnl_usdt))
          .attr("font-size", "11").attr("fill", s.color).attr("font-weight", "600")
          .text(s.symbol);
      });

      window.VIZ.setStatus("V4 loaded · " + series.length + " symbols");
    } catch (e) {
      console.error(e);
      window.VIZ.setStatus("V4 error: " + e.message);
    }
  };
})();
