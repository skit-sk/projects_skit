#!/usr/bin/env python3
"""Screenshot a specific card page by symbol, save to ALL_USERS."""

import os
import sys
import time
import json
import argparse
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument("--symbol", type=str, required=True, help="Symbol like ETH, CAKE")
parser.add_argument("--output-dir", type=str, required=True, help="Output directory")
args = parser.parse_args()

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

_font_conf = "/tmp/fonts/fonts.conf"
if os.path.isfile(_font_conf):
    os.environ["FONTCONFIG_FILE"] = _font_conf


def get_card_id(symbol):
    url = f"{BASE_URL}/trade-analytics/api/list"
    resp = urllib.request.urlopen(url, timeout=10)
    data = json.loads(resp.read())
    sym_upper = symbol.upper()
    for item in data:
        if item.get("symbol", "").upper() == sym_upper:
            return item.get("id")
    return None


def main():
    card_id = get_card_id(args.symbol)
    if not card_id:
        print(f"ERROR: symbol '{args.symbol}' not found")
        sys.exit(1)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        _chrome_path = os.environ.get("CLOAKBROWSER_BINARY_PATH") or "/tmp/cloakbrowser/chromium-146.0.7680.177.3/chrome"
        if os.path.isfile(_chrome_path):
            browser = p.chromium.launch(headless=True, executable_path=_chrome_path, args=["--no-sandbox"])
        else:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        page = browser.new_page(viewport={"width": 2560, "height": 1440})

        url = f"{BASE_URL}/card/{card_id}"
        page.goto(url, wait_until="networkidle")
        time.sleep(3)


        # Replace emoji with visible styled tags
        try:
            _emoji_js = open("/tmp/emoji_replace.js").read()
            page.evaluate(_emoji_js)
        except Exception:
            pass
        safe = args.symbol.lower()
        os.makedirs(args.output_dir, exist_ok=True)
        out_path = os.path.join(args.output_dir, f"{safe}_graph.png")

        card = page.query_selector(".card")
        if card:
            card.screenshot(path=out_path)
        else:
            page.screenshot(path=out_path, full_page=True)

        print(f"✅ {args.symbol} graph → {out_path}")
        browser.close()


if __name__ == "__main__":
    main()
