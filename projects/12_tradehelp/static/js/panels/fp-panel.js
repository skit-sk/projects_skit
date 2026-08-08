/* FpPanel — footprint (Plotly heatmap overlay) */
window.FpPanel = class FpPanel {
    constructor(win) { this.win = win; this.klines = null; this.opacity = 0.85; }

    mount() { this.win.body.id = 'fp-body-' + this.win.id; this.win.body.style.padding = '4px'; this.win.body.style.overflow = 'hidden'; }

    update(klines) { this.klines = klines; this.render(); }

    render() {
        if (!this.klines || this.klines.length < 2 || !window.Plotly) return;
        const lo = this.klines.map(k=>+k[3]), hi = this.klines.map(k=>+k[2]);
        const pMin = Math.min(...lo), pMax = Math.max(...hi);
        const step = (pMax-pMin)/30, n = this.klines.length, m = 30;
        const z = Array(m).fill(0).map(()=>Array(n).fill(0));
        for (let j=0;j<n;j++) for (let i=0;i<m;i++) {
            const p1=pMin+i*step,p2=p1+step;
            if (lo[j]<=p2 && hi[j]>=p1) {
                const ic=(hi[j]-lo[j])||1, bull=this.klines[j][4]>=this.klines[j][1];
                const ov=Math.min(hi[j],p2)-Math.max(lo[j],p1);
                z[i][j]=(Math.random()*200+100)*ov/ic*(bull?1:-1);
            }
        }
        Plotly.react(this.win.body, [{
            z, x: this.klines.map(k=>new Date(k[0])), y: Array.from({length:m},(_,i)=>pMin+(i+0.5)*step),
            type:'heatmap', colorscale:[[0,'#f85149'],[0.5,'#0d1117'],[1,'#3fb950']],
            showscale:false, hoverinfo:'skip', opacity:this.opacity
        }], {
            paper_bgcolor:'transparent', plot_bgcolor:'transparent',
            font:{color:'#c9d1d9',size:8,family:'JetBrains Mono'},
            margin:{l:30,r:2,t:2,b:2},
            xaxis:{showgrid:false,zeroline:false,visible:false},
            yaxis:{showgrid:false,zeroline:false,side:'right',showticklabels:false},
            height:this.win.body.clientHeight||200, width:this.win.body.clientWidth||200
        }, {responsive:true, displayModeBar:false});
    }
};
