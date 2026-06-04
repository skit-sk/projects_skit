(function() {
  'use strict';

  const PAGE = document.getElementById('modelsPage');
  if (!PAGE) return;

  const tbody = document.getElementById('modelsBody');
  const statsBar = document.getElementById('statsBar');
  const filterProvider = document.getElementById('filterProvider');
  const filterType = document.getElementById('filterType');
  const filterBalance = document.getElementById('filterBalance');
  const searchInput = document.getElementById('searchInput');
  const filterCount = document.getElementById('filterCount');

  let catalogData = null;
  let filteredModels = [];
  let sortColumn = 'name';
  let sortDir = 'asc';
  let aggregation = 'none';
  let aggReverse = false;

  // ─── Load catalog ──────────────────────────────────────
  async function loadCatalog() {
    try {
      const resp = await fetch('/ai-models/api/catalog');
      catalogData = await resp.json();
      render();
    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="9" class="loading-cell">❌ Failed to load: ${e.message}</td></tr>`;
    }
  }

  // ─── Render ────────────────────────────────────────────
  function render() {
    if (!catalogData) return;
    const { stats, providers } = catalogData;
    const byType = stats.by_type || {};
    const byBalance = stats.by_balance || {};

    statsBar.innerHTML = `
      <span>📊 ${stats.total_models} models · ${stats.total_providers} providers · 
      ${Object.entries(byType).map(([k,v]) => `${k}: ${v}`).join(' · ')} · 
      Balance: ${Object.entries(byBalance).map(([k,v]) => `${k} (${v})`).join(', ')}</span>
    `;
    if (catalogData.errors && catalogData.errors.length) {
      statsBar.innerHTML += `<span style="color:#fca5a5;margin-left:12px;">⚠ ${catalogData.errors.length} errors</span>`;
    }

    renderProviderFilter(providers);
    _renderTypeFilter(byType);
    applyFilters();
  }

  function renderProviderFilter(providers) {
    filterProvider.innerHTML = '<option value="">All Providers</option>';
    providers.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = `${p.label} (${p.models_count})`;
      filterProvider.appendChild(opt);
    });
  }

  function _renderTypeFilter(byType) {
    filterType.innerHTML = '<option value="">All Types</option>';
    const sorted = Object.entries(byType).sort((a, b) => b[1] - a[1]);
    sorted.forEach(([type, count]) => {
      const opt = document.createElement('option');
      opt.value = type;
      opt.textContent = `${type} (${count})`;
      filterType.appendChild(opt);
    });
  }

  // ─── Filter ────────────────────────────────────────────
  function applyFilters() {
    if (!catalogData) return;
    let models = catalogData.models || [];

    const pv = filterProvider.value;
    const tp = filterType.value;
    const bl = filterBalance.value;
    const q = searchInput.value.toLowerCase().trim();

    if (pv) models = models.filter(m => m.provider_id === pv);
    if (tp) models = models.filter(m => {
      const mtype = m.type || '';
      const caps = Object.keys(m.capabilities || {}).join(' ');
      return mtype === tp || caps.includes(tp);
    });
    if (bl) {
      const provIds = new Set((catalogData.providers || [])
        .filter(p => p.balance === bl).map(p => p.id));
      models = models.filter(m => provIds.has(m.provider_id));
    }
    if (q) {
      const terms = q.split(/\s+/).filter(Boolean);
      models = models.filter(m => {
        const haystack = (
          (m.id || '') + ' ' +
          (m.name || '') + ' ' +
          (m.provider_id || '') + ' ' +
          (m.provider_label || '') + ' ' +
          Object.keys(m.capabilities || {}).join(' ') + ' ' +
          (m.type || '')
        ).toLowerCase();
        return terms.every(t => haystack.includes(t));
      });
    }

    filteredModels = models;
    filterCount.textContent = `${models.length} models`;
    sortAndRender();
  }

  // ─── Sort ──────────────────────────────────────────────
  function sortModels() {
    if (!sortColumn) return;
    const col = sortColumn;
    filteredModels.sort((a, b) => {
      let va = getSortValue(a, col);
      let vb = getSortValue(b, col);
      if (va == null) va = '';
      if (vb == null) vb = '';
      if (typeof va === 'string') va = va.toLowerCase();
      if (typeof vb === 'string') vb = vb.toLowerCase();
      if (va < vb) return sortDir === 'asc' ? -1 : 1;
      if (va > vb) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
  }

  function getSortValue(m, col) {
    switch (col) {
      case 'name': return m.name || m.id || '';
      case 'provider_label': return m.provider_label || m.provider_id || '';
      case 'type': return m.type || '';
      case 'context': return m.context || 0;
      case 'cost_in': return m.pricing?.input_rub || m.pricing?.per_min || 0;
      case 'cost_out': return m.pricing?.output_rub || 0;
      case 'cost_total': return (m.pricing?.input_rub || 0) + (m.pricing?.output_rub || 0);
      case 'balance': return getProviderBalance(m.provider_id);
      default: return '';
    }
  }

  function sortAndRender() {
    sortModels();
    if (aggregation !== 'none') renderAggregated();
    else renderTable(filteredModels);
  }

  // ─── Aggregation toggle ────────────────────────────────
  function toggleAggregation() {
    const modes = ['none', 'type', 'provider'];
    const idx = modes.indexOf(aggregation);
    aggregation = modes[(idx + 1) % modes.length];
    const btn = document.getElementById('aggBtn');
    if (btn) btn.textContent = '📊 Group: ' + aggregation.charAt(0).toUpperCase() + aggregation.slice(1);
    if (aggregation === 'none') renderTable(filteredModels);
    else renderAggregated();
  }

  function renderAggregated() {
    if (!filteredModels.length) {
      tbody.innerHTML = '<tr><td colspan="9" class="loading-cell">No models match filters</td></tr>';
      return;
    }
    const groups = {};
    const groupKey = aggregation === 'type' ? 'type' : 'provider_id';
    const groupLabel = aggregation === 'type' ? 'type' : 'provider_label';
    let groupIdx = 0;

    filteredModels.forEach(m => {
      const key = m[groupKey] || 'unknown';
      if (!groups[key]) groups[key] = { label: m[groupLabel] || key, models: [] };
      groups[key].models.push(m);
    });

    const sortedKeys = Object.keys(groups).sort();
    let html = '';
    sortedKeys.forEach(key => {
      const g = groups[key];
      const gid = 'grp_' + (groupIdx++);
      html += `<tr class="group-header" data-group="${gid}" style="background:var(--bg-card,#1a1a1a);font-weight:600;">
        <td colspan="9" style="padding:8px 10px;font-size:13px;">
          <span class="group-toggle">▼</span>📁 ${esc(g.label)} (${g.models.length})
        </td>
      </tr>`;
      g.models.forEach((m, i) => {
        html += `<tr class="group-row ${gid}">${renderRowInner(m, i + 1)}</tr>`;
      });
    });
    tbody.innerHTML = html;

    tbody.querySelectorAll('.group-header').forEach(row => {
      row.addEventListener('click', () => {
        const gid = row.dataset.group;
        const rows = tbody.querySelectorAll('.group-row.' + gid);
        if (!rows.length) return;
        const isHidden = rows[0].classList.contains('hidden');
        rows.forEach(r => r.classList.toggle('hidden'));
        const toggle = row.querySelector('.group-toggle');
        if (toggle) toggle.textContent = isHidden ? '▶' : '▼';
      });
    });
  }

  function renderRowInner(m, idx) {
    const types = formatTypes(m);
    const ctx = formatContext(m.context);
    const costIn = formatCost(m, 'in');
    const costOut = formatCost(m, 'out');
    const costTotal = formatCostTotal(m);
    const balance = getProviderBalance(m.provider_id);
    return `<td>${idx}</td>
      <td class="model-name">${esc(m.name || m.id)}</td>
      <td class="provider-label">${esc(m.provider_label || m.provider_id)}</td>
      <td>${types}</td>
      <td class="context-cell">${ctx}</td>
      <td class="cost-cell">${costIn}</td>
      <td class="cost-cell">${costOut}</td>
      <td class="cost-cell">${costTotal}</td>
      <td><span class="balance-badge ${balance}">${balance}</span></td>`;
  }

  // ─── Render table ──────────────────────────────────────
  function renderTable(models) {
    if (!models.length) {
      tbody.innerHTML = '<tr><td colspan="9" class="loading-cell">No models match filters</td></tr>';
      return;
    }
    let html = '';
    models.forEach((m, i) => { html += renderRow(m, i + 1); });
    tbody.innerHTML = html;
  }

  function renderRow(m, idx) {
    return `<tr>${renderRowInner(m, idx)}</tr>`;
  }

  // ─── Formatters ────────────────────────────────────────
  function formatTypes(m) {
    const type = m.type || 'llm';
    const caps = Object.keys(m.capabilities || {});
    const badges = [`<span class="type-badge ${type}">${type}</span>`];
    caps.forEach(c => {
      if (c !== 'text' && c !== type) {
        badges.push(`<span class="type-badge" style="background:#333;color:#aaa;">${c}</span>`);
      }
    });
    return badges.join(' ');
  }

  function formatContext(ctx) {
    if (!ctx) return '—';
    const n = parseInt(ctx);
    if (isNaN(n)) return esc(String(ctx));
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n / 1000).toFixed(0) + 'K';
    return n.toString();
  }

  function formatCost(m, dir) {
    const p = m.pricing;
    if (!p) return '—';
    if (dir === 'in' && p.input_rub != null) return `${p.input_rub}₽`;
    if (dir === 'out' && p.output_rub != null) return `${p.output_rub}₽`;
    if (dir === 'in' && p.per_min != null) return `$${p.per_min}/min`;
    if (dir === 'in' && p.per_hour != null) return `$${p.per_hour}/hr`;
    return '—';
  }

  function formatCostTotal(m) {
    const p = m.pricing;
    if (!p) return '—';
    if (p.input_rub != null && p.output_rub != null) {
      return `${p.input_rub + p.output_rub}₽`;
    }
    if (p.per_min != null) return `$${p.per_min}/min`;
    if (p.per_hour != null) return `$${p.per_hour}/hr`;
    return '—';
  }

  function getProviderBalance(providerId) {
    if (!catalogData) return 'unknown';
    const p = catalogData.providers.find(pr => pr.id === providerId);
    return p ? p.balance : 'unknown';
  }

  function esc(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // ─── Event listeners ───────────────────────────────────
  filterProvider.addEventListener('change', applyFilters);
  filterType.addEventListener('change', applyFilters);
  filterBalance.addEventListener('change', applyFilters);
  searchInput.addEventListener('input', applyFilters);

  // ─── Sort on header click ──────────────────────────────
  document.querySelectorAll('.models-table th').forEach((th, i) => {
    th.style.cursor = 'pointer';
    const cols = ['', 'name', 'provider_label', 'type', 'context', 'cost_in', 'cost_out', 'cost_total', 'balance'];
    const col = cols[i];
    if (!col) return;
    th.addEventListener('click', () => {
      if (sortColumn === col) sortDir = sortDir === 'asc' ? 'desc' : 'asc';
      else { sortColumn = col; sortDir = 'asc'; }
      th.textContent = th.textContent.replace(/ [▲▼]$/, '') + (sortDir === 'asc' ? ' ▲' : ' ▼');
      document.querySelectorAll('.models-table th').forEach(t => {
        if (t !== th) t.textContent = t.textContent.replace(/ [▲▼]$/, '');
      });
      sortAndRender();
    });
  });

  // ─── Aggregation button ────────────────────────────────
  (function addAggBtn() {
    const sb = document.querySelector('.filters-bar');
    if (sb) {
      const btn = document.createElement('button');
      btn.id = 'aggBtn';
      btn.className = 'btn-secondary';
      btn.textContent = '📊 Group: None';
      btn.style.fontSize = '12px';
      btn.style.padding = '5px 10px';
      btn.addEventListener('click', toggleAggregation);
      sb.appendChild(btn);
    }
  })();

  // ─── Refresh JSON ──────────────────────────────────────
  document.getElementById('refreshJsonBtn')?.addEventListener('click', async () => {
    try {
      const resp = await fetch('/ai-models/api/refresh/json', { method: 'POST' });
      const data = await resp.json();
      if (data.status === 'ok') {
        await loadCatalog();
        statsBar.innerHTML += ` <span style="color:#6ee7b7;margin-left:8px;">✓ Refreshed: ${data.updated}</span>`;
      }
    } catch (e) {
      statsBar.innerHTML += ` <span style="color:#fca5a5;margin-left:8px;">❌ ${e.message}</span>`;
    }
  });

  // ─── Online Refresh Modal ──────────────────────────────
  const refreshOnlineBtn = document.getElementById('refreshOnlineBtn');
  const refreshModal = document.getElementById('onlineRefreshModal');
  const refreshSelect = document.getElementById('refreshProviderSelect');
  const startRefreshBtn = document.getElementById('startRefreshBtn');
  const refreshProgress = document.getElementById('refreshProgress');

  refreshOnlineBtn?.addEventListener('click', () => {
    refreshModal.classList.remove('hidden');
    refreshSelect.innerHTML = '<option value="">All providers</option>';
    if (catalogData && catalogData.providers) {
      catalogData.providers.forEach(p => {
        if (p.api_endpoint || p.opencode_prefix) {
          const opt = document.createElement('option');
          opt.value = p.id;
          opt.textContent = `${p.label} (${p.api_endpoint || p.opencode_prefix})`;
          refreshSelect.appendChild(opt);
        }
      });
    }
    refreshProgress.classList.add('hidden');
  });

  startRefreshBtn?.addEventListener('click', async () => {
    const providerId = refreshSelect.value;
    refreshProgress.classList.remove('hidden');
    refreshProgress.innerHTML = '<div class="step">🔄 Starting refresh...</div>';
    startRefreshBtn.disabled = true;
    try {
      const resp = await fetch('/ai-models/api/refresh/online', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider_id: providerId || undefined }),
      });
      const data = await resp.json();
      let html = '';
      for (const [pid, result] of Object.entries(data.results || {})) {
        const icon = result.status === 'ok' ? '✅' : '❌';
        html += `<div class="step ${result.status}">${icon} ${pid}: ${result.status} ${result.count ? `(${result.count} models)` : result.error || ''}</div>`;
      }
      refreshProgress.innerHTML = html;
      await loadCatalog();
    } catch (e) {
      refreshProgress.innerHTML = `<div class="step error">❌ ${e.message}</div>`;
    }
    startRefreshBtn.disabled = false;
  });

  // ─── Add Provider Modal ────────────────────────────────
  const addProviderBtn = document.getElementById('addProviderBtn');
  const addModal = document.getElementById('addProviderModal');
  const testConnBtn = document.getElementById('testConnectionBtn');
  const saveProvBtn = document.getElementById('saveProviderBtn');
  const testResult = document.getElementById('testResult');

  addProviderBtn?.addEventListener('click', () => {
    addModal.classList.remove('hidden');
    testResult.classList.add('hidden');
  });

  testConnBtn?.addEventListener('click', async () => {
    const url = document.getElementById('cpUrl').value;
    const key = document.getElementById('cpKeyVar').value;
    if (!url) return;
    testResult.classList.remove('hidden');
    testResult.className = 'test-result';
    testResult.textContent = 'Testing...';
    try {
      const resp = await fetch('/ai-models/api/providers/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, api_key: key }),
      });
      const data = await resp.json();
      testResult.className = `test-result ${data.status}`;
      testResult.textContent = data.status === 'ok' ? `✅ Connected (${data.code})` : `❌ ${data.error}`;
    } catch (e) {
      testResult.className = 'test-result error';
      testResult.textContent = `❌ ${e.message}`;
    }
  });

  saveProvBtn?.addEventListener('click', async () => {
    const id = document.getElementById('cpId').value.trim();
    if (!id) return alert('Provider ID required');
    const config = {
      id,
      label: document.getElementById('cpLabel').value || id,
      api_endpoint: document.getElementById('cpUrl').value,
      key_var: document.getElementById('cpKeyVar').value,
      models: (document.getElementById('cpModels').value || '').split(',').map(s => s.trim()).filter(Boolean),
      type: document.getElementById('cpType').value,
      pricing_unit: document.getElementById('cpPricing').value,
      balance: 'custom',
      _custom: true,
    };
    try {
      const resp = await fetch('/ai-models/api/providers/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
      const data = await resp.json();
      if (data.status === 'saved') {
        addModal.classList.add('hidden');
        await loadCatalog();
        statsBar.innerHTML += ` <span style="color:#6ee7b7;">✓ Provider ${data.provider_id} saved</span>`;
      }
    } catch (e) {
      alert('Save failed: ' + e.message);
    }
  });

  // ─── Close modals ──────────────────────────────────────
  document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', () => btn.closest('.modal').classList.add('hidden'));
  });
  document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => { if (e.target === modal) modal.classList.add('hidden'); });
  });

  // ─── Init ──────────────────────────────────────────────
  loadCatalog();
  console.log('Model Catalog initialized');
})();
