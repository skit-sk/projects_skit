#!/usr/bin/env python3
"""Генерация 10 новых слайдов MidasFlow Matrix v4.0."""

import json
from pathlib import Path
import sys

ROOT = Path('/home/user_aioc/workspace')

# Путь к скрипту оригинальных слайдов
sys.path.insert(0, str(ROOT / 'workspace'))
sys.path.insert(0, str(ROOT))


# Импортируем базовые функции из основного скрипта
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

DARK = {
    'bg': '#0d1117',
    'bg2': '#161b22',
    'bull': '#3fb950',
    'bear': '#f85149',
    'orange': '#ff9100',
    'cyan': '#00e5ff',
    'yellow': '#d29922',
    'purple': '#bc8cff',
    'text': '#ffffff',
    'dim': '#999999',
}

plt.rcParams.update({
    'figure.facecolor': DARK['bg'],
    'axes.facecolor': DARK['bg2'],
    'axes.edgecolor': '#444466',
    'axes.labelcolor': DARK['text'],
    'axes.titlecolor': DARK['text'],
    'xtick.color': '#999999',
    'ytick.color': '#999999',
    'grid.color': '#333355',
    'grid.alpha': 0.3,
    'text.color': DARK['text'],
    'font.family': 'DejaVu Sans',
    'font.size': 10,
})


def style_ax(ax, title='', xlabel='', ylabel=''):
    ax.set_facecolor(DARK['bg2'])
    ax.set_title(title, color=DARK['text'], fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel(xlabel, color='#999999')
    ax.set_ylabel(ylabel, color='#999999')
    ax.tick_params(colors='#999999')
    ax.grid(True, alpha=0.15, color='#444466')
    for spine in ax.spines.values():
        spine.set_color('#444466')
    return ax


def save(fig, name):
    out = ROOT / 'docs' / 'trading' / f'mf_slide_{name}.png'
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=120, bbox_inches='tight', facecolor=DARK['bg'])
    plt.close(fig)
    print(f"✓ {out.name}")


def slide_31_mf_standards():
    """MidasFlow Matrix v4.0 — Operational Standards"""
    fig, ax = plt.subplots(figsize=(16, 7))
    style_ax(ax, 'MidasFlow Matrix v4.0 — Operational Standards', '')

    # Three pillars
    pillars = [
        ('Naming Convention', 'OB | BB | FVG | LQ | MSS | CHoCH | BOS\nПротокол v1.1.0', DARK['orange']),
        ('3-Tier Architecture', 'Tier 1: Raw\nTier 2: Microstructure\nTier 3: Structural', DARK['cyan']),
        ('Top-Down Protocol', 'D1/H4 → Bias, ERL\nH1 → Structure, BOS, IRL\nM15/M5 → FVG, OB', DARK['purple']),
    ]
    for i, (name, desc, color) in enumerate(pillars):
        x = 0.1 + i * 0.3
        ax.add_patch(mpatches.FancyBboxPatch((x, 0.3), 0.25, 0.55, boxstyle='round,pad=0.02',
                                              facecolor=DARK['bg2'], edgecolor=color, linewidth=2))
        ax.text(x + 0.125, 0.75, name, fontsize=14, fontweight='bold', color=color,
               ha='center', transform=ax.transAxes)
        ax.text(x + 0.125, 0.5, desc, fontsize=10, color=DARK['text'],
               ha='center', transform=ax.transAxes)

    ax.text(0.5, 0.18, 'MidasFlow Matrix v4.0 — единый стандарт для алгоритмического SMC',
           fontsize=14, color=DARK['yellow'], ha='center', transform=ax.transAxes,
           bbox=dict(facecolor='#111122', alpha=0.7, edgecolor=DARK['yellow'], pad=8))

    ax.axis('off')
    save(fig, '31_mf_standards')


def slide_32_fibo_grid():
    """MidasFlow Grid 2.0 — 33 уровня"""
    fig, ax = plt.subplots(figsize=(16, 7))
    style_ax(ax, 'MidasFlow Grid 2.0 — 33 уровня Фибоначчи (-1.0 → 2.618)', '')

    levels = [-1.0, -0.705, -0.5, -0.27, 0, 0.236, 0.5, 0.618, 0.705, 0.786, 1.0, 1.236, 1.5, 1.618, 2.0, 2.618]
    names = ['Full Hunt', 'Max Pain', 'Manip Mid', 'Primary Hunt', 'Range Origin', 'Shadow Ind',
             'Equilibrium', 'OTE Start', 'SNIPER', 'Last Stand', 'INVALIDATION', 'TP 1.236',
             'Expansion Mid', 'WHALE α', 'Cycle Double', 'WHALE β']
    colors = [DARK['bear']] * 4 + [DARK['dim'], DARK['yellow'], DARK['orange'],
                                    DARK['bull'], DARK['bull'], DARK['bull'],
                                    DARK['purple'], DARK['cyan'], DARK['cyan'],
                                    DARK['cyan'], DARK['cyan'], DARK['purple']]

    x = np.arange(len(levels))
    ax.scatter(x, levels, s=300, c=colors, edgecolor=DARK['text'], linewidth=1.5, zorder=3)
    for i, (lvl, name, col) in enumerate(zip(levels, names, colors)):
        ax.text(i, lvl + 0.12 if lvl >= 0 else lvl - 0.12, f'{lvl:.3f}',
               fontsize=8, ha='center', color=DARK['text'])
        ax.text(i, lvl - 0.2 if lvl >= 0 else lvl + 0.2, name,
               fontsize=7, ha='center', color=col, rotation=30)

    ax.axhline(y=0.705, color=DARK['yellow'], linestyle='--', alpha=0.5, label='Sniper Entry (0.705)')
    ax.axhline(y=0, color=DARK['text'], linestyle='-', alpha=0.3)
    ax.axhspan(0.618, 0.786, alpha=0.1, color=DARK['bull'], label='OTE Zone')
    ax.set_xlim(-1, len(levels))
    ax.set_ylim(-1.5, 3.0)
    ax.set_xticks([])
    ax.set_ylabel('Fibonacci Coefficient')
    ax.legend(loc='upper right', fontsize=8, facecolor='#111122', labelcolor=DARK['text'])
    save(fig, '32_fibo_grid')


def slide_33_fractal_ipda():
    """Fractal Mechanics + IPDA"""
    fig, ax = plt.subplots(figsize=(16, 7))
    style_ax(ax, 'Fractal Mechanics + IPDA (Look-back 20/40/60)', '')

    # Top-Down nesting diagram
    levels = [
        ('D1/H4', 'Macro\nBias + ERL', DARK['orange']),
        ('H1', 'Structure\nBOS/CHoCH/MSS', DARK['cyan']),
        ('M15', 'FVG + OB\nIRL', DARK['purple']),
        ('M5', 'Entry\nTrigger', DARK['bull']),
        ('M1', 'Tape\nReading', DARK['yellow']),
    ]
    for i, (tf, desc, col) in enumerate(levels):
        y = 0.85 - i * 0.17
        ax.add_patch(mpatches.FancyBboxPatch((0.05, y - 0.05), 0.25, 0.12,
                                              boxstyle='round,pad=0.01',
                                              facecolor=DARK['bg2'], edgecolor=col, linewidth=1.5))
        ax.text(0.07, y, tf, fontsize=12, fontweight='bold', color=col, transform=ax.transAxes)
        ax.text(0.13, y, desc, fontsize=9, color=DARK['text'], transform=ax.transAxes)

    # IPDA look-back windows
    ax.text(0.4, 0.8, 'IPDA Look-back Periods', fontsize=14, fontweight='bold', color=DARK['yellow'], transform=ax.transAxes)
    periods = [(20, 'Short', DARK['cyan']), (40, 'Mid', DARK['orange']), (60, 'Long', DARK['purple'])]
    for j, (p, name, col) in enumerate(periods):
        y = 0.65 - j * 0.15
        ax.add_patch(mpatches.Rectangle((0.4, y - 0.04), 0.5, 0.08,
                                        facecolor=DARK['bg2'], edgecolor=col, linewidth=1.5))
        ax.text(0.42, y, f'{p} days', fontsize=11, fontweight='bold', color=col, transform=ax.transAxes)
        ax.text(0.5, y, name, fontsize=10, color=DARK['text'], transform=ax.transAxes)
        ax.text(0.55, y, f'Pool of FVG, OB, Liquidity', fontsize=9, color=DARK['dim'], transform=ax.transAxes)

    ax.text(0.5, 0.18, 'Если H4 структура противоречит D1 Bias — пропустить торговый день',
           fontsize=11, color=DARK['bear'], ha='center', transform=ax.transAxes,
           bbox=dict(facecolor='#111122', alpha=0.7, edgecolor=DARK['bear'], pad=6))
    ax.axis('off')
    save(fig, '33_fractal_ipda')


def slide_34_position_engineering():
    """Position Engineering — Scaling In/Out"""
    fig, ax = plt.subplots(figsize=(16, 7))
    style_ax(ax, 'Position Engineering — Scaling In (1/8 → 8/8) + TP (1/4 → 4/4)', '')

    # Scaling In waterfall
    in_steps = ['MSS (0.0)', 'OTE (0.618)', 'BOS (1.0)', 'Final (8/8)']
    in_cum = [0.125, 0.375, 1.0, 1.0]
    in_labels = ['1/8', '+2/8', '+5/8', '=8/8']

    x = np.arange(len(in_steps))
    ax.bar(x, in_cum, color=[DARK['bull'], DARK['cyan'], DARK['orange'], DARK['purple']], alpha=0.8)
    for i, (c, l) in enumerate(zip(in_cum, in_labels)):
        ax.text(i, c + 0.03, l, fontsize=11, fontweight='bold', color=DARK['text'], ha='center')
        ax.text(i, c / 2, in_steps[i], fontsize=8, color=DARK['bg'], ha='center', fontweight='bold')

    # TP levels
    tp_steps = ['TP1 (1.236)', 'TP2 (1.618)', 'TP3 (2.0)', 'TP4 (2.618)']
    tp_cum = [0.25, 0.5, 0.75, 1.0]
    ax2 = ax.twinx()
    ax2.plot(x[:4], tp_cum, color=DARK['yellow'], marker='o', markersize=12, linewidth=2, label='Cumulative TP')
    for i, (c, l) in enumerate(zip(tp_cum, tp_steps)):
        ax2.text(i, c + 0.04, l, fontsize=9, color=DARK['yellow'], ha='center')

    ax.set_xticks(x)
    ax.set_xticklabels(in_steps, color=DARK['text'])
    ax.set_ylabel('Cumulative Position (Sizing In)', color=DARK['bull'])
    ax2.set_ylabel('Cumulative TP (1/4 × 4)', color=DARK['yellow'])
    ax.set_ylim(0, 1.2)
    ax2.set_ylim(0, 1.2)
    ax.set_title('Position Engineering: 1/8 → 8/8 (scaling in) | 1/4 → 4/4 (scaling out)',
                color=DARK['text'], fontsize=14, fontweight='bold')
    save(fig, '34_position_engineering')


def slide_35_crp():
    """Cluster Risk Projection"""
    fig, ax = plt.subplots(figsize=(16, 7))
    style_ax(ax, 'CRP (Cluster Risk Projection) — Wyckoff 15-25 свечей', '')

    np.random.seed(42)
    prices = np.linspace(0.21, 0.32, 30)
    # D-Shape: high in lower third
    center = 0.235
    volumes = 1000 * np.exp(-((prices - center) / 0.015) ** 2) + np.random.rand(30) * 50

    ax.barh(prices, volumes, color=DARK['bull'], alpha=0.6)
    ax.axhline(y=0.235, color=DARK['orange'], linewidth=2, label=f'POC = {center:.4f} (Lower_Third)')
    ax.axhline(y=0.225, color=DARK['cyan'], linestyle='--', label='VAL = 0.225')
    ax.axhline(y=0.295, color=DARK['cyan'], linestyle='--', label='VAH = 0.295')
    ax.axhspan(0.225, 0.295, alpha=0.08, color=DARK['cyan'])

    ax.text(0.5, 0.31, 'D-Shape: Бычье накопление (POC в нижней трети)',
           fontsize=13, color=DARK['bull'], ha='center', transform=ax.transAxes,
           bbox=dict(facecolor='#111122', alpha=0.8, edgecolor=DARK['bull'], pad=6))
    ax.text(0.5, 0.04, '70-80% подтверждённых пробоев делают Pullback к VAH/VAL',
           fontsize=10, color=DARK['dim'], ha='center', transform=ax.transAxes, style='italic')

    ax.set_xlabel('Volume')
    ax.set_ylabel('Price')
    ax.legend(loc='upper right', fontsize=9, facecolor='#111122', labelcolor=DARK['text'])
    save(fig, '35_crp')


def slide_36_shadow_dom():
    """Shadow DOM"""
    fig, ax = plt.subplots(figsize=(16, 7))
    style_ax(ax, 'Shadow DOM — Скрытая плотность лимитных ордеров', '')

    np.random.seed(123)
    times = np.arange(60)
    prices = np.linspace(0.215, 0.31, 30)
    z = np.zeros((30, 60))
    for i in range(30):
        for t in range(60):
            z[i, t] = 0.2 + np.random.rand() * 0.3
    # Add icebergs (3 spikes)
    iceberg_idx = [10, 17, 23]
    for idx in iceberg_idx:
        z[idx, 10:50] = 0.85 + np.random.rand(40) * 0.15

    im = ax.imshow(z, aspect='auto', cmap='RdYlGn',
                   extent=[0, 60, prices[-1], prices[0]])
    for idx in iceberg_idx:
        p = prices[idx]
        ax.axhline(y=p, color=DARK['yellow'], linestyle='--', linewidth=2)
        ax.text(58, p, '🧊', fontsize=14, va='center', ha='left')

    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Price')
    ax.text(0.5, -0.13, 'T&S Vol > 5 × DOM Vol = Iceberg (🧊 yellow lines)',
           transform=ax.transAxes, ha='center', fontsize=10, color=DARK['yellow'])
    save(fig, '36_shadow_dom')


def slide_37_3tier():
    """3-Tier Architecture"""
    fig, ax = plt.subplots(figsize=(16, 7))
    style_ax(ax, '3-Tier Architecture: Raw → Microstructure → Structural', '')

    tiers = [
        ('Tier 1: Raw', 'OHLCV, Ticks, Sessions\nPolars Normalization\nLatency < 0.1ms', DARK['orange']),
        ('Tier 2: Micro', 'Delta, CVD, Imbalance\nVP, Footprint\nLatency < 1ms', DARK['cyan']),
        ('Tier 3: Structural', 'BOS, CHoCH, MSS\nOB, FVG, Grid\nLatency < 5ms', DARK['purple']),
    ]

    for i, (name, desc, color) in enumerate(tiers):
        y = 0.7 - i * 0.25
        ax.add_patch(mpatches.FancyBboxPatch((0.05, y - 0.08), 0.85, 0.18,
                                              boxstyle='round,pad=0.02',
                                              facecolor=DARK['bg2'], edgecolor=color, linewidth=2))
        ax.text(0.08, y, name, fontsize=14, fontweight='bold', color=color, transform=ax.transAxes)
        ax.text(0.30, y, desc, fontsize=10, color=DARK['text'], transform=ax.transAxes)
        if i < 2:
            ax.annotate('', xy=(0.5, y - 0.12), xytext=(0.5, y - 0.08),
                       arrowprops=dict(arrowstyle='->', color=DARK['yellow'], lw=2),
                       transform=ax.transAxes)

    ax.text(0.5, 0.05, 'Pipeline: Normalize → Microstructure → Pattern Recognition → Geometry → Risk → Viz',
           fontsize=10, color=DARK['text'], ha='center', transform=ax.transAxes, style='italic')
    ax.axis('off')
    save(fig, '37_3tier')


def slide_38_backend():
    """Backend Stack"""
    fig, ax = plt.subplots(figsize=(16, 7))
    style_ax(ax, 'Backend Stack: FastAPI + Polars + Numba + WebSocket', '')

    components = [
        ('FastAPI', 'ASGI, async, low-latency\nREST + WebSocket', DARK['orange']),
        ('Polars', 'Векторизация, O(1) memory\n.ewm_mean(), .rolling()', DARK['cyan']),
        ('Numba JIT', 'O(n) Fibonacci Grid\n@nb.njit компиляция', DARK['purple']),
        ('WebSocket', 'ASGI WS\nLive market data', DARK['bull']),
        ('Time-series DB', 'TimescaleDB / InfluxDB\nOHLCV optimized', DARK['yellow']),
    ]

    for i, (name, desc, color) in enumerate(components):
        x = 0.05 + (i % 5) * 0.18
        y = 0.4
        ax.add_patch(mpatches.FancyBboxPatch((x, y - 0.05), 0.16, 0.45,
                                              boxstyle='round,pad=0.02',
                                              facecolor=DARK['bg2'], edgecolor=color, linewidth=2))
        ax.text(x + 0.08, y + 0.3, name, fontsize=11, fontweight='bold', color=color, ha='center', transform=ax.transAxes)
        ax.text(x + 0.08, y + 0.1, desc, fontsize=8, color=DARK['text'], ha='center', transform=ax.transAxes)

    ax.text(0.5, 0.1, 'Total latency < 25ms (Tier 1 → 2 → 3 → Viz)',
           fontsize=12, color=DARK['yellow'], ha='center', transform=ax.transAxes,
           bbox=dict(facecolor='#111122', alpha=0.7, edgecolor=DARK['yellow'], pad=6))
    ax.axis('off')
    save(fig, '38_backend')


def slide_39_frontend():
    """Frontend Stack"""
    fig, ax = plt.subplots(figsize=(16, 7))
    style_ax(ax, 'Frontend Stack: Plotly + LWC 5.2.0 + TV Embed + WebGL', '')

    layers = [
        ('Plotly.js', 'CDN\nHeatmap, Sankey, Waterfall', DARK['orange']),
        ('LWC 5.2.0', 'Lightweight Charts\nInline в учебнике', DARK['cyan']),
        ('TV Embed', 'Advanced Chart, Heatmap\nTicker Tape, Calendar', DARK['purple']),
        ('WebGL/Canvas', 'Footprint, Heatmap\n60 FPS на миллионах тиков', DARK['bull']),
        ('Datashader', '2D-агрегация растров\nBackground layer', DARK['yellow']),
    ]

    for i, (name, desc, color) in enumerate(layers):
        x = 0.05 + (i % 5) * 0.18
        y = 0.4
        ax.add_patch(mpatches.FancyBboxPatch((x, y - 0.05), 0.16, 0.45,
                                              boxstyle='round,pad=0.02',
                                              facecolor=DARK['bg2'], edgecolor=color, linewidth=2))
        ax.text(x + 0.08, y + 0.3, name, fontsize=11, fontweight='bold', color=color, ha='center', transform=ax.transAxes)
        ax.text(x + 0.08, y + 0.1, desc, fontsize=8, color=DARK['text'], ha='center', transform=ax.transAxes)

    ax.text(0.5, 0.1, 'Static → Inline → Embedded → GPU-ускоренный рендеринг',
           fontsize=11, color=DARK['text'], ha='center', transform=ax.transAxes, style='italic')
    ax.axis('off')
    save(fig, '39_frontend')


def slide_40_web_terminal():
    """Web Terminal UX"""
    fig, ax = plt.subplots(figsize=(16, 7))
    style_ax(ax, 'Web Terminal: Vataga / Tiger Trade UX Benchmark', '')

    # Layout sketch
    rect = mpatches.Rectangle((0.05, 0.1), 0.9, 0.85, fill=False, edgecolor=DARK['text'], linewidth=1)
    ax.add_patch(rect)

    # Top bar
    ax.add_patch(mpatches.Rectangle((0.05, 0.86), 0.9, 0.09, facecolor=DARK['bg2'], edgecolor=DARK['text']))
    ax.text(0.5, 0.905, 'Top: Symbol | Account | Settings | Notifications', fontsize=9, color=DARK['text'], ha='center', transform=ax.transAxes)

    # Sidebar
    ax.add_patch(mpatches.Rectangle((0.05, 0.1), 0.1, 0.76, facecolor=DARK['bg2'], edgecolor=DARK['text']))
    ax.text(0.1, 0.5, 'Sidebar\n• Chart\n• DOM\n• Footprint\n• Journal\n• Risk', fontsize=8, color=DARK['text'], ha='center', va='center', transform=ax.transAxes)

    # Chart
    ax.add_patch(mpatches.Rectangle((0.15, 0.5), 0.5, 0.36, facecolor=DARK['bg2'], edgecolor=DARK['text']))
    ax.text(0.4, 0.68, 'Main Chart\n(LWC 5.2.0 / TV)', fontsize=10, color=DARK['orange'], ha='center', transform=ax.transAxes)

    # DOM
    ax.add_patch(mpatches.Rectangle((0.65, 0.5), 0.3, 0.36, facecolor=DARK['bg2'], edgecolor=DARK['text']))
    ax.text(0.8, 0.68, 'DOM (Order Book)\nL2 + Shadow', fontsize=10, color=DARK['cyan'], ha='center', transform=ax.transAxes)

    # Bottom: positions
    ax.add_patch(mpatches.Rectangle((0.15, 0.1), 0.8, 0.4, facecolor=DARK['bg2'], edgecolor=DARK['text']))
    ax.text(0.55, 0.3, 'Positions | Orders | PnL | Risk Engine | Journal', fontsize=10, color=DARK['bull'], ha='center', transform=ax.transAxes)

    ax.text(0.5, 0.02, 'Web-only · кросс-платформенный · 60 FPS · без установки',
           fontsize=10, color=DARK['dim'], ha='center', transform=ax.transAxes, style='italic')
    ax.axis('off')
    save(fig, '40_web_terminal')


def main():
    import matplotlib.patches as mpatches
    # Re-bind to use mpatches for the other functions
    pass

# We need to bind mpatches for the slides that use it
import matplotlib.patches as mpatches

if __name__ == '__main__':
    slide_31_mf_standards()
    slide_32_fibo_grid()
    slide_33_fractal_ipda()
    slide_34_position_engineering()
    slide_35_crp()
    slide_36_shadow_dom()
    slide_37_3tier()
    slide_38_backend()
    slide_39_frontend()
    slide_40_web_terminal()
    print("\n✅ Все 10 слайдов MidasFlow сгенерированы")
