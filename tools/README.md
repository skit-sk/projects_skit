# Tools Directory

Готовые инструменты для browser automation — три подхода к схожим задачам.

## Инструменты

| Инструмент | Путь | Суть |
|------------|------|------|
| **agent-browser** | [`agent-browser/`](agent-browser/) | Shell-команды, ref-based, LLM-first (Vercel, Rust) |
| **Playwright** | [`playwright/`](playwright/) | Python API, stock Chromium, стандарт (Microsoft) |
| **CloakBrowser** | [`cloakbrowser/`](cloakbrowser/) | Playwright API, кастомный Chromium, стелс (CloakHQ) |

---

## Матрица выбора

| Сценарий | agent-browser | Playwright | CloakBrowser |
|---|---|---|---|
| **LLM-driven browsing** (snapshot → ref → click) | ✅ нативный | ❌ | ❌ |
| **Скриншот без стелса** | ⚠️ batch-mode | ✅ `page.screenshot()` | ✅ — избыточно |
| **Скриншот TradingView / бирж** | ❌ детектится | ❌ детектится | ✅ 57 C++ патчей |
| **Обход Cloudflare Turnstile** | ❌ FAIL | ❌ FAIL | ✅ PASS |
| **Обход reCAPTCHA v3** | ❌ 0.1 (бот) | ❌ 0.1 (бот) | ✅ 0.9 (человек) |
| **Формы с humanize-поведением** | ❌ | ❌ | ✅ Bézier + посимвольный ввод |
| **Прокси + GeoIP + WebRTC spoof** | ❌ | ❌ | ✅ нативный SOCKS5 |
| **Быстрый one-shot скрипт** | ✅ `batch` | ✅ 3 строки | ⚠️ ~2-4s launch |
| **Зависимости** | Node.js + Rust CLI | Python + Chromium | Python + кастомный Chromium |
| **Размер бинарника** | ~200MB | ~200MB | ~444MB |
| **Звёзд GitHub** | 33k ★ | — (Microsoft) | 12.4k ★ |
| **Лицензия** | Apache-2.0 | Apache-2.0 | MIT |

---

## Детали

### agent-browser

Browser automation CLI для AI-агентов. Быстрый нативный Rust CLI.

```bash
# Workflow: open → snapshot → click по ref
agent-browser open example.com
agent-browser snapshot -i -c
agent-browser click @e2
agent-browser screenshot page.png
agent-browser close
```

[Документация →](agent-browser/README.md)

### Playwright

Стандартный Playwright от Microsoft. Stock Chromium, полный Python API.

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://example.com")
    page.screenshot(path="page.png")
    browser.close()
```

[Документация →](playwright/README.md)

### CloakBrowser

Кастомный Chromium v146 с 57 C++ патчами. Не детектится антиботами.

```python
from cloakbrowser import launch

browser = launch(headless=True)
page = browser.new_page()
page.goto("https://tradingview.com")
page.screenshot(path="chart.png")
browser.close()
```

[Документация →](cloakbrowser/README.md)

---

## Быстрый старт

```bash
# agent-browser (уже установлен)
./tools/agent-browser/bin/agent-browser.sh open example.com

# Playwright (установить при необходимости)
./tools/playwright/install.sh
./tools/playwright/bin/playwright.sh tools/playwright/workflows/basic.py

# CloakBrowser (уже установлен)
./tools/cloakbrowser/bin/test.sh
```

## Связанное

- [`projects/07_tg_bot_aiforguest/bot/screenshot_browser.py`](../projects/07_tg_bot_aiforguest/bot/screenshot_browser.py) — `sc` команда бота на CloakBrowser
- [`projects/07_tg_bot_aiforguest/bot/screenshot_widget.py`](../projects/07_tg_bot_aiforguest/bot/screenshot_widget.py) — `wg` команда бота на CloakBrowser
- [`docs/SECURITY_GUIDELINES.md`](../docs/SECURITY_GUIDELINES.md)
