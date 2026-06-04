(function() {
  'use strict';

  const messagesContainer = document.getElementById('messages');
  if (!messagesContainer) return;

  function removeEmpty() {
    const empty = messagesContainer.querySelector('.messages-empty');
    if (empty) empty.remove();
  }

  window.addUserMessage = function(prompt, models) {
    const card = document.createElement('div');
    card.className = 'message-card';
    const now = new Date().toLocaleTimeString();
    card.innerHTML = `
      <div class="msg-header">
        <span class="msg-model">👤 You</span>
        <span class="msg-time">${now}</span>
      </div>
      <div class="msg-content">${escapeHtml(prompt)}</div>
      <div class="msg-metrics">
        <span>🎯 ${models.length ? models.join(', ') : 'auto-select'}</span>
      </div>
    `;
    messagesContainer.insertBefore(card, messagesContainer.firstChild);
    removeEmpty();
  };

  window.addModelResponse = function(data) {
    const card = document.createElement('div');
    card.className = 'message-card';
    const now = new Date().toLocaleTimeString();

    const model = data.model || 'model';
    const provider = data.provider || '';
    const error = data.error;

    let headerLabel = model;
    if (provider) headerLabel = provider + '/' + model;

    const duration = data.metrics?.duration_ms ? `${(data.metrics.duration_ms / 1000).toFixed(1)}s` : '';
    const tokens = data.metrics?.total_tokens ? `${data.metrics.total_tokens} tok` : '';

    let metricsHtml = '';
    if (duration || tokens) {
      metricsHtml = `<div class="msg-metrics">
        ${duration ? `<span>⏱ ${duration}</span>` : ''}
        ${tokens ? `<span>🔤 ${tokens}</span>` : ''}
      </div>`;
    }

    let contentHtml = '';
    if (error) {
      contentHtml = `<div class="msg-content" style="color:#ef4444;">❌ ${escapeHtml(error.substring(0, 200))}</div>`;
    } else if (data.text) {
      const text = data.text.length > 2000 ? data.text.substring(0, 2000) + '...' : data.text;
      contentHtml = `<div class="msg-content" style="white-space:pre-wrap;font-size:12px;">${escapeHtml(text)}</div>`;
    } else {
      contentHtml = `<div class="msg-content" style="color:var(--text-muted)">(empty response)</div>`;
    }

    const hasFiles = data.files && data.files.length > 0;
    const hasScript = !!data.script;

    card.innerHTML = `
      <div class="msg-header">
        <span class="msg-model">${escapeHtml(headerLabel)}</span>
        <span class="msg-time">${now}</span>
      </div>
      ${contentHtml}
      ${metricsHtml}
      ${hasFiles ? `<div class="msg-metrics"><span>📦 ${data.files.length} file(s)</span></div>` : ''}
      ${hasScript ? `<div class="msg-metrics"><span>📜 script generated</span></div>` : ''}
    `;

    messagesContainer.insertBefore(card, messagesContainer.firstChild);
    removeEmpty();
  };

  window.addThinkingIndicator = function(model) {
    const existing = document.getElementById('thinking-indicator');
    if (existing) {
      const label = existing.querySelector('.msg-model');
      if (label) label.textContent = '⏳ ' + escapeHtml(model);
      return;
    }
    const card = document.createElement('div');
    card.className = 'message-card thinking';
    card.id = 'thinking-indicator';
    card.innerHTML = `
      <div class="msg-header">
        <span class="msg-model">⏳ ${escapeHtml(model)}</span>
        <span class="msg-time">thinking...</span>
      </div>
      <div class="msg-content"><span class="loading-dots">Processing</span></div>
    `;
    messagesContainer.insertBefore(card, messagesContainer.firstChild);
    removeEmpty();
  };

  window.removeThinkingIndicator = function() {
    const el = document.getElementById('thinking-indicator');
    if (el) el.remove();
  };

  function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
})();
