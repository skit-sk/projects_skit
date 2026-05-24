#!/usr/bin/env python3
"""Fetch positions JSON → format as Risk Summary → save to TG user dir."""

import os
import sys
import json
import urllib.request

sys.path.insert(0, os.path.expanduser("~/workspace/tools/scripts"))
from formatters.positions_risk import format_risk_summary

TG_PROJECT = os.path.expanduser("~/workspace/projects/07_tg_bot_aiforguest")
TG_ALL_DIR = os.path.join(TG_PROJECT, "TG_ALL")
BASE_URL = "http://localhost:5000"


def get_positions_json():
    url = f"{BASE_URL}/account-api/api/computed"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return json.loads(body)
        except Exception:
            return {"error": f"HTTP {e.code}: {e.reason}"}
    except urllib.error.URLError as e:
        return {"error": f"Connection error: {e.reason}"}


def get_balance():
    try:
        resp = urllib.request.urlopen(f"{BASE_URL}/account-api/api/balance", timeout=5)
        bal_data = json.loads(resp.read())
        if "futures" in bal_data:
            for item in bal_data["futures"]:
                if item.get("margin_coin") == "USDT":
                    return float(item.get("available", 0))
        if "spot" in bal_data:
            for item in bal_data["spot"]:
                if item.get("coin") == "USDT":
                    return float(item.get("available", 0))
    except Exception:
        pass
    return 0.0


def get_super_users():
    if not os.path.isdir(TG_ALL_DIR):
        return []
    users = []
    for name in os.listdir(TG_ALL_DIR):
        if name.startswith("TG_"):
            uid = name.replace("TG_", "")
            users.append(uid)
    return users


def sync_exchange():
    """POST /api/sync-all для обновления данных с биржи."""
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/api/sync-all",
            data=b"",
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}


def format_tg_rows(positions_data):
    """API-ответ → эмодзи-строки для Telegram."""
    positions = positions_data.get("positions", [])
    lines = []
    header = f"📊 Bitget Positions | {len(positions)} позиций\n"
    for p in positions:
        arrow = "↑" if p.get("profitable") else "↓"
        side = "🟢" if arrow == "↑" else "🔴"
        lines.append(
            f"{arrow} 🏗️{p.get('number', 0)} 🚏{p.get('ticker', '?')} "
            f"🧾{p.get('open_price_avg', 0):.4f} 📆{p.get('open_date', '')} "
            f"🕒{p.get('days_open', 0)}д 🧱{p.get('margin_size', 0):.4f} "
            f"🫧{p.get('pl_percent', 0):+.2f} 🪙{p.get('unrealized_pl', 0):+.4f} "
            f"{side} ⬆️{p.get('leverage', 10):.0f}x"
        )
    return header + "\n".join(lines)


def main():
    sync_exchange()
    users = get_super_users()
    if not users:
        print("No TG users found in", TG_ALL_DIR)
        sys.exit(1)

    data = get_positions_json()
    if "error" in data:
        msg = f"❌ API Error: {data['error']}"
        print(msg)
        for uid in users:
            user_dir = os.path.join(TG_ALL_DIR, f"TG_{uid}")
            os.makedirs(user_dir, exist_ok=True)
            out_path = os.path.join(user_dir, "positions_risk.txt")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(msg)
            out_path2 = os.path.join(user_dir, "positions_tg_rows.txt")
            with open(out_path2, "w", encoding="utf-8") as f:
                f.write(msg)
        sys.exit(1)

    positions = data.get("positions", [])
    totals = data.get("totals", {})
    balance = get_balance()

    text = format_risk_summary(positions, balance, totals=totals)
    tg_text = format_tg_rows(data)

    for uid in users:
        user_dir = os.path.join(TG_ALL_DIR, f"TG_{uid}")
        os.makedirs(user_dir, exist_ok=True)
        out_path = os.path.join(user_dir, "positions_risk.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"✅ Risk → {out_path}")
        out_path2 = os.path.join(user_dir, "positions_tg_rows.txt")
        with open(out_path2, "w", encoding="utf-8") as f:
            f.write(tg_text)
        print(f"✅ TG   → {out_path2}")


if __name__ == "__main__":
    main()
