# План: оптимизация скриншотов TradingView — без opencode AI

## Проблема: утечка токенов

**Было:** Пользователь пишет "сделай скриншот TradingView DOTUSDT 1D, прими куки, скрой левую панель, отправь мне"

→ бот → `opencode run` (AI-агент) → читает skill browser.md → думает как открыть
→ вызывает agent-browser → анализирует snapshot → ищет кнопки → кликает → делает скриншот
→ отдаёт результат → бот отправляет

**Расход:** ~5000-15000 токенов на один скриншот.

**Стало:** `скрин DOTUSDT 1D` → handler.py → `screenshot.py` → agent-browser напрямую → Telegram.
**0 токенов.** Нейронка вообще не участвует.

## Архитектура

```
Telegram User → handler.py (dispatch) → screenshot.py (take_screenshot)
                                             ↓
                                      agent-browser batch:
                                      1. open + wait 8
                                      2. hide right panel
                                      3. set timezone MSK
                                      4. screenshot
                                             ↓
                                      reply_photo в Telegram
```

## Текущий статус

| Компонент | Статус |
|-----------|--------|
| `bot/screenshot.py` | ✅ Создан |
| `bot/handler.py` — детект `скрин <symbol> <tf>` | ✅ Добавлен |
| Dark theme (`theme=dark`) | ✅ Работает |
| Бот запущен | ✅ PID 697712 |
| **Скрытие правой панели** | ❌ `find` молча падает в batch |
| **Установка MSK +3** | ❌ Не реализовано |

## Что нужно сделать

### 1. Разделить batch на 3 отдельных вызова

Текущий batch: 4 команды в одном `batch`. Если `find` падает — batch не сообщает об ошибке.

```python
# Было (один batch)
commands = ["open url", "wait 8", "find ... click", "wait 2", "screenshot path"]
proc = run_batch(commands)

# Стало (3 вызова)
run_batch([f"open {url}", "wait 8"])          # 1. открыть
run_batch(["find ... click", "wait 2"])         # 2. скрыть панель (ошибка игнорируется)
run_batch([f"screenshot {output_path}"])        # 3. скриншот
```

Плюсы: каждый шаг логируется, ошибки `find` не блокируют скриншот.

### 2. Добавить fallback-методы для скрытия панели

Пробовать методы по порядку:

```python
for method in [
    'find role button click --name "Watchlist, details, and news"',
    'find text "Watchlist, details, and news" click',
]:
    proc = run_batch([method, "wait 1"])
    if proc.returncode == 0 and "✗" not in proc.stderr:
        break  # сработало
```

### 3. Установка MSK (UTC+3)

**Via URL** (первая попытка):
```
https://www.tradingview.com/chart/?symbol=DOTUSDT&theme=dark&timezone=Europe/Moscow
```

**Via UI** (fallback если URL не сработал):
```python
# Клик по времени (содержит "UTC")
run_batch(['find text "UTC" click', "wait 1"])
# Откроется попап → клик "Timezone"
run_batch(['find text "Timezone" click', "wait 2"])
# Откроется список → клик "Moscow" / "Europe/Moscow"
run_batch(['find text "Moscow" click', "wait 1"])
# Или если есть поиск:
run_batch(['find role textbox fill "Moscow"', "wait 1"])
run_batch(['find text "Europe/Moscow" click', "wait 1"])
```

### 4. Логирование

```python
log = logging.getLogger("tg_bot")
for step_name, commands in steps:
    proc = run_batch(commands)
    if "✗" in proc.stderr:
        log.warning(f"[{step_name}] agent-browser: {proc.stderr[:200]}")
```

## Файлы

| Файл | Назначение |
|------|-----------|
| `bot/screenshot.py` | Модуль: `take_screenshot()` + `parse_request()` |
| `bot/handler.py` | Диспетчер: ловит `скрин ...` до opencode |
| `.opencode/plans/screenshot_command.md` | Этот план |

## Проверка

```bash
./scripts/tg_bot.sh restart
# В Telegram:
#   скрин DOTUSDT 1D → скриншот с dark theme, MSK, без Watchlist
#   скрин BTCUSDT 4h → 4-часовой график BTC
#   привет            → уходит в opencode (старый flow)
```

## Итог

После фикса:
- **0 токенов** на каждый скриншот — agent-browser напрямую
- Dark theme + MSK + скрытая правая панель — стандарт
- Fallback-методы страхуют от смены UI
- Логи: видно каждый шаг agent-browser
