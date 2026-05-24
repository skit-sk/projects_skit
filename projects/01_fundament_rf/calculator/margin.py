def calc_margin_pct(margin: float, total_margin: float) -> float:
    """Mgn% = margin / totalMargin × 100"""
    if not total_margin:
        return 0.0
    return round(margin / total_margin * 100, 2)