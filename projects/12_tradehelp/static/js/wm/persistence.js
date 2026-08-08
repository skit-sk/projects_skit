/* Persistence — save/restore window state to localStorage */
window.Persistence = class Persistence {
    static KEY = 'terminal-wm';

    static save(wm) {
        const state = {
            workspaceH: wm.workspace.clientHeight,
            windows: {}
        };
        for (const [id, w] of wm.windows) {
            state.windows[id] = {
                visible: w.state.visible,
                mode: w.state.mode,
                locked: w.state.locked,
                tileW: w.state.tileW,
                tileH: w.state.tileH,
                layerW: w.state.layerW,
                layerH: w.state.layerH,
                layerX: w.state.layerX,
                layerY: w.state.layerY,
                z: w.state.z,
                opacity: w.state.opacity
            };
        }
        try { localStorage.setItem(this.KEY, JSON.stringify(state)); } catch (e) {}
    }

    static load() {
        try {
            const s = localStorage.getItem(this.KEY);
            return s ? JSON.parse(s) : null;
        } catch (e) { return null; }
    }

    static restore(wm) {
        const saved = this.load();
        if (!saved || !saved.windows) return;
        if (saved.workspaceH) wm.workspace.style.height = saved.workspaceH + 'px';
        for (const [id, st] of Object.entries(saved.windows)) {
            const w = wm.get(id);
            if (!w) continue;
            Object.assign(w.state, st);
        }
        wm.applyCurrentLayout();
    }
};
