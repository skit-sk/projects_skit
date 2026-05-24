let currentExchange = 'bitget';
let currentMethod = null;
let methodsCache = {};
let signaturesCache = {};

document.addEventListener('DOMContentLoaded', function () {
    loadExchanges();
    loadEnvKeys();
    initDivider();
    try {
        const savedBid = localStorage.getItem('depth-bid-color');
        const savedAsk = localStorage.getItem('depth-ask-color');
        const savedBg = localStorage.getItem('depth-bg');
        if (savedBid) document.getElementById('color-bid').value = savedBid;
        if (savedAsk) document.getElementById('color-ask').value = savedAsk;
        if (savedBg) document.getElementById('color-bg').value = savedBg;
        if (savedBid || savedAsk || savedBg) onColorChange();
        
        const savedFlashVol = localStorage.getItem('flash-vol-ms');
        const savedFlashCumul = localStorage.getItem('flash-cumul-ms');
        if (savedFlashVol) document.getElementById('flash-vol-ms').value = savedFlashVol;
        if (savedFlashCumul) document.getElementById('flash-cumul-ms').value = savedFlashCumul;
        onFlashTimeChange();
    } catch(e) {}
});

function loadExchanges() {
    console.log('CCXT: loadExchanges called');
    fetch('/ccxt-api/api/exchanges')
        .then(r => {
            console.log('CCXT: response status', r.status);
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(data => {
            console.log('CCXT: received', data.length, 'exchanges');
            const sel = document.getElementById('exchange-select');
            if (!sel) { console.error('CCXT: exchange-select not found'); return; }
            sel.innerHTML = '';
            for (const ex of data) {
                const opt = document.createElement('option');
                opt.value = ex;
                opt.textContent = ex;
                if (ex === 'bitget') opt.selected = true;
                sel.appendChild(opt);
            }
            onExchangeChange();
        })
        .catch(e => {
            console.error('CCXT: loadExchanges error:', e);
            const sel = document.getElementById('exchange-select');
            if (sel) sel.innerHTML = '<option value="">Ошибка: ' + esc(e.message) + '</option>';
        });
}

function loadEnvKeys() {
    fetch('/ccxt-api/api/env-keys')
        .then(r => r.json())
        .then(data => {
            if (data.api_key) document.getElementById('api-key-input').placeholder = '✓ загружен';
            if (data.secret) document.getElementById('secret-input').placeholder = '✓ загружен';
            if (data.passphrase) document.getElementById('passphrase-input').placeholder = '✓ загружен';
        });
}

function onExchangeChange() {
    const sel = document.getElementById('exchange-select');
    currentExchange = sel.value;
    if (!currentExchange) return;
    loadMethods(currentExchange);
}

function loadMethods(exchange) {
    const tree = document.getElementById('method-tree');
    tree.innerHTML = '<div class="loading">⏳ Загрузка методов...</div>';
    currentMethod = null;
    document.getElementById('method-info').innerHTML = '<div class="placeholder">Выберите метод слева</div>';
    document.getElementById('request-url').style.display = 'none';
    document.getElementById('param-form').style.display = 'none';
    document.getElementById('execute-area').style.display = 'none';
    document.getElementById('response-area').style.display = 'none';
    document.getElementById('error-area').style.display = 'none';

    fetch('/ccxt-api/api/methods/' + exchange)
        .then(r => r.json())
        .then(data => {
            methodsCache = data.categories || {};
            signaturesCache = data.signatures || {};
            buildMethodTree(methodsCache, tree);
        })
        .catch(err => {
            tree.innerHTML = '<div class="loading">❌ Ошибка загрузки: ' + esc(err.message) + '</div>';
        });
}

function buildMethodTree(categories, container) {
    container.innerHTML = '';
    const entries = Object.entries(categories);
    if (entries.length === 0) {
        container.innerHTML = '<div class="loading">Нет методов</div>';
        return;
    }
    for (const [catName, methods] of entries) {
        const catDiv = document.createElement('div');
        catDiv.className = 'method-category';

        const hdr = document.createElement('div');
        hdr.className = 'cat-header';
        hdr.innerHTML = '<span class="cat-toggle">▶</span><span class="cat-name">' + esc(catName) + '</span><span class="cat-count">' + methods.length + '</span>';
        hdr.onclick = function () {
            toggleCategory(catDiv);
        };
        catDiv.appendChild(hdr);

        const body = document.createElement('div');
        body.className = 'cat-body';

        for (const mObj of methods) {
            const m = typeof mObj === 'string' ? mObj : mObj.name;
            const auth = typeof mObj === 'string' ? true : mObj.auth_required;
            const item = document.createElement('div');
            item.className = 'method-item';
            item.dataset.method = m;
            item.dataset.auth = auth;
            item.innerHTML = '<span class="method-icon ' + (auth ? 'auth' : 'public') + '">' + (auth ? '●' : '○') + '</span><span class="method-name">' + esc(m) + '</span>';
            item.onclick = function () { selectMethod(m, item); };
            body.appendChild(item);
        }

        catDiv.appendChild(body);
        container.appendChild(catDiv);
    }

    // Expand first category
    const firstCat = container.querySelector('.method-category');
    if (firstCat) toggleCategory(firstCat);

    applyAuthFilter();
}

function toggleCategory(catDiv) {
    const toggle = catDiv.querySelector('.cat-toggle');
    const body = catDiv.querySelector('.cat-body');
    const isExpanded = body.classList.contains('expanded');
    body.classList.toggle('expanded');
    toggle.classList.toggle('expanded');
}

function loadDocs(method) {
    const section = document.getElementById('docs-section');
    const content = document.getElementById('docs-content');
    section.style.display = 'none';

    fetch('/ccxt-api/api/docs/' + currentExchange + '/' + method)
        .then(r => r.json())
        .then(data => {
            if (data.docs && data.docs.trim()) {
                content.textContent = data.docs.trim();
                section.style.display = 'block';
                const body = section.querySelector('.docs-body');
                const toggle = section.querySelector('.docs-toggle');
                body.classList.remove('expanded');
                toggle.classList.remove('expanded');
            }
        })
        .catch(() => {});
}

function toggleDocs(header) {
    const body = header.nextElementSibling;
    const toggle = header.querySelector('.docs-toggle');
    body.classList.toggle('expanded');
    toggle.classList.toggle('expanded');
}

function applyAuthFilter() {
    const val = document.getElementById('auth-filter').value;
    const wsOnly = document.getElementById('ws-filter').checked;
    document.querySelectorAll('.method-item').forEach(el => {
        const auth = el.dataset.auth === 'true';
        const isWs = el.dataset.method.endsWith('_ws');
        let show = true;
        if (val === 'public') show = !auth;
        else if (val === 'auth') show = auth;
        if (wsOnly && show) show = isWs;
        el.style.display = show ? 'flex' : 'none';
    });
    document.querySelectorAll('.method-category').forEach(cat => {
        const visible = cat.querySelectorAll('.method-item[style*="flex"]').length;
        cat.style.display = visible ? 'block' : 'none';
    });
}

function selectMethod(method, element) {
    document.querySelectorAll('.method-item.active').forEach(el => el.classList.remove('active'));
    if (element) element.classList.add('active');
    currentMethod = method;

    const info = document.getElementById('method-info');
    const sig = signaturesCache[method] || [];
    const sigStr = sig.map(p => {
        const opt = p.default !== undefined ? '?' : '';
        const def = p.default !== undefined ? ' = ' + esc(String(p.default)) : '';
        return esc(p.name) + opt + ': ' + esc(p.annotation || 'any') + def;
    }).join(', ');
    info.innerHTML = '<span class="method-title">Method: <b>' + esc(method) + '</b></span>' +
        (sigStr ? '<div class="method-sig">(' + sigStr + ')</div>' : '');

    document.getElementById('request-url').style.display = 'none';
    document.getElementById('param-form').style.display = 'block';
    document.getElementById('execute-area').style.display = 'flex';
    document.getElementById('response-area').style.display = 'none';
    document.getElementById('error-area').style.display = 'none';

    buildParamForm(method, sig);

    loadDocs(method);
}

function buildParamForm(method, sig) {
    const container = document.getElementById('param-form');
    container.innerHTML = '';

    if (sig.length === 0) {
        container.innerHTML = '<div class="param-row"><span class="param-hint">Нет параметров</span></div>';
        return;
    }

    for (const p of sig) {
        if (p.name === 'params') continue;
        const row = document.createElement('div');
        row.className = 'param-row';

        const label = document.createElement('label');
        label.className = 'param-label';
        label.textContent = p.name;
        row.appendChild(label);

        const optional = p.default !== undefined;

        const hintText = {
            symbol: 'BTC/USDT, ETH/USDT',
            timeframe: '1m, 5m, 1h, 1d',
            since: '2026-01-01 или ms timestamp',
            limit: 'Число, макс 1000',
            params: '{"key": "value"}',
        }[p.name];

        let input;
        if (p.name === 'timeframe') {
            const sel = document.createElement('select');
            sel.className = 'param-input';
            sel.name = p.name;
            // Для WS-методов ohlcv только поддерживаемые таймфреймы
            const isWsOhlcv = currentMethod === 'fetch_ohlcv_ws';
            const tfs = isWsOhlcv
                ? ['1m', '5m', '15m', '30m', '1M']
                : ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M'];
            const def = isWsOhlcv ? '1m' : (p.default || '1d');
            for (const tf of tfs) {
                const opt = document.createElement('option');
                opt.value = tf;
                opt.textContent = tf;
                if (tf === def) opt.selected = true;
                sel.appendChild(opt);
            }
            input = sel;
        } else if (p.name === 'symbol') {
            const inp = document.createElement('input');
            inp.type = 'text';
            inp.className = 'param-input ' + (optional ? 'param-optional' : 'param-required');
            inp.name = p.name;
            inp.placeholder = 'BTC/USDT';
            inp.value = 'BTC/USDT';
            input = inp;
        } else if (p.name === 'limit') {
            const inp = document.createElement('input');
            inp.type = 'number';
            inp.className = 'param-input param-optional';
            inp.name = p.name;
            inp.placeholder = String(p.default || 100);
            inp.value = String(p.default || 100);
            inp.min = 1;
            input = inp;
        } else if (p.name === 'since') {
            const inp = document.createElement('input');
            inp.type = 'text';
            inp.className = 'param-input param-optional';
            inp.name = p.name;
            inp.placeholder = '2026-01-01 или ms timestamp';
            input = inp;
        } else {
            const inp = document.createElement('input');
            inp.type = 'text';
            inp.className = 'param-input ' + (optional ? 'param-optional' : 'param-required');
            inp.name = p.name;
            inp.placeholder = optional ? String(p.default) : '(required)';
            input = inp;
        }

        row.appendChild(input);
        if (hintText) {
            const hint = document.createElement('span');
            hint.className = 'param-format-hint';
            hint.textContent = hintText;
            row.appendChild(hint);
        }
        container.appendChild(row);
    }

    // Add params textarea (last)
    const row = document.createElement('div');
    row.className = 'param-row';
    const label = document.createElement('label');
    label.className = 'param-label';
    label.textContent = 'params';
    row.appendChild(label);
    const ta = document.createElement('textarea');
    ta.className = 'param-input param-optional';
    ta.name = 'params';
    ta.placeholder = '{"option": "value"}';
    ta.rows = 2;
    row.appendChild(ta);
    const hint = document.createElement('span');
    hint.className = 'param-format-hint';
    hint.textContent = '{"key": "value"}';
    row.appendChild(hint);
    container.appendChild(row);
}

function getParams() {
    const params = {};
    const inputs = document.querySelectorAll('#param-form .param-input');
    for (const inp of inputs) {
        const val = inp.value.trim();
        if (val === '') continue;
        params[inp.name] = val;
    }
    return params;
}

let wsSource = null;

function executeMethod() {
    if (!currentMethod || !currentExchange) return;

    if (currentMethod.endsWith('_ws')) {
        executeWSMethod();
        return;
    }

    const btn = document.getElementById('execute-btn');
    btn.disabled = true;
    btn.textContent = '⏳ ...';

    document.getElementById('response-area').style.display = 'none';
    document.getElementById('error-area').style.display = 'none';
    document.getElementById('timing-info').textContent = '';

    const params = getParams();
    const api_key = document.getElementById('api-key-input').value.trim() || undefined;
    const secret = document.getElementById('secret-input').value.trim() || undefined;
    const passphrase = document.getElementById('passphrase-input').value.trim() || undefined;

    fetch('/ccxt-api/api/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            exchange: currentExchange,
            method: currentMethod,
            params: params,
            api_key: api_key,
            secret: secret,
            passphrase: passphrase,
        }),
    })
        .then(r => r.json())
        .then(data => {
            btn.disabled = false;
            btn.textContent = '▶ Execute';

            if (data.error) {
                showError(data);
                return;
            }

            showResponse(data);
        })
        .catch(err => {
            btn.disabled = false;
            btn.textContent = '▶ Execute';
            showError({ error: err.message });
        });
}

function showResponse(data) {
    // URL
    const urlEl = document.getElementById('request-url');
    if (data.request_url) {
        urlEl.style.display = 'block';
        const methodMatch = data.request_url.match(/https?:\/\/[^/]+(\/api\/[^?]*)/);
        const path = methodMatch ? methodMatch[1] : '';
        const isGet = !data.request_url.includes('POST') && data.response && typeof data.response === 'object';
        urlEl.innerHTML = '<span class="url-method">' + (isGet ? 'GET' : 'POST') + '</span> ' + esc(data.request_url);
    } else {
        urlEl.style.display = 'none';
    }

    // Timing
    const timing = data.timing || {};
    const timingEl = document.getElementById('timing-info');
    let timingHtml = '';
    if (timing.gen_ms != null) {
        const rttCls = 'timing-rtt';
        timingHtml += '<span class="timing-badge timing-gen">🕐 Gen: ' + timing.gen_ms + 'ms</span>';
        timingHtml += '<span class="timing-badge timing-rtt">⚡ RTT: ' + timing.rtt_ms + 'ms</span>';
        timingHtml += '<span class="timing-badge timing-total">∑ ' + timing.total_ms + 'ms</span>';
    }
    timingEl.innerHTML = timingHtml;

    // Response JSON tree + table
    const area = document.getElementById('response-area');
    area.style.display = 'block';
    const viewer = document.getElementById('json-viewer');
    viewer.innerHTML = '';
    if (data.response !== undefined) {
        renderJsonTree(data.response, viewer);
        renderJsonTableIfEnabled(data.response);
    }
}

// ===== OrderBook State Machine =====
const obState = { asks: null, bids: null };
let obReady = false;

function applyBookSide(map, entries) {
    if (!map || !entries) return;
    for (const [price, size] of entries) {
        const sz = parseFloat(size);
        if (sz === 0) map.delete(price);
        else map.set(price, [price, size]);
    }
}

function getTopLevels(map, count, ascending) {
    if (!map) return [];
    return [...map.values()]
        .sort((a, b) => ascending
            ? parseFloat(a[0]) - parseFloat(b[0])
            : parseFloat(b[0]) - parseFloat(a[0]))
        .slice(0, count);
}

function getActiveBucketSize(asks, bids, depth) {
    const sel = document.getElementById('depth-aggr');
    if (!sel) return 0;
    const val = sel.value;
    if (val === '0') return 0;
    if (val === 'auto') return autoBucketSize(asks, bids, depth);
    if (val === 'custom') {
        const inp = document.getElementById('depth-aggr-custom');
        const v = inp ? parseFloat(inp.value) : 0;
        return (v > 0) ? v : 0;
    }
    return parseFloat(val) || 0;
}

function volStep(val, min, max) {
    const range = max - min || 1;
    const ratio = (val - min) / range;
    if (ratio <= 0.2) return 'depth-step-1';
    if (ratio <= 0.4) return 'depth-step-2';
    if (ratio <= 0.6) return 'depth-step-3';
    if (ratio <= 0.8) return 'depth-step-4';
    return 'depth-step-5';
}

// ===== WS State =====
let wsDataCount = 0;
let wsPaused = false;
let wsLastMsg = null;
const sparkBuf = {};
const prevValues = {};

function bufPush(field, val) {
    const n = parseFloat(val);
    if (isNaN(n)) return;
    if (!sparkBuf[field]) sparkBuf[field] = [];
    sparkBuf[field].push(n);
    if (sparkBuf[field].length > 10) sparkBuf[field].shift();
}

function sparkSVG(field, width) {
    const vals = sparkBuf[field] || [];
    if (vals.length < 2) return '';
    const min = Math.min(...vals), max = Math.max(...vals);
    const rng = max - min || 1;
    const w = 60, h = 14;
    const pts = vals.map((v, i) => `${i * (w / (vals.length - 1))},${h - ((v - min) / rng) * (h - 2) - 1}`).join(' ');
    const color = vals[vals.length - 1] >= vals[0] ? '#16a34a' : '#dc2626';
    const widthAttr = width || '100%';
    return `<svg class="sparkline" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" style="width:${widthAttr};max-width:${w}px">` +
        `<polyline fill="none" stroke="${color}" stroke-width="1.2" points="${pts}"/></svg>`;
}

function arrow(val, field) {
    const key = field + '_prev';
    const prev = prevValues[key];
    prevValues[key] = val;
    if (prev === undefined) return '<span class="arrow-flat">→</span>';
    const nv = parseFloat(val), pv = parseFloat(prev);
    if (isNaN(nv) || isNaN(pv)) return '';
    if (nv > pv) return '<span class="arrow-up">↑</span>';
    if (nv < pv) return '<span class="arrow-down">↓</span>';
    return '<span class="arrow-flat">→</span>';
}

function fmt(v) {
    if (v === undefined || v === null) return '—';
    const n = parseFloat(v);
    if (isNaN(n)) return esc(String(v));
    if (Math.abs(n) >= 1000) return n.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    if (Math.abs(n) >= 1) return n.toFixed(4);
    return n.toFixed(6);
}

function fmtPrice(v) {
    if (v === undefined || v === null) return '—';
    const n = parseFloat(v);
    if (isNaN(n)) return esc(String(v));
    return n.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
}

function flashCell(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.remove('cell-updated');
    void el.offsetWidth;
    el.classList.add('cell-updated');
}

function flashCellValue(cellId) {
    const el = document.getElementById(cellId);
    if (!el) return;
    const valueEl = el.querySelector('.cell-value');
    if (!valueEl) return;
    valueEl.classList.remove('cell-updated');
    void valueEl.offsetWidth;
    valueEl.classList.add('cell-updated');
}

function setCell(id, val, field) {
    const el = document.getElementById(id);
    if (!el) return;
    const old = el.dataset.val;
    if (old === String(val)) return;
    el.dataset.val = val;
    bufPush(field || id, val);
    el.innerHTML = fmtPrice(val) + ' ' + arrow(val, field || id) + sparkSVG(field || id);
    flashCell(id);
}

function setCellPrice(id, val, field) {
    const el = document.getElementById(id);
    if (!el) return;
    const old = el.dataset.val;
    if (old === String(val)) return;
    el.dataset.val = val;
    bufPush(field || id, val);
    el.innerHTML =
        '<div class="ob-cell-content">' +
            '<div id="' + id + '-i" class="ob-indicator">' +
                arrow(val, field || id) + sparkSVG(field || id, '100%') +
            '</div>' +
            '<div id="' + id + '-v" class="ob-value">' +
                '<span class="cell-value">' + fmtPrice(val) + '</span>' +
            '</div>' +
        '</div>';
}

function setCellVol(id, val, field) {
    const el = document.getElementById(id);
    if (!el) return;
    const old = el.dataset.val;
    if (old === String(val)) return;
    el.dataset.val = val;
    bufPush(field || id, val);
    el.innerHTML =
        '<div class="ob-cell-content">' +
            '<div id="' + id + '-v" class="ob-value flash-on-update">' +
                '<span class="cell-value">' + fmt(val) + '</span>' +
            '</div>' +
            '<div id="' + id + '-i" class="ob-indicator">' +
                arrow(val, field || id) + sparkSVG(field || id, '100%') +
            '</div>' +
        '</div>';
    flashCellValue(id);
}

function setCellSpan(id, html) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = html;
    flashCell(id);
}

// ===== Depth Control =====
let depthFollowState = null;
let pinnedTimer = null;
let pinnedBase = null;

function onDepthModeChange() {
    depthFollowState = null;
    pinnedBase = null;
    if (pinnedTimer) { clearTimeout(pinnedTimer); pinnedTimer = null; }
}

function onDepthChange() {
    if (!wsSource) return;
    const params = getParams();
    params.limit = parseInt(document.getElementById('depth-select').value) || 5;
    reconnectWS(params);
}

function onDepthStyleChange() {
    if (wsSource && currentMethod === 'fetch_order_book_ws' && obReady) {
        const depth = parseInt(document.getElementById('depth-select').value) || 5;
        const asks = getTopLevels(obState.asks, depth, true);
        const bids = getTopLevels(obState.bids, depth, false);
        renderDepthVis(asks, bids, depth);
    }
}

function reconnectWS(newParams) {
    if (wsSource) { wsSource.close(); wsSource = null; }
    wsDataCount = 0;
    depthFollowState = null;
    pinnedBase = null;
    obState.asks = null;
    obState.bids = null;
    obReady = false;
    if (pinnedTimer) { clearTimeout(pinnedTimer); pinnedTimer = null; }
    document.getElementById('ws-summary').style.display = 'none';
    document.getElementById('response-area').style.display = 'none';
    startWSStream(newParams);
}

// ===== WS Execution =====
function executeWSMethod() {
    const params = getParams();
    if (wsSource) { wsSource.close(); wsSource = null; }
    wsDataCount = 0;
    startWSStream(params);
}

function startWSStream(params) {
    const btn = document.getElementById('execute-btn');
    btn.disabled = true;
    btn.textContent = '▶ WS';

    document.getElementById('ws-summary').style.display = 'none';
    document.getElementById('response-area').style.display = 'none';
    document.getElementById('error-area').style.display = 'none';
    document.getElementById('timing-info').textContent = '';

    const url = '/ccxt-api/api/ws-stream?method=' + encodeURIComponent(currentMethod)
              + '&params=' + encodeURIComponent(JSON.stringify(params));

    document.getElementById('live-indicator').style.display = 'inline';
    document.getElementById('live-indicator').textContent = '🔄 Connecting...';
    document.getElementById('stop-btn').style.display = 'inline-block';
    document.getElementById('pause-btn').style.display = 'inline-block';
    document.getElementById('pause-btn').textContent = '⏸ Pause';
    document.getElementById('pause-btn').className = 'pause-btn';
    wsPaused = false;
    wsLastMsg = null;

    if (currentMethod === 'fetch_order_book_ws') {
        document.getElementById('depth-area').style.display = 'inline-flex';
    }

    wsSource = new EventSource(url);

    wsSource.onmessage = function(event) {
        let data;
        try { data = JSON.parse(event.data); } catch(e) { return; }

        if (data.type === 'error') {
            document.getElementById('error-area').textContent = '❌ ' + (data.message || 'WS error');
            document.getElementById('error-area').style.display = 'block';
            stopWS();
            return;
        }

        if (data.type === 'connected') {
            document.getElementById('live-indicator').textContent = '🟢 LIVE';
            document.getElementById('live-indicator').style.color = '#16a34a';
            btn.disabled = false;
            btn.textContent = '▶ Execute';
            return;
        }

        if (data.type === 'timeout') {
            document.getElementById('live-indicator').textContent = '⏸ Timeout';
            stopWS();
            return;
        }

        if (data.type === 'message' && data.data) {
            const msg = data.data;
            if (wsPaused) { wsLastMsg = msg; return; }

            const area = document.getElementById('response-area');
            const viewer = document.getElementById('json-viewer');

            // Только data-сообщения (не event: subscribe confirmation)
            const hasData = msg.action === 'snapshot' || msg.action === 'update' ||
                msg.action === 'decrement' || msg.action === 'increment' ||
                msg.data || msg.bids || msg.asks;

            if (hasData) {
                if (wsDataCount === 0) {
                    area.style.display = 'block';
                    document.getElementById('ws-summary').style.display = 'block';
                    renderWSTable(currentMethod, msg);
                    renderJsonTree(msg, viewer);
                    renderJsonTableIfEnabled(msg);
                    expandAllNodes();
                } else {
                    updateWSTable(currentMethod, msg);
                    renderJsonTree(msg, viewer);
                    renderJsonTableIfEnabled(msg);
                    expandAllNodes();
                }
                wsDataCount++;
            }
        }
    };

    wsSource.onerror = function() {
        document.getElementById('live-indicator').textContent = '🔴 Disconnected';
        document.getElementById('live-indicator').style.color = '#dc2626';
        document.getElementById('stop-btn').style.display = 'none';
        document.getElementById('pause-btn').style.display = 'none';
        document.getElementById('depth-area').style.display = 'none';
        if (wsSource) { wsSource.close(); wsSource = null; }
    };
}

function stopWS() {
    if (wsSource) { wsSource.close(); wsSource = null; }
    document.getElementById('live-indicator').textContent = '🔴 Stopped';
    document.getElementById('live-indicator').style.color = '#dc2626';
    document.getElementById('stop-btn').style.display = 'none';
    document.getElementById('pause-btn').style.display = 'none';
    document.getElementById('depth-area').style.display = 'none';
    document.getElementById('ws-summary').style.display = 'none';
    document.getElementById('ws-summary-table').innerHTML = '';
    document.getElementById('depth-vis').style.display = 'none';
    document.getElementById('depth-vis-body').innerHTML = '';
    wsDataCount = 0;
    obState.asks = null;
    obState.bids = null;
    obReady = false;
    if (pinnedTimer) { clearTimeout(pinnedTimer); pinnedTimer = null; }
    depthFollowState = null;
    setTimeout(() => { document.getElementById('live-indicator').style.display = 'none'; }, 2000);
}

function toggleOBTable(el) {
    const icon = el.querySelector('.ob-toggle-icon');
    const body = el.nextElementSibling;
    if (body) {
        body.classList.toggle('ob-table-collapsed');
        icon.textContent = body.classList.contains('ob-table-collapsed') ? '▶' : '▼';
    }
}

function expandAllNodes() {
    document.querySelectorAll('.json-children').forEach(el => el.classList.add('expanded'));
    document.querySelectorAll('.json-toggle').forEach(el => el.classList.add('expanded'));
    // Ensure sections are visible when checked
    const treeCb = document.getElementById('tree-toggle');
    const tableCb = document.getElementById('table-view');
    if (treeCb && treeCb.checked) {
        const sec = document.getElementById('json-tree-section');
        if (sec) sec.style.display = 'block';
    }
    if (tableCb && tableCb.checked) {
        const sec = document.getElementById('json-table-section');
        if (sec) sec.style.display = 'block';
    }
}

function toggleCollapse(bodyId) {
    const body = document.getElementById(bodyId);
    if (!body) return;
    const icon = body.parentElement.querySelector('.collapse-icon');
    body.classList.toggle('collapsed');
    if (icon) icon.textContent = body.classList.contains('collapsed') ? '▶' : '▼';
}

function toggleJsonTree() {
    const sec = document.getElementById('json-tree-section');
    const cb = document.getElementById('tree-toggle');
    if (sec && cb) {
        const panel = sec.closest('.json-debug-panel') || sec;
        panel.style.display = cb.checked ? '' : 'none';
    }
}

function toggleJsonView() {
    const sec = document.getElementById('json-table-section');
    const cb = document.getElementById('table-view');
    if (sec && cb) {
        const panel = sec.closest('.json-debug-panel') || sec;
        panel.style.display = cb.checked ? '' : 'none';
    }
}

function hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1,3), 16);
    const g = parseInt(hex.slice(3,5), 16);
    const b = parseInt(hex.slice(5,7), 16);
    return `rgba(${r},${g},${b},${alpha})`;
}

function onColorChange() {
    const bid = document.getElementById('color-bid').value;
    const ask = document.getElementById('color-ask').value;
    const bg = document.getElementById('color-bg')?.value || '#f0f4ff';
    document.documentElement.style.setProperty('--depth-bid-color', bid);
    document.documentElement.style.setProperty('--depth-ask-color', ask);
    document.documentElement.style.setProperty('--depth-bid-bg', hexToRgba(bid, 0.15));
    document.documentElement.style.setProperty('--depth-ask-bg', hexToRgba(ask, 0.15));
    document.documentElement.style.setProperty('--depth-bg', bg);
    try { localStorage.setItem('depth-bid-color', bid); } catch(e) {}
    try { localStorage.setItem('depth-ask-color', ask); } catch(e) {}
    try { localStorage.setItem('depth-bg', bg); } catch(e) {}
}

function onFlashTimeChange() {
    const volEl = document.getElementById('flash-vol-ms');
    const cumulEl = document.getElementById('flash-cumul-ms');
    if (volEl) {
        const ms = parseInt(volEl.value) || 0;
        const s = (ms / 1000).toFixed(2) + 's';
        document.documentElement.style.setProperty('--flash-vol-duration', s);
        try { localStorage.setItem('flash-vol-ms', String(ms)); } catch(e) {}
    }
    if (cumulEl) {
        const ms = parseInt(cumulEl.value) || 0;
        const s = (ms / 1000).toFixed(2) + 's';
        document.documentElement.style.setProperty('--flash-cumul-duration', s);
        try { localStorage.setItem('flash-cumul-ms', String(ms)); } catch(e) {}
    }
}

// ===== WS Table Renderers =====
function renderWSTable(method, msg) {
    const renderer = WS_RENDERERS[method];
    if (!renderer) return;
    renderer(msg, false);
}

function updateWSTable(method, msg) {
    const renderer = WS_RENDERERS[method];
    if (!renderer) return;
    renderer(msg, true);
}

const WS_RENDERERS = {
    fetch_ticker_ws: renderTickerTable,
    fetch_order_book_ws: renderOrderBookTable,
    fetch_trades_ws: renderTradesTable,
    fetch_ohlcv_ws: renderOHLCVTable,
    fetch_tickers_ws: renderTickersTable,
};

function renderTickerTable(msg, isUpdate) {
    setWSSummaryHeader('renderTickerTable');
    const d = msg.data && msg.data[0];
    if (!d) return;
    if (isUpdate) {
        setCell('ws-ticker-last', d.lastPr, 'ticker_last');
        setCell('ws-ticker-chg', d.change24h, 'ticker_chg');
        setCell('ws-ticker-high', d.high24h, 'ticker_high');
        setCell('ws-ticker-low', d.low24h, 'ticker_low');
        setCell('ws-ticker-ask', d.bestAsk, 'ticker_ask');
        setCell('ws-ticker-bid', d.bestBid, 'ticker_bid');
        const spread = parseFloat(d.bestAsk) - parseFloat(d.bestBid);
        setCell('ws-ticker-spread', isNaN(spread) ? '—' : spread.toFixed(2), 'ticker_spread');
        setCell('ws-ticker-vol', d.baseVolume || d.quoteVolume, 'ticker_vol');
        return;
    }
    const spread = parseFloat(d.bestAsk) - parseFloat(d.bestBid);
    const container = document.getElementById('ws-summary-table');
    container.innerHTML = `<table>
        <tr>
            <td><div class="cell-label">Last Price</div><div class="cell-value" id="ws-ticker-last" data-val="">${fmtPrice(d.lastPr)}</div><div class="cell-sub">${arrow(d.lastPr, 'ticker_last')}${sparkSVG('ticker_last')}</div></td>
            <td><div class="cell-label">Change 24h</div><div class="cell-value" id="ws-ticker-chg" data-val="">${d.change24h || '—'}%</div><div class="cell-sub">${arrow(d.change24h, 'ticker_chg')}${sparkSVG('ticker_chg')}</div></td>
            <td><div class="cell-label">High 24h</div><div class="cell-value" id="ws-ticker-high" data-val="">${fmtPrice(d.high24h)}</div></td>
            <td><div class="cell-label">Low 24h</div><div class="cell-value" id="ws-ticker-low" data-val="">${fmtPrice(d.low24h)}</div></td>
        </tr>
        <tr>
            <td><div class="cell-label">Best Ask</div><div class="cell-value" id="ws-ticker-ask" data-val="">${fmtPrice(d.bestAsk)}</div></td>
            <td><div class="cell-label">Best Bid</div><div class="cell-value" id="ws-ticker-bid" data-val="">${fmtPrice(d.bestBid)}</div></td>
            <td><div class="cell-label">Spread</div><div class="cell-value" id="ws-ticker-spread" data-val="">${isNaN(spread) ? '—' : spread.toFixed(2)}</div></td>
            <td><div class="cell-label">Volume</div><div class="cell-value" id="ws-ticker-vol" data-val="">${fmtPrice(d.baseVolume)}</div></td>
        </tr>
    </table>`;
    bufPush('ticker_last', d.lastPr);
    bufPush('ticker_chg', d.change24h);
    bufPush('ticker_high', d.high24h);
    bufPush('ticker_low', d.low24h);
    bufPush('ticker_ask', d.bestAsk);
    bufPush('ticker_bid', d.bestBid);
    bufPush('ticker_vol', d.baseVolume);
}

function computeCumul(arr) {
    let cum = 0;
    for (const e of arr) {
        cum += parseFloat(e[1]);
        e[2] = cum.toFixed(4);
    }
}

function renderOrderBookTable(msg, isUpdate) {
    setWSSummaryHeader('renderOrderBookTable');
    const d = msg.data && msg.data[0];
    if (!d) return;
    const depth = parseInt(document.getElementById('depth-select').value) || 5;

    if (d.asks || d.bids) {
        if (!obReady) {
            if (d.asks) obState.asks = new Map(d.asks.map(e => [e[0], e]));
            if (d.bids) obState.bids = new Map(d.bids.map(e => [e[0], e]));
            obReady = true;
        } else {
            if (d.asks) applyBookSide(obState.asks, d.asks);
            if (d.bids) applyBookSide(obState.bids, d.bids);
        }
    }
    if (!obReady) return;

    const rawAsks = getTopLevels(obState.asks, depth * 10, true);
    const rawBids = getTopLevels(obState.bids, depth * 10, false);
    const bucketSize = getActiveBucketSize(rawAsks, rawBids, depth);
    const isAggr = bucketSize > 0;

    const asks = isAggr ? aggregateLevels(rawAsks, bucketSize, false) : getTopLevels(obState.asks, depth, true);
    const bids = isAggr ? aggregateLevels(rawBids, bucketSize, true) : getTopLevels(obState.bids, depth, false);
    const dispDepth = Math.max(asks.length, bids.length);

    if (isAggr) {
        computeCumul(asks);
        computeCumul(bids);
    }

    if (!isUpdate) {
        let html = '<table class="orderbook-table"><thead><tr><th>#</th><th>Bid Price</th><th>Bid Vol</th><th>Bid Cumul</th>' +
            '<th></th><th>Ask Price</th><th>Ask Vol</th><th>Ask Cumul</th>' +
            '<th>#</th></tr></thead><tbody id="ob-tbody">';
        for (let i = 0; i < dispDepth; i++) {
            const b = bids[i] || [];
            const a = asks[i] || [];
            const bidCumul = isAggr && b[2] ? b[2] : '—';
            const askCumul = isAggr && a[2] ? a[2] : '—';
            html += `<tr class="ob-bid-row">
                <td>${i + 1}</td>
                ${b[0] ? `<td class="ob-price-cell" id="ob-bid-p-${i}" data-val="">
                    <div class="ob-cell-content">
                        <div id="ob-bid-p-${i}-i" class="ob-indicator">${arrow(b[0], 'ob_bid_p_'+i)}${sparkSVG('ob_bid_p_'+i, '100%')}</div>
                        <div id="ob-bid-p-${i}-v" class="ob-value"><span class="cell-value">${fmtPrice(b[0])}</span></div>
                    </div>
                </td>` : `<td class="ob-price-cell" id="ob-bid-p-${i}" data-val="">—</td>`}
                ${b[1] ? `<td class="ob-vol-cell" id="ob-bid-v-${i}" data-val="">
                    <div class="ob-cell-content">
                        <div id="ob-bid-v-${i}-v" class="ob-value flash-on-update"><span class="cell-value">${fmt(b[1])}</span></div>
                        <div id="ob-bid-v-${i}-i" class="ob-indicator">${arrow(b[1], 'ob_bid_v_'+i)}${sparkSVG('ob_bid_v_'+i, '100%')}</div>
                    </div>
                </td>` : `<td class="ob-vol-cell" id="ob-bid-v-${i}" data-val="">—</td>`}
                <td class="ob-cumul-cell" id="ob-bid-c-${i}" data-val="">${bidCumul}</td>
                <td style="width:16px;color:var(--text-muted)">│</td>
                ${a[0] ? `<td class="ob-price-cell" id="ob-ask-p-${i}" data-val="">
                    <div class="ob-cell-content">
                        <div id="ob-ask-p-${i}-i" class="ob-indicator">${arrow(a[0], 'ob_ask_p_'+i)}${sparkSVG('ob_ask_p_'+i, '100%')}</div>
                        <div id="ob-ask-p-${i}-v" class="ob-value"><span class="cell-value">${fmtPrice(a[0])}</span></div>
                    </div>
                </td>` : `<td class="ob-price-cell" id="ob-ask-p-${i}" data-val="">—</td>`}
                ${a[1] ? `<td class="ob-vol-cell" id="ob-ask-v-${i}" data-val="">
                    <div class="ob-cell-content">
                        <div id="ob-ask-v-${i}-v" class="ob-value flash-on-update"><span class="cell-value">${fmt(a[1])}</span></div>
                        <div id="ob-ask-v-${i}-i" class="ob-indicator">${arrow(a[1], 'ob_ask_v_'+i)}${sparkSVG('ob_ask_v_'+i, '100%')}</div>
                    </div>
                </td>` : `<td class="ob-vol-cell" id="ob-ask-v-${i}" data-val="">—</td>`}
                <td class="ob-cumul-cell" id="ob-ask-c-${i}" data-val="">${askCumul}</td>
                <td>${i + 1}</td>
            </tr>`;
        }
        const bestAsk = asks[0] ? parseFloat(asks[0][0]) : 0;
        const bestBid = bids[0] ? parseFloat(bids[0][0]) : 0;
        let sprdHtml = '';
        if (bestAsk && bestBid) {
            const sprd = bestAsk - bestBid;
            const sprdPct = (sprd / bestBid * 100);
            sprdHtml = `<tr><td colspan="9" style="text-align:center;font-size:10px;color:var(--text-muted)" id="ob-spread">Spread: ${sprd.toFixed(2)} (${sprdPct.toFixed(3)}%)</td></tr>`;
        }
        html += sprdHtml + '</tbody></table>';
        document.getElementById('ws-summary-table').innerHTML =
            '<div class="ob-table-wrap"><div class="ob-table-toggle" onclick="toggleOBTable(this)">' +
            '<span class="ob-toggle-icon">▼</span> OB Table' +
            '<span class="code-path"> OB Table — renderOrderBookTable ↦ ws-summary-table ← routes/ccxt_api.py:ws-stream</span></div>' +
            '<div class="ob-table-body">' + html + '</div></div>';
        document.getElementById('depth-vis').style.display = 'block';
        document.getElementById('depth-vis-body').classList.remove('collapsed');
    } else {
        // Skip cell updates if OB table is collapsed
        const obBody = document.querySelector('.ob-table-body');
        if (obBody && obBody.classList.contains('ob-table-collapsed')) {
            // Only update spread
            const bestAsk = asks[0] ? parseFloat(asks[0][0]) : 0;
            const bestBid = bids[0] ? parseFloat(bids[0][0]) : 0;
            if (bestAsk && bestBid) {
                const sprd = bestAsk - bestBid;
                const sprdPct = (sprd / bestBid * 100);
                setCellSpan('ob-spread', 'Spread: ' + sprd.toFixed(2) + ' (' + sprdPct.toFixed(3) + '%)');
            }
            renderDepthVis(asks, bids, dispDepth);
            return;
        }
        for (let i = 0; i < dispDepth; i++) {
            if (bids[i]) {
                setCellPrice('ob-bid-p-' + i, bids[i][0], 'ob_bid_p_' + i);
                setCellVol('ob-bid-v-' + i, bids[i][1], 'ob_bid_v_' + i);
                if (isAggr && bids[i][2]) setCellSpan('ob-bid-c-' + i, bids[i][2]);
            }
            if (asks[i]) {
                setCellPrice('ob-ask-p-' + i, asks[i][0], 'ob_ask_p_' + i);
                setCellVol('ob-ask-v-' + i, asks[i][1], 'ob_ask_v_' + i);
                if (isAggr && asks[i][2]) setCellSpan('ob-ask-c-' + i, asks[i][2]);
            }
        }
        const bestAsk = asks[0] ? parseFloat(asks[0][0]) : 0;
        const bestBid = bids[0] ? parseFloat(bids[0][0]) : 0;
        if (bestAsk && bestBid) {
            const sprd = bestAsk - bestBid;
            const sprdPct = (sprd / bestBid * 100);
            setCellSpan('ob-spread', 'Spread: ' + sprd.toFixed(2) + ' (' + sprdPct.toFixed(3) + '%)');
        }
    }

    renderDepthVis(asks, bids, dispDepth);
}

// ===== Depth Visualization =====
function renderDepthVis(asks, bids, depth) {
    const style = document.getElementById('depth-style')?.value || 'split';
    const labelEl = document.getElementById('depth-vis-label');
    const cap = style === 'stacked' ? 'Stacked' : 'Split';
    if (labelEl) labelEl.textContent = 'Depth Visualization — renderDepth' + cap + ' ↦ depth-vis ← api/bitget_ws.py:resolve_channel';
    const revAsks = [...(asks || [])].reverse();
    if (style === 'stacked') {
        renderDepthStacked(revAsks, bids, depth);
    } else {
        renderDepthSplit(revAsks, bids, depth);
    }
}

function toggleDepthVis(toggleEl) {
    const body = document.getElementById('depth-vis-body');
    const icon = toggleEl.querySelector('.depth-vis-icon');
    if (body) {
        body.classList.toggle('collapsed');
        icon.textContent = body.classList.contains('collapsed') ? '▶' : '▼';
    }
}

function setWSSummaryHeader(jsFn) {
    const el = document.getElementById('ws-summary-header');
    if (el) el.textContent = currentMethod + ' → ' + jsFn + ' → ws-summary-table → routes/ccxt_api.py:ws-stream';
}

function toggleLegend() {
    const el = document.getElementById('code-legend');
    if (el) el.style.display = el.style.display === 'none' ? 'block' : 'none';
}

function togglePause() {
    wsPaused = !wsPaused;
    const btn = document.getElementById('pause-btn');
    if (wsPaused) {
        btn.textContent = '▶ Resume';
        btn.className = 'resume-btn';
    } else {
        btn.textContent = '⏸ Pause';
        btn.className = 'pause-btn';
        if (wsLastMsg) {
            renderWSTable(currentMethod, wsLastMsg);
            const viewer = document.getElementById('json-viewer');
            renderJsonTree(wsLastMsg, viewer);
            renderJsonTableIfEnabled(wsLastMsg);
            expandAllNodes();
        }
    }
}

function calcDepthRange(asks, bids) {
    let min = Infinity, max = -Infinity;
    for (const arr of [asks, bids]) {
        for (const e of arr) {
            if (e) { const v = parseFloat(e[1]); if (v < min) min = v; if (v > max) max = v; }
        }
    }
    return { minVol: min === Infinity ? 0 : min, maxVol: max === -Infinity ? 1 : max };
}

// ===== Aggregation =====
function autoBucketSize(asks, bids, depth) {
    const top = asks[depth - 1] ? parseFloat(asks[depth - 1][0]) : 0;
    const bottom = bids[depth - 1] ? parseFloat(bids[depth - 1][0]) : 0;
    const bestAsk = asks[0] ? parseFloat(asks[0][0]) : 0;
    const bestBid = asks.length && bids.length ? parseFloat(bids[0][0]) : 0;
    const range = top - bottom || (bestAsk - bestBid) * depth || parseFloat(asks[depth-1][0]) - parseFloat(bids[depth-1][0]) || 0.1;

    const raw = range / Math.min(15, depth);
    if (raw <= 0) return 0;

    const mag = Math.pow(10, Math.floor(Math.log10(raw)));
    const norm = raw / mag;
    if (norm <= 1.5) return Math.max(0.001, 1 * mag);
    if (norm <= 3.5) return Math.max(0.001, 2 * mag);
    if (norm <= 7.5) return Math.max(0.001, 5 * mag);
    return Math.max(0.001, 10 * mag);
}

function aggregateLevels(entries, bucketSize, descending) {
    if (!bucketSize || bucketSize <= 0) return entries;
    const buckets = new Map();
    for (const [price, size] of entries) {
        const p = parseFloat(price);
        const key = Math.floor(p / bucketSize);
        if (buckets.has(key)) {
            const existing = buckets.get(key);
            existing[1] = (parseFloat(existing[1]) + parseFloat(size)).toFixed(8);
        } else {
            buckets.set(key, [String(key * bucketSize), size]);
        }
    }
    return [...buckets.values()].sort((a, b) =>
        descending
            ? parseFloat(b[0]) - parseFloat(a[0])
            : parseFloat(a[0]) - parseFloat(b[0])
    );
}

function getActiveBucketSize(asks, bids, depth) {
    const sel = document.getElementById('depth-aggr');
    if (!sel) return 0;
    const val = sel.value;
    if (val === '0') return 0;
    if (val === 'auto') return autoBucketSize(asks, bids, depth);
    if (val === 'custom') {
        const inp = document.getElementById('depth-aggr-custom');
        const v = inp ? parseFloat(inp.value) : 0;
        return (v > 0) ? v : 0;
    }
    return parseFloat(val) || 0;
}

function onAggrChange() {
    const sel = document.getElementById('depth-aggr');
    const inp = document.getElementById('depth-aggr-custom');
    if (sel && inp) {
        inp.style.display = sel.value === 'custom' ? 'inline-block' : 'none';
    }
    if (wsSource && currentMethod === 'fetch_order_book_ws' && obReady) {
        const depth = parseInt(document.getElementById('depth-select').value) || 5;
        const asks = getTopLevels(obState.asks, depth * 10, true);
        const bids = getTopLevels(obState.bids, depth * 10, false);
        const bucketSize = getActiveBucketSize(asks, bids, depth);
        const aggrAsks = bucketSize > 0 ? aggregateLevels(asks, bucketSize, false) : getTopLevels(obState.asks, depth, true);
        const aggrBids = bucketSize > 0 ? aggregateLevels(bids, bucketSize, true) : getTopLevels(obState.bids, depth, false);
        const effectiveDepth = bucketSize > 0 ? Math.max(aggrAsks.length, aggrBids.length) : depth;
        renderDepthVis(aggrAsks, aggrBids, effectiveDepth);
    }
}

function renderDepthSplit(asks, bids, depth) {
    const {minVol, maxVol} = calcDepthRange(asks, bids, depth);
    const range = maxVol - minVol || 1;
    const bestAsk = asks[0] ? parseFloat(asks[0][0]) : 0;
    const bestBid = bids[0] ? parseFloat(bids[0][0]) : 0;

    let html = '';
    for (let i = 0; i < depth; i++) {
        const b = bids[i], a = asks[i];
        const bv = b ? parseFloat(b[1]) : 0;
        const av = a ? parseFloat(a[1]) : 0;
        const bw = bv > 0 ? (bv - minVol) / range * 50 : 0;
        const aw = av > 0 ? (av - minVol) / range * 50 : 0;
        const bStep = bv > 0 ? volStep(bv, minVol, maxVol) : '';
        const aStep = av > 0 ? volStep(av, minVol, maxVol) : '';
        const bidVolLabel = b && bw > 20 ? fmt(b[1]) : '';
        const askVolLabel = a && aw > 20 ? fmt(a[1]) : '';
        const label = (b ? fmtPrice(b[0]) : '') + (b && a ? ' │ ' : '') + (a ? fmtPrice(a[0]) : '');

        html += '<div class="depth-row">' +
            '<div class="depth-bar-side left"><div class="depth-bar-fill bid ' + bStep + '" style="width:' + bw + '%">' + bidVolLabel + '</div></div>' +
            '<div class="depth-price-center">' + label + '</div>' +
            '<div class="depth-bar-side right"><div class="depth-bar-fill ask ' + aStep + '" style="width:' + aw + '%">' + askVolLabel + '</div></div>' +
            '</div>';
    }
    if (bestAsk && bestBid) {
        const sprd = bestAsk - bestBid;
        const sprdPct = (sprd / bestBid * 100);
        html += '<div class="depth-spread">Spread: ' + sprd.toFixed(2) + ' (' + sprdPct.toFixed(3) + '%)</div>';
    }
    document.getElementById('depth-vis-body').innerHTML = html;
}

function renderDepthStacked(asks, bids, depth) {
    const {minVol, maxVol} = calcDepthRange(asks, bids, depth);
    const range = maxVol - minVol || 1;
    const bestAsk = asks[0] ? parseFloat(asks[0][0]) : 0;
    const bestBid = bids[0] ? parseFloat(bids[0][0]) : 0;
    // Interleave: asks descending, divider, bids descending
    const rows = [];
    for (let i = 0; i < depth; i++) {
        if (asks[i]) rows.push({type: 'ask', price: asks[i][0], vol: parseFloat(asks[i][1]), entry: asks[i]});
    }
    if (bestAsk && bestBid) {
        const sprd = bestAsk - bestBid;
        const sprdPct = (sprd / bestBid * 100);
        rows.push({type: 'spread', label: 'Spread: ' + sprd.toFixed(2) + ' (' + sprdPct.toFixed(3) + '%)'});
    }
    for (let i = 0; i < depth; i++) {
        if (bids[i]) rows.push({type: 'bid', price: bids[i][0], vol: parseFloat(bids[i][1]), entry: bids[i]});
    }

    let html = '';
    for (const r of rows) {
        if (r.type === 'spread') {
            html += '<div class="depth-stacked-divider">' + r.label + '</div>';
            continue;
        }
        const w = r.vol > 0 ? (r.vol - minVol) / range * 50 : 0;
        const step = r.vol > 0 ? volStep(r.vol, minVol, maxVol) : '';
        const cls = r.type === 'ask' ? 'ask' : 'bid';
        const label = r.type === 'ask' ? 'Ask' : 'Bid';
        html += '<div class="depth-stacked-row">' +
            '<div class="depth-stacked-vol ' + cls + ' ' + step + '">' + fmtPrice(r.vol) + '</div>' +
            '<div class="depth-stacked-price">' + fmtPrice(r.price) + '</div>' +
            '<div class="depth-stacked-bar"><div class="depth-bar-fill ' + cls + ' ' + step + '" style="width:' + w + '%"></div></div>' +
            '</div>';
    }
    document.getElementById('depth-vis-body').innerHTML = html;
}

function renderTradesTable(msg, isUpdate) {
    setWSSummaryHeader('renderTradesTable');
    const trades = msg.data || [];
    if (!trades.length) return;

    if (isUpdate) {
        // Add new trades at top, keep max 10
        const table = document.querySelector('#ws-summary-table table');
        if (!table) return;
        const tbody = table.querySelector('tbody') || table;
        for (const t of trades) {
            const side = (t.side || '').toLowerCase();
            const cls = side === 'buy' ? 'trade-buy' : 'trade-sell';
            const arrow = side === 'buy' ? '🟢' : '🔴';
            const time = t.ts ? new Date(parseInt(t.ts)).toLocaleTimeString() : '—';
            const row = document.createElement('tr');
            row.style.animation = 'ws-flash 1s ease-out';
            row.innerHTML = `<td>${time}</td><td class="${cls}">${fmtPrice(t.price)}</td><td>${fmt(t.size)}</td><td class="${cls}">${arrow} ${side}</td>`;
            if (tbody.firstChild) {
                tbody.insertBefore(row, tbody.firstChild);
            } else {
                tbody.appendChild(row);
            }
            // Remove extras
            while (tbody.children.length > 10) {
                tbody.removeChild(tbody.lastChild);
            }
        }
        return;
    }

    let html = '<table class="trades-table"><thead><tr><th>Time</th><th>Price</th><th>Size</th><th>Side</th></tr></thead><tbody>';
    for (const t of trades.slice(-10).reverse()) {
        const side = (t.side || '').toLowerCase();
        const cls = side === 'buy' ? 'trade-buy' : 'trade-sell';
        const arrow = side === 'buy' ? '🟢' : '🔴';
        const time = t.ts ? new Date(parseInt(t.ts)).toLocaleTimeString() : '—';
        html += `<tr><td>${time}</td><td class="${cls}">${fmtPrice(t.price)}</td><td>${fmt(t.size)}</td><td class="${cls}">${arrow} ${side}</td></tr>`;
    }
    html += '</tbody></table>';
    document.getElementById('ws-summary-table').innerHTML = html;
}

function renderOHLCVTable(msg, isUpdate) {
    setWSSummaryHeader('renderOHLCVTable');
    const d = msg.data && msg.data[0];
    if (!d) return;
    if (isUpdate) {
        setCell('ohlcv-open', d.o, 'ohlcv_o');
        setCell('ohlcv-high', d.h, 'ohlcv_h');
        setCell('ohlcv-low', d.l, 'ohlcv_l');
        setCell('ohlcv-close', d.c, 'ohlcv_c');
        setCell('ohlcv-vol', d.vol, 'ohlcv_vol');
        return;
    }
    const container = document.getElementById('ws-summary-table');
    container.innerHTML = `<table>
        <tr>
            <td><div class="cell-label">Open</div><div class="cell-value" id="ohlcv-open" data-val="">${fmtPrice(d.o)}</div><div class="cell-sub">${arrow(d.o, 'ohlcv_o')}${sparkSVG('ohlcv_o')}</div></td>
            <td><div class="cell-label">High</div><div class="cell-value" id="ohlcv-high" data-val="">${fmtPrice(d.h)}</div><div class="cell-sub">${arrow(d.h, 'ohlcv_h')}${sparkSVG('ohlcv_h')}</div></td>
            <td><div class="cell-label">Low</div><div class="cell-value" id="ohlcv-low" data-val="">${fmtPrice(d.l)}</div><div class="cell-sub">${arrow(d.l, 'ohlcv_l')}${sparkSVG('ohlcv_l')}</div></td>
            <td><div class="cell-label">Close</div><div class="cell-value" id="ohlcv-close" data-val="">${fmtPrice(d.c)}</div><div class="cell-sub">${arrow(d.c, 'ohlcv_c')}${sparkSVG('ohlcv_c')}</div></td>
            <td><div class="cell-label">Volume</div><div class="cell-value" id="ohlcv-vol" data-val="">${fmtPrice(d.vol)}</div><div class="cell-sub">${sparkSVG('ohlcv_vol')}</div></td>
        </tr>
    </table>`;
    bufPush('ohlcv_o', d.o); bufPush('ohlcv_h', d.h);
    bufPush('ohlcv_l', d.l); bufPush('ohlcv_c', d.c); bufPush('ohlcv_vol', d.vol);
}

function renderTickersTable(msg, isUpdate) {
    setWSSummaryHeader('renderTickersTable');
    const tickers = msg.data || [];
    if (!tickers.length) return;
    if (isUpdate) {
        for (const t of tickers) {
            setCell('tkr-' + t.instId + '-last', t.lastPr, 'tkr_' + t.instId);
            setCell('tkr-' + t.instId + '-chg', t.change24h, 'tkr_chg_' + t.instId);
            setCell('tkr-' + t.instId + '-vol', t.baseVolume, 'tkr_vol_' + t.instId);
        }
        return;
    }
    let html = '<table class="trades-table"><thead><tr><th>Symbol</th><th>Last</th><th>Chg%</th><th>Volume</th></tr></thead><tbody>';
    for (const t of tickers.slice(0, 20)) {
        const chgCls = parseFloat(t.change24h) >= 0 ? 'trade-buy' : 'trade-sell';
        html += `<tr>
            <td>${esc(t.instId)}</td>
            <td id="tkr-${t.instId}-last" data-val="">${fmtPrice(t.lastPr)}</td>
            <td class="${chgCls}" id="tkr-${t.instId}-chg" data-val="">${t.change24h || '—'}%</td>
            <td id="tkr-${t.instId}-vol" data-val="">${fmtPrice(t.baseVolume)}</td>
        </tr>`;
    }
    html += '</tbody></table>';
    document.getElementById('ws-summary-table').innerHTML = html;
}

function showError(data) {
    document.getElementById('response-area').style.display = 'none';

    const timing = data.timing || {};
    const timingEl = document.getElementById('timing-info');
    if (timing.gen_ms != null) {
        timingEl.innerHTML = '<span class="timing-badge timing-gen">🕐 Gen: ' + timing.gen_ms + 'ms</span>' +
            '<span class="timing-badge timing-rtt">⚡ RTT: ' + timing.rtt_ms + 'ms</span>' +
            '<span class="timing-badge timing-total">∑ ' + timing.total_ms + 'ms</span>';
    } else {
        timingEl.textContent = '';
    }

    const urlEl = document.getElementById('request-url');
    if (data.request_url) {
        urlEl.style.display = 'block';
        urlEl.innerHTML = '<span class="url-method">URL</span> ' + esc(data.request_url);
    } else {
        urlEl.style.display = 'none';
    }

    const errEl = document.getElementById('error-area');
    errEl.style.display = 'block';
    errEl.textContent = '❌ ' + (data.error || 'Unknown error');
}

function initDivider() {
    const divider = document.getElementById('divider');
    let isDragging = false;

    divider.addEventListener('mousedown', function (e) {
        isDragging = true;
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
    });

    document.addEventListener('mousemove', function (e) {
        if (!isDragging) return;
        const left = document.getElementById('tree-panel');
        const container = document.querySelector('.ccxt-split');
        const rect = container.getBoundingClientRect();
        let newWidth = e.clientX - rect.left - 3;
        newWidth = Math.max(180, Math.min(500, newWidth));
        left.style.width = newWidth + 'px';
    });

    document.addEventListener('mouseup', function () {
        if (isDragging) {
            isDragging = false;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        }
    });
}
