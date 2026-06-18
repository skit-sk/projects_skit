#!/usr/bin/env python3
"""Screenshot the positions table (without TG rows) and save to ALL_USERS."""

import os
import sys
import time
import argparse
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument("--output-dir", help="Single output directory")
args, _ = parser.parse_known_args()

WORKSPACE = os.path.expanduser("~/workspace")
TG_PROJECT = os.path.join(WORKSPACE, "projects", "07_tg_bot_aiforguest")
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


def main():
    from playwright.sync_api import sync_playwright

    users = get_super_users()
    if not users:
        print("No TG users found in", TG_ALL_DIR)
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        page = browser.new_page(viewport={"width": 2560, "height": 1440})

        page.goto(f"{BASE_URL}/account-api/", wait_until="networkidle")
        time.sleep(1)
        page.evaluate("localStorage.setItem('theme', 'dark')")

        page.click("button:has-text('📍 Positions')")
        page.wait_for_selector("table.account-table", timeout=5000)
        page.wait_for_selector("table.account-table tbody tr", timeout=10000)
        time.sleep(2)

        page.evaluate("""
            const tg = document.querySelector('.tg-section-details') || document.querySelector('.tg-section');
            if (tg) tg.style.display = 'none';
        """)
        time.sleep(0.5)

        table = page.query_selector("table.account-table")
        if not table:
            print("ERROR: Table not found on page")
            browser.close()
            sys.exit(1)

        box = table.bounding_box()
        if not box:
            print("ERROR: Table has no bounding box")
            browser.close()
            sys.exit(1)

        page.screenshot(path="/tmp/positions_full.png", full_page=True)
        padding = 15
        crop = (
            max(0, int(box["x"]) - padding),
            max(0, int(box["y"]) - padding),
            min(int(box["x"] + box["width"] + padding), 2560),
            min(int(box["y"] + box["height"] + padding + 30), 9000),
        )
        img = Image.open("/tmp/positions_full.png")
        cropped = img.crop(crop)

        if args.output_dir:
            dirs = [args.output_dir]
        else:
            dirs = [os.path.join(TG_ALL_DIR, f"TG_{uid}") for uid in users]

        for d in dirs:
            os.makedirs(d, exist_ok=True)
            out_path = os.path.join(d, "positions_table.png")
            cropped.save(out_path, dpi=(144, 144))
            print(f"✅ Screenshot saved → {out_path}")

        browser.close()


if __name__ == "__main__":
    main()
