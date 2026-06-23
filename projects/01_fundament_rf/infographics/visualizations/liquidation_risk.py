from typing import Dict, List, Any
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


def _classify(distance_pct: float) -> str:
    if distance_pct < 5:
        return "critical"
    if distance_pct < 10:
        return "high"
    if distance_pct < 20:
        return "medium"
    return "low"


def compute(obj_id: str) -> Dict[str, Any]:
    obj = _resolve_obj(obj_id)
    if obj is None:
        return {"error": f"Object {obj_id} not found"}

    symbol = obj.data.get("emoji_entry", {}).get("symbol", "?")
    s = get_storage()
    if not s.exists_timeframe(symbol, obj_id, "1D"):
        return {"error": "No 1D data", "symbol": symbol}
    data = s.read_timeframe(symbol, obj_id, "1D")
    candles = data.get("candles", [])

    current_price = candles[-1].get("close", 0) if candles else 0
    last_liq = candles[-1].get("liq_proximity", {}) if candles else {}
    liq_10x = last_liq.get("liq_price_10x", 0)
    liq_5x  = last_liq.get("liq_price_5x", 0)
    liq_2x  = last_liq.get("liq_price_2x", 0)

    def dist_pct(liq_price: float) -> float:
        if not current_price or not liq_price:
            return 0.0
        return round(abs(current_price - liq_price) / current_price * 100, 2)

    d10 = dist_pct(liq_10x)
    d5  = dist_pct(liq_5x)
    d2  = dist_pct(liq_2x)
    closest = min(d10, d5, d2)
    risk_level = _classify(closest)

    timeline = []
    for c in candles:
        lp = c.get("liq_proximity", {})
        date = c.get("date", "")
        c10 = lp.get("liq_price_10x", 0)
        c5  = lp.get("liq_price_5x", 0)
        c2  = lp.get("liq_price_2x", 0)
        close = c.get("close", 0)
        distances = []
        if close and c10:
            distances.append(("10x", abs(close - c10) / close * 100))
        if close and c5:
            distances.append(("5x", abs(close - c5) / close * 100))
        if close and c2:
            distances.append(("2x", abs(close - c2) / close * 100))
        if not distances:
            continue
        distances.sort(key=lambda x: x[1])
        closest_level, closest_d = distances[0]
        at_risk = closest_d < 10
        triggered = lp.get("touched_10x", False) or lp.get("touched_5x", False) or lp.get("touched_2x", False)
        timeline.append({
            "date": date,
            "close": close,
            "at_risk": at_risk,
            "triggered": triggered,
            "closest_level": closest_level,
            "closest_distance_pct": round(closest_d, 2),
        })

    days_at_risk_10x = sum(1 for t in timeline if t["closest_level"] == "10x" and t["at_risk"])
    days_at_risk_5x  = sum(1 for t in timeline if t["closest_level"] == "5x"  and t["at_risk"])
    days_at_risk_2x  = sum(1 for t in timeline if t["closest_level"] == "2x"  and t["at_risk"])
    triggered_count  = sum(1 for t in timeline if t["triggered"])
    max_dd = max((t["closest_distance_pct"] for t in timeline), default=0)

    return {
        "symbol": symbol,
        "obj_id": obj_id,
        "candles_count": len(candles),
        "current": {
            "price": current_price,
            "liq_10x": liq_10x,
            "liq_5x": liq_5x,
            "liq_2x": liq_2x,
            "distance_pct": {"10x": d10, "5x": d5, "2x": d2},
            "risk_level": risk_level,
        },
        "timeline": timeline,
        "stats": {
            "days_at_risk_10x": days_at_risk_10x,
            "days_at_risk_5x": days_at_risk_5x,
            "days_at_risk_2x": days_at_risk_2x,
            "triggered_count": triggered_count,
            "max_drawdown_pct": round(max_dd, 2),
        },
    }
