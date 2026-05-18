# CloakBrowser — Stealth Chromium Automation

[CloakBrowser](https://github.com/CloakHQ/CloakBrowser) — кастомный Chromium v146 с 57 C++ патчами на уровне исходного кода. Не детектится антибот-системами.

## Установка

```bash
./tools/cloakbrowser/install.sh
```

Скачивает кастомный Chromium (~444MB) в `$CLOAKBROWSER_CACHE_DIR`.

## Использование

```bash
# Базовый тест
./tools/cloakbrowser/bin/test.sh

# Скриншот TradingView
./tools/cloakbrowser/bin/cloakbrowser.sh \
    tools/cloakbrowser/workflows/tv_screenshot.py BITGET:DOTUSDT 1D /tmp/tv.png 6M
```

## Когда использовать

- Скриншоты TradingView / бирж / банков (антибот-защита)
- Обход Cloudflare Turnstile, reCAPTCHA v3 (score 0.9)
- Парсинг сайтов с FingerprintJS, BrowserScan
- Любые сценарии где важна незаметность

## Отличия от Playwright

| | CloakBrowser | Playwright |
|---|---|---|
| Chromium | Кастомный, 57 C++ патчей | Stock Chrome for Testing |
| reCAPTCHA v3 | 0.9 (человек) | 0.1 (бот) |
| Cloudflare Turnstile | PASS | FAIL |
| Фингерпринт | GPU/WebGL/canvas/audio — всё спуфится | Реальный |
| Размер бинарника | ~444MB | ~200MB |
| Старт | ~2-4s (Python init) | ~1s |

## Интеграция в проекты

```python
# В любом Python-скрипте
import os
os.environ["CLOAKBROWSER_CACHE_DIR"] = "/tmp/cloakbrowser"
from cloakbrowser import launch

browser = launch(headless=True)
page = browser.new_page()
page.goto(url, wait_until="networkidle")
page.screenshot(path="out.png")
browser.close()
```
