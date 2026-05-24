def calc_liq_delta(current_price: float, liquidation_price: float) -> float:
    """LiqΔ% = abs((price - liqPrice) / price) × 100"""
    if not current_price or liquidation_price <= 0:
        return 0.0
    return round(abs((current_price - liquidation_price) / current_price * 100), 2)


def calc_risk_flags(roe: float, liq_delta: float, exp_pct: float) -> list:
    flags = []
    if roe < -50:
        flags.append(f"PnL {roe:.0f}%")
    if liq_delta < 5 and liq_delta > 0:
        flags.append(f"LiqΔ {liq_delta:.1f}%")
    if exp_pct > 50:
        flags.append(f"Exp {exp_pct:.0f}%")
    return flags