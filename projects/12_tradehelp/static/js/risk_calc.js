/**
 * Risk Calculator
 * Computes position size, Kelly %, R/R, ATR stop, etc.
 */
function computeRisk() {
    const equity = parseFloat(document.getElementById('equity').value) || 0;
    const risk_pct = parseFloat(document.getElementById('risk_pct').value) || 0;
    const entry = parseFloat(document.getElementById('entry').value) || 0;
    const stop = parseFloat(document.getElementById('stop').value) || 0;
    const leverage = parseFloat(document.getElementById('leverage').value) || 1;
    const atr = parseFloat(document.getElementById('atr').value) || 0;
    const winrate = parseFloat(document.getElementById('winrate').value) || 0;
    const rr = parseFloat(document.getElementById('rr').value) || 0;

    const stop_distance = Math.abs(entry - stop);
    const stop_pct = (stop_distance / entry) * 100;
    const risk_usd = equity * (risk_pct / 100);

    // Position size
    const position_size_usd = (risk_usd / stop_pct) * 100;
    const position_size_coin = position_size_usd / entry;
    const margin_required = position_size_usd / leverage;
    const liquidation_price = entry * (1 - 1 / leverage);

    // Kelly Criterion
    const p = winrate / 100;
    const q = 1 - p;
    const kelly_pct = ((rr * p - q) / rr) * 100;
    const half_kelly = kelly_pct / 2;
    const quarter_kelly = kelly_pct / 4;

    // ATR stop
    const atr_stop_1x = entry - atr;
    const atr_stop_2x = entry - 2 * atr;
    const atr_stop_3x = entry - 3 * atr;

    // Max positions before ruin
    const ruin_threshold = 50;
    const max_consecutive_losses = Math.floor(Math.log(0.5) / Math.log(1 - risk_pct / 100));

    const out = document.getElementById('risk-output');
    out.innerHTML = `
        <div class="result-row">
            <div class="result-label">Стоп-лосс:</div>
            <div class="result-val">${stop} (${stop_pct.toFixed(2)}% / ${stop_distance.toFixed(4)})</div>
        </div>
        <div class="result-row">
            <div class="result-label">Риск USD:</div>
            <div class="result-val">$${risk_usd.toFixed(2)}</div>
        </div>
        <div class="result-row">
            <div class="result-label">Размер позиции (USD):</div>
            <div class="result-val">$${position_size_usd.toFixed(2)}</div>
        </div>
        <div class="result-row">
            <div class="result-label">Размер позиции (монеты):</div>
            <div class="result-val">${position_size_coin.toFixed(4)}</div>
        </div>
        <div class="result-row">
            <div class="result-label">Маржа (${leverage}x):</div>
            <div class="result-val">$${margin_required.toFixed(2)}</div>
        </div>
        <div class="result-row">
            <div class="result-label">Цена ликвидации:</div>
            <div class="result-val neg">${liquidation_price.toFixed(4)}</div>
        </div>
        <hr>
        <div class="result-row">
            <div class="result-label">Kelly %:</div>
            <div class="result-val">${kelly_pct.toFixed(2)}% (½=${half_kelly.toFixed(2)}%, ¼=${quarter_kelly.toFixed(2)}%)</div>
        </div>
        <div class="result-row">
            <div class="result-label">ATR(14):</div>
            <div class="result-val">${atr}</div>
        </div>
        <div class="result-row">
            <div class="result-label">Стоп 1×ATR:</div>
            <div class="result-val">${atr_stop_1x.toFixed(4)}</div>
        </div>
        <div class="result-row">
            <div class="result-label">Стоп 2×ATR:</div>
            <div class="result-val">${atr_stop_2x.toFixed(4)}</div>
        </div>
        <div class="result-row">
            <div class="result-label">Стоп 3×ATR:</div>
            <div class="result-val">${atr_stop_3x.toFixed(4)}</div>
        </div>
        <hr>
        <div class="result-row">
            <div class="result-label">R/R:</div>
            <div class="result-val">${rr.toFixed(2)}</div>
        </div>
        <div class="result-row">
            <div class="result-label">Target (TP):</div>
            <div class="result-val pos">${(entry + stop_distance * rr).toFixed(4)}</div>
        </div>
        <div class="result-row">
            <div class="result-label">Макс. убытков подряд до -50%:</div>
            <div class="result-val">${max_consecutive_losses}</div>
        </div>
    `;
    // Append CSS for result-row
    if (!document.getElementById('risk-calc-css')) {
        const s = document.createElement('style');
        s.id = 'risk-calc-css';
        s.textContent = `
            .result-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid var(--border); font-size: 13px; }
            .result-label { color: var(--text-secondary); }
            .result-val { color: var(--text-primary); font-family: var(--font-mono); }
            .result-val.pos { color: var(--accent-green); }
            .result-val.neg { color: var(--accent-red); }
        `;
        document.head.appendChild(s);
    }
}
