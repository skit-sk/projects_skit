#!/usr/bin/env python3
"""Generate individual chart images per position using Plotly + API.

Usage:
  python3 generate_graphs.py --uid <uid> [--dir <output_dir>] [--limit N]
  python3 generate_graphs.py --uid 248207602
"""

import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime

import os
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib_cache")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime as dt

BASE_URL = "http://localhost:5000"
TG_PROJECT = os.path.expanduser("~/workspace/projects/07_tg_bot_aiforguest")
TG_ALL_DIR = os.path.join(TG_PROJECT, "TG_ALL")


def fetch_objects() -> list[dict]:
    """Парсит /graphics/all, извлекает id/symbol/price/date из каждого <div class='chart-card'>."""
    resp = urllib.request.urlopen(f"{BASE_URL}/graphics/all", timeout=10)
    html = resp.read().decode("utf-8")
    pattern = r'class="chart-card"[^>]*data-id="([^"]+)"[^>]*data-symbol="([^"]+)"[^>]*data-entry-price="([^"]*)"[^>]*data-entry-date="([^"]*)"'
    objects = [
        {"id": m[1], "symbol": m[2], "entry_price": m[3] or None, "entry_date": m[4] or None}
        for m in re.finditer(pattern, html)
        if m[2] and m[2] != "?"
    ]
    return objects


def fetch_chart_data(obj_id: str) -> dict | None:
    """GET /graphics/chart/<id>, возвращает JSON."""
    try:
        resp = urllib.request.urlopen(
            f"{BASE_URL}/graphics/chart/{obj_id}", timeout=15
        )
        return json.loads(resp.read())
    except Exception as e:
        print(f"WARN: fetch_chart({obj_id}) failed: {e}", file=sys.stderr)
        return None


def generate_chart(symbol: str, data: dict, output_path: str) -> int | None:
    """Создать PNG-график через matplotlib, вернуть время рендера в ms."""
    chart_points = data.get("chart", [])
    summary = data.get("summary", {})
    if not chart_points or not summary:
        return None

    dates_raw = [p.get("date", "") for p in chart_points]
    dev_pct = [p.get("deviation_percent", 0) for p in chart_points]
    profitable = [p.get("profitable", False) for p in chart_points]

    entry_price = summary.get("entry_price", 0)
    current_price = summary.get("current_price", 0)
    entry_date_raw = summary.get("entry_date", "")
    leverage = summary.get("leverage", 10)
    total_dev_pct = summary.get("total_deviation_percent", 0)
    total_dev_usdt = summary.get("total_deviation_usdt", 0)

    stats = data.get("stats", {})
    dn = stats.get("dn", 0)
    dp = stats.get("dp", 0)
    da = stats.get("da", 0)

    ohlc = data.get("ohlc", {})
    max_pct = ohlc.get("max", {}).get("pct", 0)
    min_pct = ohlc.get("min", {}).get("pct", 0)
    max_price = ohlc.get("max", {}).get("price", 0)
    min_price = ohlc.get("min", {}).get("price", 0)

    dates = []
    for d in dates_raw:
        try:
            dates.append(dt.strptime(d, "%Y-%m-%d"))
        except ValueError:
            dates.append(dt.now())

    sign = "+" if total_dev_usdt >= 0 else ""

    fig, ax = plt.subplots(figsize=(9, 4.5))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#1a1a2e")

    for i in range(1, len(chart_points)):
        color = "#16a34a" if profitable[i] else "#dc2626"
        ax.plot(
            dates[i - 1 : i + 1],
            dev_pct[i - 1 : i + 1],
            color=color,
            linewidth=1.8,
            solid_capstyle="round",
        )

    for i in range(len(chart_points)):
        color = "#16a34a" if profitable[i] else "#dc2626"
        ax.scatter(dates[i], dev_pct[i], color=color, s=20, zorder=5)

    ax.axhline(y=0, color="#9333ea", linewidth=1.2, linestyle="--", alpha=0.8)
    ax.text(
        dates[0], 0, " Entry", color="#9333ea", fontsize=8,
        va="bottom", alpha=0.8,
    )

    ax.set_title(
        f"{symbol}  |  Entry: {entry_price} ({entry_date_raw})  →  {current_price}",
        color="#e0e0e0", fontsize=11, pad=12,
    )

    ax.set_xlabel("", color="#888")
    ax.set_ylabel("%", color="#888", fontsize=9)

    ax.tick_params(colors="#888", labelsize=8)
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")

    ax.grid(True, color="#333", linewidth=0.5, alpha=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#444")
    ax.spines["bottom"].set_color("#444")

    min_y = min(dev_pct) - abs(max(dev_pct) - min(dev_pct)) * 0.15 if dev_pct else -5
    max_y = max(dev_pct) + abs(max(dev_pct) - min(dev_pct)) * 0.15 if dev_pct else 5
    if min_y > -1:
        min_y = -1
    if max_y < 1:
        max_y = 1
    ax.set_ylim(min_y, max_y)

    info_text = (
        f"PnL: {sign}{total_dev_usdt} USDT ({sign}{total_dev_pct}%)  |  "
        f"{leverage}x  |  "
        f"Max: {max_price} (+{max_pct}%)  |  "
        f"Min: {min_price} ({min_pct}%)  |  "
        f"Dp:{dp}  Dn:{dn}  Da:{da}"
    )
    fig.text(
        0.02, -0.02, info_text, color="#777", fontsize=7.5,
        transform=ax.transAxes,
    )

    fig.tight_layout()
    t0 = time.time()
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="#1a1a2e")
    plt.close(fig)
    elapsed_ms = int((time.time() - t0) * 1000)
    return elapsed_ms


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate chart images per position")
    parser.add_argument("--uid", type=str, default=None, help="TG user ID")
    parser.add_argument("--dir", type=str, default=None, help="Output directory")
    parser.add_argument("--limit", type=int, default=0, help="Max charts (0 = all)")
    args = parser.parse_args()

    if args.dir:
        user_dir = args.dir
    elif args.uid:
        user_dir = os.path.join(TG_ALL_DIR, f"TG_{args.uid}")
    else:
        uid = os.environ.get("USER", "248207602")
        user_dir = os.path.join(TG_ALL_DIR, f"TG_{uid}")

    os.makedirs(user_dir, exist_ok=True)

    t0 = time.time()
    objects = fetch_objects()
    total = len(objects)
    if not objects:
        result = {"files": [], "total_ms": 0, "total": 0, "error": "No objects found"}
        print(json.dumps(result, ensure_ascii=False))
        return

    if args.limit > 0:
        objects = objects[: args.limit]

    results = []
    for i, obj in enumerate(objects):
        symbol = obj["symbol"]
        print(f"[{i + 1}/{total}] {symbol}...", file=sys.stderr)

        chart_data = fetch_chart_data(obj["id"])
        if not chart_data:
            print(f"  SKIP: no data for {symbol}", file=sys.stderr)
            continue

        safe_sym = re.sub(r'[^\w]', '_', symbol)
        output_path = os.path.join(user_dir, f"{safe_sym}_graph.png")

        ms = generate_chart(symbol, chart_data, output_path)
        if ms is None:
            print(f"  SKIP: render failed for {symbol}", file=sys.stderr)
            continue

        date_str = datetime.now().strftime("%d.%m.%y")
        results.append({
            "symbol": symbol,
            "path": output_path,
            "date": date_str,
            "ms": ms,
        })
        print(f"  OK ({ms}ms)", file=sys.stderr)

    total_ms = int((time.time() - t0) * 1000)
    result = {"files": results, "total_ms": total_ms, "total": len(results)}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
