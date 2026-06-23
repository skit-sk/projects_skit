import time
import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from storage import get_storage
from enrichers.position_metrics import PositionMetricsEnricher


def _build_old_days(raw_candles, entry_price, entry_date, leverage, volume):
    """Replicate the OLD processor_1d._calculate_day logic via calc_day_metrics."""
    from calculator import calc_day_metrics
    days = []
    for i, rc in enumerate(raw_candles):
        o, h, l, c = float(rc["open"]), float(rc["high"]), float(rc["low"]), float(rc["close"])
        dm = calc_day_metrics(o, h, l, c, entry_price, leverage, volume)
        deviation_from_entry_usdt = c - entry_price
        deviation_from_open_usdt = c - o
        deviation_from_open_pct = ((c - o) / o * 100) if o != 0 else 0

        is_pre = (entry_date and rc.get("date", "") < entry_date)
        roe_pct = round(dm["roe_pct"], 2) if not is_pre else 0
        pnl_usdt = round(dm["pnl_usdt"], 4) if not is_pre else 0
        profitable = dm["profitable"] if not is_pre else False

        days.append({
            "date": rc["date"],
            "day_index": i,
            "pre_entry": is_pre,
            "ohlc": {
                "open": round(o, 6),
                "high": round(h, 6),
                "low": round(l, 6),
                "close": round(c, 6),
                "body": dm["body"],
                "body_pct": round(dm["body_pct"], 2),
                "upper_wick": dm["upper_wick"],
                "lower_wick": dm["lower_wick"],
            },
            "deviation": {
                "from_entry_usdt": round(deviation_from_entry_usdt, 6),
                "from_entry_pct": round(dm["deviation_pct"], 2),
                "from_open_usdt": round(deviation_from_open_usdt, 6),
                "from_open_pct": round(deviation_from_open_pct, 2),
            },
            "roe_pct": roe_pct,
            "pnl_usdt": pnl_usdt,
            "volatility": dm["volatility"],
            "profitable": profitable,
        })
    return days


def _build_old_summary(days):
    """Replicate processor_1d._calculate_summary logic."""
    filtered = [d for d in days if not d.get("pre_entry")]
    total = len(filtered)
    if total == 0:
        return {}
    profitable_count = sum(1 for d in filtered if d["profitable"])
    loss_count = sum(1 for d in filtered if d["roe_pct"] < 0)
    neutral_count = sum(1 for d in filtered if d["roe_pct"] == 0)
    avg_roe = sum(d["roe_pct"] for d in filtered) / total
    avg_vol = sum(d["volatility"] for d in filtered) / total

    last = filtered[-1]
    max_profit_day = max(filtered, key=lambda x: x["roe_pct"])
    max_loss_day = min(filtered, key=lambda x: x["roe_pct"])
    max_drawdown = min(d["deviation"]["from_entry_pct"] for d in filtered)
    max_drawdown_usdt = min(d["deviation"]["from_entry_usdt"] for d in filtered)

    streak_profit = 0
    streak_loss = 0
    current_streak = 0
    streak_type = None
    for d in filtered:
        if d["profitable"]:
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

    return {
        "total_days": total,
        "profitable_days": profitable_count,
        "loss_days": loss_count,
        "neutral_days": neutral_count,
        "current_roe_pct": round(last["roe_pct"], 2),
        "current_pnl_usdt": round(last["pnl_usdt"], 4),
        "avg_roe_pct": round(avg_roe, 2),
        "avg_volatility": round(avg_vol, 6),
        "max_profit_day": {
            "date": max_profit_day["date"],
            "roe_pct": max_profit_day["roe_pct"],
            "pnl_usdt": max_profit_day["pnl_usdt"],
        },
        "max_loss_day": {
            "date": max_loss_day["date"],
            "roe_pct": max_loss_day["roe_pct"],
            "pnl_usdt": max_loss_day["pnl_usdt"],
        },
        "max_drawdown_pct": round(max_drawdown, 2),
        "max_drawdown_usdt": round(max_drawdown_usdt, 6),
        "streak_profit": streak_profit,
        "streak_loss": streak_loss,
    }


def _compare_days(expected_days, actual_days):
    n = min(len(expected_days), len(actual_days))
    errors = 0
    for i in range(n):
        ex, ac = expected_days[i], actual_days[i]
        if ex.get("date") != ac.get("date"):
            errors += 1
        for k in ("day_index", "pre_entry", "profitable"):
            if ex.get(k) != ac.get(k):
                errors += 1
        for k in ("roe_pct", "pnl_usdt", "volatility"):
            if abs(float(ex.get(k, 0)) - float(ac.get(k, 0))) > 1e-4:
                errors += 1
        for f in ("open", "high", "low", "close", "body", "body_pct",
                   "upper_wick", "lower_wick"):
            ev = float(ex.get("ohlc", {}).get(f, 0))
            av = float(ac.get("ohlc", {}).get(f, 0))
            if abs(ev - av) > 1e-6:
                errors += 1
        for f in ("from_entry_usdt", "from_entry_pct",
                   "from_open_usdt", "from_open_pct"):
            ev = float(ex.get("deviation", {}).get(f, 0))
            av = float(ac.get("deviation", {}).get(f, 0))
            if abs(ev - av) > 1e-6:
                errors += 1
    return n, errors


def _compare_summary(expected, actual):
    exp_sum = expected
    act_sum = actual
    keys = [
        "total_days", "profitable_days", "loss_days", "neutral_days",
        "current_roe_pct", "current_pnl_usdt", "avg_roe_pct", "avg_volatility",
        "max_drawdown_pct", "max_drawdown_usdt", "streak_profit", "streak_loss",
    ]
    errors = 0
    for k in keys:
        if abs(float(exp_sum.get(k, 0)) - float(act_sum.get(k, 0))) > 1e-4:
            errors += 1
    return errors


def test_object(obj):
    s = get_storage()
    obj_id = obj.id
    symbol = obj.data.get("emoji_entry", {}).get("symbol", "?")

    # Read current 1D file to get entry_price/leverage/volume
    data = s.read_timeframe(symbol, obj_id, "1D")
    entry_price = float(data.get("entry_price", 0))
    entry_date = data.get("entry_date", "")
    leverage = int(data.get("leverage", 10))
    volume = float(data.get("volume", 1))
    new_candles = data.get("candles", [])
    if not new_candles:
        print(f"  SKIP {symbol} #{obj_id[:8]}: no new-format candles")
        return True

    # Use NEW-format candles (the current state) as the common input.
    # This is fair: both old and new code paths read the same OHLC values.
    # The test verifies that the new pipeline computes the same days/summary
    # as the OLD code would, given the same candles.
    source_candles = []
    for c in new_candles:
        source_candles.append({
            "date": c.get("date", ""),
            "open": c.get("open", 0),
            "high": c.get("high", 0),
            "low": c.get("low", 0),
            "close": c.get("close", 0),
            "volume": c.get("volume", 0),
        })

    # Build OLD days from source candles (replicating _process_object logic)
    old_days = _build_old_days(source_candles, entry_price, entry_date, leverage, volume)
    old_summary = _build_old_summary(old_days)

    # Build NEW days from the SAME candles (via _candles_to_legacy which uses
    # PositionMetricsEnricher inside the pipeline)
    tf_data = s.read_timeframe(symbol, obj_id, "1D")
    new_actual = s._candles_to_legacy(symbol, obj_id, tf_data)
    new_days = new_actual.get("days", [])
    new_summary = new_actual.get("summary", {})

    n, day_errors = _compare_days(old_days, new_days)
    sum_errors = _compare_summary(old_summary, new_summary)
    total = day_errors + sum_errors

    status = "✅" if total == 0 else "❌"
    print(f"  {status} {symbol} #{obj_id[:8]}: {n} days, "
          f"day_errors={day_errors}, sum_errors={sum_errors}")
    return total == 0


def test_candle_to_day_mapping():
    s = get_storage()
    obj = s.list()[0]
    return test_object(obj)


def test_all_objects():
    s = get_storage()
    fail = 0
    for obj in s.list():
        obj_id = obj.id
        symbol = obj.data.get("emoji_entry", {}).get("symbol", "?")
        if not s.exists_timeframe(symbol, obj_id, "1D"):
            continue
        if not s.exists_raw(symbol, obj_id):
            continue
        if not test_object(obj):
            fail += 1
    assert fail == 0, f"test_all_objects: {fail} object(s) failed"


if __name__ == "__main__":
    print("=== Detailed test (first object) ===")
    test_candle_to_day_mapping()
    print("\n=== All objects ===")
    test_all_objects()
    print("\n✅✅✅ All regression tests passed")
