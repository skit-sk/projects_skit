def calc_deviation(entry_price: float, current_price: float) -> tuple:
    diff = current_price - entry_price
    pct = (diff / entry_price) * 100 if entry_price else 0.0
    return diff, pct


def calc_pnl_pct_lev(diff_pct: float, leverage: float) -> float:
    return diff_pct * leverage


def calc_pnl_usdt(roe_pct: float, volume: float) -> float:
    return roe_pct * volume / 100