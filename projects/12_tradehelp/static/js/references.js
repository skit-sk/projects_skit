/* References manager — kanban, CRUD, plan, gallery, tree */
(function () {
    'use strict';

    let data = [];
    const $ = id => document.getElementById(id);
    const KANBAN_STATUS = ['added', 'analyzing', 'done', 'distributed'];

    async function load() {
        const statusEl = document.getElementById('data-status');
        if (statusEl) statusEl.textContent = '⏳ Loading...';
        try {
            const r = await fetch('/references/api/list');
            if (!r.ok) throw new Error('HTTP ' + r.status);
            data = await r.json();
            if (!Array.isArray(data)) throw new Error('API returned non-array');
        } catch (e) {
            console.error('References load error:', e);
            if (statusEl) statusEl.textContent = '❌ Error: ' + e.message;
            data = []; return;
        }
        if (statusEl) statusEl.textContent = `✅ ${data.length} references loaded`;
        render();
    }

    function render() { renderKanban(); renderTable(); renderPlan(); }

    function renderKanban() {
        KANBAN_STATUS.forEach(st => {
            const col = document.getElementById('kb-' + st);
            if (!col) return;
            const items = data.filter(r => r.status === st);
            col.innerHTML = items.map(r => `
                <div class="kb-card" data-id="${esc(r.id)}" draggable="true">
                    <div class="kb-card-head">
                        <span class="kb-prio kb-${(r.priority||'P3').toLowerCase()}">${esc(r.priority||'P3')}</span>
                        <span class="kb-cat">${esc(r.category||'')}</span>
                    </div>
                    <div class="kb-card-title">${esc(r.title||'')}</div>
                    <div class="kb-card-desc">${esc(short(r.description||'', 80))}</div>
                </div>`).join('');
        });
        document.querySelectorAll('.kb-card').forEach(c => {
            c.addEventListener('dragstart', e => { e.dataTransfer.setData('text/plain', c.dataset.id); c.classList.add('dragging'); });
            c.addEventListener('dragend', () => c.classList.remove('dragging'));
        });
        document.querySelectorAll('.kanban-body').forEach(body => {
            body.addEventListener('dragover', e => e.preventDefault());
            body.addEventListener('drop', async e => {
                e.preventDefault();
                const id = e.dataTransfer.getData('text/plain');
                const col = body.closest('.kanban-col');
                if (!col || !id) return;
                const ns = col.dataset.status;
                const ref = data.find(r => r.id === id);
                if (!ref || ref.status === ns) return;
                ref.status = ns;
                await fetch('/references/api/update', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ id, status:ns }) });
                render();
            });
        });
    }

    function renderTable() {
        const tbody = document.getElementById('ref-tbody');
        if (!tbody) return;
        tbody.innerHTML = data.map(r => `
            <tr>
                <td><span class="status-badge st-${r.status||'added'}">${STATUS_LABEL[r.status] || r.status || 'unknown'}</span></td>
                <td><a href="${esc(r.url||'#')}" target="_blank" class="ref-link">${esc(r.title||'')}</a></td>
                <td class="td-desc">${esc(r.description||'')}</td>
                <td>${esc(r.category||'')}</td>
                <td><span class="kb-prio kb-${(r.priority||'P3').toLowerCase()}">${esc(r.priority||'P3')}</span></td>
                <td><button class="rf-btn-sm" onclick="openDetail('${r.id}')">📋</button>
                    <button class="rf-btn-sm" onclick="deleteRef('${r.id}')">✕</button></td>
            </tr>`).join('');
    }

    function renderPlan() {
        const tbody = document.getElementById('plan-tbody');
        if (!tbody) return;
        const rows = [];
        data.forEach(r => { (r.elements || []).forEach(el => { rows.push({...el, source:r.title, priority:r.priority, status:el.status||'planned'}); }); });
        tbody.innerHTML = rows.map(r => `<tr><td>${esc(r.target)}</td><td>${esc(r.name)}</td><td>${esc(r.source)}</td><td><span class="status-badge st-${r.status}">${r.status}</span></td><td><span class="kb-prio kb-${r.priority.toLowerCase()}">${r.priority}</span></td></tr>`).join('');
    }

    /* ── Build tree from pages ── */
    function buildTree(pages, baseUrl) {
        const root = { name: baseUrl, url: baseUrl, children: [], isDir: true };
        pages.forEach(p => {
            if (!p.url || p.url === baseUrl) { root.name = p.title || baseUrl; return; }
            const rel = p.url.replace(baseUrl, '').replace(/\/$/,'');
            const parts = rel.split('/').filter(Boolean);
            if (!parts.length) { root.name = p.title || baseUrl; return; }
            let node = root;
            parts.forEach((part, i) => {
                let child = node.children.find(c => c.name === part || c._part === part);
                if (!child) {
                    child = { _part: part, name: part, url: '', children: [], isDir: true };
                    node.children.push(child);
                }
                if (i === parts.length - 1) {
                    child.isDir = false;
                    child.url = p.url;
                    child.name = p.title || part;
                }
                node = child;
            });
        });
        return root;
    }

    function renderTreeHtml(node, depth) {
        if (!node) return '';
        if (node.isDir) {
            const hasFiles = node.children.some(c => !c.isDir);
            const open = depth < 1 ? ' open' : '';
            return `<details class="tf"${open}><summary class="ts">📁 ${esc(node.name)}</summary>
                ${node.children.map(c => renderTreeHtml(c, depth + 1)).join('')}</details>`;
        }
        return `<div class="tl"><a href="${esc(node.url)}" target="_blank" class="tl-a">📄 ${esc(node.name)}</a></div>`;
    }

    function switchTab(refId, tab) {
        document.querySelectorAll('.ref-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.ref-tc').forEach(t => t.classList.remove('active'));
        document.querySelector(`.ref-tab[data-tab="${tab}"][data-ref="${refId}"]`)?.classList.add('active');
        document.getElementById(`tc-${refId}-${tab}`)?.classList.add('active');
    }
    window.switchTab = switchTab;

    /* ── Detail Modal ── */
    window.openDetail = async function (id) {
        const ref = data.find(r => r.id === id);
        if (!ref) return;
        const modal = document.getElementById('ref-modal');
        const body = document.getElementById('modal-body');
        modal.style.display = 'block';

        let galleryHtml = '', treeHtml = '', hasTabs = false;
        try {
            const tree = await (await fetch(`/static/ref/${ref.id}/tree.json`)).json();
            if (tree.pages && tree.pages.length > 0) {
                window._refPages = window._refPages || {};
                window._refPages[ref.id] = tree.pages;
                galleryHtml = `<div class="ref-gallery">${tree.pages.map((p, i) => `
                    <div class="ref-gallery-item" onclick="window._openLightbox('${ref.id}',${i})">
                        <img src="/${esc(p.screenshot||'')}" loading="lazy" onerror="this.style.display='none'">
                        <span>${esc(p.title||p.slug||'')}</span>
                    </div>`).join('')}</div>`;
                treeHtml = renderTreeHtml(buildTree(tree.pages, tree.url), 0);
                hasTabs = true;
            }
        } catch (e) {}

        body.innerHTML = `
            <div class="modal-close" onclick="closeModal()">✕</div>
            <h2>${esc(ref.title)}</h2>
            <p><a href="${esc(ref.url)}" target="_blank">${esc(ref.url)}</a></p>
            <p><strong>Статус:</strong> <span class="status-badge st-${ref.status}">${STATUS_LABEL[ref.status]||ref.status}</span>
            <strong>Категория:</strong> ${ref.category}
            <strong>Приоритет:</strong> <span class="kb-prio kb-${ref.priority.toLowerCase()}">${ref.priority}</span></p>
            ${hasTabs ? `
            <div class="ref-tabs">
                <button class="ref-tab active" data-ref="${id}" data-tab="gallery" onclick="switchTab('${id}','gallery')">🖼️ Screenshots</button>
                <button class="ref-tab" data-ref="${id}" data-tab="tree" onclick="switchTab('${id}','tree')">🌳 Structure</button>
            </div>
            <div class="ref-tc active" id="tc-${id}-gallery">${galleryHtml || '<div class="muted">No screenshots</div>'}</div>
            <div class="ref-tc" id="tc-${id}-tree">${treeHtml || '<div class="muted">No structure</div>'}</div>` : galleryHtml}
            <hr>
            <label>Описание</label><textarea class="rf-inp rf-ta" id="md-desc">${esc(ref.description)}</textarea>
            <label>Механизм</label><textarea class="rf-inp rf-ta" id="md-mech">${esc(ref.mechanism)}</textarea>
            <label>Заметки</label><textarea class="rf-inp rf-ta" id="md-notes">${esc(ref.notes)}</textarea>
            <label>Статус</label>
            <select class="rf-inp" id="md-status">${KANBAN_STATUS.map(s => `<option value="${s}" ${s===ref.status?'selected':''}>${STATUS_LABEL[s]||s}</option>`).join('')}</select>
            <label>Элементы (JSON)</label><textarea class="rf-inp rf-ta" id="md-elements" rows="4">${esc(JSON.stringify(ref.elements||[],null,2))}</textarea>
            <button class="rf-btn" onclick="saveDetail('${id}')">Сохранить</button>`;
    };

    /* ── Lightbox ── */
    window._openLightbox = function(refId, index) {
        const pages = (window._refPages||{})[refId];
        if (!pages || !pages.length) return;
        window._lb = { refId, index, pages };
        _renderLB();
        document.addEventListener('keydown', _lbKey);
    };
    function _renderLB() {
        const s = window._lb;
        document.getElementById('lb-overlay')?.remove();
        const div = document.createElement('div'); div.id = 'lb-overlay'; div.className = 'lb-overlay';
        div.innerHTML = `
            <div class="lb-bg" onclick="_closeLB()"></div>
            <div class="lb-wrap">
                <button class="lb-btn lb-prv" onclick="_lbNav(-1)">‹</button>
                <img src="/${esc(s.pages[s.index].screenshot)}" class="lb-img" id="lb-img">
                <button class="lb-btn lb-nxt" onclick="_lbNav(1)">›</button>
                <div class="lb-cnt">${s.index+1}/${s.pages.length}</div>
                <button class="lb-x" onclick="_closeLB()">✕</button>
            </div>`;
        document.body.appendChild(div);
    }
    window._lbNav = function(dir) { const s=window._lb; s.index=Math.max(0,Math.min(s.index+dir,s.pages.length-1)); _renderLB(); };
    window._closeLB = function() { document.getElementById('lb-overlay')?.remove(); document.removeEventListener('keydown',_lbKey); };
    function _lbKey(e) { if(e.key==='ArrowLeft')window._lbNav(-1); else if(e.key==='ArrowRight')window._lbNav(1); else if(e.key==='Escape')window._closeLB(); }

    window.saveDetail = async function(id) {
        const ref = data.find(r => r.id === id); if (!ref) return;
        let el; try { el=JSON.parse(document.getElementById('md-elements').value); } catch(e) { el=[]; }
        await fetch('/references/api/update', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({
            id, description:document.getElementById('md-desc').value, mechanism:document.getElementById('md-mech').value,
            notes:document.getElementById('md-notes').value, status:document.getElementById('md-status').value, elements:el
        })});
        closeModal(); await load();
    };
    window.closeModal = function() { document.getElementById('ref-modal').style.display='none'; };
    window.deleteRef = async function(id) {
        if (!confirm('Delete '+id+'?')) return;
        await fetch('/references/api/delete', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({id}) });
        await load();
    };

    function init() {
        document.getElementById('add-btn').onclick = async () => {
            const p = { url:document.getElementById('add-url').value, title:document.getElementById('add-title').value,
                category:document.getElementById('add-category').value, priority:document.getElementById('add-priority').value,
                description:document.getElementById('add-desc').value,
                id:document.getElementById('add-title').value.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'') };
            if (!p.url || !p.title) return alert('URL и название обязательны');
            await fetch('/references/api/add', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(p) });
            document.getElementById('add-url').value=''; document.getElementById('add-title').value=''; document.getElementById('add-desc').value='';
            await load();
        };
        load();
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();

    const STATUS_LABEL = { added:'Добавлено', analyzing:'В анализе', done:'Проработано', distributed:'Распределено' };
    function esc(s) { return String(s||'').replace(/[&<>"]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[m]); }
    function short(s,n) { return (s||'').length > n ? (s||'').slice(0,n)+'…' : (s||''); }
})();
