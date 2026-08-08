/**
 * TradeHelp — Live portfolio auto-refresh
 * Polls /api/live/* every 30s and updates DOM.
 */
(function () {
    const REFRESH_MS = 30000;
    const elLastUpdate = document.getElementById('last-update');
    const elEquity = document.getElementById('live-equity');
    const elPnl = document.getElementById('live-pnl');
    const elPositions = document.getElementById('live-positions');
    const elMargin = document.getElementById('live-margin');

    async function refresh() {
        try {
            const r = await fetch('/api/live/totals');
            const d = await r.json();
            if (elEquity) elEquity.textContent = '$' + (d.total_value || 0).toFixed(2);
            if (elPnl) {
                const v = d.total_pl || 0;
                elPnl.textContent = (v >= 0 ? '+$' : '-$') + Math.abs(v).toFixed(2);
                elPnl.className = 'big-value ' + (v >= 0 ? 'pos' : 'neg');
            }
            if (elPositions) elPositions.textContent = d.total_positions || 0;
            if (elMargin) elMargin.textContent = '$' + (d.total_margin || 0).toFixed(2);
            if (elLastUpdate) elLastUpdate.textContent = new Date().toISOString().replace('T', ' ').slice(0, 19) + ' UTC';
        } catch (e) {
            console.error('live refresh failed:', e);
        }
    }

    if (elLastUpdate) {
        refresh();
        setInterval(refresh, REFRESH_MS);
    }
})();
