// ===== OFD Abonent — data load, sync, charts, export =====

let currentInn = '';
let currentData = {};

document.addEventListener('DOMContentLoaded', function () {
    // Set default dates
    const to = new Date();
    const from = new Date();
    from.setDate(from.getDate() - 30);
    document.getElementById('oa-to').value = to.toISOString().slice(0, 10);
    document.getElementById('oa-from').value = from.toISOString().slice(0, 10);
});

function loadData() {
    const inn = document.getElementById('oa-inn').value.trim();
    if (!inn) return;
    currentInn = inn;
    fetch('/ofd_abonent/api/status?inn=' + inn)
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

function switchTab(tab) {
    document.querySelectorAll('.oa-tab-content').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.account-tab').forEach(el => el.classList.remove('active'));
    document.getElementById('oa-' + tab).style.display = 'block';
    event.target.classList.add('active');
    if (tab === 'charts' && currentInn) loadCharts();
}

function setStatus(msg, cls) {
    const el = document.getElementById('oa-status');
    el.style.display = 'block';
    el.textContent = msg;
    el.className = cls || '';
    if (cls !== 'error') setTimeout(() => el.style.display = 'none', 5000);
}

function doSync() {
    const inn = document.getElementById('oa-inn').value.trim();
    if (!inn) { setStatus('❌ Введите ИНН', 'error'); return; }
    const prov = document.getElementById('oa-provider').value;
    const from = document.getElementById('oa-from').value;
    const to = document.getElementById('oa-to').value;
    const token = prompt('Токен ' + prov + ' (оставьте пустым для .env):') || '';

    setStatus('⏳ Синхронизация...');
    fetch('/ofd_abonent/api/sync', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({inn, provider: prov, period_from: from, period_to: to, token}),
    })
        .then(r => r.json())
        .then(data => {
            if (data.error) { setStatus('❌ ' + data.error, 'error'); return; }
            setStatus('✅ Sync завершён: ' + data.kkt_count + ' ККТ за ' + data.elapsed_ms + 'ms');
            loadData();
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

function loadCharts() {
    const from = document.getElementById('oa-from').value;
    const to = document.getElementById('oa-to').value;
    const el = document.getElementById('oa-charts');
    el.innerHTML = '<div style="display:flex;gap:0.5rem;margin-bottom:1rem;flex-wrap:wrap;align-items:center;">' +
        '<label><input type="radio" name="chart-period" value="day" ' + (chartPeriod==='day'?'checked':'') + ' onchange="chartPeriod=this.value;loadCharts()"> 📅 День</label>' +
        '<label><input type="radio" name="chart-period" value="week" ' + (chartPeriod==='week'?'checked':'') + ' onchange="chartPeriod=this.value;loadCharts()"> 📅 Неделя</label>' +
        '<label><input type="radio" name="chart-period" value="month" ' + (chartPeriod==='month'?'checked':'') + ' onchange="chartPeriod=this.value;loadCharts()"> 📅 Месяц</label>' +
        '<span style="width:1px;height:20px;background:var(--border-color);margin:0 4px;"></span>' +
        '<label><input type="radio" name="chart-mode" value="stack" ' + (chartMode==='stack'?'checked':'') + ' onchange="chartMode=this.value;loadCharts()"> ■ Stacked</label>' +
        '<label><input type="radio" name="chart-mode" value="group" ' + (chartMode==='group'?'checked':'') + ' onchange="chartMode=this.value;loadCharts()"> ▣ Grouped</label>' +
        '</div><div id="chart-container" style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;"></div>';

    fetch('/ofd_abonent/api/charts?inn=' + currentInn + '&period=' + chartPeriod + '&from=' + from + '&to=' + to)
        .then(r => r.json())
        .then(data => {
            renderChart('chart-receipts', '📊 Чеки (шт)', data.labels, data.receipts);
            renderChart('chart-sums', '💰 Суммы (₽)', data.labels, data.sums);
        });
}

function renderChart(divId, title, labels, data) {
    const colors = { cash: '#22c55e', card: '#3b82f6', return: '#eab308', errors: '#ef4444' };
    const keys = ['cash', 'card', 'return', 'errors'];
    const traces = keys.map(k => ({
        type: 'bar', x: labels, y: data[k] || [],
        name: k, marker: { color: colors[k] },
        hovertemplate: '%{y}' + (title.includes('Суммы') ? ' ₽' : ' шт') + '<extra></extra>',
    }));

    const layout = {
        template: 'plotly_dark', paper_bgcolor: '#2d2d2d', plot_bgcolor: '#1a1a1a',
        barmode: chartMode, height: 350,
        margin: { l: 50, r: 20, t: 40, b: 50 },
        hovermode: 'x unified',
        title: { text: title, font: { size: 13 } },
        legend: { orientation: 'h', y: 1.08, x: 0.5, xanchor: 'center', font: { size: 9 } },
        xaxis: { tickangle: -45, nticks: 10, tickfont: { size: 9 } },
        yaxis: { tickfont: { size: 9 } },
    };

    const container = document.getElementById('chart-container');
    const div = document.createElement('div');
    div.id = divId;
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
    if (tab === 'charts' && currentInn) loadCharts();
    if (tab === 'export') renderExport();
}

function renderExport() {
    const el = document.getElementById('oa-export');
    el.innerHTML = '<div class="ta-section"><div class="ta-section-title">📤 Выгрузка данных</div>' +
        '<div style="display:flex;gap:1rem;flex-wrap:wrap;align-items:center;padding:0.5rem;">' +
        '<label>Период: <input type="date" id="export-from" value="' + document.getElementById('oa-from').value + '" style="width:130px"></label>' +
        '<label><input type="date" id="export-to" value="' + document.getElementById('oa-to').value + '" style="width:130px"></label>' +
        '<button class="execute-btn" onclick="doExport(\'xls\')">📥 XLS</button>' +
        '<button class="execute-btn" onclick="doExport(\'csv\')">📥 CSV</button>' +
        '</div></div>';
}

function doExport(fmt) {
    const from = document.getElementById('export-from').value;
    const to = document.getElementById('export-to').value;
    window.open('/ofd_abonent/export/' + fmt + '?inn=' + currentInn + '&from=' + from + '&to=' + to, '_blank');
}

function esc(s) {
    if (s == null) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
