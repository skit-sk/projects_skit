from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
from collections import defaultdict
from storage import get_storage


def _load_candles(symbol: str, obj_id: str, days: int = 90) -> List[dict]:
    s = get_storage()
    if not s.exists_timeframe(symbol, obj_id, "1D"):
        return []
    data = s.read_timeframe(symbol, obj_id, "1D")
    candles = data.get("candles", [])
    if days and len(candles) > days:
        candles = candles[-days:]
    return candles


def compute(obj_id: str, days: int = 30) -> Dict[str, Any]:
    from models import FundObj
    s = get_storage()
    obj = s.get(obj_id) if hasattr(s, "get") else None
    if obj is None:
        for o in s.list():
            if o.id == obj_id:
                obj = o
                break
    if obj is None:
        return {"error": f"Object {obj_id} not found"}

    symbol = obj.data.get("emoji_entry", {}).get("symbol", "?")
    candles = _load_candles(symbol, obj_id, days=days)
    if not candles:
        return {"error": "No 1D data", "symbol": symbol, "matrix": [], "sessions_overlay": {}}

    metric_key = "body_pct"
    grid = defaultdict(lambda: defaultdict(list))
    for c in candles:
        dt = c.get("datetime") or c.get("date", "")
        if not dt:
            continue
        try:
            ts = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        weekday = ts.weekday()
        hour = ts.hour
        val = c.get("candle_metrics", {}).get(metric_key, 0.0)
        grid[weekday][hour].append(val)

    matrix = []
    for wd in range(7):
        row = []
        for h in range(24):
            vals = grid[wd].get(h, [])
            row.append(round(sum(vals) / len(vals), 4) if vals else 0.0)
        matrix.append(row)

    sessions_overlay = {
        "sydney":   {"start": 0,  "end": 8,  "color": "#3b82f6"},
        "tokyo":    {"start": 0,  "end": 9,  "color": "#ef4444"},
        "frankfurt":{"start": 7,  "end": 16, "color": "#f59e0b"},
        "london":   {"start": 8,  "end": 17, "color": "#10b981"},
        "new_york": {"start": 13, "end": 22, "color": "#8b5cf6"},
    }

    weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return {
        "symbol": symbol,
        "obj_id": obj_id,
        "metric": metric_key,
        "days": days,
        "candles_count": len(candles),
        "matrix": matrix,
        "weekday_labels": weekday_labels,
        "hour_labels": list(range(24)),
        "sessions_overlay": sessions_overlay,
        "max_value": max((max(row) for row in matrix), default=0),
    }
