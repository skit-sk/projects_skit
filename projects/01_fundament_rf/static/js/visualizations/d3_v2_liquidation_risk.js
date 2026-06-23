(function() {
  "use strict";

  function renderGauge(containerId, data, settings) {
    const container = d3.select("#" + containerId);
    container.selectAll("*").remove();
    if (!data || data.error || !data.current) {
      container.append("div").attr("class", "viz-empty").text(data && data.error ? data.error : "No data");
      return;
    }

    const width = 320, height = 200;
    const svg = container.append("svg")
      .attr("width", width).attr("height", height)
      .attr("viewBox", `0 0 ${width} ${height}`);

    const cx = width / 2, cy = height * 0.85;
    const radius = 120;
    const startAngle = -Math.PI / 2;
    const endAngle   =  Math.PI / 2;

    const defs = svg.append("defs");
    const gradient = defs.append("linearGradient")
      .attr("id", "riskGradient").attr("x1", "0%").attr("x2", "100%");
    gradient.append("stop").attr("offset", "0%").attr("stop-color", "#10b981");
    gradient.append("stop").attr("offset", "33%").attr("stop-color", "#f59e0b");
    gradient.append("stop").attr("offset", "66%").attr("stop-color", "#f97316");
    gradient.append("stop").attr("offset", "100%").attr("stop-color", "#ef4444");

    const arc = d3.arc().innerRadius(radius - 30).outerRadius(radius);
    svg.append("path")
      .attr("d", arc({startAngle: startAngle, endAngle: endAngle}))
      .attr("transform", `translate(${cx}, ${cy})`)
      .attr("fill", "url(#riskGradient)")
      .attr("opacity", 0.3);

    const dists = data.current.distance_pct;
    const minDist = Math.min(dists["10x"], dists["5x"], dists["2x"]);
    const maxScale = 50;
    const ratio = Math.max(0, Math.min(1, minDist / maxScale));
    const valueAngle = startAngle + ratio * (endAngle - startAngle);

    const colorScheme = (settings && settings.color_scheme) || "default";
    const riskColor = (function() {
      if (minDist < 5) return "#ef4444";
      if (minDist < 10) return "#f97316";
      if (minDist < 20) return "#f59e0b";
      return "#10b981";
    })();

    svg.append("path")
      .attr("d", arc({startAngle: startAngle, endAngle: valueAngle}))
      .attr("transform", `translate(${cx}, ${cy})`)
      .attr("fill", riskColor);

    const needleAngle = valueAngle;
    const needleLen = radius - 10;
    const nx = cx + needleLen * Math.cos(needleAngle);
    const ny = cy + needleLen * Math.sin(needleAngle);
    svg.append("line")
      .attr("x1", cx).attr("y1", cy)
      .attr("x2", nx).attr("y2", ny)
      .attr("stroke", "#1f2937").attr("stroke-width", 3).attr("stroke-linecap", "round");
    svg.append("circle")
      .attr("cx", cx).attr("cy", cy).attr("r", 6)
      .attr("fill", "#1f2937");

    svg.append("text")
      .attr("x", cx).attr("y", cy - 40)
      .attr("text-anchor", "middle")
      .attr("font-size", "32").attr("font-weight", "700")
      .attr("fill", riskColor)
      .text(minDist.toFixed(1) + "%");
    svg.append("text")
      .attr("x", cx).attr("y", cy - 20)
      .attr("text-anchor", "middle")
      .attr("font-size", "11").attr("fill", "#6b7280")
      .text("closest distance");

    svg.append("text")
      .attr("x", 20).attr("y", cy + 4).attr("font-size", "10").attr("fill", "#6b7280").text("0%");
    svg.append("text")
      .attr("x", width - 40).attr("y", cy + 4).attr("font-size", "10").attr("fill", "#6b7280").text("50%+");

    ["10x", "5x", "2x"].forEach((lev, i) => {
      if (lev === "10x" && !settings.show_10x) return;
      if (lev === "5x"  && !settings.show_5x)  return;
      if (lev === "2x"  && !settings.show_2x)  return;
      const pct = dists[lev];
      const groupY = 30 + i * 22;
      svg.append("rect").attr("x", 10).attr("y", groupY).attr("width", 10).attr("height", 10)
        .attr("fill", riskColor).attr("opacity", 0.5 + i * 0.15);
      svg.append("text").attr("x", 26).attr("y", groupY + 9)
        .attr("font-size", "12").attr("fill", "#1f2937")
        .text(`Liq ${lev}: ${pct.toFixed(2)}% away`);
    });
  }

  function renderTimeline(containerId, data, settings) {
    const container = d3.select("#" + containerId);
    container.selectAll("*").remove();
    if (!data || data.error || !data.timeline) {
      container.append("div").attr("class", "viz-empty").text(data && data.error ? data.error : "No data");
      return;
    }

    const tl = data.timeline;
    const rangeMap = { "7d": 7, "30d": 30, "90d": 90, "all": tl.length };
    const rangeDays = rangeMap[settings.timeline_range] || 30;
    const filtered = tl.slice(-rangeDays);

    const width = 560, height = 200;
    const margin = { top: 10, right: 10, bottom: 30, left: 40 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;

    const svg = container.append("svg").attr("width", width).attr("height", height)
      .attr("viewBox", `0 0 ${width} ${height}`);
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    const x = d3.scaleBand()
      .domain(filtered.map(d => d.date))
      .range([0, innerW])
      .padding(0.1);
    const y = d3.scaleLinear()
      .domain([0, d3.max(filtered, d => Math.max(d.closest_distance_pct, 30)) || 30])
      .range([innerH, 0]);

    g.append("g").attr("transform", `translate(0,${innerH})`)
      .call(d3.axisBottom(x).tickValues(x.domain().filter((_, i) => i % Math.ceil(filtered.length / 8) === 0)))
      .selectAll("text").attr("font-size", "9").attr("transform", "rotate(-45)").attr("text-anchor", "end");

    g.append("g").call(d3.axisLeft(y).ticks(5)).selectAll("text").attr("font-size", "10");

    g.selectAll(".bar")
      .data(filtered).enter().append("rect")
      .attr("x", d => x(d.date))
      .attr("y", d => y(d.closest_distance_pct))
      .attr("width", x.bandwidth())
      .attr("height", d => innerH - y(d.closest_distance_pct))
      .attr("fill", d => {
        if (d.triggered) return "#dc2626";
        if (d.closest_distance_pct < 5) return "#ef4444";
        if (d.closest_distance_pct < 10) return "#f97316";
        if (d.closest_distance_pct < 20) return "#f59e0b";
        return "#10b981";
      })
      .on("mousemove", function(evt, d) {
        window.VIZ.showTooltip(evt, `
          <div class="tt-row"><span class="tt-label">Date:</span><span class="tt-value">${d.date}</span></div>
          <div class="tt-row"><span class="tt-label">Close:</span><span class="tt-value">${d.close.toFixed(4)}</span></div>
          <div class="tt-row"><span class="tt-label">Closest:</span><span class="tt-value">${d.closest_level} (${d.closest_distance_pct.toFixed(2)}%)</span></div>
          <div class="tt-row"><span class="tt-label">At risk:</span><span class="tt-value">${d.at_risk ? "YES" : "no"}</span></div>
          <div class="tt-row"><span class="tt-label">Triggered:</span><span class="tt-value">${d.triggered ? "YES" : "no"}</span></div>
        `);
      })
      .on("mouseleave", window.VIZ.hideTooltip);

    [5, 10, 20].forEach(threshold => {
      g.append("line")
        .attr("x1", 0).attr("x2", innerW)
        .attr("y1", y(threshold)).attr("y2", y(threshold))
        .attr("stroke", "#dc2626").attr("stroke-dasharray", "3,3").attr("opacity", 0.4);
      g.append("text")
        .attr("x", innerW - 4).attr("y", y(threshold) - 3)
        .attr("text-anchor", "end").attr("font-size", "9").attr("fill", "#dc2626")
        .text(threshold + "%");
    });
  }

  function renderStats(containerId, data) {
    const container = d3.select("#" + containerId);
    container.selectAll("*").remove();
    if (!data || data.error || !data.stats) return;

    const stats = data.stats;
    const cur = data.current;
    const rows = [
      ["Current price", cur.price.toFixed(4)],
      ["Risk level", cur.risk_level.toUpperCase()],
      ["Days at risk (10x)", stats.days_at_risk_10x],
      ["Days at risk (5x)",  stats.days_at_risk_5x],
      ["Days at risk (2x)",  stats.days_at_risk_2x],
      ["Triggered events",  stats.triggered_count],
      ["Max drawdown",       stats.max_drawdown_pct + "%"],
    ];
    rows.forEach(([label, value]) => {
      const row = container.append("div").attr("class", "stat-row");
      row.append("span").attr("class", "stat-label").text(label);
      row.append("span").attr("class", "stat-value").text(value);
    });
  }

  window.renderV2 = async function() {
    const objId = window.VIZ.getCurrentObjId();
    if (!objId) return;
    window.VIZ.setStatus("Loading V2: " + objId.slice(0, 8));
    try {
      const resp = await fetch(`/visualizations/api/liquidation_risk/${objId}`);
      const data = await resp.json();
      const settings = window.VIZ_SETTINGS ? window.VIZ_SETTINGS.get("v2_liquidation_risk") : {};
      renderGauge("viz-v2-gauge", data, settings);
      renderTimeline("viz-v2-timeline", data, settings);
      renderStats("viz-v2-stats", data);
      window.VIZ.setStatus("V2 loaded · " + (data.symbol || ""));
    } catch (e) {
      console.error(e);
      window.VIZ.setStatus("V2 error: " + e.message);
    }
  };
})();
