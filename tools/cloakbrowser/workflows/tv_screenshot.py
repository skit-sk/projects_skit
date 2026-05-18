#!/usr/bin/env python3
"""TradingView screenshot via CloakBrowser (stealth Chromium, undetectable).

Usage:
    python3 tv_screenshot.py BITGET:DOTUSDT 1D /tmp/tv.png [range]
    python3 tv_screenshot.py BITGET:DOTUSDT 1d /tmp/tv.png 6M
"""
import os
import sys
import time

from cloakbrowser import launch

TF_MAP = {
    "1m": "1", "5m": "5", "15m": "15", "30m": "30",
    "1h": "60", "2h": "120", "4h": "240",
    "1d": "1D", "1w": "1W",
}

symbol = sys.argv[1] if len(sys.argv) > 1 else "BITGET:DOTUSDT"
tf_raw = sys.argv[2] if len(sys.argv) > 2 else "1d"
out = sys.argv[3] if len(sys.argv) > 3 else "/tmp/tv_cloak.png"
range_val = sys.argv[4] if len(sys.argv) > 4 else ""

tf = TF_MAP.get(tf_raw.lower(), tf_raw)
url = f"https://www.tradingview.com/chart/?symbol={symbol}&theme=dark&interval={tf}"
if range_val:
    url += f"&range={range_val.upper()}"

os.environ.setdefault("CLOAKBROWSER_CACHE_DIR", "/tmp/cloakbrowser")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/cache")
os.environ["LD_LIBRARY_PATH"] = "/tmp/pango_libs/usr/lib/x86_64-linux-gnu"

browser = None
try:
    browser = launch(headless=True)
    page = browser.new_page()
    page.set_viewport_size({"width": 1920, "height": 1080})
    print(f"Navigating to {symbol} {tf} (stealth)...")
    page.goto(url, wait_until="networkidle", timeout=60000)
    time.sleep(4)

    try:
        page.get_by_role("button", name="Accept all").click(timeout=5000)
        print("Cookies accepted")
        time.sleep(1)
    except Exception:
        pass

    try:
        page.locator('[aria-label*="Watchlist"]').click(timeout=5000)
        print("Watchlist collapsed")
        time.sleep(1)
    except Exception:
        pass

    page.screenshot(path=out, full_page=False)
    sz = os.path.getsize(out)
    print(f"Screenshot: {out} ({sz} bytes)")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
finally:
    if browser:
        try:
            browser.close()
        except Exception:
            pass
