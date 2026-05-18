#!/usr/bin/env python3
"""Fetch positions from account-api and save as TG row text to TG user directory."""

import os
import sys
import re
import json
import urllib.request
import urllib.parse

TG_PROJECT = os.path.expanduser("~/workspace/projects/07_tg_bot_aiforguest")
TG_ALL_DIR = os.path.join(TG_PROJECT, "TG_ALL")
BASE_URL = "http://localhost:5000"

def get_positions_html():
    url = f"{BASE_URL}/account-api/partial/positions"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8")

def extract_tg_rows(html):
    rows = re.findall(r'<div class="tg-row[^>]*">(.*?)</div>', html, re.DOTALL)
    lines = []
    for row in rows:
        arrow_m = re.search(r'<span class="tg-arrow">(.*?)</span>', row)
        arrow = arrow_m.group(1) if arrow_m else ""
        data_spans = re.findall(r'<span class="tf">(.*?)</span>', row)
        data_str = "".join(data_spans)
        lines.append(f"{arrow} {data_str}")
    return lines

def get_super_users():
    """Find all TG user IDs from TG_ALL directory."""
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

    html = get_positions_html()
    lines = extract_tg_rows(html)
    text = "\n".join(lines)

    for uid in users:
        user_dir = os.path.join(TG_ALL_DIR, f"TG_{uid}")
        os.makedirs(user_dir, exist_ok=True)
        out_path = os.path.join(user_dir, "positions_tg_rows.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"✅ Saved ({len(lines)} rows) → {out_path}")

if __name__ == "__main__":
    main()
