import os
import re
import asyncio
import logging

TF_MAP = {
    "1m": "1", "3m": "3", "5m": "5", "15m": "15", "30m": "30",
    "1h": "60", "2h": "120", "3h": "180", "4h": "240",
    "1d": "1D", "2d": "2D", "3d": "3D",
    "1w": "1W",
}

TF_LABEL = {
    "1": "1m", "3": "3m", "5": "5m", "15": "15m", "30": "30m",
    "60": "1h", "120": "2h", "180": "3h", "240": "4h",
    "1D": "1d", "2D": "2d", "3D": "3d",
    "1W": "1w",
}

PATTERN = re.compile(r"sc\s+([A-Z]+(?::[A-Z]+)?)(?:\s+(\w+))?(?:\s+(\w+))?", re.IGNORECASE)

VALID_RANGES = {"1m", "3m", "5d", "1w", "6m", "12m", "1y", "2y", "5y", "10y", "all", "ytd"}

RANGE_MAP = {
    "1m": "1M", "3m": "3M", "5d": "5D", "1w": "7D",
    "6m": "6M", "12m": "12M",
    "1y": "12M", "2y": "24M", "5y": "60M", "10y": "120M",
    "all": "all", "ytd": "YTD",
}

log = logging.getLogger("tg_bot")


def parse_request(text):
    m = PATTERN.search(text)
    if not m:
        return None, None, None, ""
    raw = m.group(1).upper()
    if ":" not in raw:
        raw = f"BITGET:{raw}"
    w1 = (m.group(2) or "").lower()
    w2 = (m.group(3) or "").lower()

    tf_raw = w1 if w1 else "1d"
    if w1 and w1 not in TF_MAP:
        valid_tf = ", ".join(TF_MAP.keys())
        valid_rng = ", ".join(sorted(VALID_RANGES))
        return raw, None, None, (
            f"❌ Неизвестный таймфрейм: '{w1}'.\n"
            f"Таймфреймы: {valid_tf}\n"
            f"Диапазоны: {valid_rng}"
        )
    tf = TF_MAP[tf_raw]

    range_val = w2 if w2 else "1y"

    return raw, tf, range_val, ""


async def _capture(browser, url, output_path):
    page = await browser.new_page()
    await page.set_viewport_size({"width": 1920, "height": 1080})
    await page.goto(url, wait_until="networkidle", timeout=60000)
    await asyncio.sleep(5)

    body = await page.inner_text("body")
    if "something went wrong" in body.lower():
        await page.screenshot(path=output_path)
        await page.close()
        return "error_widget"

    await page.screenshot(path=output_path, full_page=False)
    await page.close()
    return "ok"


async def take_screenshot(symbol, timeframe, output_dir, range_val=""):
    safe_symbol = symbol.lower().replace(":", "_")
    output_path = os.path.join(output_dir, f"tv_{safe_symbol}_{timeframe}.png")

    url = (
        f"https://s.tradingview.com/widgetembed/"
        f"?symbol={symbol}"
        f"&interval={timeframe}"
        f"&timezone=Europe%2FMoscow"
        f"&theme=dark"
        f"&style=1"
        f"&hideideas=1"
        f"&hide_top_toolbar=1"
        f"&hide_side_toolbar=1"
        f"&allow_symbol_change=0"
    )
    if range_val:
        url += f"&range={RANGE_MAP.get(range_val, range_val)}"

    log.info(f"Screenshot (cloak): {symbol} {timeframe} range={range_val or 'default'}")

    os.environ.setdefault("CLOAKBROWSER_CACHE_DIR", "/tmp/cloakbrowser")
    os.environ.setdefault("XDG_CACHE_HOME", "/tmp/cache")
    ld_path = os.environ.get("LD_LIBRARY_PATH", "")
    pango = "/tmp/pango_libs/usr/lib/x86_64-linux-gnu"
    if os.path.isdir(pango) and pango not in ld_path:
        os.environ["LD_LIBRARY_PATH"] = f"{pango}:{ld_path}"

    from cloakbrowser import launch_async

    for attempt in range(2):
        browser = None
        try:
            browser = await launch_async(headless=True)
            status = await _capture(browser, url, output_path)
            await browser.close()
            browser = None
            if status == "ok":
                break
            log.warning(f"Screenshot widget error (attempt {attempt+1}), retrying...")
            await asyncio.sleep(2)
        except Exception as e:
            log.error(f"CloakBrowser error (attempt {attempt+1}): {e}")
            if browser:
                try:
                    await browser.close()
                except Exception:
                    pass
            if attempt == 1:
                return None, str(e)[:200]
            await asyncio.sleep(2)
    else:
        return None, "TradingView widget: Something went wrong"

    if not os.path.exists(output_path):
        return None, "Screenshot not created"

    sz = os.path.getsize(output_path)
    log.info(f"Screenshot saved: {output_path} ({sz} bytes)")
    if sz < 5000:
        return None, f"Screenshot too small ({sz} bytes)"
    return output_path, None
