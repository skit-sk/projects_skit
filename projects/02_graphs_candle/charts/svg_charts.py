"""SVG Candlestick chart generation - simplified version."""

from typing import List, Dict, Any


PATTERN_COLORS = {
    'Hammer': '#22c55e',
    'Shooting Star': '#ef4444', 
    'Doji': '#fbbf24',
    'Bullish Engulfing': '#22c55e',
    'Bearish Engulfing': '#ef4444',
    'Morning Star': '#22c55e',
    'Evening Star': '#ef4444',
    'Marubozu': '#22c55e',
}

PATTERN_ABBREV = {
    'Hammer': 'HMR',
    'Shooting Star': 'SST',
    'Doji': 'DOJ',
    'Bullish Engulfing': 'B.E',
    'Bearish Engulfing': 'Br.E',
    'Morning Star': 'M.S',
    'Evening Star': 'E.S',
    'Marubozu': 'MRB',
}


def generate_svg_candlestick(
    candles: List[Dict[str, Any]],
    width: int = 800,
    height: int = 400,
    pattern_times: List[str] = None,
    patterns: List[Dict[str, Any]] = None
) -> str:
    """Generate SVG candlestick chart."""

    if not candles:
        return ""

    pattern_times = set(pattern_times or [])
    patterns = patterns or []
    patterns_by_time = {p['time']: p for p in patterns}

    all_prices = []
    for c in candles:
        all_prices.extend([c['high'], c['low']])

    min_price = min(all_prices)
    max_price = max(all_prices)
    price_range = max_price - min_price or 1

    padding = 40
    chart_width = width - 2 * padding
    chart_height = height - 2 * padding

    def price_to_y(price):
        return padding + chart_height - ((price - min_price) / price_range * chart_height)

    def time_to_x(idx):
        return padding + (idx / (len(candles) - 1)) * chart_width if len(candles) > 1 else padding

    candle_width = max(2, min(6, chart_width / len(candles) * 0.7))
    lbl_size = max(6, min(10, int(400 / len(candles))))

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="background:#1f2937;">']
    svg.append(f'<rect width="{width}" height="{height}" fill="#1f2937"/>')
    svg.append('<!-- Grid lines -->')

    for i in range(5):
        y = padding + i * chart_height / 4
        pv = max_price - i * price_range / 4
        svg.append(f'<line x1="{padding}" y1="{y}" x2="{width-padding}" y2="{y}" stroke="#374151" stroke-width="1" stroke-dasharray="4"/>')
        svg.append(f'<text x="{padding-5}" y="{y+4}" fill="#9ca3af" font-size="10" text-anchor="end" font-family="monospace">${pv:,.0f}</text>')

    for i, c in enumerate(candles):
        x = time_to_x(i)
        bull = c['close'] > c['open']
        wc = '#22c55e' if bull else '#ef4444'

        hy = price_to_y(c['high'])
        ly = price_to_y(c['low'])
        bt = price_to_y(max(c['open'], c['close']))
        bb = price_to_y(min(c['open'], c['close']))
        bh = max(1, bb - bt)

        pat = patterns_by_time.get(c['time'])
        clr = PATTERN_COLORS.get(pat['pattern'], '#fbbf24') if pat else None
        abv = PATTERN_ABBREV.get(pat['pattern'], '?') if pat else None

        svg.append(f'<title>{"PAT" + pat["pattern"] + " (" + pat["type"] + ")\n" if pat else ""}Open: ${c["open"]:.2f} Close: ${c["close"]:.2f}\nHigh: ${c["high"]:.2f} Low: ${c["low"]:.2f}\nChange: {c.get("change", 0):+.2f}%{"\nStrength: " + str(pat["strength"]) + "%" + pat["description"] if pat else ""}</title>')
        svg.append(f'<line x1="{x}" y1="{hy}" x2="{x}" y2="{ly}" stroke="{wc}" stroke-width="1"/>')
        svg.append(f'<rect x="{x - candle_width/2}" y="{bt}" width="{candle_width}" height="{bh}" fill="{wc}"/>')

        if pat:
            svg.append(f'<polygon points="{x},{hy-8} {x-4},{hy-16} {x+4},{hy-16}" fill="{clr}"/>')
            svg.append(f'<text x="{x}" y="{hy-18}" fill="{clr}" font-size="{lbl_size}" text-anchor="middle" font-family="monospace" font-weight="bold">{abv}</text>')

    svg.append(f'<line x1="{padding}" y1="{height-padding}" x2="{width-padding}" y2="{height-padding}" stroke="#4b5563" stroke-width="1"/>')
    svg.append(f'<line x1="{padding}" y1="{padding}" x2="{padding}" y2="{height-padding}" stroke="#4b5563" stroke-width="1"/>')
    svg.append(f'<text x="{width/2}" y="20" fill="#e5e7eb" font-size="14" text-anchor="middle" font-weight="600">Price Action Patterns</text>')
    svg.append('</svg>')

    return '\n'.join(svg)


def generate_svg_pnl(
    points: List[Dict[str, Any]],
    width: int = 800,
    height: int = 300
) -> str:
    """Generate SVG P&L chart."""

    if not points:
        return ""

    pnl_vals = [p['pnl'] for p in points]
    min_pnl = min(pnl_vals)
    max_pnl = max(pnl_vals)
    pnl_range = max_pnl - min_pnl or 1

    padding = 40
    chart_width = width - 2 * padding
    chart_height = height - 2 * padding

    def pnl_to_y(pnl):
        return padding + chart_height - ((pnl - min_pnl) / pnl_range * chart_height)

    def time_to_x(idx):
        return padding + (idx / (len(points) - 1)) * chart_width if len(points) > 1 else padding

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="background:#1f2937;">']
    svg.append(f'<rect width="{width}" height="{height}" fill="#1f2937"/>')

    zy = pnl_to_y(0)
    if min_pnl <= 0 <= max_pnl:
        svg.append(f'<line x1="{padding}" y1="{zy}" x2="{width-padding}" y2="{zy}" stroke="#6b7280" stroke-width="1" stroke-dasharray="4"/>')

    coords = ' '.join([f'{time_to_x(i)},{pnl_to_y(p["pnl"])}' for i, p in enumerate(points)])
    svg.append(f'<polyline points="{coords}" fill="none" stroke="#3b82f6" stroke-width="2"/>')

    fill_pts = f'{padding},{zy} ' + coords + f' {time_to_x(len(points)-1)},{zy}'
    svg.append(f'<polygon points="{fill_pts}" fill="rgba(59,130,246,0.2)"/>')

    svg.append(f'<line x1="{padding}" y1="{height-padding}" x2="{width-padding}" y2="{height-padding}" stroke="#4b5563" stroke-width="1"/>')
    svg.append(f'<text x="{width/2}" y="20" fill="#e5e7eb" font-size="14" text-anchor="middle" font-weight="600">Cumulative P&L</text>')
    svg.append('</svg>')

    return '\n'.join(svg)


def generate_svg_combined(
    candles: List[Dict[str, Any]],
    pnl_points: List[Dict[str, Any]] = None,
    pattern_times: List[str] = None,
    patterns: List[Dict[str, Any]] = None,
    width: int = 800,
    height: int = 500
) -> str:
    """Combined SVG chart."""

    if not candles:
        return ""

    pattern_times = set(pattern_times or [])
    patterns = patterns or []
    patterns_by_time = {p['time']: p for p in patterns}

    all_prices = []
    for c in candles:
        all_prices.extend([c['high'], c['low']])

    min_price = min(all_prices)
    max_price = max(all_prices)
    price_range = max_price - min_price or 1

    pnl_vals = [p['pnl'] for p in pnl_points] if pnl_points else [0]
    min_pnl = min(pnl_vals)
    max_pnl = max(pnl_vals)
    pnl_range = max_pnl - min_pnl or 1

    padding = 40
    chart_width = width - 2 * padding
    chart_height = height - 2 * padding
    candle_height = int(chart_height * 0.65)
    pnl_height = int(chart_height * 0.30)

    def price_to_y(price):
        return padding + candle_height - ((price - min_price) / price_range * candle_height)

    def pnl_to_y(pnl, base_y):
        return base_y - ((pnl - min_pnl) / pnl_range * pnl_height)

    def time_to_x(idx):
        return padding + (idx / (len(candles) - 1)) * chart_width if len(candles) > 1 else padding

    candle_width = max(2, min(6, chart_width / len(candles) * 0.7))
    pnl_base_y = padding + candle_height + 20 + pnl_height
    lbl_size = max(6, min(10, int(400 / len(candles))))

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="background:#1f2937;">']
    svg.append(f'<rect width="{width}" height="{height}" fill="#1f2937"/>')

    candle_base_y = padding + candle_height
    for i in range(5):
        y = candle_base_y - i * candle_height / 4
        pv = max_price - i * price_range / 4
        svg.append(f'<line x1="{padding}" y1="{y}" x2="{width-padding}" y2="{y}" stroke="#374151" stroke-width="1" stroke-dasharray="4"/>')
        svg.append(f'<text x="{padding-5}" y="{y+4}" fill="#9ca3af" font-size="10" text-anchor="end" font-family="monospace">${pv:,.0f}</text>')

    for i, c in enumerate(candles):
        x = time_to_x(i)
        bull = c['close'] > c['open']
        wc = '#22c55e' if bull else '#ef4444'

        hy = price_to_y(c['high'])
        ly = price_to_y(c['low'])
        bt = price_to_y(max(c['open'], c['close']))
        bb = price_to_y(min(c['open'], c['close']))
        bh = max(1, bb - bt)

        pat = patterns_by_time.get(c['time'])
        clr = PATTERN_COLORS.get(pat['pattern'], '#fbbf24') if pat else None
        abv = PATTERN_ABBREV.get(pat['pattern'], '?') if pat else None

        svg.append(f'<title>{"PAT" + pat["pattern"] + " (" + pat["type"] + ")\n" if pat else ""}Open: ${c["open"]:.2f} Close: ${c["close"]:.2f}\nHigh: ${c["high"]:.2f} Low: ${c["low"]:.2f}{"\nStrength: " + str(pat["strength"]) + "%" + pat["description"] if pat else ""}</title>')
        svg.append(f'<line x1="{x}" y1="{hy}" x2="{x}" y2="{ly}" stroke="{wc}" stroke-width="1"/>')
        svg.append(f'<rect x="{x - candle_width/2}" y="{bt}" width="{candle_width}" height="{bh}" fill="{wc}"/>')

        if pat:
            svg.append(f'<polygon points="{x},{hy-8} {x-4},{hy-16} {x+4},{hy-16}" fill="{clr}"/>')
            svg.append(f'<text x="{x}" y="{hy-18}" fill="{clr}" font-size="{lbl_size}" text-anchor="middle" font-family="monospace" font-weight="bold">{abv}</text>')

    svg.append(f'<line x1="{padding}" y1="{candle_base_y + 10}" x2="{width-padding}" y2="{candle_base_y + 10}" stroke="#4b5563" stroke-width="1" stroke-dasharray="2"/>')

    if pnl_points:
        zy = pnl_to_y(0, pnl_base_y)
        if min_pnl <= 0 <= max_pnl:
            svg.append(f'<line x1="{padding}" y1="{zy}" x2="{width-padding}" y2="{zy}" stroke="#6b7280" stroke-width="1"/>')

        pnl_coords = ' '.join([f'{pnl_base_y + chart_height - ((p["pnl"] - min_pnl) / pnl_range * pnl_height)},{time_to_x(i)}' for i, p in enumerate(pnl_points)])
        coords = ' '.join([f'{time_to_x(i)},{pnl_to_y(p["pnl"], pnl_base_y)}' for i, p in enumerate(pnl_points)])
        svg.append(f'<polyline points="{coords}" fill="none" stroke="#3b82f6" stroke-width="2"/>')

        fill_pts = f'{padding},{zy} ' + coords + f' {time_to_x(len(pnl_points)-1)},{zy}'
        svg.append(f'<polygon points="{fill_pts}" fill="rgba(59,130,246,0.2)"/>')

    svg.append(f'<line x1="{padding}" y1="{height-padding}" x2="{width-padding}" y2="{height-padding}" stroke="#4b5563" stroke-width="1"/>')
    svg.append(f'<text x="{width/2}" y="20" fill="#e5e7eb" font-size="14" text-anchor="middle" font-weight="600">Price Action Patterns Cumulative P&L</text>')
    svg.append('</svg>')

    return '\n'.join(svg)