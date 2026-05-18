# BROWSER Skill — Browser Automation

**Статус:** РАБОТАЕТ
**Обновлено:** 2026-05-05

## Расположение

`tools/agent-browser/`

## Команды

```bash
# Открыть страницу
./tools/agent-browser/bin/agent-browser.sh open <url>

# Получить элементы [@e1, @e2...]
./tools/agent-browser/bin/agent-browser.sh snapshot -i

# Клик по референсу
./tools/agent-browser/bin/agent-browser.sh click @e2

# Скриншот
./tools/agent-browser/bin/agent-browser.sh screenshot

# Batch-команды
./tools/agent-browser/bin/agent-browser.sh batch \
  "open https://example.com" \
  "wait 6" \
  "snapshot -i" \
  "click @e6" \
  "wait 1" \
  "screenshot"
```

## Важно

После `click` ref может сброситься — бери новый `snapshot`.
