#!/usr/bin/env python3
"""Fetch positions JSON → format as emoji rows → save to ALL_USERS.

Usage:
  python3 get_emj_rows.py                        # write to all TG users
  python3 get_emj_rows.py --output-dir <path>    # write to single dir
"""

import os
import sys
import json
import argparse
import urllib.request

sys.path.insert(0, os.path.expanduser("~/workspace/tools/scripts"))
from formatters.positions_risk import format_risk_summary

WORKSPACE = os.path.expanduser("~/workspace")
STATE_FILE = os.path.join(WORKSPACE, "projects", "07_tg_bot_aiforguest", "bot", "state.json")
ALL_USERS_DIR = os.path.join(WORKSPACE, "ALL_USERS")
BASE_URL = "http://localhost:5000"
OUTPUT_FILE = "positions_emj_rows.txt"


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


def format_emj_rows(positions_data):
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


def write_file(path, text, label):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"✅ {label} → {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", help="Write output to a single directory")
    args = parser.parse_args()

    sync_exchange()

    data = get_positions_json()
    text = None
    emj_text = None
    if "error" in data:
        msg = f"❌ API Error: {data['error']}"
        text = msg
        emj_text = msg
    else:
        positions = data.get("positions", [])
        totals = data.get("totals", {})
        balance = get_balance()
        text = format_risk_summary(positions, balance, totals=totals)
        emj_text = format_emj_rows(data)

    if args.output_dir:
        write_file(os.path.join(args.output_dir, "positions_risk.txt"), text, "Risk")
        write_file(os.path.join(args.output_dir, OUTPUT_FILE), emj_text, "EMJ")
        return

    users = get_super_users()
    if not users:
        print("No users found in", STATE_FILE)
        sys.exit(1)

    for uid_key, tg_id, dir_path in users:
        write_file(os.path.join(dir_path, "positions_risk.txt"), text, "Risk")
        write_file(os.path.join(dir_path, OUTPUT_FILE), emj_text, "EMJ")


if __name__ == "__main__":
    main()
