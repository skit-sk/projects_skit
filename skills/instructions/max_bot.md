# MAX BOT Skill — MAX (бывш. mail.ru) Bot Proxy → OpenCode

**Статус:** РАБОТАЕТ как сателлит TG-бота
**Обновлено:** 2026-07-10
**Связан:** [tg_bot.md](./tg_bot.md) — общий state.json, общая сессионная логика

## Архитектура

```
projects/10_max_bot/
├── main.py              # точка входа, polling MAX API
├── config.py            # MAX_BOT_TOKEN, MAX_WEBHOOK_URL, …
├── max_client.py        # обёртка над MAX Bot API
├── handler.py           # диспетчер команд (большая часть — симлинки в 07_tg)
├── session.py → 07_tg_bot_aiforguest/bot/session.py   # ОБЩИЙ
├── commands.py → 07_tg_bot_aiforguest/bot/commands.py # ОБЩИЙ
├── security.py → 07_tg_bot_aiforguest/bot/security.py # ОБЩИЙ
├── state.json → 07_tg_bot_aiforguest/bot/state.json   # ОБЩИЙ
├── max_bot.sh → ../../scripts/max_bot.sh  # launcher (в workspace/scripts/)
└── bot.log
```

**Ключевая особенность:** 95% модулей в `10_max_bot/bot/` — **симлинки** в `07_tg_bot_aiforguest/bot/`.
Это значит: **все правки `session.py`, `commands.py`, `security.py` автоматически применяются к обоим ботам**.

## Команды (отличаются от TG)

| Команда | Описание | Уникальность |
|---------|----------|--------------|
| `/start` | приветствие | общая |
| `/restart` | **пересоздать сессию** (MAX-only, уникальная) | 🟢 MAX |
| `/new [name]` | новая сессия | общая |
| `/sessions` | список | общая |
| `/switch <key>` | переключить | общая |
| `/rename <key> <name>` | переименовать | общая |
| `/drop` | удалить текущую | общая |
| `/info`, `/quota`, `/files` | инфо | общая |
| `/sc`, `/wg`, `/wgc`, `/sc_positions`, `/sc_analytics` | скриншоты | общая |
| `/build`, `/plan` | режим агента | общая |
| `/stop` | — | 🔴 не поддерживается (используйте системный kill) |
| `/format` | — | 🔴 не поддерживается |
| `/shutdown` | остановка бота | super only |

## Запуск/остановка

```bash
./scripts/max_bot.sh start
./scripts/max_bot.sh stop
./scripts/max_bot.sh restart
./scripts/max_bot.sh status
./scripts/max_bot.sh logs
./scripts/max_bot.sh webhook <url>   # установить webhook
```

❌ **НИКОГДА** `python main.py` напрямую.

## Env-переменные

| Переменная | Назначение |
|------------|-----------|
| `MAX_BOT_TOKEN` | токен MAX-бота (обязательно) |
| `MAX_SUPER_USER` | internal uid super-юзера (обязательно) |
| `MAX_WEBHOOK_URL` | URL webhook |
| `MAX_WEBHOOK_SECRET` | секрет webhook |
| `WORKSPACE_DIR` | путь к workspace (для `opencode run --dir`) |
| `CLOAKBROWSER_*` | опции скриншот-браузера |

## 🔑 КАК ОТЛИЧИТЬ MAX-сессию от TG-сессии в `ps`

Самый надёжный способ — **по cwd родительского процесса**:

```bash
ps -o pid,ppid,cmd -p <OPENCODE_PID>      # получить PPID
ls -la /proc/<PPID>/cwd                    # → projects/10_max_bot OR projects/07_tg_bot_aiforguest
```

| Признак | MAX bot | TG bot |
|---------|---------|--------|
| **PPID cwd** | `…/projects/10_max_bot` | `…/projects/07_tg_bot_aiforguest` |
| **PPID cmd** | `python3 main.py` | `python3 bot/main.py` |
| **Env-префикс** | `MAX_BOT_TOKEN`, `MAX_SUPER_USER` | `TG_BOT_TOKEN`, `TG_SUPER_USER` |
| **Launcher** | `scripts/max_bot.sh` | `scripts/tg_bot.sh` |
| **`--dir` в opencode run** | `…/ALL_USERS/usr_<uid>/<max_chat>/<session_key>/` | `…/ALL_USERS/usr_<uid>/<tg_chat>/<session_key>/` |
| **Команды юзера** | `/restart`, кнопки MAX | `/start`, текст, голос, фото |
| **chat_dir префикс** | `max_<id>` | `tg_<id>` |

### Однострочник для быстрой проверки

```bash
for p in $(pgrep -f 'opencode run'); do
  parent=$(awk '/^PPid:/ {print $2}' /proc/$p/status)
  cwd=$(readlink /proc/$p/cwd)
  pcwd=$(readlink /proc/$parent/cwd)
  case "$pcwd" in
    *10_max_bot*) bot="MAX";;
    *07_tg_bot*)  bot="TG";;
    *)            bot="?";;
  esac
  echo "opencode $p | $bot | $cwd"
done
```

## Структура per-session каталогов (с 2026-07-10)

```
ALL_USERS/usr_<uid>/
├── max_<chat_id>/                      # MAX-чат
│   ├── uploads/                        # общий upload на чат
│   ├── _default/                       # мигрированные legacy файлы
│   ├── ses_<uid>_<ts>/                 # сессия 1
│   │   ├── *.png, *.md
│   │   └── .opencode/                  # opencode runtime
│   └── ses_<uid>_<ts>/                 # сессия 2
└── tg_<chat_id>/                       # TG-чат
    ├── uploads/
    ├── _default/
    └── ses_<uid>_<ts>/
```

**Имя папки = `key` сессии** (например `ses_248207602_1717000000`).

## Файлы проекта (только уникальные)

| Файл | Назначение |
|------|-----------|
| `main.py` | Точка входа, polling MAX API, signal handlers |
| `max_client.py` | Обёртка MAX Bot API (отправка сообщений, фото, кнопок) |
| `handler.py` | **Свой** диспетчер (не симлинк) — адаптация TG-логики под MAX |
| `config.py` | Свой — `MAX_BOT_TOKEN`, `MAX_WEBHOOK_URL`, super-user |
| `scripts/max_bot.sh` (в `workspace/scripts/`) | launcher (start/stop/restart/status/logs/webhook) |

**Остальное (session, commands, security, state.json) — симлинки в `07_tg_bot_aiforguest/bot/`.**

## Связь с TG-ботом

- Один юзер может иметь **оба** мессенджера — связь через `state.json → users[usr_xxx].platform_links.{tg,max}`.
- `/link <tg_uid> <max_uid>` (super) — связать TG и MAX id.
- `resolve_uid(any_id)` в `session.py` ищет по обоим спискам.
- Один юзер = один набор сессий (общий для TG и MAX).

## Диагностика

```bash
# статус
./scripts/max_bot.sh status

# логи
./scripts/max_bot.sh logs

# активные сессии
pgrep -af 'opencode run' | grep -E 'max_|tg_'

# распределение по ботам
for p in $(pgrep -f 'opencode run'); do
  parent=$(awk '/^PPid:/ {print $2}' /proc/$p/status)
  pcwd=$(readlink /proc/$parent/cwd 2>/dev/null)
  echo "$p | $pcwd"
done
```

## ⚠️ Частые ошибки

| Симптом | Причина | Решение |
|---------|---------|---------|
| `MAX_BOT_TOKEN not set` | не загружен `.env` | `source scripts/source_env.sh && ./scripts/max_bot.sh start` |
| `Bot stopped by user` | юзер нажал /stop в MAX | ожидаемо, не требует действий |
| `❌ /stop не поддерживается` | юзер шлёт /stop в MAX | ответ уже корректный |
| Дублирование сессий у одного юзера | TG и MAX создают сессии независимо | использовать `/link` для связи |
