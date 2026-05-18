import json, os, sys
from .base import load_data, enrich_summary, legend

def plot(data, height=14):
    if not data:
        return ''
    mn, mx = min(data), max(data)
    rng = mx - mn or 1
    lines = []
    for i in range(height, 0, -1):
        th = mn + rng * i / height
        line = ''
        for v in data:
            if v >= th:
                line += '█'
            elif v >= th - rng / height * 0.5:
                line += '▄'
            else:
                line += ' '
        lines.append(f'{mn + rng * i / height:8.4f} ┤{line}')
    lines.append(f'{"":>8} └{"─" * min(len(data), 60)}')
    return '\n'.join(lines)

def plot_multi(series, labels, height=14):
    if not series:
        return ''
    all_v = [v for s in series for v in s]
    mn, mx = min(all_v), max(all_v)
    rng = mx - mn or 1
    chars = ['█', '▓', '▒', '░']
    lines = []
    for i in range(height, 0, -1):
        th = mn + rng * i / height
        l = ''
        for si, s in enumerate(series):
            c = chars[si % len(chars)]
            for v in s:
                l += c if v >= th else ' '
        lines.append(f'{mn + rng * i / height:8.4f} ┤{l}')
    lines.append(f'{"":>8} └{"─" * min(len(series[0]) * len(series), 60)}')
    lines.append(f'  Legend: {", ".join(f"{chars[i%len(chars)]}={labels[i]}" for i in range(len(series)))}')
    return '\n'.join(lines)

def generate(data_path, output_dir):
    m = enrich_summary(load_data(data_path))
    r = m.get('raw', {})
    d = m.get('daily', {})
    close = r.get('close', [])
    high = r.get('high', [])
    low = r.get('low', [])
    dev = d.get('deviation_pct', [])
    s = m.get('summary', {})

    if len(close) < 2:
        return {'error': f'Not enough data ({len(close)} points)'}

    leg = legend(m)
    limit = 55
    close_d = close[-limit:]
    high_d = high[-limit:]
    low_d = low[-limit:]
    dev_d = dev[-limit:] if dev else []

    charts = []

    # 1 ─ Close Price
    c1 = plot(close_d)
    h1 = f'═ ASCII: {m["symbol"]} Close Price ({len(close_d)} days) ═\n{leg}\n{"═" * 50}\n'
    h1 += f'Min: {s.get("min_close",0):.4f}  Max: {s.get("max_close",0):.4f}  '
    h1 += f'Change: {s.get("price_change_pct",0):+.1f}%\n{"─" * 50}\n'
    charts.append({'id': 'close', 'title': '📈 Close', 'content': h1 + c1})

    # 2 ─ High/Low Range
    if high_d and low_d:
        c2 = plot_multi([high_d, low_d], ['High', 'Low'])
        h2 = f'═ ASCII: {m["symbol"]} High/Low Range ═\n{leg}\n{"═" * 50}\n'
        charts.append({'id': 'range', 'title': '📊 Range', 'content': h2 + c2})

    # 3 ─ Deviation %
    if dev_d:
        c3 = plot(dev_d)
        h3 = f'═ ASCII: {m["symbol"]} Deviation % ═\n{leg}\n{"═" * 50}\n'
        charts.append({'id': 'deviation', 'title': '📐 Deviation', 'content': h3 + c3})

    out_file = os.path.join(output_dir, 'asciichart', f"{m['symbol']}_charts.txt")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    full = '\n\n'.join(f'=== {c["title"]} ===\n{c["content"]}' for c in charts)
    with open(out_file, 'w') as f:
        f.write(full)

    return {'file': out_file, 'content': full, 'symbol': m['symbol'], 'charts': charts}

if __name__ == '__main__':
    generate(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'outputs')
