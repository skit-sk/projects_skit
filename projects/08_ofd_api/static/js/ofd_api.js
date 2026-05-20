// ===== OFD API Explorer — methods tree + execute =====

let currentMethod = null;
let methodsCache = {};

document.addEventListener('DOMContentLoaded', function () {
    loadMethods();
    const savedToken = localStorage.getItem('ofd-api-token');
    if (savedToken) document.getElementById('ofd-token-input').value = savedToken;
});

function loadMethods() {
    const tree = document.getElementById('method-tree');
    tree.innerHTML = '<div class="loading">⏳ Загрузка методов...</div>';

    fetch('/ofd-api/api/methods')
        .then(r => r.json())
        .then(data => {
            methodsCache = data.categories || {};
            buildMethodTree(methodsCache, tree);
        })
        .catch(err => {
            tree.innerHTML = '<div class="loading">❌ Ошибка: ' + esc(err.message) + '</div>';
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

        for (const mObj of methods) {
            const m = typeof mObj === 'string' ? mObj : mObj.name;
            const desc = mObj.desc || '';
            const item = document.createElement('div');
            item.className = 'method-item';
            item.dataset.method = m;
            item.innerHTML = '<span class="method-icon auth">●</span><span class="method-name">' + esc(m) + '</span><span style="font-size:10px;color:var(--text-muted);margin-left:auto;">' + esc(desc) + '</span>';
            item.onclick = function () { selectMethod(m, item); };
            body.appendChild(item);
        }

        catDiv.appendChild(body);
        container.appendChild(catDiv);
    }

    // Expand first category
    const firstCat = container.querySelector('.method-category');
    if (firstCat) toggleCategory(firstCat);
}

function toggleCategory(catDiv) {
    const toggle = catDiv.querySelector('.cat-toggle');
    const body = catDiv.querySelector('.cat-body');
    const isExpanded = body.classList.contains('expanded');
    body.classList.toggle('expanded');
    toggle.classList.toggle('expanded');
}

function selectMethod(method, element) {
    document.querySelectorAll('.method-item.active').forEach(el => el.classList.remove('active'));
    if (element) element.classList.add('active');
    currentMethod = method;

    const info = document.getElementById('method-info');
    info.innerHTML = '<span class="method-title">Method: <b>' + esc(method) + '</b></span>';

    document.getElementById('param-form').style.display = 'block';
    document.getElementById('execute-area').style.display = 'flex';
    document.getElementById('response-area').style.display = 'none';
    document.getElementById('error-area').style.display = 'none';

    buildParamForm(method);
    loadDocs(method);
}

function buildParamForm(method) {
    const container = document.getElementById('param-form');
    container.innerHTML = '';

    // Find method params from cache
    let params = null;
    for (const [catName, methods] of Object.entries(methodsCache)) {
        for (const m of methods) {
            if (m.name === method) {
                params = m.params;
                break;
            }
        }
        if (params !== null) break;
    }

    if (params === null) {
        // No params needed, just hint
        container.innerHTML = '<div class="param-row"><span class="param-hint">Параметров нет. body: {}</span></div>';
        return;
    }

    // Build JSON body editor
    const hint = document.createElement('div');
    hint.style.cssText = 'font-size:11px;color:var(--text-muted);margin-bottom:4px;';
    hint.textContent = 'JSON body (POST):';
    container.appendChild(hint);

    const ta = document.createElement('textarea');
    ta.className = 'param-input';
    ta.id = 'request-body';
    ta.rows = 4;
    ta.style.cssText = 'width:100%;font-family:monospace;font-size:12px;';
    ta.value = JSON.stringify(params, null, 2);
    container.appendChild(ta);
}

function loadDocs(method) {
    const section = document.getElementById('docs-section');
    const content = document.getElementById('docs-content');
    section.style.display = 'none';

    fetch('/ofd-api/api/docs/' + method)
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

function saveToken() {
    const inp = document.getElementById('ofd-token-input');
    if (inp) {
        try { localStorage.setItem('ofd-api-token', inp.value); } catch(e) {}
    }
}

function executeMethod() {
    if (!currentMethod) return;

    const btn = document.getElementById('execute-btn');
    btn.disabled = true;
    btn.textContent = '⏳ ...';

    document.getElementById('response-area').style.display = 'none';
    document.getElementById('error-area').style.display = 'none';

    let params = {};
    const ta = document.getElementById('request-body');
    if (ta && ta.value.trim()) {
        try {
            params = JSON.parse(ta.value);
        } catch(e) {
            showError({error: 'Invalid JSON: ' + e.message});
            btn.disabled = false;
            btn.textContent = '▶ Execute';
            return;
        }
    }

    const token = document.getElementById('ofd-token-input')?.value?.trim() || undefined;
    saveToken();

    fetch('/ofd-api/api/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            method: currentMethod,
            params: params,
            token: token,
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
    if (data.url) {
        urlEl.style.display = 'block';
        urlEl.innerHTML = '<span class="url-method">POST</span> ' + esc(data.url);
    } else {
        urlEl.style.display = 'none';
    }

    // Timing
    const timing = data.timing || {};
    const timingEl = document.getElementById('timing-info');
    let timingHtml = '';
    if (timing.total_ms != null) {
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

function showError(data) {
    document.getElementById('response-area').style.display = 'none';
    const errEl = document.getElementById('error-area');
    errEl.style.display = 'block';
    let msg = data.error || 'Unknown error';
    if (data.url) {
        msg += '\nURL: ' + data.url;
    }
    if (data.status) {
        msg += '\nStatus: ' + data.status;
    }
    errEl.textContent = '❌ ' + msg;
}
