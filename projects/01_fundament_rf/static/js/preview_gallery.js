(function() {
  'use strict';

  const gallery = document.getElementById('previewGallery');
  if (!gallery) return;

  window.addGalleryItem = function(data) {
    removeEmpty();

    const item = document.createElement('div');
    item.className = 'gallery-item';

    const modelTag = data.provider || 'unknown';
    const modelName = data.model || 'result';
    const ext = data.format || 'html';

    item.innerHTML = `
      <div class="thumb placeholder">
        ${getThumbIcon(ext)}
      </div>
      <div class="meta">
        <span class="model-tag ${modelTag}">${escapeHtml(modelName)}</span>
        <span class="label">.${ext} • ${data.size || '—'}</span>
        ${data.metrics?.duration_ms ? `<span class="label">⏱ ${(data.metrics.duration_ms / 1000).toFixed(1)}s</span>` : ''}
      </div>
    `;

    item.addEventListener('click', () => {
      if (data.url) {
        window.open(data.url, '_blank');
      }
    });

    gallery.appendChild(item);
    const btn = document.getElementById('downloadAllBtn');
    if (btn) btn.disabled = false;
  };

  function getThumbIcon(ext) {
    const icons = { html: '🌐', svg: '🖼', png: '📸', gif: '🎬', mp4: '🎥', pdf: '📕', txt: '📄', json: '📋' };
    return icons[ext] || '📊';
  }

  function removeEmpty() {
    const empty = gallery.querySelector('.gallery-empty');
    if (empty) empty.remove();
  }

  function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
})();
