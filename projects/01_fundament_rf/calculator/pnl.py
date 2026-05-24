def calc_roe(unrealized_pl: float, margin_size: float) -> float:
    """ROE% = P&L / margin × 100"""
    if not margin_size:
        return 0.0
    return round(unrealized_pl / margin_size * 100, 2)


def calc_ror(unrealized_pl: float, balance: float) -> float:
    """ROR% = P&L / balance × 100"""
    if not balance:
        return 0.0
    return round(unrealized_pl / balance * 100, 2)


def calc_pnl_pct_lev(diff_pct: float, leverage: float) -> float:
    """ROE% with leverage = price_change% × leverage"""
    return round(diff_pct * leverage, 2)


def calc_pnl_usdt(roe_pct: float, volume: float) -> float:
    """PnL in USDT = ROE% × volume / 100"""
    return round(roe_pct * volume / 100, 4)