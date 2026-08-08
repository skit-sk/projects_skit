/* ChartPanel — LWC candlestick chart */
window.ChartPanel = class ChartPanel {
    constructor(win) { this.win = win; this.chart = null; this.chartEl = null; }

    mount() {
        if (!window.LightweightCharts) { this.win.body.innerHTML = '<div style="padding:20px;color:var(--text-muted)">LWC not loaded</div>'; return; }
        const { createChart, CandlestickSeries, LineSeries, HistogramSeries } = window.LightweightCharts;
        this.chartEl = document.createElement('div');
        this.chartEl.style.cssText = 'width:100%;height:100%';
        this.win.body.appendChild(this.chartEl);
        const w = Math.max(200, this.chartEl.clientWidth || 800);
        const h = Math.max(200, this.chartEl.clientHeight || 500);
        this.chart = createChart(this.chartEl, {
            layout: { background: { type: 'solid', color: '#0d1117' }, textColor: '#c9d1d9', fontFamily: 'JetBrains Mono, monospace' },
            grid: { vertLines: { color: '#21262d' }, horzLines: { color: '#21262d' } },
            width: w, height: h,
            rightPriceScale: { borderColor: '#30363d' },
            timeScale: { borderColor: '#30363d', timeVisible: true, secondsVisible: false },
            crosshair: { mode: 0 }
        });
        this.candleSeries = this.chart.addSeries(CandlestickSeries, { upColor: '#3fb950', downColor: '#f85149', wickUpColor: '#3fb950', wickDownColor: '#f85149', borderVisible: false });
        this.volSeries = this.chart.addSeries(HistogramSeries, { priceFormat: { type: 'volume' }, priceScaleId: 'vol' });
        this.chart.priceScale('vol').applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });
        setTimeout(() => this.resize(), 100);
    }

    update(klines) {
        if (!this.chart || !Array.isArray(klines) || !klines.length) return;
        this.candleSeries.setData(klines.map(k => ({ time: Math.floor(k[0]/1000), open: +k[1], high: +k[2], low: +k[3], close: +k[4] })));
        this.volSeries.setData(klines.map(k => ({ time: Math.floor(k[0]/1000), value: +k[5], color: +k[4] >= +k[1] ? 'rgba(63,185,80,0.3)' : 'rgba(248,81,73,0.3)' })));
        const { LineSeries } = window.LightweightCharts;
        const cl = klines.map(k => +k[4]);
        const m20 = this.calcMA(cl, 20), m50 = this.calcMA(cl, 50);
        if (this.ma20) { this.chart.removeSeries(this.ma20); this.ma20 = null; }
        if (this.ma50) { this.chart.removeSeries(this.ma50); this.ma50 = null; }
        if (m20.length) { this.ma20 = this.chart.addSeries(LineSeries, { color: '#58a6ff', lineWidth: 1 }); this.ma20.setData(m20.map((v, i) => ({ time: Math.floor(klines[i+19][0]/1000), value: v }))); }
        if (m50.length) { this.ma50 = this.chart.addSeries(LineSeries, { color: '#bc8cff', lineWidth: 1 }); this.ma50.setData(m50.map((v, i) => ({ time: Math.floor(klines[i+49][0]/1000), value: v }))); }
        this.chart.timeScale().fitContent();
        setTimeout(() => this.resize(), 50);
    }

    resize() {
        if (!this.chart || !this.chartEl) return;
        const w = this.chartEl.clientWidth;
        const h = this.chartEl.clientHeight;
        if (w > 20 && h > 20) this.chart.applyOptions({ width: w, height: h });
    }

    calcMA(c, p) { const r = []; for (let i = p - 1; i < c.length; i++) { let s = 0; for (let j = 0; j < p; j++) s += c[i - j]; r.push(s / p); } return r; }
};
