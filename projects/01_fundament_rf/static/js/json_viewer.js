// ===== JSON Viewer — shared between CCXT API, OFD API, etc. =====

function esc(s) {
    if (s == null) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function flashCell(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.remove('cell-updated');
    void el.offsetWidth;
    el.classList.add('cell-updated');
}

function setCellSpan(id, html) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = html;
    flashCell(id);
}

function expandAllNodes() {
    document.querySelectorAll('.json-children').forEach(el => el.classList.add('expanded'));
    document.querySelectorAll('.json-toggle').forEach(el => el.classList.add('expanded'));
    const treeCb = document.getElementById('tree-toggle');
    const tableCb = document.getElementById('table-view');
    if (treeCb && treeCb.checked) {
        const sec = document.getElementById('json-tree-section');
        if (sec) {
            const panel = sec.closest('.json-debug-panel') || sec;
            panel.style.display = '';
        }
    }
    if (tableCb && tableCb.checked) {
        const sec = document.getElementById('json-table-section');
        if (sec) {
            const panel = sec.closest('.json-debug-panel') || sec;
            panel.style.display = '';
        }
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

// ===== JSON Tree =====

function renderJsonTree(data, container) {
    container.innerHTML = '';
    if (data === null || data === undefined) {
        container.innerHTML = '<span class="json-null">null</span>';
        return;
    }
    if (typeof data !== 'object') {
        container.appendChild(renderLeaf('', data));
        return;
    }
    const entries = Array.isArray(data)
        ? data.map((v, i) => [String(i), v])
        : Object.entries(data);
    const ul = document.createElement('ul');
    ul.className = 'json-tree';
    for (const [k, v] of entries) {
        ul.appendChild(renderNode(k, v));
    }
    container.appendChild(ul);
}

function renderLeaf(key, value) {
    const li = document.createElement('li');
    const keyHtml = key !== '' ? '<span class="json-key">' + esc(key) + '</span>: ' : '';
    if (value === null) {
        li.innerHTML = keyHtml + '<span class="json-null">null</span>';
    } else if (typeof value === 'string') {
        li.innerHTML = keyHtml + '<span class="json-string">"' + esc(value) + '"</span>';
    } else if (typeof value === 'number') {
        li.innerHTML = keyHtml + '<span class="json-number">' + value + '</span>';
    } else if (typeof value === 'boolean') {
        li.innerHTML = keyHtml + '<span class="json-bool">' + value + '</span>';
    } else {
        li.innerHTML = keyHtml + '<span class="json-null">' + typeof value + '</span>';
    }
    return li;
}

const TUPLE_SIGS = {
    6: ['ts', 'open', 'high', 'low', 'close', 'volume'],
    2: ['price', 'amount'],
};

function renderNode(key, value) {
    if (value === null || typeof value !== 'object') {
        return renderLeaf(key, value);
    }

    const isArray = Array.isArray(value);
    const isTypedTuple = isArray && TUPLE_SIGS[value.length] && value.every(v => typeof v === 'number');
    const entries = isTypedTuple
        ? TUPLE_SIGS[value.length].map((label, i) => [label, value[i]])
        : isArray
            ? value.map((v, i) => [String(i), v])
            : Object.entries(value);
    const typeLabel = isArray ? 'Array [' + entries.length + ']' : 'Object {' + entries.length + '}';

    if (entries.length === 0) {
        const li = document.createElement('li');
        li.innerHTML = '<span class="json-key">' + esc(key) + '</span>: <span class="json-type">' + (isArray ? '[]' : '{}') + '</span>';
        return li;
    }

    const collapseId = 'j-' + Math.random().toString(36).substr(2, 8);
    const li = document.createElement('li');
    li.className = 'json-collapsible';

    const toggleSpan = document.createElement('span');
    toggleSpan.className = 'json-toggle';
    toggleSpan.textContent = '▶';
    toggleSpan.onclick = function () {
        const children = li.querySelector('.json-children');
        const isExpanded = children.classList.contains('expanded');
        children.classList.toggle('expanded');
        toggleSpan.classList.toggle('expanded');
    };

    const keySpan = document.createElement('span');
    keySpan.className = 'json-key';
    keySpan.textContent = key + ': ';

    const typeSpan = document.createElement('span');
    typeSpan.className = 'json-type';
    typeSpan.textContent = typeLabel;

    const childUl = document.createElement('ul');
    childUl.className = 'json-children';
    childUl.id = collapseId;
    for (const [k, v] of entries) {
        childUl.appendChild(renderNode(k, v));
    }

    li.appendChild(toggleSpan);
    li.appendChild(keySpan);
    li.appendChild(typeSpan);
    li.appendChild(childUl);
    return li;
}

function valClass(v) {
    if (v === null || v === undefined) return 'json-null';
    if (typeof v === 'string') return 'json-string';
    if (typeof v === 'number') return 'json-number';
    if (typeof v === 'boolean') return 'json-bool';
    return '';
}

function valHtml(v) {
    if (v === null) return '<span class="json-null">null</span>';
    if (v === undefined) return '<span class="json-null">undefined</span>';
    if (typeof v === 'string') return '<span class="json-string">"' + esc(v) + '"</span>';
    if (typeof v === 'number') return '<span class="json-number">' + v + '</span>';
    if (typeof v === 'boolean') return '<span class="json-bool">' + v + '</span>';
    if (typeof v === 'object') return '<span class="json-type">' + (Array.isArray(v) ? 'Array[' + v.length + ']' : 'Object{' + Object.keys(v).length + '}') + '</span>';
    return esc(String(v));
}

function renderJsonTable(data, depth) {
    if (depth === undefined) depth = 0;
    const maxDepth = 6;
    const rows = [];

    function walk(obj, path) {
        if (obj === null || obj === undefined || typeof obj !== 'object') {
            rows.push({ path: path.slice(), value: obj });
            return;
        }
        const entries = Array.isArray(obj)
            ? obj.map((v, i) => [i, v])
            : Object.entries(obj);
        for (const [k, v] of entries) {
            if (v !== null && typeof v === 'object' && path.length < maxDepth) {
                rows.push({ path: path.concat([String(k)]), value: null, isBranch: true });
                walk(v, path.concat([String(k)]));
            } else {
                rows.push({ path: path.concat([String(k)]), value: v });
            }
        }
    }
    walk(data, []);

    if (!rows.length) {
        const el = document.getElementById('json-table');
        if (el) el.innerHTML = '';
        return;
    }

    let html = '<table class="json-table"><tr><th>#</th>';
    for (let i = 0; i < maxDepth + 1; i++) {
        html += '<th>' + (i === 0 ? 'field' : 'sub' + i) + '</th>';
    }
    html += '<th>Value</th></tr>';

    let idx = 0;
    for (const r of rows) {
        idx++;
        const level = r.path.length - 1;
        html += '<tr><td>' + idx + '</td>';
        for (let i = 0; i < maxDepth + 1; i++) {
            const label = (i < r.path.length) ? esc(r.path[i]) : '';
            const cls = (i === r.path.length - 1 && r.isBranch) ? 'json-table-branch' : '';
            html += '<td class="' + cls + '">' + label + '</td>';
        }
        html += '<td>' + valHtml(r.value) + '</td></tr>';
    }
    html += '</table>';
    const el = document.getElementById('json-table');
    if (el) el.innerHTML = html;
}

function renderJsonTableIfEnabled(data) {
    const el = document.getElementById('json-table');
    const cb = document.getElementById('table-view');
    if (el && cb && cb.checked) {
        renderJsonTable(data);
    }
}
