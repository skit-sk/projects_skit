"""charts.py — Генератор ASCII-инфографики для объектов fundament_rf.

Читает данные из fundament_rf/data/card/{SYMBOL}_{uuid}/
Генерирует 13 моделей визуализации через ascii_charts.py + ascii_visuals.py.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

import ascii_charts as ac
import ascii_visuals as av
import indicators as ind


BASE_DIR = Path(__file__).parent
# Vercel: data is inside project dir; local dev: fallback to fundament_rf
FUNDAMENT_DATA_DIR = BASE_DIR / "data"
if not FUNDAMENT_DATA_DIR.exists():
    FUNDAMENT_DATA_DIR = BASE_DIR.parent / "01_fundament_rf" / "data"
if not FUNDAMENT_DATA_DIR.exists():
    FUNDAMENT_DATA_DIR = Path("/home/user_aioc/workspace/projects/01_fundament_rf/data")

# Vercel read-only filesystem: write runtime outputs to /tmp when env var is set
if os.environ.get("DEMO_OUTPUT_DIR"):
    OUTPUT_DIR = Path(os.environ["DEMO_OUTPUT_DIR"])
else:
    OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _find_json_recursive(obj_id: str, suffix: str = "") -> Optional[Path]:
    """Recursively search for {obj_id}{suffix}.json under FUNDAMENT_DATA_DIR."""
    target = f"{obj_id}{suffix}.json"
    if not FUNDAMENT_DATA_DIR.exists():
        return None
    for root, _dirs, files in os.walk(FUNDAMENT_DATA_DIR):
        if target in files:
            return Path(root) / target
    return None


def load_fundament_data(obj_id: str) -> Optional[Dict[str, Any]]:
    """Загрузить JSON объекта из data/ (recursive search)."""
    f = _find_json_recursive(obj_id)
    if f and f.exists():
        with open(f, 'r', encoding='utf-8') as fp:
            return json.load(fp)
    return None


def load_1d_data(obj_id: str) -> Optional[Dict[str, Any]]:
    """Загрузить 1D данные (OHLCV)."""
    f = _find_json_recursive(obj_id, "_1D")
    if f and f.exists():
        with open(f, 'r', encoding='utf-8') as fp:
            return json.load(fp)
    return None


def save_output(symbol: str, name: str, content: str) -> Path:
    """Сохранить ASCII-файл в outputs/{symbol}/."""
    out_dir = OUTPUT_DIR / symbol
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.txt"
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return path


def ensure_symbol_dir(symbol: str) -> Path:
    """Создать директорию outputs/{symbol}/."""
    d = OUTPUT_DIR / symbol
    d.mkdir(parents=True, exist_ok=True)
    return d


# ═══════════════════════════════════════════════════════════
# Модели
# ═══════════════════════════════════════════════════════════

def model_candlestick(obj: Dict, days_1d: Optional[Dict] = None) -> str:
    """1. Свечной график (plotext)."""
    symbol = obj['data']['emoji_entry']['symbol']
    entry_price = obj['data']['emoji_entry']['entry_price']
    leverage = obj['data'].get('leverage', 10)
    title = f"{symbol} — Candlestick (x{leverage})"

    if days_1d and 'days' in days_1d:
        days = days_1d['days']
        dates = [d['date'] for d in days]
        ohlc = []
        for d in days:
            o = d.get('ohlc', {})
            ohlc.append({
                'open': o.get('open', entry_price),
                'high': o.get('high', entry_price),
                'low': o.get('low', entry_price),
                'close': o.get('close', entry_price),
            })
        return ac.plotext_candle(dates, ohlc, title)

    # Fallback: текущие точки (entry, current, max, min)
    current = obj['data']['emoji_upd']['current_price']
    mx = obj['data']['ohlc']['max']['price']
    mn = obj['data']['ohlc']['min']['price']
    dates = ['Entry', 'Current', 'Max', 'Min']
    ohlc = [
        {'open': entry_price, 'high': entry_price, 'low': entry_price, 'close': entry_price},
        {'open': entry_price, 'high': current, 'low': entry_price, 'close': current},
        {'open': entry_price, 'high': mx, 'low': entry_price, 'close': mx},
        {'open': entry_price, 'high': mn, 'low': mn, 'close': mn},
    ]
    return ac.plotext_candle(dates, ohlc, title)


def model_deviation(obj: Dict) -> str:
    """2. Отклонения от entry (error bars + scatter)."""
    symbol = obj['data']['emoji_entry']['symbol']
    entry = obj['data']['emoji_entry']['entry_price']
    current = obj['data']['emoji_upd']['current_price']
    mx = obj['data']['ohlc']['max']
    mn = obj['data']['ohlc']['min']
    stats = obj['data']['stats']
    da = stats.get('da', 76)

    title = f"{symbol} Deviation from Entry ({entry})"

    # Синтетические данные отклонений по дням
    deviations = []
    for i in range(da):
        # Простая интерполяция для демо
        progress = i / da if da else 0
        val = mn['pct'] + (mx['pct'] - mn['pct']) * progress
        noise = (i % 7 - 3) * 0.5  # небольшой шум
        deviations.append(val + noise)
    dates = [f"D{i+1}" for i in range(da)]

    # Пробуем plotext
    out = ac.plotext_error(dates, deviations, title)
    if out and not out.startswith('['):
        return out

    # Fallback: plotille scatter
    return ac.plotille_scatter(list(range(da)), deviations, title)


def model_histogram(obj: Dict) -> str:
    """3. Гистограмма распределения Dn/Dp."""
    symbol = obj['data']['emoji_entry']['symbol']
    mx = obj['data']['ohlc']['max']['pct']
    mn = obj['data']['ohlc']['min']['pct']
    stats = obj['data']['stats']
    dn = stats.get('dn', 0)
    dp = stats.get('dp', 0)
    da = stats.get('da', 76)

    title = f"{symbol} Distribution: Dn({dn}) / Dp({dp}) / Da({da})"

    # Синтетические данные
    data = []
    for _ in range(dn):
        data.append(mn + (0 - mn) * (_ / max(dn, 1)))
    for _ in range(dp):
        data.append(0 + (mx - 0) * (_ / max(dp, 1)))

    out = ac.plotext_hist(data, bins=20, title=title)
    if out and not out.startswith('['):
        return out
    return ac.plotille_hist(data, bins=20, title=title)


def model_box(obj: Dict) -> str:
    """4. Ящик с усами (box plot)."""
    symbol = obj['data']['emoji_entry']['symbol']
    entry = obj['data']['emoji_entry']['entry_price']
    current = obj['data']['emoji_upd']['current_price']
    mx = obj['data']['ohlc']['max']
    mn = obj['data']['ohlc']['min']

    # Box data: [min, q1, median, q3, max, current]
    data = [
        mn['pct'],
        mn['pct'] * 0.5,
        (current - entry) / entry * 100,
        mx['pct'] * 0.5,
        mx['pct'],
    ]

    title = f"{symbol} Box: Min({mn['pct']:.1f}%) → Max({mx['pct']:.1f}%)"
    return ac.plotext_box(data, symbol, title)


def model_range_bar(obj: Dict) -> str:
    """5. Горизонтальный бар диапазона."""
    symbol = obj['data']['emoji_entry']['symbol']
    entry = obj['data']['emoji_entry']['entry_price']
    current = obj['data']['emoji_upd']['current_price']
    mx = obj['data']['ohlc']['max']
    mn = obj['data']['ohlc']['min']

    labels = ['Min', 'Entry', 'Current', 'Max']
    values = [
        (mn['price'] - entry) / entry * 100,
        0,
        (current - entry) / entry * 100,
        (mx['price'] - entry) / entry * 100,
    ]

    title = f"{symbol} Range: Entry={entry} Current={current}"
    out = ac.plotext_bar_h(labels, values, title)
    if out and not out.startswith('['):
        return out

    # Fallback: plotille
    return ac.plotille_range_bar(entry, current, mn['price'], mx['price'], title)


def model_heatmap(obj: Dict) -> str:
    """6. Тепловая карта волатильности."""
    symbol = obj['data']['emoji_entry']['symbol']
    vol = obj['data']['ohlc']['max'].get('volatility', 0.000425)
    stats = obj['data']['stats']
    da = stats.get('da', 76)

    # Матрица 10×N дней
    rows, cols = 10, max(da // 10, 7)
    matrix = []
    for r in range(rows):
        row = []
        for c in range(cols):
            # Симуляция волатильности
            val = abs(vol * (1 + (r - rows/2) * 0.1) * (1 + (c - cols/2) * 0.05))
            row.append(val)
        matrix.append(row)

    title = f"{symbol} Volatility Matrix (σ={vol:.6f})"
    return ac.plotext_matrix(matrix, title)


def model_indicator(obj: Dict) -> str:
    """7. KPI индикатор."""
    symbol = obj['data']['emoji_entry']['symbol']
    pnl_pct = obj['data']['emoji_upd']['pnl_percent']
    pnl_usdt = obj['data']['emoji_upd']['pnl_usdt']
    roe = obj['data']['emoji_upd'].get('roe_usdt', 0)

    label = f"{symbol} ROE"
    delta = f"PnL: {pnl_usdt:.2f} USDT"

    out = ac.plotext_indicator(roe, label)
    if out and not out.startswith('['):
        return out
    return ac.ascii_indicator(roe, label, delta)


def model_subplot(obj: Dict) -> str:
    """8. Сетка subplot 2×3."""
    symbol = obj['data']['emoji_entry']['symbol']
    entry = obj['data']['emoji_entry']['entry_price']
    current = obj['data']['emoji_upd']['current_price']
    mx = obj['data']['ohlc']['max']
    mn = obj['data']['ohlc']['min']
    stats = obj['data']['stats']
    da = stats.get('da', 76)

    # Собрать данные для subplot
    charts_data = {
        'candle': {
            'dates': ['E', 'C', 'Max', 'Min'],
            'ohlc': {
                'Open': [entry, entry, entry, entry],
                'High': [entry, current, mx['price'], mn['price']],
                'Low':  [entry, entry, entry, mn['price']],
                'Close':[entry, current, mx['price'], mn['price']],
            }
        },
        'box': {
            'label': symbol,
            'data': [mn['pct'], mn['pct']*0.5, (current-entry)/entry*100, mx['pct']*0.5, mx['pct']]
        },
        'indicator': {
            'value': obj['data']['emoji_upd'].get('roe_usdt', 0),
            'label': symbol,
        },
        'deviation': {
            'values': list(range(-10, 20, 1)),
        },
        'hist': {
            'data': [mn['pct'] + (mx['pct']-mn['pct'])*(i/da) for i in range(da)],
            'bins': 20,
        },
        'matrix': {
            'data': [[abs(i-j)*0.01 for j in range(10)] for i in range(10)]
        }
    }

    title = f"{symbol} Dashboard — {stats.get('dp',0)}↑ / {stats.get('dn',0)}↓ / {da}d"
    return ac.plotext_subplots(charts_data, title)


# ── Helpers for multi-symbol charts ───────────────────────

def load_all_cards() -> List[Tuple[str, float, float]]:
    """Load all cards: returns [(symbol, roe_pct, pnl_usdt), ...]."""
    results = []
    if not FUNDAMENT_DATA_DIR.exists():
        return results
    for root, _dirs, files in os.walk(FUNDAMENT_DATA_DIR):
        for fname in files:
            if not fname.endswith(".json") or fname.endswith(("_1D.json", "_RAW.json")):
                continue
            f = Path(root) / fname
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    obj = json.load(fp)
                sym = obj['data']['emoji_entry']['symbol']
                roe = obj['data']['emoji_upd'].get('roe_usdt', 0)
                pnl = obj['data']['emoji_upd'].get('pnl_usdt', 0)
                results.append((sym, roe, pnl))
            except Exception:
                continue
    return results


# ═══════════════════════════════════════════════════════════
# Новые модели (ascii_visuals)
# ═══════════════════════════════════════════════════════════

def model_radar(obj: Dict, days_1d: Optional[Dict] = None) -> str:
    """9. Radar chart — multi-metric profile."""
    symbol = obj['data']['emoji_entry']['symbol']
    ohlc = obj['data']['ohlc']
    stats = obj['data']['stats']
    roe = obj['data']['emoji_upd'].get('roe_usdt', 0)
    mx_pct = ohlc['max'].get('pct', 0)
    mn_pct = ohlc['min'].get('pct', 0)

    # Normalize metrics to 0..1
    metrics = {
        "Body%": min(1.0, abs(ohlc['current'].get('body_pct', 0)) / 10),
        "UpperWick": min(1.0, ohlc['current'].get('upper_wick', 0) / 0.001),
        "LowerWick": min(1.0, ohlc['current'].get('lower_wick', 0) / 0.001),
        "Volatility": min(1.0, ohlc['max'].get('volatility', 0) * 1000),
        "Range": min(1.0, (mx_pct - mn_pct) / 100) if mx_pct != mn_pct else 0,
        "ROE": min(1.0, abs(roe) / 100),
    }
    return av.radar_chart(metrics, f"{symbol} — Radar Profile")


def model_waterfall(obj: Dict) -> str:
    """10. Waterfall: Min → Entry → Current cumulative delta."""
    symbol = obj['data']['emoji_entry']['symbol']
    entry = obj['data']['emoji_entry']['entry_price']
    current = obj['data']['emoji_upd']['current_price']
    mx = obj['data']['ohlc']['max']['price']
    mn = obj['data']['ohlc']['min']['price']

    bars = [
        ("Min→Entry", entry - mn),
        ("Entry→Current", current - entry),
        ("Current→Max", mx - current),
    ]
    return av.waterfall_chart(bars, f"{symbol} — Price Path Waterfall")


def model_pareto(obj: Dict) -> str:
    """11. Pareto: all symbols sorted by ROE%."""
    items = load_all_cards()
    # sort by abs ROE descending
    chart_items = [(sym, roe) for sym, roe, _ in items]
    return av.pareto_chart(chart_items, "Portfolio Pareto (ROE %)")


def model_sankey(obj: Dict) -> str:
    """12. Sankey flow: Min → Entry → Current → Max."""
    symbol = obj['data']['emoji_entry']['symbol']
    entry = obj['data']['emoji_entry']['entry_price']
    current = obj['data']['emoji_upd']['current_price']
    mx = obj['data']['ohlc']['max']['price']
    mn = obj['data']['ohlc']['min']['price']

    nodes = [("Min", mn), ("Entry", entry), ("Current", current), ("Max", mx)]
    return av.sankey_flow(nodes, f"{symbol} — Flow Min→Entry→Current→Max")


def model_treemap(obj: Dict) -> str:
    """13. Treemap: position sizes by PnL USDT."""
    items = load_all_cards()
    blocks = [(sym, abs(pnl)) for sym, _, pnl in items]
    return av.treemap_chart(blocks, "Portfolio Treemap (|PnL| USDT)")


def model_indicators(obj: Dict, days_1d: Optional[Dict] = None) -> str:
    """14. Technical indicators overlay (SMA/BB/RSI/MACD) as ASCII."""
    symbol = obj['data']['emoji_entry']['symbol']
    if not days_1d or 'days' not in days_1d:
        return f"{symbol} Indicators\n[no daily data]"

    days = days_1d['days']
    ind_data = ind.compute_all_indicators(days)
    summary = ind.indicator_summary(ind_data)

    lines = [f"{symbol} — Technical Indicators"]
    lines.append("")
    lines.append(f"SMA5:  {summary.get('sma5', 'N/A'):>10}")
    lines.append(f"SMA20: {summary.get('sma20', 'N/A'):>10}")
    lines.append(f"BB Upper: {summary.get('bb_upper', 'N/A'):>10}")
    lines.append(f"BB Lower: {summary.get('bb_lower', 'N/A'):>10}")
    lines.append(f"RSI:   {summary.get('rsi', 'N/A'):>10}")
    lines.append(f"MACD:  {summary.get('macd', 'N/A'):>10}")
    lines.append(f"Signal:{summary.get('macd_signal', 'N/A'):>10}")
    lines.append(f"Anomalies: {summary.get('anomaly_count', 0)}")
    lines.append("")

    # Sparkline of deviation
    dev = ind_data.get('deviation', [])
    if dev:
        lines.append(f"Deviation sparkline: {av.sparkline(dev, 50)}")
        anomalies = ind_data.get('anomalies', [])
        if any(anomalies):
            a_line = "".join("⚠" if a else " " for a in anomalies)
            lines.append(f"Anomaly markers:     {a_line[:50]}")

    # RSI panel
    rsi = ind_data.get('rsi', [])
    if rsi:
        lines.append("")
        lines.append("RSI 0-100 panel:")
        for v in rsi[-20:]:  # last 20 points
            if v is None:
                lines.append("  ---")
            else:
                bar_len = int(v / 2)
                color = av._GREEN if v < 30 else (av._RED if v > 70 else av._YELLOW)
                lines.append(f"  {color}{'█'*bar_len}{av._RST}{'░'*(50-bar_len)} {v:.1f}")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
# Главная функция
# ═══════════════════════════════════════════════════════════

MODELS = [
    ('candlestick', model_candlestick),
    ('deviation', model_deviation),
    ('histogram', model_histogram),
    ('box_plot', model_box),
    ('range_bar', model_range_bar),
    ('heatmap', model_heatmap),
    ('indicator', model_indicator),
    ('subplot_grid', model_subplot),
    ('radar', model_radar),
    ('waterfall', model_waterfall),
    ('pareto', model_pareto),
    ('sankey', model_sankey),
    ('treemap', model_treemap),
    ('indicators', model_indicators),
]


def generate_all(obj_id: str) -> Dict[str, Path]:
    """Сгенерировать все модели для объекта и сохранить в files.
    
    Returns:
        {model_name: Path_to_file, ...}
    """
    obj = load_fundament_data(obj_id)
    if not obj:
        raise FileNotFoundError(f"Object {obj_id} not found in fundament_rf/data/card/")

    symbol = obj['data']['emoji_entry']['symbol']
    days_1d = load_1d_data(obj_id)

    ensure_symbol_dir(symbol)
    results = {}

    for name, func in MODELS:
        if name in ('candlestick', 'radar', 'indicators'):
            content = func(obj, days_1d)
        else:
            content = func(obj)
        path = save_output(symbol, name, content)
        results[name] = path
        print(f"  ✅ {name:20} → {path}")

    return results


def generate_single(obj_id: str, model_name: str) -> Path:
    """Сгенерировать одну модель."""
    obj = load_fundament_data(obj_id)
    if not obj:
        raise FileNotFoundError(f"Object {obj_id} not found")

    symbol = obj['data']['emoji_entry']['symbol']
    func = dict(MODELS).get(model_name)
    if not func:
        raise ValueError(f"Unknown model: {model_name}. Available: {[n for n,_ in MODELS]}")

    days_1d = load_1d_data(obj_id) if model_name in ('candlestick', 'radar', 'indicators') else None
    content = func(obj, days_1d) if days_1d else func(obj)
    return save_output(symbol, model_name, content)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python charts.py <obj_id> [model_name]")
        print("Examples:")
        print("  python charts.py 44e2bfad-d090-46bd-9c73-377d6e44871c")
        print("  python charts.py 44e2bfad-d090-46bd-9c73-377d6e44871c candlestick")
        sys.exit(1)

    obj_id = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else None

    if model:
        path = generate_single(obj_id, model)
        print(f"Generated: {path}")
    else:
        results = generate_all(obj_id)
        print(f"\nDone! {len(results)} charts generated.")
