(function() {
  'use strict';

  const LAB = document.getElementById('vizLab');
  if (!LAB) return;

  const promptInput = document.getElementById('promptInput');
  const analyzeBtn = document.getElementById('analyzeBtn');
  const dropZone = document.getElementById('dropZone');
  const fileInput = document.getElementById('fileInput');
  const fileList = document.getElementById('fileList');
  const addModelBtn = document.getElementById('addModelBtn');

  let currentSessionId = null;
  let uploadedFiles = [];
  let activeModels = ['deepseek-free', 'gemini-2.5-flash', 'gpt-4o-mini', 'tv-screenshot'];

  // ─── Resizable dividers ─────────────────────────────
  initResizable();

  function initResizable() {
    document.querySelectorAll('#dv-left, #dv-right, #dh-center').forEach(function(el) {
      var isVertical = el.classList.contains('divider-v');
      var prev = el.previousElementSibling;
      var next = el.nextElementSibling;
      if (!prev || !next) return;

      el.addEventListener('mousedown', function(e) {
        e.preventDefault();
        el.classList.add('active');
        var startPos = isVertical ? e.clientX : e.clientY;
        var startPrev = isVertical ? prev.offsetWidth : prev.offsetHeight;
        var parent = el.parentElement;
        var total = isVertical ? parent.offsetWidth : parent.offsetHeight;

        function onMove(e2) {
          var pos = isVertical ? e2.clientX : e2.clientY;
          var delta = pos - startPos;
          var newPrev = startPrev + delta;
          var min = 80;
          var dividerSize = isVertical ? el.offsetWidth : el.offsetHeight;
          if (newPrev < min) { newPrev = min; delta = min - startPrev; }
          var remain = total - newPrev - dividerSize;
          if (remain < min) { newPrev = total - min - dividerSize; }
          if (isVertical) {
            prev.style.width = newPrev + 'px';
            prev.style.flex = 'none';
            next.style.flex = '1 1 0%';
            next.style.width = 'auto';
          } else {
            prev.style.height = newPrev + 'px';
            prev.style.flex = 'none';
            next.style.flex = '1 1 0%';
            next.style.height = 'auto';
          }
        }

        function onUp() {
          el.classList.remove('active');
          document.removeEventListener('mousemove', onMove);
          document.removeEventListener('mouseup', onUp);
        }

        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
      });
    });
  }

  // Sync currentSessionId when session is deleted via tree
  document.addEventListener('viz-session-changed', function() {
    if (!window.__vizLabSessionId) currentSessionId = null;
  });

  async function ensureSession(forceNew) {
    if (forceNew || !currentSessionId) {
      try {
        const resp = await fetch('/viz-lab/api/session', { method: 'POST' });
        const data = await resp.json();
        currentSessionId = data.session_id;
        window.__vizLabSessionId = currentSessionId;
        sessionStorage.setItem('viz_lab_session', currentSessionId);
        document.dispatchEvent(new CustomEvent('viz-session-changed'));
        return currentSessionId;
      } catch (e) {
        console.error('Failed to create session:', e);
        return null;
      }
    }
    return currentSessionId;
  }

  // ─── Output Types ──────────────────────────────────────
  LAB.querySelectorAll('.output-btn').forEach(btn => {
    btn.addEventListener('click', () => btn.classList.toggle('selected'));
  });

  // ─── Source files from checkboxes ──────────────────────
  let sourceFiles = [];
  document.addEventListener('source-files-changed', (e) => {
    sourceFiles = e.detail.files;
  });

  // ─── Model Cards ───────────────────────────────────────
  function updateModelCards() {
    const container = document.getElementById('modelCards');
    const cards = container.querySelectorAll('.model-card');
    cards.forEach(card => {
      const model = card.dataset.model;
      card.classList.toggle('selected', activeModels.includes(model));
    });
  }

  // Toggle model on/off by clicking the card (not action buttons)
  LAB.addEventListener('click', function(e) {
    const card = e.target.closest('.model-card');
    if (!card) return;
    if (e.target.closest('.card-actions')) return;
    const model = card.dataset.model;
    const idx = activeModels.indexOf(model);
    if (idx >= 0) {
      activeModels.splice(idx, 1);
      card.classList.remove('selected');
    } else {
      activeModels.push(model);
      card.classList.add('selected');
    }
  });

  LAB.querySelectorAll('.model-card .card-remove').forEach(el => {
    el.addEventListener('click', (e) => {
      e.stopPropagation();
      const card = el.closest('.model-card');
      const model = card.dataset.model;
      activeModels = activeModels.filter(m => m !== model);
      card.remove();
    });
  });

  LAB.querySelectorAll('.model-card .card-settings').forEach(el => {
    el.addEventListener('click', (e) => {
      e.stopPropagation();
      const card = el.closest('.model-card');
      const model = card.dataset.model;
      openSettings(model);
    });
  });

  // Set title on existing model cards
  LAB.querySelectorAll('.model-card').forEach(card => {
    if (!card.title) card.title = card.dataset.model || '';
  });

  // ─── Add Model ─────────────────────────────────────────
  addModelBtn?.addEventListener('click', openAddModel);

  async function openAddModel() {
    const modal = document.getElementById('addModelModal');
    const provSelect = document.getElementById('addProviderSelect');
    const modelSelect = document.getElementById('addModelSelect');
    const searchRow = document.getElementById('addModelSearchRow');
    const searchInput = document.getElementById('addModelSearch');
    modal.classList.remove('hidden');
    searchRow.style.display = 'none';
    searchInput.value = '';
    delete modelSelect._allModels;

    try {
      const resp = await fetch('/ai-models/api/providers');
      const data = await resp.json();
      provSelect.innerHTML = '<option value="">Select provider...</option>';
      (data.providers || []).forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.id;
        opt.textContent = `${p.label} (${p.models_count})`;
        opt.title = p.id;
        provSelect.appendChild(opt);
      });
    } catch (e) {
      provSelect.innerHTML = '<option>Failed to load providers</option>';
    }
    modelSelect.innerHTML = '<option value="">Select provider first</option>';

    function renderModels(models, query) {
      modelSelect.innerHTML = '';
      const tokens = (query || '').toLowerCase().split(/\s+/).filter(Boolean);
      let added = 0;
      models.forEach(m => {
        const mid = m.name || m.id;
        const text = ((m.name || '') + ' ' + m.id + ' ' + (m.name || '')).toLowerCase();
        if (tokens.length && !tokens.every(function(t) { return text.includes(t); })) return;
        if (!activeModels.includes(mid) && !activeModels.includes(m.id)) {
          const opt = document.createElement('option');
          opt.value = mid;
          opt.textContent = `${mid} (${m.type || '?'})`;
          opt.title = mid;
          modelSelect.appendChild(opt);
          added++;
        }
      });
      if (modelSelect.options.length === 0) {
        modelSelect.innerHTML = '<option value="">' + (query ? 'No matches' : 'All models already added') + '</option>';
      } else if (!query) {
        modelSelect.insertBefore(new Option('— ' + added + ' models available —', ''), modelSelect.firstChild);
      }
    }

    provSelect.onchange = async () => {
      const pid = provSelect.value;
      if (!pid) { modelSelect.innerHTML = '<option value="">Select provider first</option>'; searchRow.style.display = 'none'; return; }
      modelSelect.innerHTML = '<option value="">⏳ Loading...</option>';
      searchInput.value = '';
      try {
        const resp = await fetch(`/ai-models/api/models?provider_id=${pid}&limit=200`);
        if (!resp.ok) {
          const errBody = await resp.text().catch(() => '');
          throw new Error(`HTTP ${resp.status}: ${errBody.slice(0, 100)}`);
        }
        const data = await resp.json();
        const models = data.models || [];
        modelSelect._allModels = models;
        if (models.length === 0) {
          modelSelect.innerHTML = '<option value="">No models for this provider</option>';
          searchRow.style.display = 'none';
          return;
        }
        searchRow.style.display = 'block';
        renderModels(models, '');
      } catch (e) {
        console.error('Model load error:', e);
        modelSelect.innerHTML = `<option value="">❌ ${e.message}</option>`;
        searchRow.style.display = 'none';
      }
    };

    searchInput.oninput = function() {
      const models = modelSelect._allModels || [];
      renderModels(models, this.value);
    };
  }

  document.getElementById('confirmAddModel')?.addEventListener('click', () => {
    const model = document.getElementById('addModelSelect').value;
    if (!model) return;
    if (!activeModels.includes(model)) {
      activeModels.push(model);
      const container = document.getElementById('modelCards');
      const card = document.createElement('div');
      card.className = 'model-card selected';
      card.dataset.model = model;
      card.title = model;
      card.innerHTML = `
        <span class="card-name">✦ ${model}</span>
        <span class="card-actions">
          <span class="card-settings" title="Settings">⚙</span>
          <span class="card-remove" title="Remove">✕</span>
        </span>
      `;
      card.querySelector('.card-remove').addEventListener('click', (e) => {
        e.stopPropagation();
        activeModels = activeModels.filter(m => m !== model);
        card.remove();
      });
      card.querySelector('.card-settings').addEventListener('click', (e) => {
        e.stopPropagation();
        openSettings(model);
      });
      container.insertBefore(card, addModelBtn);
    }
    document.getElementById('addModelModal').classList.add('hidden');
  });

  // ─── Model settings (preferred output types) ──────────
  let modelSettings = {};
  try {
    const saved = sessionStorage.getItem('viz_lab_model_settings');
    if (saved) modelSettings = JSON.parse(saved);
  } catch(e) {}

  function saveModelSettingsToStorage() {
    try {
      sessionStorage.setItem('viz_lab_model_settings', JSON.stringify(modelSettings));
    } catch(e) {}
  }

  async function openSettings(model) {
    const modal = document.getElementById('modelSettingsModal');
    modal.classList.remove('hidden');
    document.getElementById('settingsModelName').textContent = model;
    document.getElementById('settingsProvider').textContent = 'Loading...';

    const prefs = modelSettings[model] || ['documentation', 'image', 'presentation'];
    document.querySelectorAll('#settingsOutputTypes input[type="checkbox"]').forEach(cb => {
      cb.checked = prefs.includes(cb.dataset.ot);
    });

    try {
      const resp = await fetch(`/ai-models/api/models?search=${model}&limit=5`);
      const data = await resp.json();
      const found = (data.models || []).find(m => m.id === model);
      if (found) {
        document.getElementById('settingsProvider').textContent = found.provider_label || found.provider_id || '—';
      }
    } catch (e) {}

    document.getElementById('saveModelSettings').onclick = () => {
      const checked = [];
      document.querySelectorAll('#settingsOutputTypes input[type="checkbox"]:checked').forEach(cb => {
        checked.push(cb.dataset.ot);
      });
      modelSettings[model] = checked;
      saveModelSettingsToStorage();
      modal.classList.add('hidden');
    };
  }

  // ─── Generate ──────────────────────────────────────────
  analyzeBtn.addEventListener('click', async () => {
    const prompt = promptInput.value.trim();
    if (!prompt) { promptInput.focus(); return; }

    const outputTypes = [];
    LAB.querySelectorAll('.output-btn.selected').forEach(btn => {
      outputTypes.push(btn.dataset.type);
    });

    const newSess = document.getElementById('newSessionCb')?.checked || false;
    const sessionId = await ensureSession(newSess);
    if (window.addUserMessage) {
      window.addUserMessage(prompt, activeModels);
    }

    activeModels.forEach(m => {
      if (window.addThinkingIndicator) window.addThinkingIndicator(m);
    });

    analyzeBtn.disabled = true;
    analyzeBtn.textContent = '⏳ Generating...';

    try {
      const resp = await fetch(`/viz-lab/api/session/${sessionId}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: prompt,
          models: activeModels,
          output_types: outputTypes,
          files: uploadedFiles,
          source_files: sourceFiles,
        }),
      });
      const data = await resp.json();

      if (window.removeThinkingIndicator) window.removeThinkingIndicator();

      if (data.transcription) {
        const tr = data.transcription;
        if (window.addModelResponse) {
          const lines = [
            `⛓ Chain: ${tr.chain || 'local-whisper'}`,
            `🤖 Model: ${tr.model || '—'}`,
            `⏱ Duration: ${(tr.duration || 0).toFixed(1)}s`,
            `🔤 Tokens: ${tr.tokens || 0}`,
            tr.output ? `📄 ${tr.output.split('/').pop()}` : '',
            '',
            tr.summary ? `📝 ${tr.summary}` : `📝 ${(tr.text || '').substring(0, 300)}`,
          ].filter(Boolean);
          window.addModelResponse({
            model: tr.chain ? `${tr.chain}/${tr.model}` : (tr.model || 'transcription'),
            text: lines.join('\n'),
          });
        }
        if (window.__vizLabSessionId) {
          document.dispatchEvent(new CustomEvent('viz-session-changed'));
        }
      }

      if (data.results) {
        data.results.forEach(result => {
          if (window.addModelResponse) window.addModelResponse(result);
          if (result.files && result.files.length > 0) {
            result.files.forEach(f => {
              if (window.addGalleryItem) {
                window.addGalleryItem({
                  provider: result.provider || 'unknown',
                  model: result.model || 'result',
                  format: f.name.split('.').pop() || 'html',
                  size: f.name,
                  url: null,
                  metrics: result.metrics,
                });
              }
            });
          } else if (result.script) {
            if (window.addGalleryItem) {
              window.addGalleryItem({
                provider: result.provider || 'unknown',
                model: result.model || 'result',
                format: 'py',
                size: result.script.length + ' chars',
                url: null,
                metrics: result.metrics,
              });
            }
          }
        });
      }
      if (data.results && window.__vizLabSessionId) {
        document.dispatchEvent(new CustomEvent('viz-session-changed'));
      }
    } catch (e) {
      console.error('Generation failed:', e);
      if (window.removeThinkingIndicator) window.removeThinkingIndicator();
      if (window.addModelResponse) {
        window.addModelResponse({ model: 'system', text: 'Error: ' + e.message });
      }
    } finally {
      analyzeBtn.disabled = false;
      analyzeBtn.textContent = '🚀 Generate';
    }
  });

  // ─── Drag & Drop ───────────────────────────────────────
  dropZone.addEventListener('click', () => fileInput.click());
  dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('drag-over'); });
  dropZone.addEventListener('dragleave', () => { dropZone.classList.remove('drag-over'); });
  dropZone.addEventListener('drop', (e) => { e.preventDefault(); dropZone.classList.remove('drag-over'); handleFiles(e.dataTransfer.files); });
  fileInput.addEventListener('change', () => { handleFiles(fileInput.files); fileInput.value = ''; });

  async function handleFiles(files) {
    const sessionId = await ensureSession();
    Array.from(files).forEach(file => {
      uploadedFiles.push({ name: file.name, size: file.size, type: file.type });
      addFileItem(file, sessionId);
      uploadFileToServer(file, sessionId);
    });
  }

  async function uploadFileToServer(file, sessionId) {
    const formData = new FormData();
    formData.append('file', file);
    try {
      await fetch(`/viz-lab/api/session/${sessionId}/upload`, { method: 'POST', body: formData });
      document.dispatchEvent(new CustomEvent('viz-session-changed'));
    } catch (e) { console.error('Upload error:', e); }
  }

  function addFileItem(file, sessionId) {
    const item = document.createElement('div');
    item.className = 'file-item';
    const icon = file.type.startsWith('image') ? '🖼' : '📄';
    item.innerHTML = `<span>${icon}</span><span>${file.name}</span><span class="file-status" style="font-size:10px;color:var(--text-muted)">⏳</span><span class="remove" data-name="${file.name}">✕</span>`;
    item.querySelector('.remove').addEventListener('click', async () => {
      item.remove();
      uploadedFiles = uploadedFiles.filter(f => f.name !== file.name);
      if (sessionId) {
        try {
          await fetch(`/viz-lab/api/session/${sessionId}/files/${encodeURIComponent(file.name)}`, { method: 'DELETE' });
          document.dispatchEvent(new CustomEvent('viz-session-changed'));
        } catch(e) {}
      }
    });
    fileList.appendChild(item);
    setTimeout(() => { const s = item.querySelector('.file-status'); if (s) s.textContent = '✓'; }, 500);
  }

  // ─── Shortcut ──────────────────────────────────────────
  promptInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); analyzeBtn.click(); }
  });

  // ─── Clear ─────────────────────────────────────────────
  document.getElementById('clearMessagesBtn')?.addEventListener('click', () => {
    document.getElementById('messages').innerHTML = '<div class="messages-empty">Responses from models will appear here</div>';
  });
  document.getElementById('clearGalleryBtn')?.addEventListener('click', () => {
    document.getElementById('previewGallery').innerHTML = '<div class="gallery-empty">Select output types and models, then Generate</div>';
    const btn = document.getElementById('downloadAllBtn');
    if (btn) btn.disabled = true;
  });

  // ─── File Preview ──────────────────────────────────────
  document.addEventListener('file-selected', async (e) => {
    const filePath = e.detail.path;
    const previewPanel = document.getElementById('filePreview');
    if (!previewPanel) return;
    previewPanel.classList.remove('hidden');
    previewPanel.innerHTML = '<div class="preview-loading">Loading...</div>';
    try {
      const resp = await fetch(`/viz-lab/api/file-content?path=${encodeURIComponent(filePath)}`);
      const data = await resp.json();
      if (data.type === 'text') {
        previewPanel.innerHTML = `<div class="preview-toolbar"><span>${filePath.split('/').pop()}</span><span class="preview-meta">${data.lines} lines · ${formatSize(data.size)}${data.truncated ? ' · truncated' : ''}</span><button class="btn-small preview-close">✕</button></div><pre class="preview-content"><code>${escapeHtml(data.content)}</code></pre>`;
      } else if (data.type === 'image') {
        previewPanel.innerHTML = `<div class="preview-toolbar"><span>${filePath.split('/').pop()}</span><button class="btn-small preview-close">✕</button></div><img src="${data.url}" class="preview-image">`;
      } else {
        previewPanel.innerHTML = `<div class="preview-toolbar"><span>${filePath.split('/').pop()}</span><span class="preview-meta">${formatSize(data.size)} · binary</span><button class="btn-small preview-close">✕</button></div><div class="preview-binary">Binary file</div>`;
      }
      previewPanel.querySelector('.preview-close')?.addEventListener('click', () => previewPanel.classList.add('hidden'));
    } catch (e) { previewPanel.innerHTML = '<div class="preview-error">Failed to load preview</div>'; }
  });

  function formatSize(bytes) {
    if (!bytes) return '0 B';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  }

  function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // ─── Close modals ──────────────────────────────────────
  document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', () => btn.closest('.modal').classList.add('hidden'));
  });
  document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => { if (e.target === modal) modal.classList.add('hidden'); });
  });

  console.log('Viz Lab v2 initialized');
})();
