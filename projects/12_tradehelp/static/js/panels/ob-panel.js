/* ObPanel — order book table */
window.ObPanel = class ObPanel {
    constructor(win) { this.win = win; this.last = null; this.bucket = 0; this.depth = 20; }

    mount() {
        this.win.body.innerHTML = `<div class="ob-body"><table class="ob-table"><thead><tr>
            <th class="th-ba">BA</th><th class="th-price">Price</th><th class="th-mid">%Mid</th>
            <th class="th-vol">Vol</th><th class="th-volusdt">Vol$</th><th class="th-cum">CumVol</th><th class="th-cumusdt">CumVol$</th>
        </tr></thead><tbody id="ob-rows-${this.win.id}"></tbody></table></div>`;
        this.rows = this.win.body.querySelector('tbody');
    }

    update(data) { this.last = data; this.render(); }

    render() {
        if (!this.last || !this.rows) return;
        const depth = this.depth;
        const raw = this.last.raw || this.last;
        const bs = this.bucket;
        const asks = this.aggregate(raw.asks || [], bs).slice(-depth).reverse();
        const bids = this.aggregate(raw.bids || [], bs).slice(-depth).reverse();
        const dAsks = asks.slice(0, depth), dBids = bids.slice(0, depth);
        const ba = dAsks.length ? dAsks[dAsks.length-1][0] : 0;
        const bb = dBids.length ? dBids[0][0] : 0;
        const mid = ba && bb ? (ba + bb) / 2 : 0;
        const maxV = Math.max(...[...dAsks.map(a=>a[1]), ...dBids.map(b=>b[1])], 0.001);
        let rows = '';
        let ac = 0, ac$ = 0;
        for (const a of dAsks) { const v=a[1], v$=a[0]*v; ac+=v; ac$+=v$; rows += this.row('A',a[0],v,v$,ac,ac$,mid,maxV); }
        const sp = ba && bb ? ba-bb : 0, spPct = bb ? (sp/bb)*100 : 0;
        rows += `<tr class="ob-row-spread"><td colspan="7">Spread: ${sp.toFixed(2)} (${spPct.toFixed(3)}%) · Mid: ${mid.toFixed(2)}</td></tr>`;
        let bc=0, bc$=0;
        for (let i=dBids.length-1;i>=0;i--) { const b=dBids[i], v=b[1], v$=b[0]*v; bc+=v; bc$+=v$; rows += this.row('B',b[0],v,v$,bc,bc$,mid,maxV); }
        this.rows.innerHTML = rows;
    }

    row(side, p, v, v$, cv, cv$, mid, maxV) {
        const pct = (v/maxV)*100, op = 0.3+(pct/100)*0.5;
        const pm = mid ? ((p-mid)/mid*100) : 0; const ps = pm > 0 ? '+' : '';
        const pc = pm > 0.001 ? 'pos' : pm < -0.001 ? 'neg' : 'zero';
        const cls = side === 'A' ? 'ask' : 'bid';
        const baCls = side === 'A' ? 'td-ba-ask' : 'td-ba-bid';
        const prCls = side === 'A' ? 'price-ask' : 'price-bid';
        const priceStr = p > 100 ? p.toFixed(2) : p > 1 ? p.toFixed(4) : p.toFixed(6);
        return `<tr class="ob-row-${cls}"><td class="td-ba ${baCls}">${side}</td><td class="td-price ${prCls}">${priceStr}</td><td class="td-mid mid-${pc}">${ps}${pm.toFixed(3)}%</td><td class="td-vol"><div class="vol-bar-wrap"><div class="vol-bar vol-bar-${cls}" style="width:${pct}%;opacity:${op}"></div><span class="vol-text">${this.fmt(v)}</span></div></td><td class="td-volusdt">${this.fmt$(v$)}</td><td class="td-cum">${this.fmt(cv)}</td><td class="td-cumusdt">${this.fmt$(cv$)}</td></tr>`;
    }

    aggregate(e, bs) {
        if (!bs || bs <= 0) return e.map(x=>[+x[0],+x[1]]);
        const bk={}; for(const[p,v]of e){const k=Math.floor(+p/bs)*bs;bk[k]=(bk[k]||0)+ +v;}
        return Object.keys(bk).sort((a,b)=>+a-+b).map(k=>[+k,bk[k]]);
    }

    fmt(v) { const n=+v; if(isNaN(n))return'—'; if(n>=1e3)return n.toFixed(2); if(n>=1)return n.toFixed(4); return n.toFixed(6); }
    fmt$(v) { if(v>=1e6)return(v/1e6).toFixed(2)+'M'; if(v>=1e3)return(v/1e3).toFixed(2)+'K'; return v.toFixed(2); }

    centerOnSpread() {
        const body = this.win.body.querySelector('.ob-body') || this.win.body;
        const spread = body.querySelector('.ob-row-spread');
        if (body && spread) {
            const rel = spread.getBoundingClientRect().top - body.getBoundingClientRect().top;
            body.scrollTop = Math.max(0, rel - body.clientHeight / 2);
        }
    }
};
