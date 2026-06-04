(function() {
  'use strict';

  const treeContainer = document.getElementById('projectTree');
  if (!treeContainer) return;

  let checkedFiles = [];
  if (!window.__trash) window.__trash = {};
  var TRASH_KEY = 'global_viz_trash';

  function getSessionId() {
    if (window.__vizLabSessionId) return window.__vizLabSessionId;
    return sessionStorage.getItem('viz_lab_session');
  }

  addTreeHeader();
  loadSessions();

  function addTreeHeader() {
    var header = document.createElement('div');
    header.style.cssText = 'display:flex;justify-content:space-between;align-items:center;padding:4px 8px;';
    header.innerHTML = '<span style="font-size:11px;font-weight:600;">📁 Sessions</span>' +
      '<div style="display:flex;gap:2px;">' +
      '<button id="treeNewProjectBtn" style="background:none;border:none;cursor:pointer;font-size:12px;padding:2px 4px;border-radius:3px;" title="New Project">📁+</button>' +
      '<button id="treeRefreshBtn" style="background:none;border:none;cursor:pointer;font-size:14px;padding:2px 4px;border-radius:3px;" title="Refresh">🔄</button>' +
      '</div>';
    treeContainer.parentElement?.insertBefore(header, treeContainer);
    document.getElementById('treeRefreshBtn')?.addEventListener('click', function() { loadSessions(); });
    document.getElementById('treeNewProjectBtn')?.addEventListener('click', function() { createNewProject(); });
  }

  function createNewProject() {
    var sid = getSessionId();
    if (!sid) { alert('No active session. Run Generate first.'); return; }
    fetch('/viz-lab/api/session/' + sid + '/project', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({}),
    }).then(function(r) { return r.json(); }).then(function() {
      document.dispatchEvent(new CustomEvent('viz-session-changed'));
    }).catch(function() {});
  }

  async function loadSessions() {
    try {
      var resp = await fetch('/viz-lab/api/sessions');
      var data = await resp.json();
      renderSessions(data.sessions || []);
    } catch(e) {
      treeContainer.innerHTML = '<div class="tree-empty" style="padding:20px;text-align:center;color:var(--text-muted);font-size:12px;">📂 No sessions</div>';
    }
  }

  function isTrashed(name, path) {
    return (window.__trash[TRASH_KEY] || []).some(function(f) { return f.name === name || f.path === path; });
  }

  function renderSessions(sessions) {
    treeContainer.innerHTML = '';
    var root = createNode('sessions', '📂', true, true);

    // Add current session as first node
    var curSid = getSessionId();
    if (curSid) {
      var sessNode = createNode(curSid.substring(0, 22), '📁', true, true);
      sessNode.querySelector('.tree-label').title = curSid;
      loadProjectsIntoSess(sessNode, curSid);
      root.querySelector('.tree-children').appendChild(sessNode);
    }

    // Add other sessions
    sessions.forEach(function(s) {
      if (s.id === curSid) return;
      var sNode = createNode(s.id.substring(0, 22), '📁', false, false);
      sNode.querySelector('.tree-label').title = s.id;
      var delSess = document.createElement('span');
      delSess.textContent = '🗑';
      delSess.style.cssText = 'cursor:pointer;margin-left:auto;font-size:10px;opacity:0.4;';
      delSess.title = 'Delete session';
      delSess.addEventListener('click', function(e) {
        e.stopPropagation();
        if (!confirm('Delete session ' + s.id + '?\nAll files will be permanently deleted.')) return;
        fetch('/viz-lab/api/session/' + s.id, { method: 'DELETE' }).then(function(r) { return r.json(); }).then(function() {
          if (window.__vizLabSessionId === s.id) {
            window.__vizLabSessionId = null;
            sessionStorage.removeItem('viz_lab_session');
          }
          loadSessions();
        }).catch(function() {});
      });
      sNode.querySelector('.tree-label').appendChild(delSess);
      loadProjectsIntoSess(sNode, s.id);
      root.querySelector('.tree-children').appendChild(sNode);
    });

    treeContainer.appendChild(root);
  }

  async function loadProjectsIntoSess(sessNode, sid) {
    try {
      var resp = await fetch('/viz-lab/api/session/' + sid + '/projects');
      var data = await resp.json();
      (data.projects || []).forEach(function(p) {
        var pNode = createNode(p.name || p.id, '📂', true, false);
        pNode.querySelector('.tree-label').title = p.id;
        // Delete project button
        var delP = document.createElement('span');
        delP.textContent = '✕';
        delP.style.cssText = 'cursor:pointer;margin-left:auto;font-size:9px;opacity:0.4;';
        delP.title = 'Delete project';
        delP.addEventListener('click', function(e) {
          e.stopPropagation();
          if (!confirm('Delete project ' + (p.name || p.id) + '?')) return;
          fetch('/viz-lab/api/session/' + sid + '/project/' + p.id, { method: 'DELETE' }).then(function(r) { return r.json(); }).then(function() {
            document.dispatchEvent(new CustomEvent('viz-session-changed'));
          }).catch(function() {});
        });
        pNode.querySelector('.tree-label').appendChild(delP);
        loadProjectFiles(pNode, sid, p.id);
        sessNode.querySelector('.tree-children').appendChild(pNode);
      });
    } catch(e) {}
  }

  async function loadProjectFiles(pNode, sid, pid) {
    var inputFolder = createNode('input', '📥', true, false);
    try {
      var r = await fetch('/viz-lab/api/session/' + sid + '/project/' + pid + '/input-files');
      var data = await r.json();
      (data.files || []).forEach(function(f) {
        if (isTrashed(f.filename, f.full_path || f.filename)) return;
        inputFolder.querySelector('.tree-children').appendChild(
          createFileNode(f.filename, f.full_path || f.filename, true)
        );
      });
    } catch(e) {}

    var historyFolder = createNode('history', '📜', true, false);
    try {
      var r = await fetch('/viz-lab/api/session/' + sid + '/project/' + pid + '/history');
      var data = await r.json();
      (data.files || []).forEach(function(f) {
        if (isTrashed(f.name, f.path)) return;
        historyFolder.querySelector('.tree-children').appendChild(
          createFileNode(f.name, f.path, false)
        );
      });
    } catch(e) {}

    var resultsFolder = createNode('results', '📦', true, false);
    try {
      var r = await fetch('/viz-lab/api/session/' + sid + '/project/' + pid + '/results');
      var data = await r.json();
      (data.files || []).forEach(function(f) {
        if (isTrashed(f.name, f.path)) return;
        resultsFolder.querySelector('.tree-children').appendChild(
          createFileNode(f.name, f.path, false)
        );
      });
    } catch(e) {}

    var trashFolder = createNode('trash', '🗑', true, false);
    var trashItems = window.__trash[TRASH_KEY] || [];
    if (trashItems.length > 0) {
      trashItems.forEach(function(f) {
        var node = createFileNode(f.name, f.path, false);
        node.querySelector('.tree-label').querySelectorAll('span').forEach(function(span) {
          if (span.textContent === '🗑') {
            span.textContent = '💣';
            span.title = 'Delete permanently';
            span.addEventListener('click', function(e2) {
              e2.stopPropagation();
              deleteFilePermanently(f.name, f.path);
            });
          }
        });
        trashFolder.querySelector('.tree-children').appendChild(node);
      });
      var clearRow = document.createElement('div');
      clearRow.className = 'tree-node';
      var clearLabel = document.createElement('div');
      clearLabel.className = 'tree-label';
      clearLabel.style.cssText = 'padding:2px 4px;font-size:10px;color:var(--text-muted);cursor:pointer;';
      clearLabel.textContent = '🧹 Clear trash';
      clearLabel.title = 'Permanently delete all trashed files';
      clearLabel.addEventListener('click', function() { clearTrash(); });
      clearRow.appendChild(clearLabel);
      trashFolder.querySelector('.tree-children').appendChild(clearRow);
    }

    pNode.querySelector('.tree-children').appendChild(inputFolder);
    pNode.querySelector('.tree-children').appendChild(historyFolder);
    pNode.querySelector('.tree-children').appendChild(resultsFolder);
    pNode.querySelector('.tree-children').appendChild(trashFolder);
  }

  // ─── Backward compat: handle old routes that need sid input-files/history/results
  // These are handled by redirecting to current project in the route

  function deleteFilePermanently(name, path) {
    var sid = getSessionId();
    fetch('/viz-lab/api/session/' + sid + '/files/remove-by-path', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ path: path }),
    }).then(function(r) { return r.json(); }).then(function() {
      if (window.__trash[TRASH_KEY]) {
        window.__trash[TRASH_KEY] = window.__trash[TRASH_KEY].filter(function(f) { return f.name !== name; });
      }
      document.dispatchEvent(new CustomEvent('viz-session-changed'));
    }).catch(function() {});
  }

  function clearTrash() {
    var items = window.__trash[TRASH_KEY] || [];
    var sid = getSessionId();
    if (!sid) return;
    var promises = [];
    items.forEach(function(f) {
      promises.push(
        fetch('/viz-lab/api/session/' + sid + '/files/remove-by-path', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ path: f.path }),
        }).then(function(r) { return r.json(); })
      );
    });
    Promise.all(promises).then(function() {
      delete window.__trash[TRASH_KEY];
      document.dispatchEvent(new CustomEvent('viz-session-changed'));
    }).catch(function() {});
  }

  function createNode(label, icon, expandable, expanded) {
    var wrapper = document.createElement('div');
    wrapper.className = 'tree-node';
    var labelEl = document.createElement('div');
    labelEl.className = 'tree-label';
    if (expandable) {
      var toggle = document.createElement('span');
      toggle.className = 'toggle';
      toggle.textContent = expanded ? '▼' : '▶';
      labelEl.appendChild(toggle);
    } else {
      var spacer = document.createElement('span');
      spacer.style.width = '14px';
      labelEl.appendChild(spacer);
    }
    var iconEl = document.createElement('span');
    iconEl.className = 'icon';
    iconEl.textContent = icon;
    labelEl.appendChild(iconEl);
    var nameEl = document.createElement('span');
    nameEl.className = 'name';
    nameEl.textContent = label;
    nameEl.title = label;
    labelEl.appendChild(nameEl);
    var childContainer = document.createElement('div');
    childContainer.className = 'tree-children';
    childContainer.style.display = expanded ? 'block' : 'none';
    if (expandable) {
      labelEl.addEventListener('click', function() {
        var isHidden = childContainer.style.display === 'none';
        childContainer.style.display = isHidden ? 'block' : 'none';
        var t = labelEl.querySelector('.toggle');
        if (t) t.textContent = isHidden ? '▼' : '▶';
      });
    }
    wrapper.appendChild(labelEl);
    wrapper.appendChild(childContainer);
    return wrapper;
  }

  function createFileNode(name, path, withCheckbox) {
    var wrapper = document.createElement('div');
    wrapper.className = 'tree-node';
    wrapper.title = path || name;
    var label = document.createElement('div');
    label.className = 'tree-label';
    var spacer = document.createElement('span');
    spacer.style.width = '14px';
    label.appendChild(spacer);
    var ext = name.split('.').pop()?.toLowerCase();
    var icons = { py:'🐍', js:'📜', html:'🌐', css:'🎨', json:'📋', csv:'📊', png:'🖼', svg:'🖼', md:'📝', txt:'📄', mp3:'🎵', mp4:'🎬' };
    var icon = document.createElement('span');
    icon.className = 'icon';
    icon.textContent = icons[ext] || '📄';
    label.appendChild(icon);
    var nameEl = document.createElement('span');
    nameEl.className = 'name';
    nameEl.textContent = name;
    nameEl.title = name;
    label.appendChild(nameEl);
    if (withCheckbox) {
      var cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.style.marginLeft = 'auto';
      cb.dataset.name = name;
      cb.dataset.path = path;
      cb.addEventListener('change', function() {
        if (cb.checked) {
          if (!checkedFiles.find(function(f) { return f.name === name; })) checkedFiles.push({ name: name, path: path });
        } else {
          checkedFiles = checkedFiles.filter(function(f) { return f.name !== name; });
        }
        document.dispatchEvent(new CustomEvent('source-files-changed', { detail: { files: checkedFiles } }));
      });
      label.appendChild(cb);
    } else {
      label.addEventListener('dblclick', function() {
        document.dispatchEvent(new CustomEvent('file-selected', { detail: { path: path, name: name, size: 0 } }));
      });
    }
    var delBtn = document.createElement('span');
    delBtn.textContent = '🗑';
    delBtn.style.cssText = 'cursor:pointer;margin-left:4px;font-size:10px;opacity:0.5;';
    delBtn.title = 'Move to trash';
    delBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      if (!window.__trash[TRASH_KEY]) window.__trash[TRASH_KEY] = [];
      if (!window.__trash[TRASH_KEY].find(function(f) { return f.name === name; })) {
        window.__trash[TRASH_KEY].push({ name: name, path: path, source: withCheckbox ? 'input' : 'other' });
      }
      wrapper.remove();
      document.dispatchEvent(new CustomEvent('viz-session-changed'));
    });
    label.appendChild(delBtn);
    wrapper.appendChild(label);
    return wrapper;
  }

  window.getCheckedSourceFiles = function() { return checkedFiles; };

  document.addEventListener('viz-session-changed', function() { loadSessions(); });

  console.log('Session tree v2 initialized');
})();
