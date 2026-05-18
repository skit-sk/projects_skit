import json, os, sys
from .base import load_data, enrich_summary, legend

BAR = '█'
BAR_G = '🟩'  # green
BAR_R = '🟥'  # red (in terminal fallback to █)

def bar_chart(items, width=36, pos_color=None):
    """items: [(label, value, is_positive?), ...]"""
    if not items:
        return ''
    mx = max(abs(v) for _, v, *_ in items) or 1
    lines = []
    for row in items:
        label = row[0]
        val = row[1]
        is_pos = row[2] if len(row) > 2 else (val >= 0)
        bar_len = int(abs(val) / mx * width)
        char = BAR_G if is_pos and pos_color else BAR_R if not is_pos and pos_color else BAR
        bar = char * max(bar_len, 1)
        sign = '+' if is_pos else ''
        lines.append(f'{label} │{bar} {sign}{val:.4f}')
    return '\n'.join(lines)


def generate(data_path, output_dir):
    m = enrich_summary(load_data(data_path))
    r = m.get('raw', {})
    d = m.get('daily', {})
    close = r.get('close', [])
    vol = r.get('volume', [])
    dev = d.get('deviation_pct', [])
    prof = d.get('profitable', [])
    dates_r = r.get('dates', [])
    dates_d = d.get('dates', [])

    if not close:
        return {'error': 'No data'}

    s = m.get('summary', {})
    leg = legend(m)
    limit = 18

    charts = []

    # 1 ─ Volume bars
    vol_items = [(dates_r[i][-5:], vol[i], True) for i in range(min(limit, len(vol)))]
    c1 = f'═ TERMGRAPH: {m["symbol"]} Volume (first {len(vol_items)} days) ═\n{leg}\n{"─" * 50}\n'
    c1 += bar_chart(vol_items)
    charts.append({'id': 'volume', 'title': '📊 Volume', 'content': c1})

    # 2 ─ Deviation % (color-coded)
    dev_items = [(dates_d[i][-5:], dev[i], prof[i] if i < len(prof) else dev[i] >= 0)
                 for i in range(min(limit, len(dev)))]
    if dev_items:
        c2 = f'═ TERMGRAPH: {m["symbol"]} Deviation % ═\n{leg}\n{"─" * 50}\n'
        c2 += bar_chart(dev_items, pos_color=True)
        charts.append({'id': 'deviation', 'title': '📐 Deviation', 'content': c2})

    # 3 ─ PnL per day (if available)
    if s.get('current_pnl_usdt') is not None:
        # Estimate daily PnL from deviation
        pnl_items = [(dates_d[i][-5:], dev[i] * 0.01 * (s.get('current_pnl_usdt', 1) / max(abs(d) for d in dev) if max(abs(d) for d in dev) else 1),
                      prof[i] if i < len(prof) else dev[i] >= 0)
                     for i in range(min(limit, len(dev)))]
        c3 = f'═ TERMGRAPH: {m["symbol"]} Daily PnL {s.get("current_pnl_usdt",0):+.2f} ═\n{leg}\n{"─" * 50}\n'
        c3 += bar_chart(pnl_items, pos_color=True)
        charts.append({'id': 'pnl', 'title': '💰 PnL', 'content': c3})

    out_file = os.path.join(output_dir, 'termgraph', f"{m['symbol']}_charts.txt")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    full = '\n\n'.join(f'=== {c["title"]} ===\n{c["content"]}' for c in charts)
    with open(out_file, 'w') as f:
        f.write(full)

    return {'file': out_file, 'content': full, 'symbol': m['symbol'], 'charts': charts}

if __name__ == '__main__':
    generate(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'outputs')
