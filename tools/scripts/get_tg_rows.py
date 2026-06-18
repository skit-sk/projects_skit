#!/usr/bin/env python3
"""Fetch positions JSON → format as Risk Summary → save to ALL_USERS."""

import os
import sys
import json
import urllib.request

sys.path.insert(0, os.path.expanduser("~/workspace/tools/scripts"))
from formatters.positions_risk import format_risk_summary

WORKSPACE = os.path.expanduser("~/workspace")
STATE_FILE = os.path.join(WORKSPACE, "projects", "07_tg_bot_aiforguest", "bot", "state.json")
ALL_USERS_DIR = os.path.join(WORKSPACE, "ALL_USERS")
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
    if not os.path.exists(STATE_FILE):
        return []
    with open(STATE_FILE, encoding="utf-8") as f:
        state = json.load(f)
    users = []
    for uid_key, user in state.get("users", {}).items():
        role = user.get("role")
        if role == "super" or role == "normal":
            links = user.get("platform_links", {})
            tg_ids = links.get("tg", [])
            if tg_ids:
                dir_path = os.path.join(ALL_USERS_DIR, uid_key, f"tg_{tg_ids[0]}")
                users.append((uid_key, tg_ids[0], dir_path))
    return users


def sync_exchange():
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


def _sfmt(v, dec):
    if abs(v) >= 10:
        dec = min(dec, 2)
    return f"{v:.{dec}f}"


def format_tg_rows(positions_data):
    positions = positions_data.get("positions", [])
    lines = []
    header = f"📊 Bitget Positions | {len(positions)} позиций\n"
    for p in positions:
        arrow = "↑" if p.get("profitable") else "↓"
        side = "🟢" if arrow == "↑" else "🔴"
        lines.append(
            f"{arrow} 🏗️{p.get('number', 0)} 🚏{p.get('ticker', '?')} "
            f"🧾{_sfmt(p.get('open_price_avg', 0), 4)} 📆{p.get('entry_date') or p.get('open_date', '')} "
            f"🕒{p.get('days_open', 0)}д 🧱{_sfmt(p.get('margin_size', 0), 4)} "
            f"🫧{_sfmt(p.get('pl_percent', 0), 2)}% 🪙{_sfmt(p.get('unrealized_pl', 0), 4)} "
            f"{side} ⬆️{p.get('leverage', 10):.0f}x"
        )
    return header + "\n".join(lines)


def main():
    sync_exchange()
    users = get_super_users()
    if not users:
        print("No users found in", STATE_FILE)
        sys.exit(1)

    data = get_positions_json()
    if "error" in data:
        msg = f"❌ API Error: {data['error']}"
        print(msg)
        for uid_key, tg_id, dir_path in users:
            os.makedirs(dir_path, exist_ok=True)
            out_path = os.path.join(dir_path, "positions_risk.txt")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(msg)
            out_path2 = os.path.join(dir_path, "positions_tg_rows.txt")
            with open(out_path2, "w", encoding="utf-8") as f:
                f.write(msg)
        sys.exit(1)

    positions = data.get("positions", [])
    totals = data.get("totals", {})
    balance = get_balance()

    text = format_risk_summary(positions, balance, totals=totals)
    tg_text = format_tg_rows(data)

    for uid_key, tg_id, dir_path in users:
        os.makedirs(dir_path, exist_ok=True)
        out_path = os.path.join(dir_path, "positions_risk.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"✅ Risk → {out_path}")
        out_path2 = os.path.join(dir_path, "positions_tg_rows.txt")
        with open(out_path2, "w", encoding="utf-8") as f:
            f.write(tg_text)
        print(f"✅ TG   → {out_path2}")


if __name__ == "__main__":
    main()
