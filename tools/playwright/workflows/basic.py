#!/usr/bin/env python3
"""Minimal Playwright example: open → screenshot → close."""
import os
import sys

from playwright.sync_api import sync_playwright

url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
out = sys.argv[2] if len(sys.argv) > 2 else "/home/user_aioc/workspace/tools/browser-temp/screenshots/pw_basic.png"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.set_viewport_size({"width": 1920, "height": 1080})
    page.goto(url, wait_until="networkidle", timeout=30000)
    print(f"Title: {page.title()}")
    page.screenshot(path=out, full_page=False)
    sz = os.path.getsize(out)
    print(f"Screenshot: {out} ({sz} bytes)")
    browser.close()
