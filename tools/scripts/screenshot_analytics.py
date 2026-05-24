#!/usr/bin/env python3
"""Screenshot analytics charts (main chart + indicators) for TG bot."""

import os
import sys
import time
import json
import urllib.request

TG_PROJECT = os.path.expanduser("~/workspace/projects/07_tg_bot_aiforguest")
TG_ALL_DIR = os.path.join(TG_PROJECT, "TG_ALL")
BASE_URL = "http://localhost:5000"

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.expanduser("~/workspace/tools/playwright/browsers")
_old_pw = os.path.expanduser("~/workspace/tools/browser-temp/browsers")
if not os.path.isdir(os.path.expanduser("~/workspace/tools/playwright/browsers")) and os.path.isdir(_old_pw):
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = _old_pw

pango_libs = os.path.expanduser("~/workspace/tools/playwright/lib")
if not os.path.isdir(pango_libs):
    pango_libs = os.path.expanduser("~/workspace/tools/browser-temp/pango_libs/usr/lib/x86_64-linux-gnu")
if os.path.isdir(pango_libs):
    ld_path = os.environ.get("LD_LIBRARY_PATH", "")
    if pango_libs not in ld_path:
        os.environ["LD_LIBRARY_PATH"] = f"{pango_libs}:{ld_path}" if ld_path else pango_libs


def get_super_users():
    if not os.path.isdir(TG_ALL_DIR):
        return []
    users = []
    for name in os.listdir(TG_ALL_DIR):
        if name.startswith("TG_"):
            uid = name.replace("TG_", "")
            users.append(uid)
    return users


def get_objects_list():
    try:
        resp = urllib.request.urlopen(f"{BASE_URL}/trade-analytics/api/list", timeout=10)
        return json.loads(resp.read())
    except Exception as e:
        print(f"ERROR: cannot fetch object list: {e}")
        sys.exit(1)


def resolve_symbol(symbol_or_number: str, objects: list) -> dict:
    """Match 'ETC', 'etc', '#11', '11' → object dict or None."""
    s = symbol_or_number.upper().lstrip("#")
    for obj in objects:
        if not obj.get("has_1d") or not obj.get("has_raw"):
            continue
        name = obj.get("name", "")
        sym = obj.get("symbol", "").upper()
        num = name.split("#")[-1] if "#" in name else ""
        if s == sym or s == num or f"#{s}" == f"#{num}":
            return obj
    return None


def main():
    import argparse
    from playwright.sync_api import sync_playwright

    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", type=str, default=None, help="Symbol ticker or number (e.g. ETC, 11)")
    parser.add_argument("--all", action="store_true", help="Process all symbols")
    args = parser.parse_args()

    objects = get_objects_list()
    if args.symbol:
        obj = resolve_symbol(args.symbol, objects)
        if not obj:
            print(f"ERROR: symbol '{args.symbol}' not found or has no analytics data")
            sys.exit(1)
        targets = [obj]
    elif args.all:
        targets = [o for o in objects if o.get("has_1d") and o.get("has_raw")]
        if not targets:
            print("ERROR: no objects with analytics data")
            sys.exit(1)
    else:
        targets = [o for o in objects if o.get("has_1d") and o.get("has_raw")]
        if not targets:
            print("ERROR: no objects with analytics data")
            sys.exit(1)

    users = get_super_users()
    if not users:
        print("No TG users found in", TG_ALL_DIR)
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        for obj in targets:
            sym = obj["symbol"]
            obj_id = obj["id"]
            url = f"{BASE_URL}/trade-analytics/dashboard/{obj_id}"
            page.goto(url, wait_until="networkidle")
            time.sleep(4)

            for uid in users:
                user_dir = os.path.join(TG_ALL_DIR, f"TG_{uid}")
                os.makedirs(user_dir, exist_ok=True)

                # Screenshot main chart section
                main_el = page.query_selector(".ta-section.block-chart")
                if main_el:
                    main_path = os.path.join(user_dir, f"{sym}_main_chart.png")
                    main_el.screenshot(path=main_path)
                    print(f"✅ Main chart → {main_path}")
                else:
                    print(f"WARN: .block-chart not found for {sym}")

                # Screenshot indicators section
                indic_el = page.query_selector(".ta-section.block-indic")
                if indic_el:
                    indic_path = os.path.join(user_dir, f"{sym}_indicators.png")
                    indic_el.screenshot(path=indic_path)
                    print(f"✅ Indicators → {indic_path}")
                else:
                    print(f"WARN: .block-indic not found for {sym}")

        browser.close()


if __name__ == "__main__":
    main()
