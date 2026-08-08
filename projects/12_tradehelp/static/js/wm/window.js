/* Window class — panel in CSS Grid workspace */
window.Window = class Window {
    constructor(id, config) {
        this.id = id;
        this.config = config;
        this.state = {
            visible: config.defVis !== false,
            locked: false,
            gridCol: config.defCol || 1,
            gridRow: config.defRow || 1,
            gridColSpan: config.defColSpan || 1,
            gridRowSpan: config.defRowSpan || 1,
            z: 1,
            opacity: 1
        };
        this.root = null;
        this.body = null;
        this.header = null;
        this.panel = null;
    }

    mount(container) {
        this.root = document.createElement('div');
        this.root.className = 'window';
        this.root.dataset.windowId = this.id;
        this.root.style.opacity = this.state.opacity;

        this.header = document.createElement('div');
        this.header.className = 'window-header';
        this.header.draggable = true;
        const c = this.config;
        this.header.innerHTML = `
            <span class="wh-marker" style="background:${c.color}"></span>
            <span class="wh-icon">${c.icon}</span>
            <span class="wh-title">${c.title} #${c.number}</span>
            <span class="wh-context">${c.defSym || 'BTCUSDT'}</span>
            <span class="wh-spacer"></span>
            <button class="wh-btn wh-lock" title="Lock position">🔓</button>
            <button class="wh-btn wh-close" title="Close">✕</button>
        `;

        this.body = document.createElement('div');
        this.body.className = 'window-body';

        this.root.appendChild(this.header);
        this.root.appendChild(this.body);

        // Resize handle (bottom-right corner)
        this.resizer = document.createElement('div');
        this.resizer.className = 'window-resizer';
        this.resizer.title = 'Drag to resize';
        this.root.appendChild(this.resizer);

        container.appendChild(this.root);

        // Panel init
        const PanelClass = this.config.panelClass;
        if (PanelClass) {
            this.panel = new PanelClass(this);
            this.panel.mount();
        }

        // Header buttons
        this.header.querySelector('.wh-lock').onclick = e => { e.stopPropagation(); this.toggleLock(); };
        this.header.querySelector('.wh-close').onclick = e => {
            e.stopPropagation();
            this.setVisible(false);
            document.dispatchEvent(new CustomEvent('wm:closed', { detail: { id: this.id } }));
        };

        // ResizeObserver for panel
        if (window.ResizeObserver) {
            new ResizeObserver(() => {
                if (this.panel && this.state.visible && this.panel.resize) this.panel.resize();
            }).observe(this.body);
        }

        return this;
    }

    setVisible(v) {
        this.state.visible = v;
        if (this.root) this.root.style.display = v ? '' : 'none';
        if (v && this.panel && this.panel.resize) setTimeout(() => this.panel.resize(), 50);
    }

    toggleLock() {
        this.state.locked = !this.state.locked;
        if (this.header) {
            this.header.querySelector('.wh-lock').textContent = this.state.locked ? '🔒' : '🔓';
        }
    }

    setOpacity(o) { this.state.opacity = o; if (this.root) this.root.style.opacity = o; }
    setZ(z) { this.state.z = z; if (this.root) this.root.style.zIndex = z; }
    destroy() { if (this.root && this.root.parentNode) this.root.parentNode.removeChild(this.root); }
};
