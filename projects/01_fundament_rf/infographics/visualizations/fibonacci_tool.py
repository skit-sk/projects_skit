from typing import Dict, List, Any
from datetime import datetime
from storage import get_storage


def _resolve_obj(obj_id: str):
    s = get_storage()
    try:
        obj = s.get(obj_id) if hasattr(s, "get") else None
    except Exception:
        obj = None
    if obj is not None:
        return obj
    for o in s.list():
        if o.id == obj_id:
            return o
    return None


RETRACEMENT_LEVELS = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.618]
EXTENSION_LEVELS   = [0.0, 0.618, 1.0, 1.272, 1.618, 2.0, 2.618]


def compute(obj_id: str, date_from: str = None, date_to: str = None, mode: str = "retracement") -> Dict[str, Any]:
    obj = _resolve_obj(obj_id)
    if obj is None:
        return {"error": f"Object {obj_id} not found"}

    symbol = obj.data.get("emoji_entry", {}).get("symbol", "?")
    s = get_storage()
    if not s.exists_timeframe(symbol, obj_id, "1D"):
        return {"error": "No 1D data", "symbol": symbol}
    data = s.read_timeframe(symbol, obj_id, "1D")
    candles = data.get("candles", [])

    df = None
    dt = None
    try:
        if date_from:
            df = datetime.fromisoformat(date_from)
        if date_to:
            dt = datetime.fromisoformat(date_to)
    except (ValueError, TypeError):
        df = dt = None

    filtered = []
    for c in candles:
        d_str = c.get("date", "")
        try:
            d = datetime.fromisoformat(d_str)
        except (ValueError, TypeError):
            filtered.append(c)
            continue
        if df and d < df:
            continue
        if dt and d > dt:
            continue
        filtered.append(c)
    if not filtered:
        filtered = candles

    if not filtered:
        return {"error": "Empty range", "symbol": symbol}

    highs = [c.get("high", 0) for c in filtered if c.get("high")]
    lows  = [c.get("low", 0)  for c in filtered if c.get("low")]
    if not highs or not lows:
        return {"error": "No OHLC", "symbol": symbol}

    high_idx = highs.index(max(highs))
    low_idx  = lows.index(min(lows))
    high_price = max(highs)
    low_price  = min(lows)
    range_p    = high_price - low_price

    levels = RETRACEMENT_LEVELS if mode == "retracement" else EXTENSION_LEVELS
    fib_levels = []
    for lv in levels:
        if mode == "retracement":
            price = high_price - range_p * lv
        else:
            price = low_price + range_p * lv
        fib_levels.append({"level": lv, "price": round(price, 6)})

    chart = []
    for c in filtered:
        chart.append({
            "date": c.get("date", ""),
            "open": c.get("open", 0),
            "high": c.get("high", 0),
            "low":  c.get("low", 0),
            "close": c.get("close", 0),
        })

    return {
        "symbol": symbol,
        "obj_id": obj_id,
        "mode": mode,
        "range": {
            "high": high_price,
            "low": low_price,
            "size": round(range_p, 6),
            "high_idx": high_idx,
            "low_idx": low_idx,
        },
        "levels": fib_levels,
        "candles": chart,
        "date_from": date_from,
        "date_to": date_to,
    }
