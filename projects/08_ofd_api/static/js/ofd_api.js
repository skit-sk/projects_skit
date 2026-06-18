// ===== OFD API Explorer — providers tree + param form + execute =====

let currentProvider = 'yandex_ofd';
let currentMethod = null;
let methodsCache = {};
let currentParamMeta = {};

document.addEventListener('DOMContentLoaded', function () {
    loadProviders();
    const savedToken = localStorage.getItem('ofd-api-token');
    if (savedToken) document.getElementById('ofd-token-input').value = savedToken;
    document.getElementById('param-mode-basic').addEventListener('change', function() {
        document.getElementById('param-basic').style.display = 'block';
        document.getElementById('param-advanced').style.display = 'none';
    });
    document.getElementById('param-mode-advanced').addEventListener('change', function() {
        document.getElementById('param-basic').style.display = 'none';
        document.getElementById('param-advanced').style.display = 'block';
        syncBasicToAdvanced();
    });
});

// ── Providers ──
function loadProviders() {
    fetch('/ofd-api/api/providers')
        .then(r => r.json())
        .then(data => {
            const sel = document.getElementById('ofd-provider-select');
            sel.innerHTML = '';
            for (const p of data) {
                const opt = document.createElement('option');
                opt.value = p.id;
                opt.textContent = p.name + (p.version ? ' (' + p.version + ')' : '');
                if (p.id === 'yandex_ofd') opt.selected = true;
                sel.appendChild(opt);
            }
            onProviderChange();
        })
        .catch(e => {
            const treeEl = document.getElementById('method-tree');
            if (treeEl) treeEl.innerHTML = '<div class="loading">❌ ' + e.message + '</div>';
        });
}

function onProviderChange() {
    const sel = document.getElementById('ofd-provider-select');
    currentProvider = sel.value;
    if (!currentProvider) return;
    loadMethods(currentProvider);
}

// ── Methods ──
function loadMethods(provider) {
    const tree = document.getElementById('method-tree');
    if (!tree) return;
    tree.innerHTML = '<div class="loading">⏳ Загрузка методов...</div>';
    currentMethod = null;
    const mi = document.getElementById('method-info');
    if (mi) mi.innerHTML = '<div class="placeholder">Выберите метод слева</div>';
    ['param-form', 'execute-area', 'response-area', 'error-area'].forEach(function(id) {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });

    fetch('/ofd-api/api/methods/' + provider)
        .then(r => r.json())
        .then(data => {
            methodsCache = data.categories || {};
            buildMethodTree(methodsCache, tree);
        })
        .catch(e => {
            tree.innerHTML = '<div class="loading">❌ ' + e.message + '</div>';
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
        hdr.onclick = function () { toggleCategory(catDiv); };
        catDiv.appendChild(hdr);

        const body = document.createElement('div');
        body.className = 'cat-body';

        for (const m of methods) {
            const item = document.createElement('div');
            item.className = 'method-item';
            item.dataset.key = m.key;
            item.innerHTML = '<span class="method-icon auth">●</span><span class="method-name">' + esc(m.name) + '</span><span class="method-desc">' + esc(m.desc) + '</span>';
            item.onclick = function () { selectMethod(m, item); };
            body.appendChild(item);
        }

        catDiv.appendChild(body);
        container.appendChild(catDiv);
    }

    const first = container.querySelector('.method-category');
    if (first) toggleCategory(first);
}

function toggleCategory(catDiv) {
    const toggle = catDiv.querySelector('.cat-toggle');
    const body = catDiv.querySelector('.cat-body');
    const isExpanded = body.classList.contains('expanded');
    body.classList.toggle('expanded');
    toggle.classList.toggle('expanded');
}

// ── Method Selection ──
function selectMethod(m, element) {
    document.querySelectorAll('.method-item.active').forEach(el => el.classList.remove('active'));
    if (element) element.classList.add('active');
    currentMethod = m;
    currentParamMeta = m.params || {};

    const info = document.getElementById('method-info');
    if (info) info.innerHTML = '<span class="method-title">' + esc(m.method || 'POST') + ' <b>' + esc(m.name) + '</b></span>';

    const urlEl = document.getElementById('request-url');
    const paramEl = document.getElementById('param-form');
    const execEl = document.getElementById('execute-area');
    const respEl = document.getElementById('response-area');
    const errEl = document.getElementById('error-area');
    if (urlEl) urlEl.style.display = 'none';
    if (paramEl) paramEl.style.display = 'block';
    if (execEl) execEl.style.display = 'flex';
    if (respEl) respEl.style.display = 'none';
    if (errEl) errEl.style.display = 'none';

    buildParamForm(currentParamMeta);
    loadDocs(m.key);
}

// ── Param Form (Basic/Advanced tabs) ──
function buildParamForm(params) {
    const mode = document.querySelector('input[name="param-mode"]:checked');
    if (!mode) return;

    const basic = document.getElementById('param-basic');
    if (!basic) return;
    basic.innerHTML = '';
    const keys = Object.keys(params);
    if (keys.length === 0) {
        basic.innerHTML = '<div class="param-hint" style="padding:0.5rem;font-size:11px;color:var(--text-muted);">Нет параметров</div>';
    } else {
        for (const k of keys) {
            const meta = params[k];
            const pType = meta.type || 'string';
            const isReq = meta.required;
            const desc = meta.desc || '';
            const example = meta.example !== undefined ? meta.example : '';
            const row = document.createElement('div');
            row.className = 'param-row';
            row.innerHTML = '<label class="param-label">' + esc(k) + (isReq ? ' <span class="param-required">*</span>' : '') + '</label>' +
                '<input type="text" class="param-input" id="param-' + esc(k) + '" placeholder="' + esc(desc) + '" value="' + esc(String(example)) + '" data-type="' + esc(pType) + '">';
            basic.appendChild(row);
        }
    }

    // Advanced
    const advInput = document.getElementById('param-advanced-input');
    if (advInput) advInput.value = JSON.stringify(buildParamsFromBasic(), null, 2);
}

function buildParamsFromBasic() {
    const result = {};
    const rows = document.querySelectorAll('#param-basic .param-row');
    rows.forEach(function(row) {
        const inp = row.querySelector('.param-input');
        if (!inp) return;
        const label = row.querySelector('.param-label');
        if (!label) return;
        const key = label.textContent.replace(' *', '').trim();
        const val = inp.value.trim();
        const pType = inp.getAttribute('data-type') || 'string';
        if (val) {
            if (pType === 'number') result[key] = parseFloat(val) || 0;
            else if (pType === 'array') {
                try { result[key] = JSON.parse(val); } catch(e) { result[key] = val; }
            } else result[key] = val;
        }
    });
    return result;
}

function syncBasicToAdvanced() {
    const advInput = document.getElementById('param-advanced-input');
    if (advInput) advInput.value = JSON.stringify(buildParamsFromBasic(), null, 2);
}

function syncAdvancedToBasic() {
    const advInput = document.getElementById('param-advanced-input');
    if (!advInput) return;
    try {
        const data = JSON.parse(advInput.value);
        for (const k in data) {
            const inp = document.getElementById('param-' + k);
            if (inp) inp.value = String(data[k]);
        }
    } catch(e) {}
}

// ── Docs ──
function loadDocs(methodKey) {
    const section = document.getElementById('docs-section');
    const content = document.getElementById('docs-content');
    section.style.display = 'none';

    fetch('/ofd-api/api/docs/' + currentProvider + '/' + methodKey)
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
        .catch(function() {});
}

function toggleDocs(header) {
    const body = header.nextElementSibling;
    const toggle = header.querySelector('.docs-toggle');
    body.classList.toggle('expanded');
    toggle.classList.toggle('expanded');
}

// ── Execute ──
function executeMethod() {
    if (!currentMethod) return;

    const btn = document.getElementById('execute-btn');
    if (!btn) return;
    btn.disabled = true;
    btn.textContent = '⏳ ...';

    const respArea = document.getElementById('response-area');
    const errArea = document.getElementById('error-area');
    if (respArea) respArea.style.display = 'none';
    if (errArea) errArea.style.display = 'none';

    const execStart = performance.now();

    const isAdvanced = document.querySelector('input[name="param-mode"]:checked').value === 'advanced';
    let params = {};
    if (isAdvanced) {
        try {
            params = JSON.parse(document.getElementById('param-advanced-input').value);
        } catch(e) {
            showError({error: 'Invalid JSON: ' + e.message});
            btn.disabled = false;
            btn.textContent = '▶ Execute';
            return;
        }
    } else {
        params = buildParamsFromBasic();
    }

    const token = document.getElementById('ofd-token-input')?.value?.trim() || undefined;
    saveToken();

    fetch('/ofd-api/api/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            provider: currentProvider,
            method: currentMethod.name,
            params: params,
            token: token,
        }),
    })
        .then(r => r.json())
        .then(data => {
            btn.disabled = false;
            btn.textContent = '▶ Execute';
            const execEnd = performance.now();
            if (data.timing) data.timing.client_ms = roundTo((execEnd - execStart), 2);

            if (data.error) { showError(data); return; }
            showResponse(data);
        })
        .catch(err => {
            btn.disabled = false;
            btn.textContent = '▶ Execute';
            showError({ error: err.message });
        });
}

// ── Response ──
function showResponse(data) {
    const urlEl = document.getElementById('request-url');
    if (data.url) {
        urlEl.style.display = 'block';
        urlEl.innerHTML = '<span class="url-method">POST</span> ' + esc(data.url);
    } else {
        urlEl.style.display = 'none';
    }

    const timing = data.timing || {};
    const timingEl = document.getElementById('timing-info');
    let timingHtml = '';
    if (timing.total_ms != null) timingHtml += '<span class="timing-badge timing-total">∑ ' + roundTo(timing.total_ms, 1) + 'ms</span>';
    if (timing.client_ms != null) timingHtml += '<span class="timing-badge timing-client">⏱ ' + roundTo(timing.client_ms, 1) + 'ms</span>';
    if (timingEl) timingEl.innerHTML = timingHtml;

    const area = document.getElementById('response-area');
    if (!area) return;
    area.style.display = 'block';
    let viewer = document.getElementById('json-viewer');
    if (!viewer) {
        viewer = document.createElement('div');
        viewer.id = 'json-viewer';
        viewer.className = 'json-viewer';
        area.appendChild(viewer);
    }
    viewer.innerHTML = '';
    if (data.response !== undefined) {
        renderJsonTree(data.response, viewer);
        renderJsonTableIfEnabled(data.response);
    }
}

function showError(data) {
    const respArea = document.getElementById('response-area');
    if (respArea) respArea.style.display = 'none';
    const errEl = document.getElementById('error-area');
    if (!errEl) return;
    errEl.style.display = 'block';
    let msg = data.error || 'Unknown error';
    if (data.url) msg += '\nURL: ' + data.url;
    if (data.status) msg += '\nStatus: ' + data.status;
    errEl.textContent = '❌ ' + msg;
}

function saveToken() {
    const inp = document.getElementById('ofd-token-input');
    if (inp) {
        try { localStorage.setItem('ofd-api-token', inp.value); } catch(e) {}
    }
}

function esc(s) {
    if (s == null) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function roundTo(v, d) {
    const m = Math.pow(10, d);
    return Math.round(v * m) / m;
}
