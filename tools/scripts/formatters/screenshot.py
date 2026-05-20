"""Rich Table → HTML с ANSI → Playwright → PNG для Telegram."""

import os
import sys

# Playwright browsers path
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.expanduser("~/workspace/tools/playwright/browsers")
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

    # Экспорт HTML с ANSI-стилями
    html = console.export_html(code_format="<pre style='font-family: \"Courier New\", monospace; font-size:14px; line-height:1.5; background:#1e1e1e; color:#d4d4d4; padding:16px; border-radius:8px; overflow:auto;'>{code}</pre>")

    # Добавить заголовок если есть
    if title:
        html = html.replace(
            "<body>",
            f"<body><div style='font-family:monospace;font-size:16px;color:#d4d4d4;background:#1e1e1e;padding:16px 16px 0 16px;font-weight:bold;'>{title}</div>"
        )

    # Полный HTML документ
    full_html = f"""<!DOCTYPE html>
<html><head>
<meta charset='utf-8'>
<style>
  body {{ margin: 0; padding: 20px; background: #1e1e1e; }}
  pre {{ margin: 0; }}
</style>
</head><body>
{html}
</body></html>"""

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1200, "height": 400})
            page.set_content(full_html)
            # Ждём рендеринга
            page.wait_for_timeout(500)
            page.screenshot(path=output_path, full_page=True)
            browser.close()
        return output_path if os.path.exists(output_path) else None
    except Exception as e:
        print(f"Screenshot error: {e}")
        return None
