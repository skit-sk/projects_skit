/* Terminal — Bootstrap Window Manager with Grid layout */
(function () {
    'use strict';

    const $ = id => document.getElementById(id);
    const WM_CFG = {
        chart: { title:'Chart', icon:'📊', color:'#58a6ff', number:1, panelClass:window.ChartPanel, defVis:true, defCol:1, defRow:1, defColSpan:1, defRowSpan:1 },
        ob:    { title:'Order Book', icon:'📋', color:'#3fb950', number:2, panelClass:window.ObPanel, defVis:false, defCol:1, defRow:1, defColSpan:1, defRowSpan:1 },
        lh:    { title:'Liquidity', icon:'🌊', color:'#bc8cff', number:3, panelClass:window.LhPanel, defVis:false, defCol:1, defRow:1, defColSpan:1, defRowSpan:1 },
        fp:    { title:'Footprint', icon:'🦶', color:'#f0883e', number:4, panelClass:window.FpPanel, defVis:false, defCol:1, defRow:1, defColSpan:1, defRowSpan:1 }
    };

    const ws = $('workspace');
    const wm = new WindowManager(ws);
    const fetcher = new DataFetcher({});
    let ctxSym = 'BTCUSDT';

    function loadGrid() {
        try {
            const s = localStorage.getItem('terminal-grid');
            if (s) { const p = JSON.parse(s); return p; }
        } catch (e) {}
        return { cols: 1, rows: 1 };
    }

    function saveGrid() {
        try {
            const state = {
                cols: wm.gridCols, rows: wm.gridRows,
                colWidths: wm.getColWidths ? wm.getColWidths() : null,
                rowHeights: wm.getRowHeights ? wm.getRowHeights() : null
            };
            localStorage.setItem('terminal-grid', JSON.stringify(state));
        } catch (e) {}
    }

    /* Create windows */
    Object.entries(WM_CFG).forEach(([id, cfg]) => {
        const w = new Window(id, cfg);
        w.mount(ws);
        wm.add(w);
        if (!cfg.defVis) w.setVisible(false);
    });

    function updateBtn(id) {
        const w = wm.get(id);
        if (!w) return;
        $(`btn-${id}`).classList.toggle('tb-active', w.state.visible);
    }

    function toggleWin(id) {
        wm.toggle(id);
        setTimeout(() => { updateBtn(id); save(); }, 10);
    }

    function updateContext() {
        wm.windows.forEach(w => {
            const el = w.header && w.header.querySelector('.wh-context');
            if (el) el.textContent = ctxSym;
        });
    }

    /* Toolbar */
    $('btn-chart').onclick = () => toggleWin('chart');
    $('btn-ob').onclick = () => toggleWin('ob');
    $('btn-lh').onclick = () => toggleWin('lh');
    $('btn-fp').onclick = () => toggleWin('fp');

    const gridSel = $('grid-select');
    gridSel.onchange = () => {
        const parts = gridSel.value.split('x');
        wm.setGrid(+parts[0], +parts[1]);
        saveGrid();
        save();
    };

    $('btn-addcol').onclick = () => {
        if (wm.gridCols >= 8) return;
        const w = wm.getColWidths ? wm.getColWidths() : null;
        wm.setGrid(wm.gridCols + 1, wm.gridRows);
        if (w) {
            const avg = Math.max(100, Math.floor(w.reduce((a,b)=>a+b,0) / w.length));
            w.push(avg); wm.setColWidths(w);
        } else { const arr = Array(wm.gridCols).fill(100); wm.setColWidths(arr); }
        saveGrid(); save();
    };

    $('btn-addrow').onclick = () => {
        if (wm.gridRows >= 8) return;
        const h = wm.getRowHeights ? wm.getRowHeights() : null;
        wm.setGrid(wm.gridCols, wm.gridRows + 1);
        if (h) {
            const avg = Math.max(100, Math.floor(h.reduce((a,b)=>a+b,0) / h.length));
            h.push(avg); wm.setRowHeights(h);
        } else { const arr = Array(wm.gridRows).fill(100); wm.setRowHeights(arr); }
        saveGrid(); save();
    };

    $('btn-rmcol').onclick = () => {
        if (wm.gridCols <= 1) return;
        wm.windows.forEach(w => { if (w.state.visible && w.state.gridCol > wm.gridCols - 1) w.state.gridCol = wm.gridCols - 1; });
        wm.setGrid(wm.gridCols - 1, wm.gridRows);
        saveGrid(); save();
    };

    $('btn-rmrow').onclick = () => {
        if (wm.gridRows <= 1) return;
        wm.windows.forEach(w => { if (w.state.visible && w.state.gridRow > wm.gridRows - 1) w.state.gridRow = wm.gridRows - 1; });
        wm.setGrid(wm.gridCols, wm.gridRows - 1);
        saveGrid(); save();
    };

    $('btn-clean').onclick = () => {
        wm.cleanEmpty();
        saveGrid(); save();
    };

    /* Center mode */
    let centerMode = false;
    let lastMid = 0;
    $('btn-center').onclick = () => {
        centerMode = !centerMode;
        $('btn-center').classList.toggle('tb-active', centerMode);
        if (centerMode) centerWindows();
    };

    function centerWindows() {
        const ob = wm.get('ob'); const lh = wm.get('lh'); const ch = wm.get('chart');
        if (lastMid) {
            if (ob && ob.state.visible && ob.panel.centerOnSpread) ob.panel.centerOnSpread();
            if (lh && lh.state.visible && lh.panel.centerOnSpread) lh.panel.centerOnSpread(lastMid);
        }
        if (ch && ch.panel) ch.panel.resize();
    }

    /* Close button sync */
    document.addEventListener('wm:closed', e => {
        updateBtn(e.detail.id);
        wm.syncGrid();
        save();
    });

    /* Update lastMid from OB data */
    fetcher.on('ob', data => {
        const raw = data.raw || data;
        const asks = raw.asks || []; const bids = raw.bids || [];
        if (asks.length && bids.length) {
            const ba = parseFloat(asks[asks.length-1][0]);
            const bb = parseFloat(bids[0][0]);
            if (ba && bb) lastMid = (ba + bb) / 2;
        }
        ['ob', 'lh'].forEach(id => { const w = wm.get(id); if (w && w.state.visible && w.panel) w.panel.update(data); });
        if (centerMode && lastMid) setTimeout(centerWindows, 50);
    });

    $('sym-select').onchange = e => {
        ctxSym = e.target.value;
        updateContext();
        fetcher.setSymbol(ctxSym);
        save();
    };
    $('tf-select').onchange = e => { fetcher.setInterval_(e.target.value); save(); };
    $('aggr-select').onchange = e => {
        const v = e.target.value;
        $('aggr-custom').style.display = v === 'custom' ? 'inline-block' : 'none';
        const bucket = v === 'custom' ? parseFloat($('aggr-custom').value)||0 : parseFloat(v);
        fetcher.setBucket(bucket);
        ['ob','lh'].forEach(id => { const w = wm.get(id); if (w) w.panel.bucket = bucket; });
        save();
    };
    $('aggr-custom').oninput = e => {
        const bucket = parseFloat(e.target.value)||0;
        fetcher.setBucket(bucket);
        ['ob','lh'].forEach(id => { const w = wm.get(id); if (w) w.panel.bucket = bucket; });
        save();
    };
    $('depth-input').oninput = e => {
        const d = Math.max(1, parseInt(e.target.value)||20);
        fetcher.setDepth(d);
        ['ob','lh'].forEach(id => { const w = wm.get(id); if (w) w.panel.depth = d; });
        save();
    };

    /* Workspace resize */
    const wsResize = $('ws-resize');
    let wsDrag = false, wsStartY = 0, wsStartH = 0;
    wsResize.onmousedown = e => {
        wsDrag = true; wsStartY = e.clientY; wsStartH = ws.clientHeight;
        document.body.style.cursor = 'ns-resize'; e.preventDefault();
    };
    document.addEventListener('mousemove', e => {
        if (!wsDrag) return;
        ws.style.height = Math.max(300, Math.min(2000, wsStartH + (e.clientY - wsStartY))) + 'px';
    });
    document.addEventListener('mouseup', () => { if (wsDrag) { wsDrag = false; document.body.style.cursor = ''; } });

    /* Data flow (only klines handler — OB handler moved above) */
    fetcher.on('klines', klines => {
        ['chart', 'fp'].forEach(id => { const w = wm.get(id); if (w && w.state.visible && w.panel) w.panel.update(klines); });
    });

    function save() {
        try { localStorage.setItem('terminal-windows', JSON.stringify(
            [...wm.windows.entries()].map(([id, w]) => [id, {
                visible: w.state.visible,
                col: w.state.gridCol, row: w.state.gridRow,
                colSpan: w.state.gridColSpan, rowSpan: w.state.gridRowSpan
            }])
        )); } catch (e) {}
    }

    /* Init */
    const savedGrid = loadGrid();
    gridSel.value = savedGrid.cols + 'x' + savedGrid.rows;
    wm.setGrid(savedGrid.cols, savedGrid.rows);
    wm.initDragDrop();
    wm.initResize();
    wm.updateGridHandles();

    function syncBtns() { ['chart','ob','lh','fp'].forEach(id => updateBtn(id)); }

    if (savedGrid.colWidths) wm.setColWidths(savedGrid.colWidths);
    if (savedGrid.rowHeights) wm.setRowHeights(savedGrid.rowHeights);

    try {
        const saved = localStorage.getItem('terminal-windows');
        if (saved) {
            JSON.parse(saved).forEach(([id, st]) => {
                const w = wm.get(id);
                if (w) {
                    w.state.visible = st.visible;
                    w.state.gridCol = st.col || 1;
                    w.state.gridRow = st.row || 1;
                    w.state.gridColSpan = st.colSpan || 1;
                    w.state.gridRowSpan = st.rowSpan || 1;
                }
            });
            wm.syncGrid();
        }
    } catch (e) {}

    updateContext();
    syncBtns();
    fetcher.start();
})();
