(function() {
  "use strict";

  function kernelDensityEstimator(kernel, X) {
    return function(V) {
      return X.map(function(x) {
        return [x, d3.mean(V, function(v) { return kernel(x - v); }) || 0];
      });
    };
  }

  function kernelEpanechnikov(k) {
    return function(v) {
      return Math.abs((v /= k)) <= 1 ? (0.75 * (1 - v * v)) / k : 0;
    };
  }

  function kde(values, min, max) {
    if (values.length < 2) return [];
    const n = values.length;
    const std = d3.deviation(values) || 1;
    const bandwidth = 1.06 * std * Math.pow(n, -1/5);
    const xs = d3.range(min, max, (max - min) / 50);
    return kernelDensityEstimator(kernelEpanechnikov(bandwidth), xs)(values);
  }

  window.renderV5 = async function() {
    const container = d3.select("#viz-v5-chart");
    container.selectAll("*").remove();
    const settings = window.VIZ_SETTINGS ? window.VIZ_SETTINGS.get("v5_session_volatility") : {};
    const objId = window.VIZ.getCurrentObjId();
    if (!objId) return;

    const lookback = parseInt(document.getElementById("viz-v5-lookback").value, 10) || 90;
    const metric = settings.metric || "body_pct";

    window.VIZ.setStatus("Loading V5: " + objId.slice(0, 8));
    try {
      const resp = await fetch(`/visualizations/api/session_volatility/${objId}?lookback_days=${lookback}&metric=${metric}`);
      const data = await resp.json();
      if (data.error || !data.sessions || !data.sessions.length) {
        container.append("div").text(data.error || "No data");
        return;
      }

      const width = 700, height = 280;
      const margin = { top: 20, right: 30, bottom: 40, left: 80 };
      const innerW = width - margin.left - margin.right;
      const innerH = height - margin.top - margin.bottom;

      const svg = container.append("svg")
        .attr("width", width).attr("height", height)
        .attr("viewBox", `0 0 ${width} ${height}`);
      const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

      const sessions = data.sessions;
      const y = d3.scaleBand().domain(sessions.map(s => s.session)).range([0, innerH]).padding(0.2);

      const allVals = sessions.flatMap(s => s.values);
      const xMin = d3.min(allVals) || 0;
      const xMax = d3.max(allVals) || 1;
      const x = d3.scaleLinear().domain([Math.max(0, xMin * 0.9), xMax * 1.1]).range([0, innerW]).nice();

      g.append("g").call(d3.axisLeft(y));
      g.append("g").attr("transform", `translate(0,${innerH})`)
        .call(d3.axisBottom(x).ticks(6));

      const sessionColors = {
        sydney: "#3b82f6", tokyo: "#ef4444", frankfurt: "#f59e0b",
        london: "#10b981", new_york: "#8b5cf6",
      };

      sessions.forEach(sess => {
        const color = sessionColors[sess.session] || "#6b7280";
        const cy = (y(sess.session) || 0) + y.bandwidth() / 2;
        const values = sess.values;
        const stats = sess.stats;
        if (values.length < 2) {
          if (settings.show_outliers || true) {
            values.forEach(v => {
              g.append("circle").attr("cx", x(v)).attr("cy", cy).attr("r", 2).attr("fill", color);
            });
          }
          return;
        }

        const density = kde(values, xMin, xMax);
        const maxDensity = d3.max(density, d => d[1]) || 1;
        const violW = y.bandwidth() / 2;

        const area = d3.area()
          .x(d => x(d[0]))
          .y0(cy)
          .y1(d => cy - (d[1] / maxDensity) * violW)
          .curve(d3.curveCatmullRom);

        const areaDown = d3.area()
          .x(d => x(d[0]))
          .y0(cy)
          .y1(d => cy + (d[1] / maxDensity) * violW)
          .curve(d3.curveCatmullRom);

        if (settings.plot_type === "violin" || settings.plot_type === "both") {
          g.append("path").datum(density).attr("d", area).attr("fill", color).attr("opacity", 0.5);
          g.append("path").datum(density).attr("d", areaDown).attr("fill", color).attr("opacity", 0.5);
        }

        if (settings.plot_type === "box" || settings.plot_type === "both") {
          const boxW = 8;
          g.append("rect")
            .attr("x", x(stats.q1)).attr("y", cy - boxW / 2)
            .attr("width", Math.max(1, x(stats.q3) - x(stats.q1)))
            .attr("height", boxW)
            .attr("fill", color).attr("stroke", "#1f2937");
          g.append("line")
            .attr("x1", x(stats.median)).attr("x2", x(stats.median))
            .attr("y1", cy - boxW).attr("y2", cy + boxW)
            .attr("stroke", "#1f2937").attr("stroke-width", 2);
          g.append("line")
            .attr("x1", x(stats.min)).attr("x2", x(stats.max))
            .attr("y1", cy).attr("y2", cy)
            .attr("stroke", color).attr("stroke-width", 1);
          if (settings.show_outliers) {
            const iqr = stats.q3 - stats.q1;
            const lo = stats.q1 - 1.5 * iqr;
            const hi = stats.q3 + 1.5 * iqr;
            values.filter(v => v < lo || v > hi).forEach(v => {
              g.append("circle").attr("cx", x(v)).attr("cy", cy).attr("r", 2.5).attr("fill", "#1f2937");
            });
          }
        }

        if (settings.show_mean_line) {
          g.append("line")
            .attr("x1", x(stats.mean)).attr("x2", x(stats.mean))
            .attr("y1", cy - violW - 4).attr("y2", cy + violW + 4)
            .attr("stroke", "#dc2626").attr("stroke-width", 1.5).attr("stroke-dasharray", "3,2");
        }
      });

      const table = d3.select("#viz-v5-stats");
      table.selectAll("*").remove();
      const tbl = table.append("table").attr("class", "viz-stats-table");
      const thead = tbl.append("thead");
      thead.append("tr")
        .selectAll("th").data(["Session", "n", "min", "median", "mean", "max", "std"]).enter()
        .append("th").text(d => d);
      const tbody = tbl.append("tbody");
      sessions.forEach(sess => {
        const tr = tbody.append("tr");
        const color = sessionColors[sess.session] || "#6b7280";
        tr.append("td").html(`<span style="display:inline-block;width:10px;height:10px;background:${color};margin-right:6px;border-radius:2px"></span>${sess.session}`);
        tr.append("td").text(sess.stats.n);
        tr.append("td").text(sess.stats.min.toFixed(4));
        tr.append("td").text(sess.stats.median.toFixed(4));
        tr.append("td").text(sess.stats.mean.toFixed(4));
        tr.append("td").text(sess.stats.max.toFixed(4));
        tr.append("td").text(sess.stats.std.toFixed(4));
      });

      window.VIZ.setStatus("V5 loaded · " + data.symbol + " · " + sessions.length + " sessions");
    } catch (e) {
      console.error(e);
      window.VIZ.setStatus("V5 error: " + e.message);
    }
  };

  document.addEventListener("DOMContentLoaded", function() {
    const btn = document.getElementById("viz-v5-apply");
    if (btn) btn.addEventListener("click", function() { window.renderV5 && window.renderV5(); });
  });
})();
