/**
 * TradeHelp — Lightweight Charts (LWC) v5.2.0 init
 * Loads via CDN, fetches klines via /api/klines proxy.
 */
async function initLWC(containerId, symbol = 'BTCUSDT', interval = '1d', indicators = ['MA20', 'MA50', 'BB']) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.warn('LWC container not found:', containerId);
        return null;
    }
    if (!window.LightweightCharts) {
        console.warn('LWC not loaded');
        return null;
    }
    const { createChart, CandlestickSeries, LineSeries, AreaSeries } = window.LightweightCharts;
    const chart = createChart(container, {
        layout: {
            background: { type: 'solid', color: '#0d1117' },
            textColor: '#c9d1d9',
            fontFamily: 'JetBrains Mono, monospace',
        },
        grid: {
            vertLines: { color: '#21262d' },
            horzLines: { color: '#21262d' },
        },
        width: container.clientWidth || 800,
        height: container.clientHeight || 400,
        rightPriceScale: { borderColor: '#30363d' },
        timeScale: { borderColor: '#30363d', timeVisible: true, secondsVisible: false },
    });

    try {
        const r = await fetch(`/api/klines?symbol=${symbol}&interval=${interval}&limit=200`);
        const klines = await r.json();
        if (!Array.isArray(klines) || !klines.length) {
            console.warn('No klines for', symbol);
            return chart;
        }
        const data = klines.map(k => ({
            time: Math.floor(k[0] / 1000),
            open: parseFloat(k[1]),
            high: parseFloat(k[2]),
            low: parseFloat(k[3]),
            close: parseFloat(k[4]),
        }));
        chart.addSeries(CandlestickSeries, {
            upColor: '#3fb950', downColor: '#f85149',
            wickUpColor: '#3fb950', wickDownColor: '#f85149',
            borderVisible: false,
        }).setData(data);

        if (indicators.includes('MA20')) addMA(chart, klines, 20, '#58a6ff');
        if (indicators.includes('MA50')) addMA(chart, klines, 50, '#bc8cff');
        if (indicators.includes('BB')) addBB(chart, klines, 20, 2);
        if (indicators.includes('VOL')) addVolume(chart, klines);

        chart.timeScale().fitContent();
    } catch (e) {
        console.error('LWC init failed:', e);
    }
    return chart;
}

function addMA(chart, klines, period, color) {
    const { LineSeries } = window.LightweightCharts;
    const closes = klines.map(k => parseFloat(k[4]));
    const ma = [];
    for (let i = 0; i < closes.length; i++) {
        if (i < period - 1) continue;
        let sum = 0;
        for (let j = 0; j < period; j++) sum += closes[i - j];
        ma.push({ time: Math.floor(klines[i][0] / 1000), value: sum / period });
    }
    chart.addSeries(LineSeries, { color, lineWidth: 1, title: `MA${period}` }).setData(ma);
}

function addBB(chart, klines, period, std) {
    const { LineSeries } = window.LightweightCharts;
    const closes = klines.map(k => parseFloat(k[4]));
    const upper = [], lower = [];
    for (let i = 0; i < closes.length; i++) {
        if (i < period - 1) continue;
        const slice = closes.slice(i - period + 1, i + 1);
        const mean = slice.reduce((a, b) => a + b, 0) / period;
        const variance = slice.reduce((a, b) => a + (b - mean) ** 2, 0) / period;
        const sd = Math.sqrt(variance);
        upper.push({ time: Math.floor(klines[i][0] / 1000), value: mean + std * sd });
        lower.push({ time: Math.floor(klines[i][0] / 1000), value: mean - std * sd });
    }
    chart.addSeries(LineSeries, { color: 'rgba(88, 166, 255, 0.5)', lineWidth: 1, lineStyle: 2, title: 'BB Upper' }).setData(upper);
    chart.addSeries(LineSeries, { color: 'rgba(88, 166, 255, 0.5)', lineWidth: 1, lineStyle: 2, title: 'BB Lower' }).setData(lower);
}

function addVolume(chart, klines) {
    const { HistogramSeries } = window.LightweightCharts;
    const data = klines.map((k, i) => ({
        time: Math.floor(k[0] / 1000),
        value: parseFloat(k[5]),
        color: parseFloat(k[4]) >= parseFloat(k[1]) ? 'rgba(63, 185, 80, 0.4)' : 'rgba(248, 81, 73, 0.4)',
    }));
    chart.addSeries(HistogramSeries, { priceFormat: { type: 'volume' }, priceScaleId: 'vol' })
        .setData(data);
    chart.priceScale('vol').applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });
}
