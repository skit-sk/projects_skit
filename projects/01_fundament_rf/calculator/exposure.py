def calc_bal_pct(margin: float, balance: float) -> float:
    """Bal% = margin / balance × 100"""
    if not balance:
        return 0.0
    return round(margin / balance * 100, 2)


def calc_exp_pct(margin: float, leverage: float, balance: float) -> float:
    """Exp% = (margin × leverage) / balance × 100"""
    if not balance:
        return 0.0
    return round(margin * leverage / balance * 100, 2)