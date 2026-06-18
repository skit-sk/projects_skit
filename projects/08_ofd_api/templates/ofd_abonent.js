// ===== OFD Abonent — data load, sync, charts, export =====

let currentInn = '';
let currentData = {};

document.addEventListener('DOMContentLoaded', function () {
    const to = new Date();
    const from = new Date();
    from.setDate(from.getDate() - 30);
    document.getElementById('oa-to').value = to.toISOString().slice(0, 10);
    document.getElementById('oa-from').value = from.toISOString().slice(0, 10);
    loadInnList();
});

function loadInnList() {
    fetch('/ofd_abonent/api/list_inns')
        .then(r => r.json())
        .then(data => {
            const sel = document.getElementById('oa-inn');
            const current = sel.value;
            sel.innerHTML = '<option value="">— выберите —</option>';
            for (const inn of data) {
                const opt = document.createElement('option');
                opt.value = inn.inn;
                opt.textContent = inn.inn + (inn.name ? ' — ' + inn.name : '') + ' (' + inn.kkt_count + ' ККТ)';
                sel.appendChild(opt);
            }
            if (current && [...sel.options].some(o => o.value === current)) sel.value = current;
            // Auto-discover if no INNs exist
            if (data.length === 0) autoDiscover();
        });
}

function autoDiscover() {
    fetch('/ofd_abonent/api/defaults')
        .then(r => r.json())
        .then(data => {
            if (!data.tokens || data.tokens.length === 0) return;
            const tok = data.tokens[0];
            // Try to discover INN from the first available token
            fetch('/ofd_abonent/api/discover_inn', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({provider: tok.provider, token: ''}),
            })
                .then(r => r.json())
                .then(resp => {
                    if (resp.inn) {
                        // Auto-save and add to list
                        fetch('/ofd_abonent/api/save_inn', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({inn: resp.inn, provider: tok.provider}),
                        })
                            .then(r2 => r2.json())
                            .then(saved => {
                                if (saved.ok) {
                                    loadInnList();
                                    setTimeout(() => {
                                        document.getElementById('oa-inn').value = resp.inn;
                                        loadData();
                                    }, 200);
                                }
                            });
                    }
                })
                .catch(() => {});
        });
}

function loadData() {
    const val = document.getElementById('oa-inn').value;
    if (!val) {
        currentInn = '';
        ['oa-overview','oa-kkt','oa-charts','oa-data','oa-export'].forEach(function(id) {
            document.getElementById(id).innerHTML = '';
        });
        return;
    }
    currentInn = val;
    fetch('/ofd_abonent/api/status?inn=' + val)
        .then(r => r.json())
        .then(data => {
            currentData = data;
            if (data.has_data) {
                renderOverview(data.abonent);
                renderKKT(data.abonent);
            } else {
                document.getElementById('oa-overview').innerHTML = '<div class="placeholder">Нет данных. Нажмите Sync для загрузки.</div>';
            }
        });
}

function showAddInnDialog() {
    document.getElementById('oa-add-dialog').style.display = 'block';
    document.getElementById('oa-new-inn').value = '';
    document.getElementById('oa-new-token').value = '';
}
function hideAddInnDialog() {
    document.getElementById('oa-add-dialog').style.display = 'none';
}

function addInnToSelect(inn) {
    const sel = document.getElementById('oa-inn');
    const opt = document.createElement('option');
    opt.value = inn;
    opt.textContent = inn + ' (новый)';
    sel.appendChild(opt);
    sel.value = inn;
    hideAddInnDialog();
    loadData();
}

function discoverInn() {
    const prov = document.getElementById('oa-new-provider').value;
    const token = document.getElementById('oa-new-token').value.trim();
    setStatus('⏳ Определяю ИНН по токену...');
    fetch('/ofd_abonent/api/discover_inn', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({provider: prov, token}),
    })
        .then(r => r.json())
        .then(data => {
            if (data.error) { setStatus('❌ ' + data.error, 'error'); return; }
            document.getElementById('oa-new-inn').value = data.inn;
            if (data.inn) {
                // Auto-save after discover (pass token for local .env)
                const prov = document.getElementById('oa-new-provider').value;
                const token = document.getElementById('oa-new-token').value.trim();
                fetch('/ofd_abonent/api/save_inn', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({inn: data.inn, provider: prov, token}),
                })
                    .then(r => r.json())
                    .then(saved => {
                        if (saved.ok) {
                            setStatus('✅ ИНН: ' + data.inn + ' — сохранён');
                            addInnToSelect(data.inn);
                        }
                    })
                    .catch(() => {});
            }
        })
        .catch(e => setStatus('❌ ' + e.message, 'error'));
}

function addInn() {
    const inn = document.getElementById('oa-new-inn').value.trim();
    const token = document.getElementById('oa-new-token').value.trim();
    if (!inn) { setStatus('❌ Введите ИНН', 'error'); return; }
    // Save to storage immediately, then select it
    fetch('/ofd_abonent/api/save_inn', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({inn, token, provider: document.getElementById('oa-new-provider').value}),
    })
        .then(r => r.json())
        .then(data => {
            if (data.error) { setStatus('❌ ' + data.error, 'error'); return; }
            addInnToSelect(inn);
            loadInnList();
        })
        .catch(e => setStatus('❌ ' + e.message, 'error'));
}

function deleteInn() {
    const inn = currentInn;
    if (!inn) { setStatus('❌ Выберите ИНН', 'error'); return; }
    if (!confirm('Удалить все данные по ИНН ' + inn + '?')) return;
    fetch('/ofd_abonent/api/delete_inn', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({inn}),
    })
        .then(r => r.json())
        .then(data => {
            if (data.error) { setStatus('❌ ' + data.error, 'error'); return; }
            currentInn = '';
            ['oa-overview','oa-kkt','oa-charts','oa-data','oa-export'].forEach(function(id) {
                document.getElementById(id).innerHTML = '';
            });
            setStatus('✅ ИНН ' + inn + ' удалён');
            loadInnList();
        })
        .catch(e => setStatus('❌ ' + e.message, 'error'));
}

function setStatus(msg, cls) {
    const el = document.getElementById('oa-status');
    el.style.display = 'block';
    el.textContent = msg;
    el.className = cls || '';
    if (cls !== 'error') setTimeout(() => el.style.display = 'none', 5000);
}

function doSync() {
    const inn = currentInn;
    if (!inn) { setStatus('❌ Выберите ИНН', 'error'); return; }
    const from = document.getElementById('oa-from').value;
    const to = document.getElementById('oa-to').value;

    setStatus('⏳ Синхронизация...');
    fetch('/ofd_abonent/api/sync', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({inn, period_from: from, period_to: to}),
    })
        .then(r => r.json())
        .then(data => {
            if (data.error) { setStatus('❌ ' + data.error, 'error'); return; }
            setStatus('✅ Sync завершён: ' + data.kkt_count + ' ККТ за ' + data.elapsed_ms + 'ms');
            loadInnList();
            loadData();
            // Обновить активную вкладку
            var visibleTab = document.querySelector('.oa-tab-content[style*="block"]');
            if (visibleTab) {
                var tabId = visibleTab.id.replace('oa-', '');
                if (tabId === 'charts' && currentInn) loadCharts();
                if (tabId === 'data' && currentInn) renderData();
            }
        })
        .catch(e => setStatus('❌ ' + e.message, 'error'));
}

// ── Overview tab ──
function renderOverview(abonent) {
    const el = document.getElementById('oa-overview');
    let html = '<div class="ta-section">';
    html += '<div class="ta-section-title">📊 Сводка по абоненту</div>';
    html += '<table class="account-table"><thead><tr><th>ККТ</th><th>ФН</th><th>Провайдер</th><th>Смены</th><th>Чеки</th><th>Сумма</th><th>Ошибки</th></tr></thead><tbody>';
    for (const k of (abonent.kkt_summary || [])) {
        html += '<tr><td>' + esc(k.kkt_name) + '</td><td>' + esc(k.fn_current || '—') + '</td><td>' + esc(k.provider || '—') +
            '</td><td>' + k.totals.shifts + '</td><td>' + k.totals.receipts.total + '</td><td>' + k.totals.sums.total.toFixed(2) +
            '</td><td>' + k.totals.errors + '</td></tr>';
    }
    html += '</tbody></table></div>';
    el.innerHTML = html;
}

// ── KKT tab ──
function renderKKT(abonent) {
    const el = document.getElementById('oa-kkt');
    let html = '<div class="ta-section"><div class="ta-section-title">📟 ККТ и ФН</div>';
    for (const k of (abonent.kkt_summary || [])) {
        html += '<div style="margin-bottom:1rem;padding:0.5rem;border:1px solid var(--border-color);border-radius:8px;">';
        html += '<strong>' + esc(k.kkt_name) + '</strong> (RNM: ' + esc(k.rnm) + ') · ' + esc(k.provider) + '<br>';
        html += 'ФН: ' + esc(k.fn_current || '—') + '<br>';
        html += '📊 ' + k.totals.shifts + ' смен · ' + k.totals.receipts.total + ' чеков · 💰 ' + k.totals.sums.total.toFixed(2) + '₽<br>';
        html += '<span style="color:#22c55e">🟢 нал: ' + k.totals.receipts.cash + '</span> · ' +
                '<span style="color:#3b82f6">🔵 карта: ' + k.totals.receipts.card + '</span> · ' +
                '<span style="color:#eab308">🟡 возврат: ' + k.totals.receipts.return + '</span> · ' +
                '<span style="color:#ef4444">🔴 ошибки: ' + k.totals.errors + '</span>';
        html += '</div>';
    }
    html += '</div>';
    el.innerHTML = html;
}

// ── Charts tab ──
let chartMode = 'stack';
let chartPeriod = 'day';

function getDefaultFrom() {
    const d = new Date(); d.setDate(d.getDate() - 30); return d.toISOString().slice(0, 10);
}
function getDefaultTo() {
    return new Date().toISOString().slice(0, 10);
}

function loadCharts() {
    const from = document.getElementById('chart-from')?.value || getDefaultFrom();
    const to = document.getElementById('chart-to')?.value || getDefaultTo();
    const el = document.getElementById('oa-charts');

    // Build KKT filters
    let kktHtml = '<div id="kkt-filters" style="display:flex;gap:0.3rem;flex-wrap:wrap;font-size:11px;align-items:center;">';
    kktHtml += '<label><input type="checkbox" class="kkt-filter" value="__all__" checked onchange="filterKkt()"> 📟 Все</label>';

    // Fetch KKT list
    fetch('/ofd_abonent/api/status?inn=' + currentInn)
        .then(r => r.json())
        .then(statusData => {
            const kktList = statusData?.abonent?.kkt_summary || [];
            for (const k of kktList) {
                kktHtml += '<label><input type="checkbox" class="kkt-filter" value="' + esc(k.rnm) + '" checked onchange="filterKkt()"> ' + esc(k.kkt_name || 'ККТ') + '</label>';
            }
            kktHtml += '</div>';

            el.innerHTML = '<div style="display:flex;gap:0.5rem;margin-bottom:0.5rem;flex-wrap:wrap;align-items:center;">' +
                '<label><input type="radio" name="chart-period" value="day" ' + (chartPeriod==='day'?'checked':'') + ' onchange="chartPeriod=this.value;loadCharts()"> 📅 День</label>' +
                '<label><input type="radio" name="chart-period" value="week" ' + (chartPeriod==='week'?'checked':'') + ' onchange="chartPeriod=this.value;loadCharts()"> 📅 Неделя</label>' +
                '<label><input type="radio" name="chart-period" value="month" ' + (chartPeriod==='month'?'checked':'') + ' onchange="chartPeriod=this.value;loadCharts()"> 📅 Месяц</label>' +
                '<span style="width:1px;height:20px;background:var(--border-color);margin:0 4px;"></span>' +
                '<label><input type="radio" name="chart-mode" value="stack" ' + (chartMode==='stack'?'checked':'') + ' onchange="chartMode=this.value;loadCharts()"> ■ Stacked</label>' +
                '<label><input type="radio" name="chart-mode" value="group" ' + (chartMode==='group'?'checked':'') + ' onchange="chartMode=this.value;loadCharts()"> ▣ Grouped</label>' +
                '<span style="width:1px;height:20px;background:var(--border-color);margin:0 4px;"></span>' +
                '📅 <input type="date" id="chart-from" value="' + from + '" style="width:120px;font-size:11px;">' +
                '<input type="date" id="chart-to" value="' + to + '" style="width:120px;font-size:11px;">' +
                '<button onclick="loadCharts()" class="execute-btn" style="font-size:10px;">🔄</button>' +
                '</div>' + kktHtml + '<div id="chart-container" style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;"></div>';

            // Fetch chart data with current KKT filter
            doFetchCharts(from, to);
        });
}

function filterKkt() {
    const allCb = document.querySelector('.kkt-filter[value="__all__"]');
    if (!allCb) return;
    const from = document.getElementById('chart-from')?.value || getDefaultFrom();
    const to = document.getElementById('chart-to')?.value || getDefaultTo();
    if (allCb.checked) {
        doFetchCharts(from, to);
    } else {
        const checked = document.querySelectorAll('.kkt-filter:checked');
        const rnms = Array.from(checked).map(cb => cb.value);
        doFetchCharts(from, to, rnms);
    }
}

function doFetchCharts(from, to, rnms) {
    let url = '/ofd_abonent/api/charts?inn=' + currentInn + '&period=' + chartPeriod + '&from=' + from + '&to=' + to;
    if (rnms && rnms.length > 0) {
        rnms.forEach(r => { url += '&rnm=' + encodeURIComponent(r); });
    }
    document.getElementById('oa-charts').querySelector('#chart-container').innerHTML = '<div class="loading">⏳ Загрузка графиков...</div>';
    fetch(url)
        .then(r => r.json())
        .then(data => {
            const ct = document.getElementById('chart-container');
            ct.innerHTML = '';
            renderChart('chart-receipts', '📊 Чеки (шт)', data.labels, data.receipts, ct);
            renderChart('chart-sums', '💰 Суммы (₽)', data.labels, data.sums, ct);
        });
}

function renderChart(divId, title, labels, data, container) {
    const colors = { cash: '#22c55e', card: '#3b82f6', return: '#eab308', errors: '#ef4444' };
    const keys = ['cash', 'card', 'return', 'errors'];
    const wd = ['Вс','Пн','Вт','Ср','Чт','Пт','Сб'];
    const dayNames = labels.map(d => { try { return wd[new Date(d).getDay()] || ''; } catch(e) { return ''; } });
    const traces = keys.map(k => ({
        type: 'bar', x: labels, y: data[k] || [],
        name: k, marker: { color: colors[k] },
        text: dayNames,
        textposition: 'outside',
        textfont: { size: 8, color: '#888' },
        hovertemplate: '%{y}' + (title.includes('Суммы') ? ' ₽' : ' шт') + '<extra></extra>',
    }));

    const layout = {
        template: 'plotly_dark', paper_bgcolor: '#2d2d2d', plot_bgcolor: '#1a1a1a',
        barmode: chartMode, height: 350,
        margin: { l: 50, r: 20, t: 60, b: 50 },
        hovermode: 'x unified',
        title: { text: title, font: { size: 13, color: '#ddd' } },
        legend: { orientation: 'h', y: 1.18, x: 0.5, xanchor: 'center',
                  font: { size: 9, color: '#ccc' } },
        xaxis: { tickangle: -45, nticks: 10, tickfont: { size: 9, color: '#aaa' }, tickformat: '%d.%m' },
        yaxis: { tickfont: { size: 9, color: '#aaa' } },
    };

    const div = document.createElement('div'); div.id = divId;
    div.style.cssText = 'background:var(--bg-card);border-radius:8px;padding:0.5rem;';
    container.appendChild(div);
    Plotly.newPlot(divId, traces, layout, { responsive: true, displayModeBar: false });
}

// ── Export tab ──
function switchTab(tab) {
    document.querySelectorAll('.oa-tab-content').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.account-tab').forEach(el => el.classList.remove('active'));
    document.getElementById('oa-' + tab).style.display = 'block';
    document.querySelector('.account-tab[onclick*="' + tab + '"]').classList.add('active');
    if (!currentInn) return;
    if (tab === 'charts' && currentInn) loadCharts();
    if (tab === 'export') renderExport();
    if (tab === 'data' && currentInn) renderData();
}

function renderData() {
    const el = document.getElementById('oa-data');
    el.innerHTML = '<div class="loading">⏳ Загрузка данных...</div>';

    fetch('/ofd_abonent/api/fields?inn=' + currentInn)
        .then(r => r.json())
        .then(data => {
            const fields = data.fields || [];
            let html = '<div class="ta-section"><div class="ta-section-title">📋 Поля API (последний sync)</div>';
            html += '<div style="font-size:10px;color:var(--text-muted);margin-bottom:0.5rem;">Всего полей: ' + data.count + '</div>';
            html += '<table class="account-table"><thead><tr><th>API</th><th>Endpoint</th><th>Field</th><th>Type</th><th>Value</th></tr></thead><tbody>';
            let lastApi = '';
            for (const f of fields) {
                const rowClass = (f.api !== lastApi) ? 'style="border-top:2px solid var(--border-color);"' : '';
                html += '<tr ' + rowClass + '><td>' + esc(f.api) + '</td><td style="font-size:10px;">' + esc(f.endpoint) + '</td><td>' + esc(f.field) + '</td><td>' + esc(f.type) + '</td><td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;">' + esc(f.value) + '</td></tr>';
                lastApi = f.api;
            }
            html += '</tbody></table></div>';
            el.innerHTML = html;
        })
        .catch(e => { el.innerHTML = '<div class="error-state">❌ ' + e.message + '</div>'; });
}

function renderExport() {
    const el = document.getElementById('oa-export');
    el.innerHTML = '<div class="ta-section"><div class="ta-section-title">📤 Выгрузка данных</div>' +
        '<div style="display:flex;gap:1rem;flex-wrap:wrap;align-items:center;padding:0.5rem;">' +
        '<label>Период: <input type="date" id="export-from" value="' + (document.getElementById('chart-from')?.value || getDefaultFrom()) + '" style="width:130px"></label>' +
        '<label><input type="date" id="export-to" value="' + (document.getElementById('chart-to')?.value || getDefaultTo()) + '" style="width:130px"></label>' +
        '<label><input type="checkbox" id="export-aggr" checked> 🔀 Агрегировать товары</label>' +
        '<button class="execute-btn" onclick="doExport(\'xls\')">📥 XLS</button>' +
        '<button class="execute-btn" onclick="doExport(\'csv\')">📥 CSV</button>' +
        '<button class="execute-btn" onclick="doExport(\'csv-items\')">📥 CSV Товары</button>' +
        '</div></div>';
}

function doExport(fmt) {
    const from = document.getElementById('export-from').value;
    const to = document.getElementById('export-to').value;
    const aggr = document.getElementById('export-aggr').checked ? '1' : '0';
    window.open('/ofd_abonent/api/export/' + fmt + '?inn=' + currentInn + '&from=' + from + '&to=' + to + '&aggr=' + aggr, '_blank');
}

function esc(s) {
    if (s == null) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
