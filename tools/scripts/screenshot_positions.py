#!/usr/bin/env python3
"""Screenshot the positions table (without TG rows) and save to TG user directory."""

import os
import sys
import time

TG_PROJECT = os.path.expanduser("~/workspace/projects/07_tg_bot_aiforguest")
TG_ALL_DIR = os.path.join(TG_PROJECT, "TG_ALL")
BASE_URL = "http://localhost:5000"

# Force Playwright to use our browsers
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.expanduser("~/workspace/tools/playwright/browsers")

# Ensure pango libs are available
pango_libs = os.path.expanduser("~/workspace/tools/playwright/lib")
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
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        page.goto(f"{BASE_URL}/account-api/", wait_until="networkidle")
        time.sleep(1)

        page.click("button:has-text('Positions')")
        page.wait_for_selector("table.account-table", timeout=5000)
        time.sleep(1)

        tg = page.query_selector(".tg-section")
        if tg:
            tg.evaluate("el => el.style.display = 'none'")

        time.sleep(0.3)

        table = page.query_selector("table.account-table")
        if not table:
            print("ERROR: Table not found on page")
            browser.close()
            sys.exit(1)

        for uid in users:
            user_dir = os.path.join(TG_ALL_DIR, f"TG_{uid}")
            os.makedirs(user_dir, exist_ok=True)
            out_path = os.path.join(user_dir, "positions_table.png")
            table.screenshot(path=out_path)
            print(f"✅ Screenshot saved → {out_path}")

        browser.close()


if __name__ == "__main__":
    main()
