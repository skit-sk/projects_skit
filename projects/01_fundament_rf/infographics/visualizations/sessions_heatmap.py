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


def compute(obj_id: str, days: int = 30, metric: str = "body_pct", timezone_offset: int = 3) -> Dict[str, Any]:
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
        return {
            "error": "No 1D data", "symbol": symbol, "matrix": [], "counts": [],
            "summary": {"max": None, "min": None, "avg": 0, "total_cells": 0, "top5": []},
            "sessions_overlay": {},
        }

    grid = defaultdict(lambda: defaultdict(list))
    for c in candles:
        dt_str = c.get("datetime") or c.get("date", "")
        if not dt_str:
            continue
        try:
            ts = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        ts_local = ts + timedelta(hours=timezone_offset)
        weekday = ts_local.weekday()
        hour = ts_local.hour
        val = _metric_value(c, metric)
        grid[weekday][hour].append(val)

    matrix = []
    counts = []
    for wd in range(7):
        row = []
        cnt_row = []
        for h in range(24):
            vals = grid[wd].get(h, [])
            row.append(round(sum(vals) / len(vals), 6) if vals else 0.0)
            cnt_row.append(len(vals))
        matrix.append(row)
        counts.append(cnt_row)

    sessions_overlay = {
        "sydney":   {"start": 0,  "end": 8,  "color": "#3b82f6"},
        "tokyo":    {"start": 0,  "end": 9,  "color": "#ef4444"},
        "frankfurt":{"start": 7,  "end": 16, "color": "#f59e0b"},
        "london":   {"start": 8,  "end": 17, "color": "#10b981"},
        "new_york": {"start": 13, "end": 22, "color": "#8b5cf6"},
    }

    weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    flat = []
    for wd in range(7):
        for h in range(24):
            v = matrix[wd][h]
            n = counts[wd][h]
            if n > 0:
                flat.append({"weekday": wd, "hour": h, "value": v, "count": n})
    flat.sort(key=lambda x: -x["value"])
    summary = {
        "max": flat[0] if flat else None,
        "min": flat[-1] if flat else None,
        "avg": round(sum(f["value"] for f in flat) / len(flat), 6) if flat else 0,
        "total_cells": sum(1 for r in counts for c in r if c > 0),
        "top5": flat[:5],
    }

    metric_labels = {
        "body_pct":   "волатильность (body_pct, %)",
        "total_range":"диапазон (total_range, %)",
        "volatility": "волатильность (position_metrics, %)",
        "volume":     "объём (volume)",
    }

    return {
        "symbol": symbol,
        "obj_id": obj_id,
        "metric": metric,
        "metric_label": metric_labels.get(metric, metric),
        "days": days,
        "timezone_offset": timezone_offset,
        "candles_count": len(candles),
        "matrix": matrix,
        "counts": counts,
        "summary": summary,
        "weekday_labels": weekday_labels,
        "hour_labels": list(range(24)),
        "sessions_overlay": sessions_overlay,
        "max_value": max((max(row) for row in matrix), default=0),
    }
