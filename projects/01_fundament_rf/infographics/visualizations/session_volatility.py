from typing import Dict, List, Any
from collections import defaultdict
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


def _metric_value(candle: dict, metric: str) -> float:
    if metric == "body_pct":
        return candle.get("candle_metrics", {}).get("body_pct", 0.0)
    if metric == "total_range":
        return candle.get("candle_metrics", {}).get("total_range", 0.0)
    if metric == "volatility":
        return candle.get("position_metrics", {}).get("volatility", 0.0)
    if metric == "volume":
        return float(candle.get("volume", 0))
    return 0.0


def _stats(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"n": 0, "min": 0, "max": 0, "mean": 0, "median": 0, "q1": 0, "q3": 0, "std": 0}
    s = sorted(values)
    n = len(s)
    def pct(p):
        if n == 1:
            return s[0]
        k = (n - 1) * p
        f = int(k)
        c = min(f + 1, n - 1)
        return s[f] + (s[c] - s[f]) * (k - f)
    mean = sum(s) / n
    var = sum((x - mean) ** 2 for x in s) / n
    return {
        "n": n,
        "min": round(s[0], 6),
        "max": round(s[-1], 6),
        "mean": round(mean, 6),
        "median": round(pct(0.5), 6),
        "q1": round(pct(0.25), 6),
        "q3": round(pct(0.75), 6),
        "std": round(var ** 0.5, 6),
    }


def compute(obj_id: str, lookback_days: int = 90, metric: str = "body_pct") -> Dict[str, Any]:
    obj = _resolve_obj(obj_id)
    if obj is None:
        return {"error": f"Object {obj_id} not found"}

    symbol = obj.data.get("emoji_entry", {}).get("symbol", "?")
    s = get_storage()
    if not s.exists_timeframe(symbol, obj_id, "1D"):
        return {"error": "No 1D data", "symbol": symbol}
    data = s.read_timeframe(symbol, obj_id, "1D")
    candles = data.get("candles", [])
    if lookback_days and len(candles) > lookback_days:
        candles = candles[-lookback_days:]

    by_session = defaultdict(list)
    for c in candles:
        active = c.get("sessions", {}).get("active", [])
        val = _metric_value(c, metric)
        for sess in active:
            by_session[sess].append(val)

    sessions_data = []
    for sess_name, vals in by_session.items():
        stats = _stats(vals)
        sessions_data.append({
            "session": sess_name,
            "values": [round(v, 6) for v in vals],
            "stats": stats,
        })

    sessions_data.sort(key=lambda x: -x["stats"]["mean"])

    return {
        "symbol": symbol,
        "obj_id": obj_id,
        "lookback_days": lookback_days,
        "metric": metric,
        "candles_count": len(candles),
        "sessions": sessions_data,
    }
