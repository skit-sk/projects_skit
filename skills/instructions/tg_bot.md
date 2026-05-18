# TG BOT Skill — Telegram Bot Proxy → OpenCode

**Статус:** РАБОТАЕТ
**Обновлено:** 2026-05-15

## ⚠️ СТРОГИЕ ПРАВИЛА

### 1. Запуск/остановка — ТОЛЬКО через скрипт

```bash
./scripts/tg_bot.sh start              # запуск
./scripts/tg_bot.sh stop               # остановка
./scripts/tg_bot.sh restart            # перезапуск
./scripts/tg_bot.sh status             # статус
./scripts/tg_bot.sh logs               # tail -f лога
```

❌ **НИКОГДА** `python bot/main.py` напрямую.

### 2. Рестарт — только когда нет активных запросов и plan mode

Перед рестартом проверить:

```bash
ps aux | grep 'opencode run' | grep -v grep
```

Если есть активный `opencode run` — **дождаться завершения**, иначе ответ пользователя будет потерян.

Build mode после запроса автоматически сбрасывается в plan — не требует ручного вмешательства.

### 3. Изменение кода — всегда проверять импорты

Файлы бота:

| Файл | Назначение |
|------|-----------|
| `bot/main.py` | Точка входа, polling, логирование |
| `bot/handler.py` | Диспетчер команд, маршрутизация |
| `bot/commands.py` | Реализация всех команд и `cmd_message()` |
| `bot/session.py` | Управление сессиями, пользователями, state.json |
| `bot/config.py` | Конфигурация, переменные окружения |
| `bot/security.py` | Фильтры безопасности, `run_opencode()` |
| `bot/templates.py` | Футер, форматирование вывода |

### 4. Структура проекта

```
TG_ALL/
  TG_{uid}/          # рабочая директория пользователя
    uploads/          # загруженные файлы
bot/
  state.json          # состояние: пользователи, сессии, лимиты
  bot.log             # лог бота
```

### 5. Модель данных state.json

```json
{
  "super": 123456789,
  "default_model": "opencode/deepseek-v4-flash-free",
  "users": {
    "123456789": {
      "name": "Name",
      "role": "super|normal",
      "model": null,
      "limits": null,
      "sessions": {
        "current": "ses_xxx",
        "list": {
          "ses_xxx": {
            "name": "session name",
            "messages": 0,
            "tokens": 0,
            "opencode_id": "ses_xxx"
          }
        }
      }
    }
  }
}
```

### 6. Счётчик токенов — ТОЛЬКО из step_finish

Запрещено использовать `opencode export` для подсчёта токенов (race condition).
Токены парсить из `json_lines` ответа `run_opencode`:

```
step_finish → part.tokens.total
```

Сумма накапливается: `state.tokens += текущие_токены`.

### 7. Вывод — обрезка до 4000 символов

Любой ответ пользователю обрезается:

```python
if len(response) > 4000:
    response = response[:4000] + "\n\n... (обрезано)"
```

### 8. Обработка скриншотов

- Детект изображений: `wd.rglob("*.[pj][np]g")` до и после `run_opencode`.
- Отправка: `update.message.reply_photo(photo=f)`.
- Максимум 3 изображения за один ответ.
- Снимок ДО сохраняется в переменную `before`, ПОСЛЕ — `after`. Разница = новые.

### 9. Режим agent — строгое правило

- **Все пользователи** по умолчанию: `agent="plan"` (только план, без выполнения).
- **Build mode** — временное переключение для выполнения конкретного запроса.
- Команда: `/build` — включает build mode для следующего сообщения.
- После ответа opencode build mode **автоматически сбрасывается** в plan.
- Состояние build mode хранится в сессии (`session._build_mode`).
- Реализация: `cmd_message()` проверяет `get_build_mode(uid)` → если True, `agent=None`.

### 10. Безопасность

- Фильтр `pre_filter()` блокирует: `.env`, токены, пароли, системные пути, `sudo`, `pip install`, опасные shell-команды.
- Неавторизованные пользователи логируются через `log_unauthorized()`.
- Super user задаётся в `.env: TG_SUPER_USER`.

### 11. Сессии — по одной на чат

- `/new [name]` — создать новую сессию.
- `/switch <key>` — переключиться.
- `/sessions` — список.
- `/drop` — удалить текущую.
- Каждая сессия хранит: `messages`, `tokens`, `opencode_id`.

### 12. Формат футера

```python
f"━━━━━━━━━━━━━━━━━━━━\n"
f"💬 {msgs}/{limit} · 🔤 {tokens_used}/{token_limit} · 💾 {storage}/{storage_limit} · 📄 {files}/{file_limit}\n"
f"🤖 {model_name} | [{provider}]\n"
f"📁 {session_name}"
```

### 13. Команды

| Команда | Доступ | Описание |
|---------|--------|----------|
| `/start` | Все | Приветствие |
| `/new [name]` | Все | Новая сессия |
| `/sessions` | Все | Список сессий |
| `/switch <key>` | Все | Переключить сессию |
| `/drop` | Все | Удалить сессию |
| `/info` | Все | Инфо о пользователе |
| `/quota` | Все | Квота файлов |
| `/models [filter]` | Все | Список моделей |
| `/request model <name>` | Normal | Запрос модели |
| `/request limit <type> <n>` | Normal | Запрос лимита |
| `/setmodel <id\|default> <model>` | Super | Назначить модель |
| `/setlimit <id> <type> <n>` | Super | Назначить лимит |
| `/users` | Super | Список пользователей |
| `/adduser <id> <name>` | Super | Добавить |
| `/removeuser <id>` | Super | Удалить |
| `/cd [path]` | Super | Сменить директорию |
| `/shutdown` | Super | Остановка бота |
