(function() {
  "use strict";

  function dateInputs() {
    const from = document.getElementById("viz-v3-from");
    const to = document.getElementById("viz-v3-to");
    return { from: from.value || null, to: to.value || null };
  }

  window.renderV3 = async function() {
    const container = d3.select("#viz-v3-chart");
    container.selectAll("*").remove();
    const settings = window.VIZ_SETTINGS ? window.VIZ_SETTINGS.get("v3_fibonacci_tool") : {};
    const objId = window.VIZ.getCurrentObjId();
    if (!objId) return;

    const { from, to } = dateInputs();
    const mode = settings.mode || "retracement";

    window.VIZ.setStatus("Loading V3: " + objId.slice(0, 8));
    try {
      const params = new URLSearchParams();
      if (from) params.append("from", from);
      if (to)   params.append("to", to);
      params.append("mode", mode);
      const resp = await fetch(`/visualizations/api/fibonacci_tool/${objId}?${params}`);
      const data = await resp.json();
      if (data.error) { container.append("div").text(data.error); return; }

      const candles = data.candles || [];
      if (!candles.length) { container.append("div").text("No candles in range"); return; }

      const width = 800, height = 400;
      const margin = { top: 20, right: 80, bottom: 40, left: 60 };
      const innerW = width - margin.left - margin.right;
      const innerH = height - margin.top - margin.bottom;

      const svg = container.append("svg")
        .attr("width", width).attr("height", height)
        .attr("viewBox", `0 0 ${width} ${height}`);
      const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

      const allPrices = candles.flatMap(c => [c.high, c.low]);
      const fibPrices = data.levels.map(l => l.price);
      const yDomain = [d3.min([...allPrices, ...fibPrices]), d3.max([...allPrices, ...fibPrices])];

      const x = d3.scaleBand().domain(candles.map(c => c.date)).range([0, innerW]).padding(0.2);
      const y = d3.scaleLinear().domain(yDomain).range([innerH, 0]).nice();

      g.append("g").attr("transform", `translate(0,${innerH})`)
        .call(d3.axisBottom(x).tickValues(x.domain().filter((_, i) => i % Math.ceil(candles.length / 10) === 0)))
        .selectAll("text").attr("font-size", "9").attr("transform", "rotate(-45)").attr("text-anchor", "end");
      g.append("g").call(d3.axisLeft(y).ticks(8));

      const levelKey = (lv) => "level_" + String(Math.round(lv * 1000));
      const levelVisible = (lv) => {
        if (lv === 0)   return settings.level_0;
        if (lv === 0.236) return settings.level_236;
        if (lv === 0.382) return settings.level_382;
        if (lv === 0.5)   return settings.level_5;
        if (lv === 0.618) return settings.level_618;
        if (lv === 0.786) return settings.level_786;
        if (lv === 1)     return settings.level_1;
        if (lv === 1.618) return settings.level_1618;
        return true;
      };

      data.levels.forEach((lev, i) => {
        if (!levelVisible(lev.level)) return;
        const yPos = y(lev.price);
        const color = d3.interpolateRainbow(i / data.levels.length);
        g.append("line")
          .attr("x1", 0).attr("x2", innerW)
          .attr("y1", yPos).attr("y2", yPos)
          .attr("stroke", color).attr("stroke-width", 1.5).attr("stroke-dasharray", "4,3")
          .attr("opacity", 0.7);
        if (settings.show_level_labels) {
          g.append("text")
            .attr("x", innerW + 4).attr("y", yPos + 3)
            .attr("font-size", "10").attr("fill", color).attr("font-weight", "600")
            .text(lev.level.toFixed(3));
        }
        if (settings.show_price_markers) {
          g.append("text")
            .attr("x", 4).attr("y", yPos - 3)
            .attr("font-size", "9").attr("fill", color)
            .text(lev.price.toFixed(4));
        }
      });

      candles.forEach(c => {
        const cx = x(c.date) + x.bandwidth() / 2;
        const isGreen = c.close >= c.open;
        const color = isGreen ? "#10b981" : "#ef4444";
        g.append("line")
          .attr("x1", cx).attr("x2", cx)
          .attr("y1", y(c.high)).attr("y2", y(c.low))
          .attr("stroke", color).attr("stroke-width", 1);
        const bodyTop = y(Math.max(c.open, c.close));
        const bodyBot = y(Math.min(c.open, c.close));
        g.append("rect")
          .attr("x", cx - x.bandwidth() / 3)
          .attr("y", bodyTop)
          .attr("width", x.bandwidth() * 0.66)
          .attr("height", Math.max(1, bodyBot - bodyTop))
          .attr("fill", color);
      });

      g.on("mousemove", function(evt) {
        const [mx, my] = d3.pointer(evt);
        const price = y.invert(my);
        const matched = data.levels
          .map(l => ({ l, dist: Math.abs(y(l.price) - my) }))
          .sort((a, b) => a.dist - b.dist)[0];
        if (matched && matched.dist < 8 && levelVisible(matched.l.level)) {
          window.VIZ.showTooltip(evt, `
            <div class="tt-row"><span class="tt-label">Level:</span><span class="tt-value">${matched.l.level.toFixed(3)}</span></div>
            <div class="tt-row"><span class="tt-label">Price:</span><span class="tt-value">${matched.l.price.toFixed(4)}</span></div>
          `);
        } else {
          window.VIZ.hideTooltip();
        }
      }).on("mouseleave", window.VIZ.hideTooltip);

      const levelsList = d3.select("#viz-v3-levels");
      levelsList.selectAll("*").remove();
      data.levels.forEach((lev, i) => {
        if (!levelVisible(lev.level)) return;
        const pill = levelsList.append("span")
          .attr("class", "viz-level-pill")
          .style("border-left", `3px solid ${d3.interpolateRainbow(i / data.levels.length)}`);
        pill.append("strong").text(lev.level.toFixed(3) + " ");
        pill.append("span").text(lev.price.toFixed(4));
      });

      window.VIZ.setStatus("V3 loaded · " + data.symbol + " · " + candles.length + " candles · " + data.levels.length + " levels");
    } catch (e) {
      console.error(e);
      window.VIZ.setStatus("V3 error: " + e.message);
    }
  };

  document.addEventListener("DOMContentLoaded", function() {
    const btn = document.getElementById("viz-v3-apply");
    if (btn) btn.addEventListener("click", function() { window.renderV3 && window.renderV3(); });
  });
})();
