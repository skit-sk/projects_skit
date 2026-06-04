"""Rich Table → HTML с ANSI → Playwright → PNG для Telegram."""

import os
import sys
import re

# Playwright browsers path — try browser-temp first, then playwright dir
BTEMP = os.path.expanduser("~/workspace/tools/browser-temp")
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = f"{BTEMP}/browsers"
_old_pw = os.path.expanduser("~/workspace/tools/playwright/browsers")
# Fallback: если BTEMP пустой, используем tools/playwright/browsers
if not (os.path.isdir(f"{BTEMP}/browsers") and os.listdir(f"{BTEMP}/browsers")) and os.path.isdir(_old_pw):
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = _old_pw

pango = f"{BTEMP}/pango_libs/usr/lib/x86_64-linux-gnu"
if not os.path.isdir(pango):
    pango = os.path.expanduser("~/workspace/tools/playwright/lib")
if os.path.isdir(pango) and pango not in os.environ.get("LD_LIBRARY_PATH", ""):
    lp = os.environ.get("LD_LIBRARY_PATH", "")
    os.environ["LD_LIBRARY_PATH"] = f"{pango}:{lp}" if lp else pango


def render_rich_to_png(console, output_path: str, title: str = "") -> str:
    """Rich Console (record=True) → export HTML → Playwright screenshot → PNG.
    
    Args:
        console: Rich Console с record=True, уже содержащий таблицу
        output_path: путь для сохранения PNG
        title: заголовок (опционально)
    
    Returns:
        output_path при успехе, None при ошибке
    """
    from playwright.sync_api import sync_playwright

    full_html = _build_html(console, title)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1200, "height": 400})
            page.set_content(full_html)
            page.wait_for_timeout(500)
            _box = page.evaluate("() => ({w: document.body.scrollWidth, h: document.body.scrollHeight})")
            page.set_viewport_size({"width": _box["w"], "height": _box["h"]})
            page.screenshot(path=output_path, full_page=True)
            browser.close()
        return output_path if os.path.exists(output_path) else None
    except Exception as e:
        print(f"Screenshot error: {e}")
        return None


def _build_html(console, title: str = "") -> str:
    """Общая HTML-сборка для sync и async render."""
    _full = console.export_html()
    _style = re.search(r'<style>(.*?)</style>', _full, re.DOTALL)
    _raw_css = _style.group(1) if _style else ""
    # strip body CSS from Rich export (it overrides our dark theme)
    _raw_css = re.sub(r'\nbody\s*\{[^}]*\}', '', _raw_css)
    _body = re.search(r'<body[^>]*>(.*?)</body>', _full, re.DOTALL)
    _body_html = _body.group(1) if _body else ""
    # replace pre's inline style with our own
    _body_html = re.sub(
        r'<pre[^>]*>',
        r'<pre style="font-family: \'Courier New\', monospace; font-size:14px; line-height:1.5; background:#1e1e1e; color:#d4d4d4; border-radius:8px; overflow:auto; margin:0;">',
        _body_html,
    )
    if title:
        _body_html = (
            f"<div style='font-family:monospace;font-size:16px;color:#d4d4d4;background:#1e1e1e;padding:16px 16px 0 16px;font-weight:bold;'>{title}</div>"
            + _body_html
        )
    return f"""<!DOCTYPE html>
<html><head>
<meta charset='utf-8'>
<style>
  body {{ margin: 0; padding: 0; background: #1e1e1e; display: inline-block; }}
  pre {{ margin: 0; padding: 12px; background: #1e1e1e; }}
  code {{ font-family: inherit; }}
{_raw_css}
</style>
</head><body>
{_body_html}
</body></html>"""


async def async_render_rich_to_png(console, output_path: str, title: str = "") -> str:
    """Async версия: Rich Console → HTML → Playwright Async → PNG.
    
    Используется из asyncio handlers (например, _handle_positions_image),
    чтобы не падать с "Playwright Sync API inside the asyncio loop".
    """
    from playwright.async_api import async_playwright

    full_html = _build_html(console, title)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            try:
                page = await browser.new_page(viewport={"width": 1200, "height": 400})
                await page.set_content(full_html, wait_until="load")
                await page.wait_for_timeout(500)
                _box = await page.evaluate("() => ({w: document.body.scrollWidth, h: document.body.scrollHeight})")
                await page.set_viewport_size({"width": _box["w"], "height": _box["h"]})
                await page.screenshot(path=output_path, full_page=True)
            finally:
                await browser.close()
        return output_path if os.path.exists(output_path) else None
    except Exception as e:
        print(f"Screenshot error: {e}")
        return None
