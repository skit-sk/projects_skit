def calc_body(o: float, c: float) -> tuple:
    body = abs(c - o)
    body_pct = (body / o * 100) if o else 0.0
    return body, body_pct


def calc_wicks(o: float, h: float, l: float, c: float) -> tuple:
    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - l
    return upper_wick, lower_wick


def calc_volatility(h: float, l: float) -> float:
    return h - l


def calc_volatility_pct(h: float, l: float, close: float) -> float:
    if not close:
        return 0.0
    vol = h - l
    return round(vol / close * 100, 2)


def calc_volatility_lev(vol_pct: float, leverage: float) -> float:
    return round(vol_pct * leverage, 2)


def calc_day_metrics(o: float, h: float, l: float, c: float,
                     entry_price: float, leverage: float, volume: float) -> dict:
    from .deviation import calc_pnl_pct_lev, calc_pnl_usdt
    body, body_pct = calc_body(o, c)
    upper_wick, lower_wick = calc_wicks(o, h, l, c)
    volatility = calc_volatility(h, l)
    vol_pct = calc_volatility_pct(h, l, c)

    deviation_pct = ((c - entry_price) / entry_price * 100) if entry_price else 0.0
    roe_pct = calc_pnl_pct_lev(deviation_pct, leverage)
    pnl_usdt = calc_pnl_usdt(roe_pct, volume)
    profitable = roe_pct > 0

    return {
        "body": round(body, 6),
        "body_pct": round(body_pct, 4),
        "upper_wick": round(upper_wick, 6),
        "lower_wick": round(lower_wick, 6),
        "volatility": round(volatility, 6),
        "volatility_pct": vol_pct,
        "volatility_lev": calc_volatility_lev(vol_pct, leverage),
        "deviation_pct": round(deviation_pct, 4),
        "roe_pct": round(roe_pct, 4),
        "pnl_usdt": round(pnl_usdt, 6),
        "profitable": profitable,
    }