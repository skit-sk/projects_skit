"""ascii_visuals.py — Pure-ASCII advanced chart primitives.

New chart types:
  radar, waterfall, pareto, sankey, treemap, gauge, sparkline

Uses Unicode box-drawing, 256-color ANSI, and block characters.
"""
import math
import shutil
import textwrap
from typing import Dict, List, Optional, Tuple

# ── ANSI helpers ──────────────────────────────────────────────────────────

def _c256(code: int) -> str:
    return f"\x1b[38;5;{code}m"

def _bg256(code: int) -> str:
    return f"\x1b[48;5;{code}m"

def _reset() -> str:
    return "\x1b[0m"

# Color ramps
_RED = _c256(196)
_GREEN = _c256(46)
_YELLOW = _c256(220)
_BLUE = _c256(39)
_CYAN = _c256(51)
_MAGENTA = _c256(201)
_WHITE = _c256(255)
_GRAY = _c256(245)
_DIM = _c256(240)
_RST = _reset()

_BOX = {
    "tl": "┌", "tr": "┐", "bl": "└", "br": "┘",
    "h": "─", "v": "│",
    "ml": "├", "mr": "┤", "tm": "┬", "bm": "┴", "cross": "┼"
}

# ── Terminal width ────────────────────────────────────────────────────────

def _term_width(default: int = 120) -> int:
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return default


def _clamp_width(w: int, max_w: Optional[int] = None) -> int:
    if max_w is None:
        max_w = _term_width()
    return min(w, max_w)


# ── Sparkline (8-level Unicode blocks) ────────────────────────────────────

def sparkline(data: List[float], width: int = 50) -> str:
    """One-line sparkline using Unicode block elements ▁▂▃▄▅▆▇█."""
    if not data:
        return ""
    lo, hi = min(data), max(data)
    if hi == lo:
        return "█" * min(len(data), width)
    blocks = "▁▂▃▄▅▆▇█"
    step = (hi - lo) / 7.0
    out = []
    stride = max(1, len(data) // width)
    for i in range(0, len(data), stride):
        val = data[i]
        idx = min(7, int((val - lo) / step))
        out.append(blocks[idx])
    return "".join(out)


# ── Radar / Spider chart ──────────────────────────────────────────────────

def radar_chart(metrics: Dict[str, float], title: str, width: int = 60) -> str:
    """Draw a radar chart with named axes. Metrics values in 0..1."""
    size = min(width, 60)
    cx, cy = size // 2, size // 2
    radius = size // 2 - 2
    labels = list(metrics.keys())
    n = len(labels)
    if n < 3:
        return f"{title}\n[radar needs ≥3 axes]"

    # canvas[y][x] = char
    canvas = [[" " for _ in range(size + 1)] for _ in range(size + 1)]

    # helper
    def setc(x, y, ch):
        if 0 <= x <= size and 0 <= y <= size:
            canvas[y][x] = ch

    # grid circles
    for r in range(1, radius + 1, max(1, radius // 4)):
        for angle in range(360):
            rad = math.radians(angle)
            x = int(cx + r * math.cos(rad))
            y = int(cy + r * math.sin(rad) * 0.5)  # squash vertically
            setc(x, y, "·")

    # axes
    for i in range(n):
        a = 2 * math.pi * i / n - math.pi / 2
        for r in range(1, radius + 1):
            x = int(cx + r * math.cos(a))
            y = int(cy + r * math.sin(a) * 0.5)
            setc(x, y, "·")

    # polygon
    points = []
    for i in range(n):
        a = 2 * math.pi * i / n - math.pi / 2
        val = max(0.0, min(1.0, metrics.get(labels[i], 0)))
        r = val * radius
        x = int(cx + r * math.cos(a))
        y = int(cy + r * math.sin(a) * 0.5)
        points.append((x, y))

    # draw edges
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        dx, dy = x2 - x1, y2 - y1
        steps = max(abs(dx), abs(dy), 1)
        for s in range(steps + 1):
            px = int(x1 + dx * s / steps)
            py = int(y1 + dy * s / steps)
            setc(px, py, "█")

    # labels on canvas edges
    for i in range(n):
        a = 2 * math.pi * i / n - math.pi / 2
        lx = int(cx + (radius + 2) * math.cos(a))
        ly = int(cy + (radius + 2) * math.sin(a) * 0.5)
        lbl = labels[i][:8]
        for k, ch in enumerate(lbl):
            setc(lx + k - len(lbl) // 2, ly, ch)

    # build output
    lines = [f"{_YELLOW}{title}{_RST}"]
    for row in canvas:
        lines.append("".join(row).rstrip())
    return "\n".join(lines)


# ── Waterfall chart ───────────────────────────────────────────────────────

def waterfall_chart(bars: List[Tuple[str, float]], title: str, width: int = 70) -> str:
    """
    bars = [(label, delta), ...]
    Draws cumulative waterfall with green/red delta bars + cumulative line.
    """
    if not bars:
        return f"{title}\n[no data]"

    # compute cumulative
    cum = [0.0]
    for _, d in bars:
        cum.append(cum[-1] + d)
    total = cum[-1]

    # rendering params
    chart_w = _clamp_width(width, 80) - 20
    max_abs = max(abs(v) for v in cum + [b[1] for b in bars] + [total])
    if max_abs == 0:
        max_abs = 1.0
    scale = chart_w / (2 * max_abs)
    zero = int(max_abs * scale)

    lines = [f"{_YELLOW}{title}{_RST}"]
    lines.append(f"{_WHITE}Total: {smart_label(total)}{_RST}")
    lines.append(f"{_BOX['tl']}{_BOX['h']*(chart_w+2)}{_BOX['tr']}")

    for i, (label, delta) in enumerate(bars):
        c = cum[i]
        c_next = cum[i + 1]
        # bar direction
        if delta >= 0:
            bar_color = _GREEN
            ch = "▓"
        else:
            bar_color = _RED
            ch = "░"

        row = [f"{_BOX['v']}"]
        # build horizontal bar string
        bar = [" "] * (chart_w + 2)
        # zero line
        bar[zero] = "│"

        # cumulative start and end positions
        p1 = zero + int(c * scale)
        p2 = zero + int(c_next * scale)
        p1 = max(0, min(chart_w + 1, p1))
        p2 = max(0, min(chart_w + 1, p2))

        # fill bar
        if p2 >= p1:
            for p in range(p1, p2 + 1):
                if bar[p] == " ":
                    bar[p] = ch
        else:
            for p in range(p2, p1 + 1):
                if bar[p] == " ":
                    bar[p] = ch

        row.append(bar_color + "".join(bar) + _RST)
        row.append(f"{_BOX['v']} {label:>6} {smart_label(delta)}")
        lines.append("".join(row))

    lines.append(f"{_BOX['bl']}{_BOX['h']*(chart_w+2)}{_BOX['br']}")
    return "\n".join(lines)


# ── Pareto chart ──────────────────────────────────────────────────────────

def pareto_chart(items: List[Tuple[str, float]], title: str, width: int = 70) -> str:
    """
    items = [(label, value), ...] — will be sorted descending.
    Draws bars + cumulative percentage line.
    """
    if not items:
        return f"{title}\n[no data]"

    items = sorted(items, key=lambda x: x[1], reverse=True)
    total = sum(v for _, v in items)
    if total == 0:
        return f"{title}\n[zero total]"

    chart_w = _clamp_width(width, 70) - 20
    max_v = max(v for _, v in items)
    scale = chart_w / max_v if max_v else 1

    lines = [f"{_YELLOW}{title}{_RST}"]
    lines.append(f"{_BOX['tl']}{_BOX['h']*chart_w}{_BOX['tr']}")

    cum = 0.0
    for label, val in items:
        cum += val
        pct = 100 * cum / total
        bar_len = int(val * scale)
        bar = "█" * bar_len + "░" * max(0, chart_w - bar_len)

        # cumulative line marker
        cum_pos = int(chart_w * pct / 100)
        bar_list = list(bar)
        if 0 <= cum_pos < len(bar_list):
            bar_list[cum_pos] = "◆"
        bar = "".join(bar_list)

        color = _GREEN if val >= 0 else _RED
        row = f"{_BOX['v']}{color}{bar}{_RST}{_BOX['v']} {label:>5} {smart_label(val)} ({pct:.0f}%)"
        lines.append(row)

    lines.append(f"{_BOX['bl']}{_BOX['h']*chart_w}{_BOX['br']}")
    return "\n".join(lines)


# ── Sankey flow (Min → Entry → Current → Max) ─────────────────────────────

def sankey_flow(nodes: List[Tuple[str, float]], title: str, width: int = 70) -> str:
    """
    nodes = [(label, value), ...] — sequential flow.
    Example: [("Min", 0.0012), ("Entry", 0.00146), ("Current", 0.001514), ("Max", 0.001737)]
    """
    if len(nodes) < 2:
        return f"{title}\n[need ≥2 nodes]"

    chart_w = _clamp_width(width, 80) - 10
    vals = [v for _, v in nodes]
    lo, hi = min(vals), max(vals)
    span = hi - lo if hi != lo else 1.0

    lines = [f"{_YELLOW}{title}{_RST}"]

    # compute positions
    positions = []
    for label, val in nodes:
        pos = int(chart_w * (val - lo) / span)
        positions.append((label, val, pos))

    # draw flow arrows
    arrow_line = [" "] * (chart_w + 4)
    for i in range(len(positions) - 1):
        p1 = positions[i][2]
        p2 = positions[i + 1][2]
        start, end = min(p1, p2), max(p1, p2)
        for p in range(start, end + 1):
            arrow_line[p + 2] = "─"
        # arrow head
        if p2 > p1:
            arrow_line[end + 2] = "►"
        elif p2 < p1:
            arrow_line[start + 2] = "◄"

    # node markers
    for label, val, pos in positions:
        arrow_line[pos + 2] = "●"

    lines.append("".join(arrow_line))

    # labels + deltas
    for i in range(len(positions) - 1):
        lbl1, val1, p1 = positions[i]
        lbl2, val2, p2 = positions[i + 1]
        delta = val2 - val1
        delta_s = f"{delta:+.6f}"
        color = _GREEN if delta >= 0 else _RED
        mid = (p1 + p2) // 2
        pad = " " * (mid + 2)
        lines.append(f"{pad}{color}{delta_s}{_RST}")
        pad2 = " " * (p1 + 2 - len(lbl1) // 2)
        lines.append(f"{pad2}{lbl1}({val1:.6f})")

    # last label
    last_lbl, last_val, last_p = positions[-1]
    pad_last = " " * (last_p + 2 - len(last_lbl) // 2)
    lines.append(f"{pad_last}{last_lbl}({last_val:.6f})")

    return "\n".join(lines)


# ── Treemap (nested rectangles) ───────────────────────────────────────────

def treemap_chart(blocks: List[Tuple[str, float]], title: str, width: int = 70, height: int = 20) -> str:
    """
    blocks = [(label, size), ...]
    Draws proportional nested rectangles using block chars.
    """
    if not blocks:
        return f"{title}\n[no data]"

    total = sum(s for _, s in blocks)
    if total == 0:
        return f"{title}\n[zero total]"

    w = _clamp_width(width, 80)
    h = min(height, 30)

    # sort descending
    blocks = sorted(blocks, key=lambda x: x[1], reverse=True)

    # simple greedy layout
    canvas = [[" " for _ in range(w)] for _ in range(h)]
    colors = [_GREEN, _CYAN, _BLUE, _MAGENTA, _YELLOW, _RED]

    def draw_rect(x, y, rw, rh, ch):
        for yy in range(y, min(y + rh, h)):
            for xx in range(x, min(x + rw, w)):
                if yy == y or yy == min(y + rh - 1, h - 1):
                    canvas[yy][xx] = ch
                elif xx == x or xx == min(x + rw - 1, w - 1):
                    canvas[yy][xx] = ch
                else:
                    canvas[yy][xx] = ch

    x, y = 0, 0
    for idx, (label, size) in enumerate(blocks):
        pct = size / total
        # allocate area proportional to size
        area = int(w * h * pct)
        rw = max(5, int(math.sqrt(area * 2)))
        rh = max(2, area // rw)
        if x + rw > w:
            x = 0
            y += rh + 1
        if y + rh > h:
            break
        color = colors[idx % len(colors)]
        fill = ["█", "▓", "▒", "░"][idx % 4]
        draw_rect(x, y, rw, rh, fill)
        # place label
        lbl = label[:rw - 2]
        lx = x + max(1, (rw - len(lbl)) // 2)
        ly = y + rh // 2
        if ly < h and lx + len(lbl) < w:
            for k, ch in enumerate(lbl):
                canvas[ly][lx + k] = ch
        x += rw + 1

    lines = [f"{_YELLOW}{title}{_RST}"]
    for row in canvas:
        lines.append("".join(row))
    return "\n".join(lines)


# ── Gauge chart (semicircle) ──────────────────────────────────────────────

def gauge_chart(value: float, min_val: float, max_val: float, label: str, width: int = 50) -> str:
    """Semicircular gauge. Value in [min_val, max_val]."""
    if max_val <= min_val:
        max_val = min_val + 1.0
    pct = max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))

    w = _clamp_width(width, 60)
    radius = w // 2

    lines = []
    # top arc
    for y in range(radius // 2, -1, -1):
        row = [" "] * w
        for x in range(w):
            dx = x - radius
            dy = y
            dist = math.sqrt(dx * dx + dy * dy)
            if radius - 2 <= dist <= radius + 1:
                # determine if this point is "filled"
                angle = math.atan2(dy, dx)  # 0..pi
                fill_pct = angle / math.pi
                if fill_pct <= pct:
                    row[x] = "█"
                else:
                    row[x] = "░"
        lines.append("".join(row).rstrip())

    # needle at bottom center
    needle_pos = int(radius - radius * math.cos(pct * math.pi))
    bottom = [" "] * w
    if 0 <= needle_pos < w:
        bottom[needle_pos] = "▲"
    lines.append("".join(bottom))

    # label + value
    val_color = _GREEN if pct > 0.5 else (_YELLOW if pct > 0.25 else _RED)
    lines.append(f"  {label}: {val_color}{smart_label(value)}{_RST} ({pct*100:.0f}%)")

    return "\n".join(lines)


# ── Smart label formatter ─────────────────────────────────────────────────

def smart_label(val: float, max_decimals: int = 6) -> str:
    """Format a number with smart decimal places."""
    if abs(val) >= 1000:
        return f"{val:,.0f}"
    elif abs(val) >= 1:
        return f"{val:,.2f}"
    elif abs(val) >= 0.01:
        return f"{val:.4f}"
    else:
        return f"{val:.{max_decimals}f}"


# ── Anomaly marker line ───────────────────────────────────────────────────

def anomaly_line(data: List[float], threshold_sigma: float = 2.0) -> str:
    """Returns a string with ⚠ markers where |data[i] - mean| > threshold_sigma * std."""
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
            out.append("⚠")
        else:
            out.append(" ")
    return "".join(out)


# ── 256-color gradient bar ────────────────────────────────────────────────

def gradient_bar(value: float, min_val: float, max_val: float, width: int = 40) -> str:
    """Returns a colored bar with 256-color gradient (blue→green→yellow→red)."""
    if max_val <= min_val:
        pct = 0.5
    else:
        pct = max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))

    filled = int(width * pct)
    empty = width - filled

    # gradient color: 21 (blue) → 46 (green) → 220 (yellow) → 196 (red)
    if pct < 0.33:
        color = _c256(21 + int((46 - 21) * (pct / 0.33)))
    elif pct < 0.66:
        color = _c256(46 + int((220 - 46) * ((pct - 0.33) / 0.33)))
    else:
        color = _c256(220 + int((196 - 220) * ((pct - 0.66) / 0.34)))

    return f"{color}{'█'*filled}{_RST}{'░'*empty}"
