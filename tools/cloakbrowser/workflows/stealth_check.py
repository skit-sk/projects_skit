#!/usr/bin/env python3
"""Check CloakBrowser stealth against live detection services.

Tests: deviceandbrowserinfo.com, browserscan.net, fingerprint.com
"""
import os
import sys

BTEMP = "/home/user_aioc/workspace/tools/browser-temp"
os.environ.setdefault("CLOAKBROWSER_CACHE_DIR", f"{BTEMP}/cache/cloakbrowser")
os.environ.setdefault("XDG_CACHE_HOME", f"{BTEMP}/cache")
os.environ["LD_LIBRARY_PATH"] = f"{BTEMP}/pango_libs/usr/lib/x86_64-linux-gnu"

from cloakbrowser import launch

SITES = [
    ("deviceandbrowserinfo.com", "https://deviceandbrowserinfo.com"),
    ("browserscan.net", "https://browserscan.net"),
    ("fingerprint.com (demo)", "https://demo.fingerprint.com"),
]

browser = None
try:
    browser = launch(headless=False, humanize=True)
    page = browser.new_page()
    page.set_viewport_size({"width": 1920, "height": 1080})

    for name, url in SITES:
        print(f"\n--- {name} ---")
        page.goto(url, wait_until="networkidle", timeout=30000)
        print(f"  Page loaded: {page.title()}")
        page.screenshot(path=f"{BTEMP}/screenshots/stealth_{name.replace(' ', '_')}.png")
        print(f"  Screenshot saved")

    print(f"\nALL CHECKS DONE — review screenshots in {BTEMP}/screenshots/stealth_*.png")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
finally:
    if browser:
        try:
            browser.close()
        except Exception:
            pass
