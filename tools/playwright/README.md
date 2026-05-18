# Playwright — Stock Chromium Automation

[Microsoft Playwright](https://playwright.dev/) — Python/JS API для Chromium. Без стелс-патчей, без обёрток.

## Установка

```bash
./tools/playwright/install.sh
```

Скачивает stock Chromium for Testing в `$PLAYWRIGHT_BROWSERS_PATH` (`/tmp/playwright-browsers`).

## Использование

```bash
# Базовый пример
./tools/playwright/bin/playwright.sh tools/playwright/workflows/basic.py

# Скриншот TradingView
./tools/playwright/bin/playwright.sh tools/playwright/workflows/tv_screenshot.py BITGET:DOTUSDT 1D
```

## Когда использовать

- Быстрый скриншот где стелс не важен
- Формы, клики, парсинг без антибот-защиты
- Лёгкая альтернатива CloakBrowser (-200MB, -2с launch)
- Разработка и отладка скриптов перед переносом на CloakBrowser

## Отличия от agent-browser

| | Playwright | agent-browser |
|---|---|---|
| API | Python `page.goto()` / `page.screenshot()` | shell `agent-browser open` / `screenshot` |
| Выбор элементов | CSS/XPath/role-локаторы | refs (`@e1`) из snapshot |
| LLM-friendly | ❌ | ✅ компактный output |
| Зависимости | Python + Chromium (~200MB) | Node.js + Rust CLI + Chrome (~200MB) |
