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

  let currentMode = "calendar";
  let currentData = null;
  const VALID_VIEWS = ["calendar", "bars", "direction", "weekday", "heatmap"];

  function renderCalendar(container, data) {
    container.selectAll("*").remove();
    if (!data.calendar || !data.calendar.length) {
      container.append("div").text("Нет данных для отображения");
      return;
    }
    const cellW = 16, cellH = 16, gap = 3;
    const monthLabelW = 14, dayLabelH = 14;
    const months = data.calendar;
    const width = monthLabelW + months.length * (cellW * 7 + gap + 30);
    const height = dayLabelH + 31 * (cellH + gap) + 30;

    const svg = container.append("svg")
      .attr("width", width).attr("height", height)
      .attr("viewBox", "0 0 " + width + " " + height);

    const maxVal = data.max_value || 1;
    const colors = SCHEMES.viridis;

    const monthNames = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"];

    months.forEach(function(m, mi) {
      const xBase = monthLabelW + mi * (cellW * 7 + gap + 30);
      const [yStr, mStr] = m.month.split("-");
      const monthLabel = monthNames[parseInt(mStr, 10) - 1] + " " + yStr;
      svg.append("text")
        .attr("x", xBase).attr("y", dayLabelH - 2)
        .attr("font-size", "11").attr("fill", "#374151").attr("font-weight", "600")
        .text(monthLabel);

      for (let dayIdx = 0; dayIdx < 31; dayIdx++) {
        const v = m.days[dayIdx];
        const wd = (dayIdx + 1);
        const ts = new Date(Date.UTC(parseInt(yStr, 10), parseInt(mStr, 10) - 1, wd));
        const dayOfWeek = ts.getUTCDay();
        const col = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
        const row = Math.floor((wd - 1) / 7);
        const x = xBase + col * (cellW + 0.5);
        const y = dayLabelH + 4 + row * (cellH + gap);
        svg.append("rect")
          .attr("x", x).attr("y", y)
          .attr("width", cellW).attr("height", cellH)
          .attr("rx", 2)
          .attr("fill", v > 0 ? colorFor("viridis", v / maxVal) : "#f3f4f6")
          .attr("stroke", "#e5e7eb")
          .attr("stroke-width", 0.5)
          .on("mousemove", function(evt) {
            window.VIZ.showTooltip(evt, `
              <div class="tt-row"><span class="tt-label">Дата:</span><span class="tt-value">${m.month}-${String(wd).padStart(2, "0")}</span></div>
              <div class="tt-row"><span class="tt-label">${data.metric}:</span><span class="tt-value">${v > 0 ? (v * 100).toFixed(2) + "%" : "нет данных"}</span></div>
            `);
          })
          .on("mouseleave", window.VIZ.hideTooltip);
      }
    });

    const legendY = height - 18;
    const legendW = 200;
    const legendX0 = 14;
    const steps = 20;
    for (let i = 0; i < steps; i++) {
      svg.append("rect")
        .attr("x", legendX0 + (i * legendW / steps))
        .attr("y", legendY)
        .attr("width", legendW / steps).attr("height", 10)
        .attr("fill", colorFor("viridis", i / (steps - 1)));
    }
    svg.append("text").attr("x", legendX0).attr("y", legendY - 3)
      .attr("font-size", "10").attr("fill", "#6b7280").text("0%");
    svg.append("text").attr("x", legendX0 + legendW).attr("y", legendY - 3)
      .attr("text-anchor", "end").attr("font-size", "10").attr("fill", "#6b7280")
      .text((maxVal * 100).toFixed(1) + "%");
    svg.append("text").attr("x", legendX0).attr("y", legendY + 22)
      .attr("font-size", "10").attr("fill", "#6b7280").text("низкая");
    svg.append("text").attr("x", legendX0 + legendW).attr("y", legendY + 22)
      .attr("text-anchor", "end").attr("font-size", "10").attr("fill", "#6b7280").text("высокая");
  }

  function renderDailyBars(container, data) {
    container.selectAll("*").remove();
    const bars = data.bars || [];
    if (!bars.length) {
      container.append("div").text("Нет данных");
      return;
    }
    const width = Math.max(700, bars.length * 12 + 80);
    const height = 320;
    const margin = { top: 20, right: 20, bottom: 40, left: 60 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;
    const svg = container.append("svg")
      .attr("width", width).attr("height", height)
      .attr("viewBox", "0 0 " + width + " " + height);
    const g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");
    const x = d3.scaleBand().domain(bars.map(function(b) { return b.date; })).range([0, innerW]).padding(0.15);
    const maxV = data.max_value || 1;
    const y = d3.scaleLinear().domain([0, maxV * 1.1]).range([innerH, 0]).nice();
    g.append("g").attr("transform", "translate(0," + innerH + ")")
      .call(d3.axisBottom(x).tickValues(x.domain().filter(function(_, i) {
        return i % Math.ceil(bars.length / 10) === 0;
      })))
      .selectAll("text").attr("font-size", "9").attr("transform", "rotate(-45)").attr("text-anchor", "end");
    g.append("g").call(d3.axisLeft(y).ticks(6).tickFormat(function(d) { return (d * 100).toFixed(1) + "%"; }));
    g.selectAll(".bar")
      .data(bars).enter().append("rect")
      .attr("class", "bar")
      .attr("x", function(b) { return x(b.date); })
      .attr("y", function(b) { return y(b.value); })
      .attr("width", x.bandwidth())
      .attr("height", function(b) { return innerH - y(b.value); })
      .attr("fill", function(b) { return b.direction === "up" ? "#10b981" : "#ef4444"; })
      .attr("opacity", 0.85)
      .on("mousemove", function(evt, b) {
        window.VIZ.showTooltip(evt, `
          <div class="tt-row"><span class="tt-label">Дата:</span><span class="tt-value">${b.date}</span></div>
          <div class="tt-row"><span class="tt-label">${data.metric}:</span><span class="tt-value">${(b.value * 100).toFixed(2)}%</span></div>
          <div class="tt-row"><span class="tt-label">High/Low:</span><span class="tt-value">${b.high.toFixed(2)} / ${b.low.toFixed(2)}</span></div>
          <div class="tt-row"><span class="tt-label">Direction:</span><span class="tt-value">${b.direction === "up" ? "▲ зелёный" : "▼ красный"}</span></div>
        `);
      })
      .on("mouseleave", window.VIZ.hideTooltip);
  }

  function renderDirection(container, data) {
    container.selectAll("*").remove();
    const width = 700, height = 320;
    const margin = { top: 20, right: 20, bottom: 20, left: 20 };
    const radius = Math.min(width, height) / 2 - 40;
    const svg = container.append("svg")
      .attr("width", width).attr("height", height)
      .attr("viewBox", "0 0 " + width + " " + height);
    const cx = 200, cy = height / 2;

    const total = data.total || 1;
    const green = data.green_count || 0;
    const red = data.red_count || 0;
    const greenAngle = (green / total) * Math.PI * 2;

    const g = svg.append("g").attr("transform", "translate(" + cx + "," + cy + ")");

    const arcUp = d3.arc().innerRadius(radius * 0.55).outerRadius(radius)
      .startAngle(0).endAngle(greenAngle);
    const arcDown = d3.arc().innerRadius(radius * 0.55).outerRadius(radius)
      .startAngle(greenAngle).endAngle(Math.PI * 2);

    g.append("path")
      .attr("d", arcUp)
      .attr("fill", "#10b981").attr("opacity", 0.9)
      .on("mousemove", function(evt) {
        window.VIZ.showTooltip(evt, `
          <div class="tt-row"><span class="tt-label">Зелёные дни:</span><span class="tt-value">${green} (${data.green_pct}%)</span></div>
        `);
      })
      .on("mouseleave", window.VIZ.hideTooltip);

    g.append("path")
      .attr("d", arcDown)
      .attr("fill", "#ef4444").attr("opacity", 0.9)
      .on("mousemove", function(evt) {
        window.VIZ.showTooltip(evt, `
          <div class="tt-row"><span class="tt-label">Красные дни:</span><span class="tt-value">${red} (${data.red_pct}%)</span></div>
        `);
      })
      .on("mouseleave", window.VIZ.hideTooltip);

    g.append("text").attr("text-anchor", "middle").attr("y", -8)
      .attr("font-size", "32").attr("font-weight", "700").attr("fill", "#10b981")
      .text(data.green_pct + "%");
    g.append("text").attr("text-anchor", "middle").attr("y", 18)
      .attr("font-size", "12").attr("fill", "#6b7280")
      .text("зелёных дней");
    g.append("text").attr("text-anchor", "middle").attr("y", 36)
      .attr("font-size", "12").attr("fill", "#6b7280")
      .text("из " + total);

    const sideX = 420, sideY = 60;
    const rows = [
      ["📅 Всего дней", data.total],
      ["▲ Зелёных", green + " (" + data.green_pct + "%)"],
      ["▼ Красных", red + " (" + data.red_pct + "%)"],
      ["🔥 Longest зелёная серия", data.longest_green_streak + " дн."],
      ["❄ Longest красная серия", data.longest_red_streak + " дн."],
    ];
    rows.forEach(function(r, i) {
      const tr = svg.append("g").attr("transform", "translate(" + sideX + "," + (sideY + i * 36) + ")");
      tr.append("text").attr("x", 0).attr("y", 14)
        .attr("font-size", "13").attr("fill", "#374151").attr("font-weight", "500")
        .text(r[0]);
      tr.append("text").attr("x", 0).attr("y", 32)
        .attr("font-size", "16").attr("fill", "#1f2937").attr("font-weight", "700")
        .text(r[1]);
    });
  }

  function renderWeekday(container, data) {
    container.selectAll("*").remove();
    const summary = data.weekday_summary || [];
    if (!summary.length) {
      container.append("div").text("Нет данных");
      return;
    }
    const width = 700, height = 320;
    const margin = { top: 20, right: 20, bottom: 40, left: 60 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;
    const svg = container.append("svg")
      .attr("width", width).attr("height", height)
      .attr("viewBox", "0 0 " + width + " " + height);
    const g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");
    const wdLabels = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];
    const x = d3.scaleBand().domain(summary.map(function(s) { return s.weekday; })).range([0, innerW]).padding(0.25);
    const maxV = Math.max.apply(null, summary.map(function(s) { return s.max || 0; }).concat([0.001]));
    const y = d3.scaleLinear().domain([0, maxV * 1.15]).range([innerH, 0]).nice();
    g.append("g").attr("transform", "translate(0," + innerH + ")")
      .call(d3.axisBottom(x).tickFormat(function(d) { return wdLabels[d]; }));
    g.append("g").call(d3.axisLeft(y).ticks(6).tickFormat(function(d) { return (d * 100).toFixed(1) + "%"; }));
    summary.forEach(function(s) {
      const cx = (x(s.weekday) || 0) + x.bandwidth() / 2;
      const barW = Math.min(20, x.bandwidth() * 0.3);
      g.append("line")
        .attr("x1", cx).attr("x2", cx)
        .attr("y1", y(s.min || 0)).attr("y2", y(s.max || 0))
        .attr("stroke", "#6b7280").attr("stroke-width", 1.5);
      g.append("rect")
        .attr("x", cx - barW / 2)
        .attr("y", y(s.avg || 0))
        .attr("width", barW)
        .attr("height", Math.max(0, innerH - y(s.avg || 0)))
        .attr("fill", "#2563eb").attr("opacity", 0.85);
      g.append("circle")
        .attr("cx", cx).attr("cy", y(s.avg || 0))
        .attr("r", 4)
        .attr("fill", "#1e3a8a");
    });
    g.selectAll(".wd-label")
      .data(summary).enter().append("text")
      .attr("x", function(s) { return (x(s.weekday) || 0) + x.bandwidth() / 2; })
      .attr("y", -4)
      .attr("text-anchor", "middle")
      .attr("font-size", "10")
      .attr("fill", "#6b7280")
      .text(function(s) { return s.count + " дн."; });
  }

  function renderHeatmap(container, data) {
    container.selectAll("*").remove();
    if (!data.matrix || !data.matrix.length) {
      container.append("div").text("Нет данных");
      return;
    }
    const cellW = 28, cellH = 22;
    const labelW = 50, labelH = 24;
    const width = labelW + 24 * cellW + 20;
    const height = labelH + 7 * cellH + 80;

    const svg = container.append("svg")
      .attr("width", width).attr("height", height)
      .attr("viewBox", "0 0 " + width + " " + height);

    const maxVal = data.max_value || 1;
    const wd = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

    const g = svg.append("g").attr("transform", "translate(" + labelW + "," + labelH + ")");
    g.selectAll(".cell")
      .data(data.matrix.flatMap(function(row, w) { return row.map(function(v, h) { return { w: w, h: h, v: v }; }); }))
      .enter().append("rect")
      .attr("class", "cell")
      .attr("x", function(d) { return d.h * cellW; })
      .attr("y", function(d) { return d.w * cellH; })
      .attr("width", cellW - 1).attr("height", cellH - 1)
      .attr("fill", function(d) { return d.v > 0 ? colorFor("viridis", d.v / maxVal) : "#1f2937"; })
      .attr("opacity", function(d) { return d.v > 0 ? 0.9 : 0.2; })
      .on("mousemove", function(evt, d) {
        const n = (data.counts && data.counts[d.w] && data.counts[d.w][d.h]) || 0;
        window.VIZ.showTooltip(evt, `
          <div class="tt-row"><span class="tt-label">День:</span><span class="tt-value">${wd[d.w]}</span></div>
          <div class="tt-row"><span class="tt-label">Час (МСК):</span><span class="tt-value">${String(d.h).padStart(2, "0")}:00</span></div>
          <div class="tt-row"><span class="tt-label">${data.metric}:</span><span class="tt-value">${d.v > 0 ? (d.v * 100).toFixed(2) + "%" : "нет данных"}</span></div>
          <div class="tt-row"><span class="tt-label">Свечей:</span><span class="tt-value">${n}</span></div>
        `);
      })
      .on("mouseleave", window.VIZ.hideTooltip);

    svg.selectAll(".wd-label")
      .data(wd).enter().append("text")
      .attr("x", labelW - 6).attr("y", function(_, i) { return labelH + i * cellH + cellH / 2 + 3; })
      .attr("text-anchor", "end").attr("font-size", "10").attr("fill", "#374151")
      .text(function(d) { return d; });

    svg.selectAll(".h-label")
      .data(d3.range(0, 24, 3)).enter().append("text")
      .attr("x", function(d) { return labelW + d * cellW + cellW / 2; })
      .attr("y", labelH - 4)
      .attr("text-anchor", "middle").attr("font-size", "9").attr("fill", "#6b7280")
      .text(function(d) { return d; });

    if (data.data_note) {
      const noteY = labelH + 7 * cellH + 10;
      svg.append("rect")
        .attr("x", 0).attr("y", noteY)
        .attr("width", width).attr("height", 36)
        .attr("fill", "#fef3c7").attr("stroke", "#f59e0b").attr("stroke-width", 0.5);
      const lines = data.data_note.match(/.{1,90}(\s|$)/g) || [data.data_note];
      lines.slice(0, 2).forEach(function(line, i) {
        svg.append("text")
          .attr("x", 8).attr("y", noteY + 14 + i * 14)
          .attr("font-size", "10").attr("fill", "#92400e")
          .text("⚠ " + line.trim());
      });
    }
  }

  function renderStats(container, data) {
    container.selectAll("*").remove();
    if (!data) return;
    const view = data.view || currentMode;
    const rows = [];
    if (view === "direction") {
      rows.push(["📅 Всего дней", data.total]);
      rows.push(["▲ Зелёных", data.green_count + " (" + data.green_pct + "%)"]);
      rows.push(["▼ Красных", data.red_count + " (" + data.red_pct + "%)"]);
      rows.push(["🔥 Зелёная серия", data.longest_green_streak + " дн."]);
      rows.push(["❄ Красная серия", data.longest_red_streak + " дн."]);
    } else if (view === "weekday" && data.weekday_summary) {
      const wdLabels = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];
      data.weekday_summary.forEach(function(s) {
        if (s.count > 0) {
          rows.push(["📅 " + wdLabels[s.weekday], (s.avg * 100).toFixed(2) + "% (n=" + s.count + ", min=" + (s.min * 100).toFixed(1) + "%, max=" + (s.max * 100).toFixed(1) + "%)"]);
        }
      });
    } else if (view === "calendar" && data.calendar) {
      rows.push(["📅 Месяцев", data.calendar.length]);
      rows.push(["📊 Свечей", data.candles_count]);
      rows.push(["📈 Max " + data.metric, (data.max_value * 100).toFixed(2) + "%"]);
    } else if (view === "bars") {
      const bars = data.bars || [];
      const green = bars.filter(function(b) { return b.direction === "up"; }).length;
      rows.push(["📊 Всего свечей", bars.length]);
      rows.push(["📈 Max " + data.metric, (data.max_value * 100).toFixed(2) + "%"]);
      rows.push(["▲ Зелёных / ▼ Красных", green + " / " + (bars.length - green)]);
    } else if (view === "heatmap" && data.summary) {
      const s = data.summary;
      const wdLabels = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];
      function fmtCell(x) {
        if (!x) return "—";
        return wdLabels[x.weekday] + " " + String(x.hour).padStart(2, "0") + ":00 (" + (x.value * 100).toFixed(2) + "%, n=" + x.count + ")";
      }
      rows.push(["🔥 Max", fmtCell(s.max)]);
      rows.push(["❄ Min", fmtCell(s.min)]);
      rows.push(["📊 Avg", (s.avg * 100).toFixed(2) + "%"]);
      rows.push(["📅 Ячеек с данными", s.total_cells + " / 168"]);
      if (s.top5 && s.top5.length) {
        rows.push(["🏆 Top 5", s.top5.map(function(x) {
          return wdLabels[x.weekday] + " " + String(x.hour).padStart(2, "0") + " (" + (x.value * 100).toFixed(1) + "%)";
        }).join(" · ")]);
      }
    }
    rows.forEach(function(row) {
      const r = container.append("div").attr("class", "stat-row");
      r.append("span").attr("class", "stat-label").text(row[0]);
      r.append("span").attr("class", "stat-value").text(row[1]);
    });
  }

  window.renderV1 = async function() {
    const container = d3.select("#viz-v1-heatmap");
    const statsContainer = d3.select("#viz-v1-stats");
    const settings = window.VIZ_SETTINGS ? window.VIZ_SETTINGS.get("v1_sessions_heatmap") : {};
    const objId = window.VIZ.getCurrentObjId();
    if (!objId) return;

    const days = settings.days || window.VIZ.getCurrentDays();
    const metric = settings.metric || "body_pct";
    const view = currentMode;

    window.VIZ.setStatus("Loading V1 · " + view + " · " + objId.slice(0, 8));
    try {
      const resp = await fetch("/visualizations/api/sessions_heatmap/" + objId +
        "?days=" + days + "&metric=" + metric + "&view=" + view + "&tz=3");
      const data = await resp.json();
      if (data.error) {
        container.selectAll("*").remove();
        container.append("div").attr("class", "viz-v1-error")
          .text("⚠ " + data.error);
        statsContainer.selectAll("*").remove();
        return;
      }
      currentData = data;
      if (view === "calendar")     renderCalendar(container, data);
      else if (view === "bars")    renderDailyBars(container, data);
      else if (view === "direction") renderDirection(container, data);
      else if (view === "weekday") renderWeekday(container, data);
      else if (view === "heatmap") renderHeatmap(container, data);
      renderStats(statsContainer, data);
      window.VIZ.setStatus("V1 · " + view + " · " + data.symbol + " · " + data.candles_count + " свечей");
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
        if (currentData && currentData.view === currentMode && currentData.candles_count) {
          const container = d3.select("#viz-v1-heatmap");
          const statsContainer = d3.select("#viz-v1-stats");
          if (currentMode === "calendar")     renderCalendar(container, currentData);
          else if (currentMode === "bars")    renderDailyBars(container, currentData);
          else if (currentMode === "direction") renderDirection(container, currentData);
          else if (currentMode === "weekday") renderWeekday(container, currentData);
          else if (currentMode === "heatmap") renderHeatmap(container, currentData);
          renderStats(statsContainer, currentData);
        } else {
          window.renderV1();
        }
      });
    });
  });
})();
