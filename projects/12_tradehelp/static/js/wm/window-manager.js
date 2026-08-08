/* WindowManager — CSS Grid with handles, drag-drop, resize */
window.WindowManager = class WindowManager {
    constructor(workspace) {
        this.workspace = workspace;
        this.windows = new Map();
        this.gridCols = 2;
        this.gridRows = 2;
        this._handleCleanup = [];
    }

    add(win) { this.windows.set(win.id, win); this.syncGrid(); }
    get(id) { return this.windows.get(id); }

    toggle(id) {
        const w = this.windows.get(id);
        if (!w) return;
        w.setVisible(!w.state.visible);
        this.syncGrid();
    }

    /* Set grid dimensions */
    setGrid(cols, rows) {
        this.gridCols = Math.max(1, Math.min(cols, 8));
        this.gridRows = Math.max(1, Math.min(rows, 8));
        this.workspace.style.setProperty('--g-cols', this.gridCols);
        this.workspace.style.setProperty('--g-rows', this.gridRows);
        this.syncGrid();
        this.updateGridHandles();
    }

    /* Collect all occupied cells including spans */
    _getOccupied() {
        const occ = new Set();
        [...this.windows.values()].filter(w => w.state.visible).forEach(w => {
            for (let c = w.state.gridCol; c < w.state.gridCol + w.state.gridColSpan; c++)
                for (let r = w.state.gridRow; r < w.state.gridRow + w.state.gridRowSpan; r++)
                    occ.add(c + ',' + r);
        });
        return occ;
    }

    /* Find first free cell */
    _findFree(occupied) {
        for (let r = 1; r <= this.gridRows; r++)
            for (let c = 1; c <= this.gridCols; c++)
                if (!occupied.has(c + ',' + r)) return { col: c, row: r };
        return null;
    }

    /* Sync all visible windows to grid */
    syncGrid() {
        const visible = [...this.windows.values()].filter(w => w.state.visible);
        this._clampPositions(visible);
        const occupied = this._getOccupied();

        visible.forEach(w => {
            // Force-allocate new windows (not yet in workspace)
            if (w.root.parentNode !== this.workspace) {
                const free = this._findFree(occupied);
                if (free) {
                    w.state.gridCol = free.col; w.state.gridRow = free.row;
                    w.state.gridColSpan = 1; w.state.gridRowSpan = 1;
                    for (let c = free.col; c < free.col + 1; c++)
                        for (let r = free.row; r < free.row + 1; r++)
                            occupied.add(c + ',' + r);
                }
            }
        });

        visible.forEach(w => {
            const ce = Math.min(w.state.gridCol + w.state.gridColSpan, this.gridCols + 1);
            const re = Math.min(w.state.gridRow + w.state.gridRowSpan, this.gridRows + 1);
            w.root.style.cssText = `grid-column:${w.state.gridCol}/${ce};grid-row:${w.state.gridRow}/${re};opacity:${w.state.opacity};z-index:${w.state.z};display:grid;`;
            w.root.className = 'window';
            if (!this.workspace.contains(w.root)) this.workspace.appendChild(w.root);
        });

        // Empty cell placeholders
        this.workspace.querySelectorAll('.grid-cell-empty').forEach(el => el.remove());
        let seq = 1;
        for (let r = 1; r <= this.gridRows; r++)
            for (let c = 1; c <= this.gridCols; c++)
                if (!occupied.has(c + ',' + r)) {
                    const ph = document.createElement('div');
                    ph.className = 'grid-cell-empty';
                    ph.textContent = seq++;
                    ph.style.gridColumn = c + '/' + (c + 1);
                    ph.style.gridRow = r + '/' + (r + 1);
                    this.workspace.appendChild(ph);
                }

        this.reflowChart();
    }

    _clampPositions(visible) {
        visible.forEach(w => {
            if (w.state.gridCol > this.gridCols) w.state.gridCol = 1;
            if (w.state.gridRow > this.gridRows) w.state.gridRow = 1;
            if (w.state.gridCol + w.state.gridColSpan - 1 > this.gridCols) w.state.gridColSpan = 1;
            if (w.state.gridRow + w.state.gridRowSpan - 1 > this.gridRows) w.state.gridRowSpan = 1;
        });
    }

    /* Move window to a specific grid cell (with span check) */
    moveWindowTo(win, col, row) {
        if (win.state.locked) return;
        const occupant = [...this.windows.values()].find(w => {
            if (!w.state.visible || w === win) return false;
            for (let c = w.state.gridCol; c < w.state.gridCol + w.state.gridColSpan; c++)
                for (let r = w.state.gridRow; r < w.state.gridRow + w.state.gridRowSpan; r++)
                    if (c === col && r === row) return true;
            return false;
        });
        if (occupant) {
            const oC = occupant.state.gridCol, oR = occupant.state.gridRow;
            occupant.state.gridCol = win.state.gridCol; occupant.state.gridRow = win.state.gridRow;
            win.state.gridCol = col; win.state.gridRow = row;
        } else { win.state.gridCol = col; win.state.gridRow = row; }
        this.syncGrid();
    }

    /* -=- Grid Handles -=- */
    updateGridHandles() {
        this._removeHandles();
        for (let c = 1; c <= this.gridCols; c++) {
            const h = document.createElement('div');
            h.className = 'grid-handle grid-handle-c';
            h.style.cssText = `grid-column:${c}/${c+1};grid-row:1/${this.gridRows+1};justify-self:end;z-index:20;`;
            if (c < this.gridCols) {
                h.dataset.idx = c;
                this._attachColDrag(h, c);
            } else {
                h.dataset.idx = this.gridCols;
                this._attachColEdgeDrag(h);
            }
            this.workspace.appendChild(h);
            this._handleCleanup.push(h);
        }
        for (let r = 1; r <= this.gridRows; r++) {
            const h = document.createElement('div');
            h.className = 'grid-handle grid-handle-r';
            h.style.cssText = `grid-column:1/${this.gridCols+1};grid-row:${r}/${r+1};align-self:end;z-index:20;height:8px;`;
            if (r < this.gridRows) {
                h.dataset.idx = r;
                this._attachRowDrag(h, r);
            } else {
                h.dataset.idx = this.gridRows;
                this._attachRowEdgeDrag(h);
            }
            this.workspace.appendChild(h);
            this._handleCleanup.push(h);
        }
    }

    _removeHandles() {
        this._handleCleanup.forEach(h => {
            // Remove all listeners (cloned in _attach*)
            const clone = h.cloneNode(true);
            h.parentNode && h.parentNode.replaceChild(clone, h);
        });
        this._handleCleanup = [];
    }

    _attachColDrag(handle, idx) {
        let drag = false, sx = 0, cw = [];
        const onMove = e => {
            if (!drag) return;
            const dx = e.clientX - sx;
            const a = Math.max(40, (cw[idx-1]||100) + dx);
            const b = Math.max(40, (cw[idx]||100) - dx);
            cw[idx-1] = a; cw[idx] = b;
            this.setColWidths(cw); sx = e.clientX;
        };
        const onUp = () => { drag = false; document.removeEventListener('mousemove', onMove); document.removeEventListener('mouseup', onUp); };
        handle.addEventListener('mousedown', e => { drag = true; sx = e.clientX; cw = this.getColWidths(); e.preventDefault(); document.addEventListener('mousemove', onMove); document.addEventListener('mouseup', onUp); });
    }

    _attachColEdgeDrag(handle) {
        let drag = false, sx = 0, cw = [];
        const onMove = e => {
            if (!drag) return;
            const dx = e.clientX - sx;
            const maxSpace = this.workspace.clientWidth - 2 - (this.gridCols - 1);
            const otherSum = cw.reduce((a,b) => a + b, 0) - (cw[this.gridCols-1]||0);
            cw[this.gridCols - 1] = Math.max(40, Math.min(maxSpace - otherSum, (cw[this.gridCols-1]||100) + dx));
            this.setColWidths(cw); sx = e.clientX;
        };
        const onUp = () => { drag = false; document.removeEventListener('mousemove', onMove); document.removeEventListener('mouseup', onUp); };
        handle.addEventListener('mousedown', e => { drag = true; sx = e.clientX; cw = this.getColWidths(); e.preventDefault(); document.addEventListener('mousemove', onMove); document.addEventListener('mouseup', onUp); });
    }

    _attachRowDrag(handle, idx) {
        let drag = false, sy = 0, rh = [];
        const onMove = e => {
            if (!drag) return;
            const dy = e.clientY - sy;
            const a = Math.max(40, (rh[idx-1]||100) + dy);
            const b = Math.max(40, (rh[idx]||100) - dy);
            rh[idx-1] = a; rh[idx] = b;
            this.setRowHeights(rh); sy = e.clientY;
        };
        const onUp = () => { drag = false; document.removeEventListener('mousemove', onMove); document.removeEventListener('mouseup', onUp); };
        handle.addEventListener('mousedown', e => { drag = true; sy = e.clientY; rh = this.getRowHeights(); e.preventDefault(); document.addEventListener('mousemove', onMove); document.addEventListener('mouseup', onUp); });
    }

    _attachRowEdgeDrag(handle) {
        let drag = false, sy = 0, rh = [];
        const onMove = e => {
            if (!drag) return;
            const dy = e.clientY - sy;
            const maxSpace = this.workspace.clientHeight - 2 - (this.gridRows - 1);
            const otherSum = rh.reduce((a,b) => a + b, 0) - (rh[this.gridRows-1]||0);
            rh[this.gridRows - 1] = Math.max(40, Math.min(maxSpace - otherSum, (rh[this.gridRows-1]||100) + dy));
            this.setRowHeights(rh); sy = e.clientY;
        };
        const onUp = () => { drag = false; document.removeEventListener('mousemove', onMove); document.removeEventListener('mouseup', onUp); };
        handle.addEventListener('mousedown', e => { drag = true; sy = e.clientY; rh = this.getRowHeights(); e.preventDefault(); document.addEventListener('mousemove', onMove); document.addEventListener('mouseup', onUp); });
    }

    getColWidths() { return this._getTrackWidths('column'); }
    getRowHeights() { return this._getTrackWidths('row'); }

    _getTrackWidths(dir) {
        const isCol = dir === 'column';
        const count = isCol ? this.gridCols : this.gridRows;
        const prop = isCol ? 'gridTemplateColumns' : 'gridTemplateRows';
        const style = getComputedStyle(this.workspace);
        const tracks = (style[prop] || '').split(' ').filter(Boolean);
        const result = [];
        const avail = (isCol ? this.workspace.clientWidth : this.workspace.clientHeight) - 2 - (count - 1);
        let pxSum = 0, frCount = 0;
        for (let i = 0; i < Math.min(tracks.length, count); i++) {
            const t = tracks[i];
            if (t.endsWith('px')) { const v = parseInt(t); result[i] = v; pxSum += v; }
            else { result[i] = 0; frCount++; }
        }
        while (result.length < count) { result.push(0); frCount++; }
        const frPx = frCount > 0 ? Math.floor((avail - pxSum) / frCount) : 100;
        return result.map(v => v || Math.max(40, frPx));
    }

    setColWidths(arr) {
        const space = this.workspace.clientWidth - 2 - (this.gridCols - 1);
        let sum = arr.reduce((a,b) => a + b, 0);
        if (sum > space) arr = arr.map(w => Math.floor(w * space / sum));
        this.workspace.style.gridTemplateColumns = arr.map(w => w + 'px').join(' ');
    }

    setRowHeights(arr) {
        const space = this.workspace.clientHeight - 2 - (this.gridRows - 1);
        let sum = arr.reduce((a,b) => a + b, 0);
        if (sum > space) arr = arr.map(h => Math.floor(h * space / sum));
        this.workspace.style.gridTemplateRows = arr.map(h => h + 'px').join(' ');
    }

    /* Clean empty cols/rows */
    cleanEmpty() {
        const occCols = new Set(), occRows = new Set();
        this.windows.forEach(w => {
            if (!w.state.visible) return;
            for (let c = w.state.gridCol; c < w.state.gridCol + w.state.gridColSpan; c++) occCols.add(c);
            for (let r = w.state.gridRow; r < w.state.gridRow + w.state.gridRowSpan; r++) occRows.add(r);
        });
        const newC = Math.max(1, Math.min(Math.max(...occCols) || 1, 8));
        const newR = Math.max(1, Math.min(Math.max(...occRows) || 1, 8));
        this.setGrid(newC, newR);
    }

    /* -=- Init -=- */
    initDragDrop() {
        let draggedWin = null;
        this.workspace.addEventListener('dragstart', e => {
            if (!e.target.closest('.window-header')) return;
            const root = e.target.closest('.window'); if (!root) return;
            const win = this.windows.get(root.dataset.windowId); if (!win || win.state.locked) return;
            draggedWin = win;
            e.dataTransfer.effectAllowed = 'move'; e.dataTransfer.setData('text/plain', win.id);
            root.classList.add('dragging');
        });
        this.workspace.addEventListener('dragend', () => {
            this.workspace.querySelectorAll('.dragging,.drag-over').forEach(el => el.classList.remove('dragging','drag-over'));
            draggedWin = null;
        });
        this.workspace.addEventListener('dragover', e => e.preventDefault());
        this.workspace.addEventListener('drop', e => {
            e.preventDefault();
            this.workspace.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
            if (!draggedWin) return;
            const cw = this.getColWidths();
            const rh = this.getRowHeights();
            const x = e.clientX - this.workspace.getBoundingClientRect().left;
            const y = e.clientY - this.workspace.getBoundingClientRect().top;
            let col = this.gridCols, row = this.gridRows;
            let acc = 1;
            for (let i = 0; i < cw.length; i++) { if (x < acc + cw[i] + (i > 0 ? 1 : 0)) { col = i + 1; break; } acc += cw[i] + 1; }
            acc = 1;
            for (let i = 0; i < rh.length; i++) { if (y < acc + rh[i] + (i > 0 ? 1 : 0)) { row = i + 1; break; } acc += rh[i] + 1; }
            this.moveWindowTo(draggedWin, Math.min(this.gridCols, Math.max(1, col)), Math.min(this.gridRows, Math.max(1, row)));
            draggedWin = null;
        });
    }

    initResize() {
        let rw = null, sx = 0, sy = 0, cx = 0, cy = 0;
        document.addEventListener('mousedown', e => {
            const rz = e.target.closest('.window-resizer'); if (!rz) return;
            const root = rz.closest('.window'); if (!root) return;
            rw = this.windows.get(root.dataset.windowId); if (!rw || rw.state.locked) return;
            sx = e.clientX; sy = e.clientY; cx = rw.state.gridColSpan; cy = rw.state.gridRowSpan; e.preventDefault();
        });
        document.addEventListener('mousemove', e => {
            if (!rw) return;
            const r = this.workspace.getBoundingClientRect();
            const dx = Math.round((e.clientX - sx) / (r.width / this.gridCols));
            const dy = Math.round((e.clientY - sy) / (r.height / this.gridRows));
            rw.state.gridColSpan = Math.max(1, Math.min(cx + dx, this.gridCols - rw.state.gridCol + 1));
            rw.state.gridRowSpan = Math.max(1, Math.min(cy + dy, this.gridRows - rw.state.gridRow + 1));
            this.syncGrid();
        });
        document.addEventListener('mouseup', () => { rw = null; });
    }

    reflowChart() {
        const ch = this.windows.get('chart');
        if (ch && ch.panel && ch.state.visible && ch.panel.resize) ch.panel.resize();
    }
};
