"""
Unified data loader for 03_demo_charts_ascii.

Reads 1D data from 01_fundament_rf via HTTP API (when available) with
filesystem fallback (for Vercel deploys or offline use).
"""
import json
import os
import urllib.request
import urllib.error
from pathlib import Path

FUNDAMENT_DIR = Path("/home/user_aioc/workspace/projects/01_fundament_rf/data/card")
LOCAL_DATA_DIR = Path(__file__).parent / "data"  # 03's own local mirror (for Vercel)
HTTP_BASE = os.environ.get("FUNDAMENT_HTTP", "http://localhost:5000")
HTTP_TIMEOUT = 2.0


def _fetch_1d_http(obj_id: str) -> dict | None:
    """Try to fetch 1D data in legacy format (days[]/chart_data[]/summary) via processor_1d API."""
    try:
        url = f"{HTTP_BASE}/processor_1d/data/{obj_id}"
        with urllib.request.urlopen(url, timeout=HTTP_TIMEOUT) as r:
            return json.loads(r.read())
    except (urllib.error.URLError, OSError, ValueError, KeyError):
        return None


def _fetch_raw_http(obj_id: str) -> dict | None:
    """Try to fetch RAW data via the processor_1d API."""
    try:
        url = f"{HTTP_BASE}/processor_1d/raw/{obj_id}"
        with urllib.request.urlopen(url, timeout=HTTP_TIMEOUT) as r:
            return json.loads(r.read())
    except (urllib.error.URLError, OSError, ValueError, KeyError):
        return None


def _fetch_1d_filesystem(obj_id: str) -> dict | None:
    """Try 03's local data first (already in legacy format), then 01's dir (new format)."""
    # 03's own local data (committed for Vercel) — already legacy format
    for f in LOCAL_DATA_DIR.rglob(f"{obj_id}_1D.json"):
        try:
            with open(f) as fp:
                data = json.load(fp)
            if data.get("days"):
                    return data  # legacy format
        except (OSError, json.JSONDecodeError):
            continue
    # 01's data — new format, needs conversion
    for f in FUNDAMENT_DIR.rglob(f"{obj_id}_1D.json"):
        try:
            with open(f) as fp:
                data = json.load(fp)
            return _new_to_legacy(data, obj_id)
        except (OSError, json.JSONDecodeError):
            continue
    return None


def _fetch_raw_filesystem(obj_id: str) -> dict | None:
    """Fallback: read RAW from filesystem."""
    for f in FUNDAMENT_DIR.rglob(f"{obj_id}_RAW.json"):
        try:
            with open(f) as fp:
                return json.load(fp)
        except (OSError, json.JSONDecodeError):
            continue
    return None


def load_1d(obj_id: str) -> dict | None:
    """
    Load 1D data: HTTP-first, FS-fallback.

    Returns the legacy format (days[]/chart_data[]/summary) for backward compat
    with 03's consumers (which expect days[]).
    """
    return _fetch_1d_http(obj_id) or _fetch_1d_filesystem(obj_id)


def load_raw(obj_id: str) -> dict | None:
    """Load RAW data: HTTP-first, FS-fallback."""
    return _fetch_raw_http(obj_id) or _fetch_raw_filesystem(obj_id)


def _new_to_legacy(data: dict, obj_id: str) -> dict:
    """
    Convert new-format 1D data (candles[]) to legacy shape (days[]/chart_data[]/summary).
    Inline copy of 01_fundament_rf/storage._candles_to_legacy to keep 03 self-contained.
    """
    candles = data.get("candles", [])
    days = []
    chart_data = []
    pre_entry_count = 0
    profitable_count = 0
    loss_count = 0
    neutral_count = 0
    sum_roe = 0.0
    sum_volatility = 0.0
    current_roe = 0.0
    current_pnl = 0.0
    max_profit_day = None
    max_loss_day = None
    max_drawdown_pct = 0.0
    max_drawdown_usdt = 0.0
    streak_profit = 0
    streak_loss = 0
    current_streak = 0
    streak_type = None

    for i, c in enumerate(candles):
        pm = c.get("position_metrics", {})
        cm = c.get("candle_metrics", {})
        is_pre = pm.get("pre_entry", False)
        roe = pm.get("roe_pct", 0) if not is_pre else 0
        pnl = pm.get("pnl_usdt", 0) if not is_pre else 0
        profitable = pm.get("profitable", False) if not is_pre else False
        volatility = pm.get("volatility", 0)
        deviation = pm.get("deviation", {})
        day = {
            "date": c.get("date", ""),
            "day_index": i,
            "pre_entry": is_pre,
            "ohlc": {
                "open": c.get("open", 0),
                "high": c.get("high", 0),
                "low": c.get("low", 0),
                "close": c.get("close", 0),
                "body": cm.get("body", 0),
                "body_pct": pm.get("body_pct", 0),
                "upper_wick": cm.get("upper_wick", 0),
                "lower_wick": cm.get("lower_wick", 0),
            },
            "deviation": deviation,
            "roe_pct": roe,
            "pnl_usdt": pnl,
            "volatility": volatility,
            "profitable": profitable,
        }
        days.append(day)
        chart_data.append({
            "date": c.get("date", ""),
            "deviation_pct": deviation.get("from_entry_pct", 0),
            "profitable": profitable,
            "pre_entry": is_pre,
        })
        if not is_pre:
            if profitable:
                profitable_count += 1
            if roe < 0:
                loss_count += 1
            if roe == 0:
                neutral_count += 1
            sum_roe += roe
            sum_volatility += volatility
            current_roe = roe
            current_pnl = pnl
            if max_profit_day is None or roe > max_profit_day["roe_pct"]:
                max_profit_day = day
            if max_loss_day is None or roe < max_loss_day["roe_pct"]:
                max_loss_day = day
            max_drawdown_pct = min(max_drawdown_pct, deviation.get("from_entry_pct", 0))
            max_drawdown_usdt = min(max_drawdown_usdt, deviation.get("from_entry_usdt", 0))
            if profitable:
                if streak_type == "profit":
                    current_streak += 1
                else:
                    current_streak = 1
                    streak_type = "profit"
                streak_profit = max(streak_profit, current_streak)
            else:
                if streak_type == "loss":
                    current_streak += 1
                else:
                    current_streak = 1
                    streak_type = "loss"
                streak_loss = max(streak_loss, current_streak)

    total_days = sum(1 for d in days if not d["pre_entry"])
    summary = {
        "total_days": total_days,
        "profitable_days": profitable_count,
        "loss_days": loss_count,
        "neutral_days": neutral_count,
        "current_roe_pct": round(current_roe, 2),
        "current_pnl_usdt": round(current_pnl, 4),
        "avg_roe_pct": round(sum_roe / total_days, 2) if total_days else 0,
        "avg_volatility": round(sum_volatility / total_days, 6) if total_days else 0,
        "max_profit_day": {
            "date": max_profit_day["date"], "roe_pct": max_profit_day["roe_pct"],
            "pnl_usdt": max_profit_day["pnl_usdt"],
        } if max_profit_day else {},
        "max_loss_day": {
            "date": max_loss_day["date"], "roe_pct": max_loss_day["roe_pct"],
            "pnl_usdt": max_loss_day["pnl_usdt"],
        } if max_loss_day else {},
        "max_drawdown_pct": round(max_drawdown_pct, 2),
        "max_drawdown_usdt": round(max_drawdown_usdt, 6),
        "streak_profit": streak_profit,
        "streak_loss": streak_loss,
    } if total_days else {}

    return {
        "id": f"{obj_id}_1D",
        "parent_id": obj_id,
        "symbol": data.get("symbol", ""),
        "entry_price": data.get("entry_price", 0),
        "entry_date": data.get("entry_date", ""),
        "leverage": data.get("leverage", 10),
        "volume": data.get("volume", 1),
        "status": "completed",
        "days": days,
        "chart_data": chart_data,
        "summary": summary,
    }
