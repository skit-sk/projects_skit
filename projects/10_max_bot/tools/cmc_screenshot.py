#!/usr/bin/env python3
"""CoinMarketCap screenshot via CloakBrowser (stealth Chromium).

Screenshots the top-100 crypto market cap table on coinmarketcap.com
in portrait mode (1080x1920). Auto-detects the table element to avoid
right-side cropping on narrow viewports.

Usage:
    python3 cmc_screenshot.py                    # auto-named in tmp/
    python3 cmc_screenshot.py /path/out.png      # explicit output

Output:
    <script_dir>/tmp/cmc_<YYYY-MM-DD_HH-MM-SS>.png
"""
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

import cloakbrowser

URL = "https://coinmarketcap.com"
SCRIPT_DIR = Path(__file__).resolve().parent
OUT_DIR = SCRIPT_DIR / "tmp"
OUT_DIR.mkdir(exist_ok=True)

VIEWPORT_W = 1080
VIEWPORT_H = 1920
WAIT_MS = 4000

TABLE_SELECTORS = [
    'div[data-test="table-container"]',
    'div[class*="tableWrap"]',
    'table.cmc-table',
    'div.cmc-tab-content table',
    'section table',
    'table',
]


def _hide_banners_js() -> str:
    return """() => {
        const sels = [
            '[class*="cookie"]', '[class*="Cookie"]',
            '[id*="cookie"]',    '[id*="onetrust"]',
            '[class*="consent"]','[class*="banner"]',
            '[data-test="cookie-banner"]',
        ];
        for (const sel of sels) {
            document.querySelectorAll(sel).forEach(el => el.remove());
        }
    }"""


async def main() -> int:
    if len(sys.argv) > 1:
        out_path = Path(sys.argv[1])
    else:
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        out_path = OUT_DIR / f"cmc_{ts}.png"

    print(f"[{datetime.now().isoformat()}] Launching cloakbrowser…", flush=True)
    try:
        browser = await cloakbrowser.launch_async(headless=True)
    except Exception as e:
        print(f"LAUNCH_ERROR: {type(e).__name__}: {e}", flush=True)
        return 2

    try:
        page = await browser.new_page(
            viewport={"width": VIEWPORT_W, "height": VIEWPORT_H},
            device_scale_factor=1,
        )
        print(f"[{datetime.now().isoformat()}] Goto {URL}…", flush=True)
        await page.goto(URL, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(WAIT_MS)

        try:
            await page.evaluate(_hide_banners_js())
        except Exception:
            pass

        print(f"[{datetime.now().isoformat()}] Looking for table…", flush=True)
        target = None
        for sel in TABLE_SELECTORS:
            try:
                el = await page.query_selector(sel)
                if not el:
                    continue
                box = await el.bounding_box()
                if box and box["width"] > 800 and box["height"] > 400:
                    target = el
                    print(
                        f"  Selected: {sel} "
                        f"({int(box['width'])}x{int(box['height'])})",
                        flush=True,
                    )
                    break
            except Exception:
                continue

        if target is not None:
            await target.screenshot(path=str(out_path), timeout=60000)
        else:
            print("  No table found, full_page=True fallback", flush=True)
            await page.screenshot(
                path=str(out_path), full_page=True, timeout=60000
            )

        size = out_path.stat().st_size if out_path.exists() else 0
        print(f"OK: {out_path} ({size} bytes)", flush=True)
        return 0 if size > 0 else 3
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR: {type(e).__name__}: {e}", flush=True)
        return 4
    finally:
        try:
            await browser.close()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
