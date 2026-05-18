import json, os

def load_data(data_path):
    base_dir = os.path.dirname(data_path)
    raw = None
    day = None
    symbol = os.path.basename(base_dir).split('_')[0]

    for fn in os.listdir(base_dir):
        fp = os.path.join(base_dir, fn)
        if fn.endswith('_RAW.json'):
            with open(fp) as f:
                raw = json.load(f)
        elif fn.endswith('_1D.json'):
            with open(fp) as f:
                day = json.load(f)

    result = {'symbol': symbol}

    if raw and 'candles' in raw:
        c = raw['candles']
        result['raw'] = {
            'dates': [i['date'] for i in c],
            'open': [i['open'] for i in c],
            'high': [i['high'] for i in c],
            'low': [i['low'] for i in c],
            'close': [i['close'] for i in c],
            'volume': [i.get('volume', 0) for i in c],
        }

    if day and 'chart_data' in day:
        cd = day['chart_data']
        result['daily'] = {
            'dates': [i['date'] for i in cd],
            'deviation_pct': [i.get('deviation_pct', 0) for i in cd],
            'profitable': [i.get('profitable', False) for i in cd],
        }
        if 'summary' in day:
            result['summary'] = day['summary']
        result['entry_price'] = day.get('entry_price', 0)
        result['leverage'] = day.get('leverage', 1)

    return result


def enrich_summary(m):
    s = dict(m.get('summary') or {})
    d = m.get('daily')
    if d and d.get('dates'):
        total = len(d['dates'])
        prof = sum(1 for p in d['profitable'] if p)
        s['total_days'] = total
        s['profitable_days'] = prof
        s['loss_days'] = total - prof
        s['win_rate'] = round(prof / total * 100, 1) if total else 0

    r = m.get('raw')
    if r and r.get('close'):
        s['min_close'] = min(r['close'])
        s['max_close'] = max(r['close'])
        s['first_close'] = r['close'][0]
        s['last_close'] = r['close'][-1]
        s['price_change_pct'] = round((r['close'][-1] - r['close'][0]) / r['close'][0] * 100, 2)

    m['summary'] = s
    return m


def legend(m, extra=None):
    parts = [f"Symbol: {m['symbol']}"]
    r, s = m.get('raw'), m.get('summary')
    if r and r.get('dates'):
        parts.append(f"{r['dates'][0]} → {r['dates'][-1]} ({len(r['dates'])}d)")
    if s and 'price_change_pct' in s:
        parts.append(f"Chg: {s['price_change_pct']:+.1f}%")
    if s and 'current_roe_pct' in s:
        parts.append(f"ROE: {s['current_roe_pct']:+.1f}%")
    if s and 'current_pnl_usdt' in s:
        parts.append(f"PnL: ${s['current_pnl_usdt']:.2f}")
    if s and 'avg_volatility' in s:
        parts.append(f"Vol: {s['avg_volatility']:.3f}")
    if s and 'win_rate' in s:
        parts.append(f"Win: {s['win_rate']:.0f}%")
    if extra:
        parts.append(extra)
    return ' │ '.join(parts)


def sparkline(data, width=40):
    if not data:
        return ''
    mn, mx = min(data), max(data)
    rng = mx - mn or 1
    ch = '▁▂▃▄▅▆▇█'
    return ''.join(ch[min(int((v - mn) / rng * 7), 7)] for v in data[-width:])
