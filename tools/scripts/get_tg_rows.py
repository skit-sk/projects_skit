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
    url = f"{BASE_URL}/account-api/api/positions"
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


def main():
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
        sys.exit(1)

    positions = data.get("positions", [])
    fill_counts = data.get("fill_counts", {})
    order_counts = data.get("order_counts", {})
    balance = get_balance()

    text = format_risk_summary(positions, balance, fill_counts, order_counts)

    for uid in users:
        user_dir = os.path.join(TG_ALL_DIR, f"TG_{uid}")
        os.makedirs(user_dir, exist_ok=True)
        out_path = os.path.join(user_dir, "positions_risk.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"✅ Saved → {out_path}")


if __name__ == "__main__":
    main()
