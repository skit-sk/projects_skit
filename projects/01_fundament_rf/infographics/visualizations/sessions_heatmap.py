from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
from collections import defaultdict
from storage import get_storage


VALID_VIEWS = ("calendar", "bars", "direction", "weekday", "heatmap")


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


def _view_calendar(candles: List[dict], metric: str, tz_offset: int) -> Dict[str, Any]:
    months: Dict[str, List[float]] = {}
    for c in candles:
        date_str = c.get("date", "")
        if not date_str:
            continue
        try:
            ts = datetime.fromisoformat(date_str + "T00:00:00")
        except (ValueError, TypeError):
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        ts_local = ts + timedelta(hours=tz_offset)
        ym = ts_local.strftime("%Y-%m")
        day_idx = ts_local.day - 1
        months.setdefault(ym, [0.0] * 31)
        months[ym][day_idx] = round(_metric_value(c, metric), 6)

    calendar = []
    for ym in sorted(months.keys()):
        calendar.append({"month": ym, "days": months[ym]})
    max_val = 0.0
    for m in calendar:
        for v in m["days"]:
            if v > max_val:
                max_val = v
    return {"calendar": calendar, "max_value": max_val}


def _view_daily_bars(candles: List[dict], metric: str) -> Dict[str, Any]:
    bars = []
    for c in candles:
        is_green = c.get("close", 0) >= c.get("open", 0)
        bars.append({
            "date": c.get("date", ""),
            "value": _metric_value(c, metric),
            "direction": "up" if is_green else "down",
            "high": c.get("high", 0),
            "low": c.get("low", 0),
            "open": c.get("open", 0),
            "close": c.get("close", 0),
        })
    max_val = max((b["value"] for b in bars), default=0)
    return {"bars": bars, "max_value": max_val}


def _view_direction(candles: List[dict]) -> Dict[str, Any]:
    total = len(candles)
    green = sum(1 for c in candles if c.get("close", 0) >= c.get("open", 0))
    red = total - green

    longest_green = longest_red = current_g = current_r = 0
    for c in candles:
        is_green = c.get("close", 0) >= c.get("open", 0)
        if is_green:
            current_g += 1
            current_r = 0
            if current_g > longest_green:
                longest_green = current_g
        else:
            current_r += 1
            current_g = 0
            if current_r > longest_red:
                longest_red = current_r

    return {
        "total": total,
        "green_count": green,
        "red_count": red,
        "green_pct": round(green / total * 100, 2) if total else 0,
        "red_pct": round(red / total * 100, 2) if total else 0,
        "longest_green_streak": longest_green,
        "longest_red_streak": longest_red,
    }


def _view_weekday(candles: List[dict], metric: str) -> Dict[str, Any]:
    by_wd: Dict[int, List[float]] = defaultdict(list)
    for c in candles:
        date_str = c.get("date", "")
        if not date_str:
            continue
        try:
            ts = datetime.fromisoformat(date_str + "T00:00:00")
        except (ValueError, TypeError):
            continue
        by_wd[ts.weekday()].append(_metric_value(c, metric))

    summary = []
    for wd in range(7):
        vals = by_wd.get(wd, [])
        if vals:
            summary.append({
                "weekday": wd,
                "avg": round(sum(vals) / len(vals), 6),
                "min": round(min(vals), 6),
                "max": round(max(vals), 6),
                "count": len(vals),
            })
        else:
            summary.append({"weekday": wd, "avg": 0, "min": 0, "max": 0, "count": 0})
    max_val = max((s["max"] for s in summary if s["max"] > 0), default=0)
    return {"weekday_summary": summary, "max_value": max_val}


def _view_hour_heatmap(candles: List[dict], metric: str, tz_offset: int) -> Dict[str, Any]:
    grid: Dict[int, Dict[int, List[float]]] = defaultdict(lambda: defaultdict(list))
    for c in candles:
        date_str = c.get("date", "")
        if not date_str:
            continue
        try:
            ts = datetime.fromisoformat(date_str + "T00:00:00")
        except (ValueError, TypeError):
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        ts_local = ts + timedelta(hours=tz_offset)
        grid[ts_local.weekday()][ts_local.hour].append(_metric_value(c, metric))

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
    max_val = max((max(r) for r in matrix), default=0)
    return {
        "matrix": matrix,
        "counts": counts,
        "summary": summary,
        "max_value": max_val,
        "data_note": "1D timeframe: каждый день = 1 точка. Heatmap показывает распределение по (weekday × hour_from_date), не реальные hourly движения. Для настоящего 24×7 нужны синхронизированные 1h данные.",
    }


def compute(obj_id: str, days: int = 90, metric: str = "body_pct",
            view: str = "calendar", timezone_offset: int = 3) -> Dict[str, Any]:
    if view not in VALID_VIEWS:
        return {"error": f"Unknown view: {view}", "valid_views": list(VALID_VIEWS)}

    obj = _resolve_obj(obj_id)
    if obj is None:
        return {"error": f"Object {obj_id} not found"}

    symbol = obj.data.get("emoji_entry", {}).get("symbol", "?")
    s = get_storage()
    if not s.exists_timeframe(symbol, obj_id, "1D"):
        return {
            "error": f"No 1D data for {symbol}",
            "symbol": symbol,
            "needs_sync": True,
            "view": view,
        }

    candles = _load_candles(symbol, obj_id, days=days)
    if not candles:
        return {
            "error": "Empty 1D data",
            "symbol": symbol,
            "view": view,
        }

    base = {
        "symbol": symbol,
        "obj_id": obj_id,
        "metric": metric,
        "view": view,
        "days": days,
        "candles_count": len(candles),
        "tz_offset": timezone_offset,
    }

    if view == "calendar":
        base.update(_view_calendar(candles, metric, timezone_offset))
    elif view == "bars":
        base.update(_view_daily_bars(candles, metric))
    elif view == "direction":
        base.update(_view_direction(candles))
    elif view == "weekday":
        base.update(_view_weekday(candles, metric))
    elif view == "heatmap":
        base.update(_view_hour_heatmap(candles, metric, timezone_offset))

    return base
