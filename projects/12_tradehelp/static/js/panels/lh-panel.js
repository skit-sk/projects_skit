/* LhPanel — liquidity heatmap (Plotly hbars) */
window.LhPanel = class LhPanel {
    constructor(win) { this.win = win; this.last = null; this.bucket = 0; this.depth = 20; }

    mount() { this.win.body.id = 'lh-body-' + this.win.id; this.win.body.style.padding = '4px'; this.win.body.style.overflow = 'hidden'; }

    update(data) { this.last = data; this.render(); }

    fmtPrice(p) { return p > 100 ? p.toFixed(2) : p > 1 ? p.toFixed(4) : p.toFixed(6); }

    render() {
        if (!this.last || !window.Plotly) return;
        const raw = this.last.raw || this.last;
        const bs = this.bucket, depth = this.depth;
        const asks = this.aggregate(raw.asks||[], bs).slice(-depth).reverse();
        const bids = this.aggregate(raw.bids||[], bs).slice(-depth).reverse();
        if (!asks.length && !bids.length) return;
        const maxV = Math.max(...[...asks.map(a=>a[1]),...bids.map(b=>b[1])], 0.001);
        const fmtP = p => this.fmtPrice(p);
        const traces = [];
        if (asks.length) traces.push({ type:'bar', orientation:'h', x: asks.map(a=>(a[1]/maxV)*100), y: asks.map(a=>fmtP(a[0])), text: asks.map(a=>fmtP(a[0])), textposition:'inside', textfont:{size:8,color:'#c9d1d9'}, marker:{color:'#f85149',opacity:0.5}, width:0.9, hoverinfo:'skip' });
        if (bids.length) traces.push({ type:'bar', orientation:'h', x: bids.map(b=>(b[1]/maxV)*100), y: bids.map(b=>fmtP(b[0])), text: bids.map(b=>fmtP(b[0])), textposition:'inside', textfont:{size:8,color:'#c9d1d9'}, marker:{color:'#3fb950',opacity:0.5}, width:0.9, hoverinfo:'skip' });
        Plotly.react(this.win.body, traces, {
            paper_bgcolor:'transparent', plot_bgcolor:'transparent', font:{color:'#c9d1d9',size:8,family:'JetBrains Mono'},
            margin:{l:2,r:2,t:2,b:2}, xaxis:{showgrid:false,zeroline:false,visible:false,range:[0,110]},
            yaxis:{showgrid:false,zeroline:false,side:'right',showticklabels:false},
            barmode:'overlay', bargap:0.02, height: this.win.body.clientHeight||200, width: this.win.body.clientWidth||100
        }, {responsive:true, displayModeBar:false});
    }

    centerOnSpread(lastMid) {
        if (!window.Plotly || !this.win.body.data || !lastMid) return;
        const allP = this.win.body.data.reduce((a, t) => a.concat(t.y || []), []);
        if (!allP.length) return;
        const midStr = this.fmtPrice(lastMid);
        let idx = allP.indexOf(midStr);
        if (idx < 0) idx = Math.floor(allP.length / 2);
        const range = Math.max(4, Math.floor(allP.length / 3));
        const lo = Math.max(0, idx - range);
        const hi = Math.min(allP.length - 1, idx + range);
        Plotly.relayout(this.win.body, { 'yaxis.range': [allP[hi], allP[lo]] });
    }

    aggregate(e, bs) {
        if (!bs||bs<=0) return e.map(x=>[+x[0],+x[1]]);
        const bk={}; for(const[p,v]of e){const k=Math.floor(+p/bs)*bs;bk[k]=(bk[k]||0)+ +v;}
        return Object.keys(bk).sort((a,b)=>+a-+b).map(k=>[+k,bk[k]]);
    }
};
