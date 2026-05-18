"""ascii_charts.py — Низкоуровневые ASCII-примитивы для инфографики.

plotext/plotille wrappers для генерации ASCII графиков.
"""

import io
import sys
import os
from typing import Dict, Any, List, Tuple, Optional

# ─── plotext ──────────────────────────────────────────────
try:
    import plotext as plt
except ImportError:
    plt = None

# ─── plotille ─────────────────────────────────────────────
try:
    import plotille
except ImportError:
    plotille = None


def _capture_plotext_output() -> str:
    """Захватить stdout plotext и вернуть строку."""
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    try:
        plt.show()
    finally:
        sys.stdout = old_stdout
    return buffer.getvalue()


def _safe_plotext(func):
    """Декоратор: если plotext недоступен — вернуть заглушку."""
    def wrapper(*args, **kwargs):
        if plt is None:
            return f"[plotext not installed]\n{func.__name__}"
        plt.clf()
        try:
            func(*args, **kwargs)
            return _capture_plotext_output()
        except Exception as e:
            return f"[plotext error: {e}]"
    return wrapper


def _safe_plotille(func):
    """Декоратор: если plotille недоступен — вернуть заглушку."""
    def wrapper(*args, **kwargs):
        if plotille is None:
            return f"[plotille not installed]\n{func.__name__}"
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return f"[plotille error: {e}]"
    return wrapper


# ═══════════════════════════════════════════════════════════
# 1. Candlestick
# ═══════════════════════════════════════════════════════════

@_safe_plotext
def plotext_candle(dates: List[str], ohlc: List[Dict[str, float]], title: str = ""):
    """OHLC свечной график через plotext."""
    plt.date_form('Y-m-d')
    data = {
        'Open':  [x['open'] for x in ohlc],
        'High':  [x['high'] for x in ohlc],
        'Low':   [x['low']  for x in ohlc],
        'Close': [x['close'] for x in ohlc],
    }
    plt.candlestick(dates, data)
    if title:
        plt.title(title)
    plt.plotsize(120, 30)
    plt.theme('dark')


# ═══════════════════════════════════════════════════════════
# 2. Deviation Error Bars
# ═══════════════════════════════════════════════════════════

@_safe_plotext
def plotext_error(dates: List[str], deviations: List[float], title: str = ""):
    """График отклонений с error bars."""
    plt.date_form('Y-m-d')
    yerr = [abs(d) * 0.1 for d in deviations]  # 10% error
    plt.error(deviations, xerr=None, yerr=yerr)
    if title:
        plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Deviation %")
    plt.plotsize(120, 25)
    plt.theme('dark')
    plt.vline(0, 'green')
    plt.hline(0, 'green')


@_safe_plotille
def plotille_scatter(x: List, y: List, title: str = "") -> str:
    """Scatter через plotille (braille fallback)."""
    fig = plotille.Figure()
    fig.width = 80
    fig.height = 25
    fig.color_mode = 'names'
    fig.scatter(x, y, lc='green', label='deviation')
    fig.set_x_label('Day')
    fig.set_y_label('Deviation %')
    out = fig.show(legend=True)
    if title:
        out = f"📈 {title}\n" + out
    return out


# ═══════════════════════════════════════════════════════════
# 3. Histogram
# ═══════════════════════════════════════════════════════════

@_safe_plotext
def plotext_hist(data: List[float], bins: int = 20, title: str = ""):
    """Гистограмма распределения."""
    plt.hist(data, bins=bins, label="distribution")
    if title:
        plt.title(title)
    plt.xlabel("Deviation %")
    plt.ylabel("Count")
    plt.plotsize(100, 25)
    plt.theme('dark')


@_safe_plotille
def plotille_hist(data: List[float], bins: int = 20, title: str = "") -> str:
    """Гистограмма через plotille."""
    out = plotille.hist(data, bins=bins, lc='blue')
    if title:
        out = f"📊 {title}\n" + out
    return out


# ═══════════════════════════════════════════════════════════
# 4. Box Plot
# ═══════════════════════════════════════════════════════════

@_safe_plotext
def plotext_box(data: List[float], label: str = "", title: str = ""):
    """Ящик с усами."""
    plt.box([label], [data], width=0.5)
    if title:
        plt.title(title)
    plt.ylabel("Deviation %")
    plt.plotsize(60, 20)
    plt.theme('dark')


# ═══════════════════════════════════════════════════════════
# 5. Range Bar (horizontal)
# ═══════════════════════════════════════════════════════════

@_safe_plotext
def plotext_bar_h(labels: List[str], values: List[float], title: str = ""):
    """Горизонтальные бары."""
    plt.bar(labels, values, orientation='horizontal')
    if title:
        plt.title(title)
    plt.plotsize(80, 15)
    plt.theme('dark')


@_safe_plotille
def plotille_range_bar(entry: float, current: float, min_p: float, max_p: float,
                       title: str = "") -> str:
    """ASCII range bar через plotille Figure."""
    fig = plotille.Figure()
    fig.width = 80
    fig.height = 10
    # Normalize 0-1
    rng = max_p - min_p
    entry_n = (0 - min_p) / rng if rng else 0.5
    current_n = (current - min_p) / rng if rng else 0.5
    fig.plot([0, 1], [0.5, 0.5], lc='gray')
    fig.scatter([entry_n], [0.5], lc='blue', label='entry')
    fig.scatter([current_n], [0.5], lc='green', label='current')
    out = fig.show(legend=True)
    if title:
        out = f"🏗️ {title}\n{out}"
    return out


# ═══════════════════════════════════════════════════════════
# 6. Heatmap (volatility matrix)
# ═══════════════════════════════════════════════════════════

@_safe_plotext
def plotext_matrix(matrix: List[List[float]], title: str = ""):
    """Матричный heatmap."""
    plt.matrix_plot(matrix)
    if title:
        plt.title(title)
    plt.plotsize(80, 30)
    plt.theme('dark')


# ═══════════════════════════════════════════════════════════
# 7. Indicator (KPI)
# ═══════════════════════════════════════════════════════════

@_safe_plotext
def plotext_indicator(value: float, label: str = ""):
    """Индикатор-циферблат."""
    plt.indicator(value, label)
    plt.plotsize(40, 15)
    plt.theme('dark')


def ascii_indicator(value: float, label: str = "", delta: str = "") -> str:
    """Ручной ASCII индикатор (без plotext)."""
    color = '\033[32m' if value >= 0 else '\033[31m'
    reset = '\033[0m'
    sign = '+' if value >= 0 else ''
    lines = [
        "┌─────────────────────────┐",
        f"│  {color}{sign}{value:.2f}%{reset}                  │",
        f"│  {label:^23} │",
    ]
    if delta:
        lines.append(f"│  {delta:^23} │")
    lines.append("└─────────────────────────┘")
    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════
# 8. Subplot Grid
# ═══════════════════════════════════════════════════════════

@_safe_plotext
def plotext_subplots(charts_data: Dict[str, Any], title: str = ""):
    """Сетка subplot 2×3 через plotext."""
    plt.clf()
    plt.subplots(2, 3)
    # Candlestick
    plt.subplot(1, 1)
    if 'candle' in charts_data:
        d = charts_data['candle']
        # Use numeric indices to avoid date format issues in subplot mode
        n = len(d['ohlc'])
        plt.candlestick(list(range(n)), d['ohlc'])
        plt.xticks(list(range(n)), d['dates'])
        plt.title("Candle")
    # Box
    plt.subplot(1, 2)
    if 'box' in charts_data:
        d = charts_data['box']
        plt.box([d['label']], [d['data']])
        plt.title("Box")
    # Indicator
    plt.subplot(1, 3)
    if 'indicator' in charts_data:
        d = charts_data['indicator']
        plt.indicator(d['value'], d['label'])
        plt.title("KPI")
    # Deviation
    plt.subplot(2, 1)
    if 'deviation' in charts_data:
        d = charts_data['deviation']
        plt.error(d['values'])
        plt.title("Deviation")
    # Histogram
    plt.subplot(2, 2)
    if 'hist' in charts_data:
        d = charts_data['hist']
        plt.hist(d['data'], bins=d.get('bins', 20))
        plt.title("Distribution")
    # Heatmap
    plt.subplot(2, 3)
    if 'matrix' in charts_data:
        d = charts_data['matrix']
        plt.matrix_plot(d['data'])
        plt.title("Heatmap")
    if title:
        plt.title(title)
    plt.plotsize(180, 50)
    plt.theme('dark')


# ═══════════════════════════════════════════════════════════
# Enhanced ASCII Utilities (256-color, box-drawing, etc.)
# ═══════════════════════════════════════════════════════════

import shutil
import math


def term_width(default: int = 120) -> int:
    """Get terminal width, fallback to default."""
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return default


def c256(code: int) -> str:
    """256-color ANSI foreground."""
    return f"\x1b[38;5;{code}m"


def bg256(code: int) -> str:
    """256-color ANSI background."""
    return f"\x1b[48;5;{code}m"


def reset() -> str:
    return "\x1b[0m"


# Enhanced box-drawing set
BOX = {
    "tl": "╔", "tr": "╗", "bl": "╚", "br": "╝",
    "h": "═", "v": "║",
    "ml": "╠", "mr": "╣", "tm": "╦", "bm": "╩", "cross": "╬",
    "h_thin": "─", "v_thin": "│",
    "tl_thin": "┌", "tr_thin": "┐", "bl_thin": "└", "br_thin": "┘",
}


def gradient_color(value: float, min_val: float, max_val: float) -> str:
    """Map value to 256-color gradient: blue→green→yellow→red."""
    if max_val <= min_val:
        pct = 0.5
    else:
        pct = max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))
    if pct < 0.33:
        code = 21 + int((46 - 21) * (pct / 0.33))
    elif pct < 0.66:
        code = 46 + int((220 - 46) * ((pct - 0.33) / 0.33))
    else:
        code = 220 + int((196 - 220) * ((pct - 0.66) / 0.34))
    return c256(code)


def smart_y_label(val: float, max_decimals: int = 6) -> str:
    """Format number with smart decimal places for Y-axis."""
    if abs(val) >= 10000:
        return f"{val:,.0f}"
    elif abs(val) >= 100:
        return f"{val:,.1f}"
    elif abs(val) >= 1:
        return f"{val:,.2f}"
    elif abs(val) >= 0.01:
        return f"{val:.4f}"
    else:
        return f"{val:.{max_decimals}f}"


def anomaly_line(data: List[float], threshold_sigma: float = 2.0) -> str:
    """Return string with red ⚠ markers where |data[i] - mean| > threshold_sigma * std."""
    if len(data) < 2:
        return ""
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    std = math.sqrt(variance)
    if std == 0:
        return ""
    out = []
    for v in data:
        if abs(v - mean) > threshold_sigma * std:
            out.append(f"{c256(196)}⚠{reset()}")
        else:
            out.append(" ")
    return "".join(out)


def frame_box(content_lines: List[str], title: str = "", width: int = 0) -> str:
    """Wrap content in Unicode double-line box."""
    if not content_lines:
        return ""
    if width == 0:
        width = max(len(line) for line in content_lines) + 2
    w = width
    lines = []
    if title:
        title_str = f" {title} "
        pad = (w - len(title_str)) // 2
        top = BOX["tl"] + BOX["h"] * pad + title_str + BOX["h"] * (w - pad - len(title_str)) + BOX["tr"]
    else:
        top = BOX["tl"] + BOX["h"] * w + BOX["tr"]
    lines.append(top)
    for line in content_lines:
        lines.append(BOX["v"] + " " + line.ljust(w - 2) + " " + BOX["v"])
    lines.append(BOX["bl"] + BOX["h"] * w + BOX["br"])
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
# Utilities
# ═══════════════════════════════════════════════════════════

@_safe_plotille
def plotille_line(x: List, y: List, title: str = "") -> str:
    """Простая линия через plotille."""
    fig = plotille.Figure()
    fig.width = 80
    fig.height = 20
    fig.plot(x, y, lc='green')
    fig.set_x_label('Day')
    fig.set_y_label('Price')
    out = fig.show(legend=True)
    if title:
        out = f"📈 {title}\n" + out
    return out
