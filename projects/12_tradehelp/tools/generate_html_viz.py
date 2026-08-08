"""TradeHelp — generate HTML viz pages from real OHLCV data.
Generates static .html files with Plotly/lightweight-charts
using real data from project 01.
"""
import json
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path('/home/user_aioc/workspace/projects/12_tradehelp')
HIST = ROOT / 'data' / 'history'
VIZ_DIR = ROOT / 'viz' / 'interactive'
VIZ_DIR.mkdir(parents=True, exist_ok=True)


def load_1d(symbol):
    for p in HIST.glob(f'{symbol}_*/*_1D.json'):
        try:
            with open(p) as f:
                d = json.load(f)
            return d.get('candles', [])
        except Exception:
            pass
    return []


def page_volume_profile(symbol='API3'):
    candles = load_1d(symbol)
    if not candles:
        return
    df = pd.DataFrame(candles)
    df['date'] = pd.to_datetime(df['date'])
    closes = df['close'].values
    highs = df['high'].values
    lows = df['low'].values
    volumes = df['volume'].values
    times = df['date']

    price_min, price_max = lows.min(), highs.max()
    step = (price_max - price_min) / 30 or 0.001
    num = int((price_max - price_min) / step) + 1
    bins = [0.0] * num
    centers = [price_min + (i + 0.5) * step for i in range(num)]
    for i in range(len(df)):
        for j in range(num):
            p1 = price_min + j * step
            p2 = p1 + step
            if lows[i] <= p2 and highs[i] >= p1:
                rng = highs[i] - lows[i] or 1
                bins[j] += volumes[i] * (min(highs[i], p2) - max(lows[i], p1)) / rng

    poc_idx = bins.index(max(bins))
    poc_price = centers[poc_idx]
    sorted_bins = sorted(range(num), key=lambda j: -bins[j])
    total = sum(bins)
    cum = 0
    va_set = set()
    for j in sorted_bins:
        cum += bins[j]
        va_set.add(j)
        if cum >= total * 0.682:
            break
    va_min = min(centers[j] for j in va_set)
    va_max = max(centers[j] for j in va_set)

    fig = make_subplots(rows=1, cols=2, column_widths=[0.78, 0.22], shared_yaxes=True)
    fig.add_trace(go.Candlestick(x=times, open=df['open'], high=highs, low=lows, close=closes,
                                 increasing_line_color='#3fb950', decreasing_line_color='#f85149',
                                 increasing_fillcolor='#3fb950', decreasing_fillcolor='#f85149',
                                 name='OHLC'), row=1, col=1)
    fig.add_hline(y=poc_price, line_color='#d29922', line_width=2, row=1, col=1,
                  annotation_text=f'POC {poc_price:.4f}', annotation_position='top left')
    fig.add_hrect(y0=va_min, y1=va_max, fillcolor='rgba(57,197,207,0.08)', line_width=0, row=1, col=1)
    fig.add_trace(go.Bar(x=bins, y=centers, orientation='h',
                         marker=dict(color='rgba(88,166,255,0.6)'),
                         showlegend=False), row=1, col=2)

    fig.update_layout(
        title=f'Volume Profile · {symbol} · Динамический шаг ATR×0.2',
        template='plotly_dark',
        paper_bgcolor='#0d1117', plot_bgcolor='#161b22',
        font=dict(color='#c9d1d9', family='JetBrains Mono'),
        xaxis=dict(rangeslider=dict(visible=False), gridcolor='#21262d'),
        yaxis=dict(side='right', gridcolor='#21262d'),
        xaxis2=dict(gridcolor='#21262d'),
        height=600,
    )
    out = VIZ_DIR / 'volume_profile.html'
    fig.write_html(str(out), include_plotlyjs='cdn', full_html=True)
    print(f"✓ {out.name}")


if __name__ == '__main__':
    page_volume_profile('API3')
    print("Done.")
