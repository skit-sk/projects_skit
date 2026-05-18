# agent-browser — браузерная автоматизация для AI-агентов

Инструмент от Vercel Labs для управления браузером из CLI.

## Быстрый справочник

Полная инструкция: `skills/instructions/browser.md`

## Установка

См. `tools/agent-browser/` в корне репозитория.

## Команды

```bash
# Открыть страницу
./tools/agent-browser/bin/agent-browser.sh open <url>

# Получить элементы страницы
./tools/agent-browser/bin/agent-browser.sh snapshot -i

# Клик по элементу
./tools/agent-browser/bin/agent-browser.sh click @e2

# Заполнить поле
./tools/agent-browser/bin/agent-browser.sh fill @e3 "text"

# Скриншот
./tools/agent-browser/bin/agent-browser.sh screenshot
./tools/agent-browser/bin/agent-browser.sh screenshot --annotate
```

## Batch-режим

```bash
./tools/agent-browser/bin/agent-browser.sh batch \
  "open https://example.com" \
  "wait 6" \
  "snapshot -i" \
  "click @e6" \
  "wait 1" \
  "screenshot"
```
