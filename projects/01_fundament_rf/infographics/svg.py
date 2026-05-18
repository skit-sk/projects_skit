from typing import Dict, Any, List


def get_roe_color(roe: float) -> str:
    """Returns color based on ROE 9-tier gradient."""
    if roe >= 200: return '#166534'
    if roe >= 100: return '#22c55e'
    if roe >= 50:  return '#86efac'
    if roe >= 10:  return '#bbf7d0'
    if roe >= 0:   return '#d1d5db'
    if roe >= -10: return '#fca5a5'
    if roe >= -50: return '#ef4444'
    if roe >= -100: return '#dc2626'
    return '#991b1b'


def get_mini_color(roe: float, min_roe: float, max_roe: float) -> str:
    """Returns color based on ROE relative to symbol min/max."""
    if max_roe == min_roe:
        return '#9ca3af'
    ratio = (roe - min_roe) / (max_roe - min_roe)
    if ratio >= 0.85: return '#16a34a'
    if ratio >= 0.7: return '#22c55e'
    if ratio >= 0.55: return '#86efac'
    if ratio > 0.45: return '#9ca3af'
    if ratio > 0.3: return '#fca5a5'
    if ratio > 0.15: return '#ef4444'
    return '#dc2626'


class SVGDashboard:
    @staticmethod
    def donut_chart(win: int, loss: int, size: int = 200) -> str:
        total = win + loss
        if total == 0:
            return SVGDashboard._empty_donut(size)

        win_angle = (win / total) * 360
        loss_angle = (loss / total) * 360

        r = size // 2 - 10
        cx = size // 2
        cy = size // 2

        win_path = SVGDashboard._arc_path(cx, cy, r, 0, win_angle)
        loss_path = SVGDashboard._arc_path(cx, cy, r, win_angle, win_angle + loss_angle)

        win_color = '#22c55e'
        loss_color = '#ef4444'
        bg_color = '#1f2937'

        svg = f'''<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="{bg_color}"/>
  <path d="{win_path}" fill="{win_color}" opacity="0.9"/>
  <path d="{loss_path}" fill="{loss_color}" opacity="0.9"/>
  <circle cx="{cx}" cy="{cy}" r="{r * 0.6}" fill="#111827"/>
  <text x="{cx}" y="{cy - 8}" text-anchor="middle" fill="white" font-size="24" font-weight="bold">{win + loss}</text>
  <text x="{cx}" y="{cy + 12}" text-anchor="middle" fill="#9ca3af" font-size="11">trades</text>
  <text x="{cx - r - 5}" y="{cy - r - 5}" text-anchor="end" fill="{win_color}" font-size="10">{win} win</text>
  <text x="{cx + r + 5}" y="{cy + r + 15}" text-anchor="start" fill="{loss_color}" font-size="10">{loss} loss</text>
</svg>'''
        return svg

    @staticmethod
    def _arc_path(cx: float, cy: float, r: float, start_angle: float, end_angle: float) -> str:
        start_rad = (start_angle - 90) * 3.14159 / 180
        end_rad = (end_angle - 90) * 3.14159 / 180

        x1 = cx + r * (end_rad and 1 or 0) if abs(end_angle - start_angle) > 180 else cx + r
        y1 = cy + r * 0
        x2 = cx + r
        y2 = cy + r

        if abs(end_angle - start_angle) >= 360:
            return f'M {cx} {cy - r} A {r} {r} 0 1 1 {cx - 0.001} {cy - r} A {r} {r} 0 1 1 {cx} {cy - r} Z'

        if abs(end_angle - start_angle) > 180:
            large_arc = 1
        else:
            large_arc = 0

        sx = cx + r * (start_rad and 1 or 0) if abs(end_angle - start_angle) > 180 else cx + r
        sy = cy - r if abs(end_angle - start_angle) > 180 else cy - r
        ex = cx + r * (end_rad and 1 or 0)
        ey = cy + r * (end_rad and 1 or 0)

        return f'M {cx} {cy - r} A {r} {r} 0 {large_arc} 1 {ex} {ey} L {cx} {cy} Z'

    @staticmethod
    def _empty_donut(size: int) -> str:
        cx = size // 2
        cy = size // 2
        r = size // 2 - 10
        return f'''<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="#1f2937"/>
  <circle cx="{cx}" cy="{cy}" r="{r * 0.6}" fill="#111827"/>
  <text x="{cx}" y="{cy}" text-anchor="middle" fill="#9ca3af" font-size="12">No data</text>
</svg>'''

    @staticmethod
    def kpi_card(label: str, value: str, subvalue: str = None, color: str = '#3b82f6', icon: str = None) -> str:
        icon_html = ''
        if icon:
            icon_html = f'<span class="kpi-icon">{icon}</span>'

        subvalue_html = ''
        if subvalue:
            subvalue_html = f'<div class="kpi-subvalue">{subvalue}</div>'

        return f'''<div class="kpi-card" style="border-left: 3px solid {color}">
  {icon_html}
  <div class="kpi-content">
    <div class="kpi-label">{label}</div>
    <div class="kpi-value" style="color: {color}">{value}</div>
    {subvalue_html}
  </div>
</div>'''

    @staticmethod
    def kpi_row(kpis: Dict[str, Any]) -> str:
        cards = []
        for key, data in kpis.items():
            color = data.get('color', '#3b82f6')
            icon = data.get('icon', '')
            label = data.get('label', key)
            value = data.get('value', '0')
            subvalue = data.get('subvalue', '')
            cards.append(SVGDashboard.kpi_card(label, value, subvalue, color, icon))

        return '<div class="kpi-row">' + ''.join(cards) + '</div>'

    @staticmethod
    def heatmap_mini_cells(days_data: List[Dict], min_roe: float, max_roe: float) -> str:
        """Generate HTML for mini-cells in one row (Variant 1)."""
        if not days_data:
            return '<div class="mini-cell empty"></div>'

        html = ''
        for day in days_data:
            roe = day.get('roe_pct', 0)
            date = day.get('date', '')
            color = get_mini_color(roe, min_roe, max_roe)
            html += f'<div class="mini-cell" style="background:{color}" title="{date}: {roe}%"></div>'
        return html
