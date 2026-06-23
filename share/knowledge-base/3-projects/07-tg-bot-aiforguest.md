# 07 — TG Bot AIForGuest

**ID:** 07
**Расположение:** `projects/07_tg_bot_aiforguest/`
**Тип:** bot
**Порт:** —
**Запуск:** `./scripts/tg_bot.sh start`

## Назначение

Telegram-бот, проксирующий запросы пользователей в OpenCode и другие сервисы.

## Стек

- Python
- python-telegram-bot
- requests

## Архитектура

```
projects/07_tg_bot_aiforguest/
├── bot/
│   ├── main.py           # Entry point
│   ├── handler.py        # Обработчики команд
│   └── config.py
├── tools/scripts/        # Общие скрипты (shared с MAX Bot)
└── bot.log
```

## Entry points

- Telegram-бот (polling/webhook)

## Зависимости

| Тип | Зависимость | Описание |
|---|---|---|
| Внутренняя | `projects/01_fundament_rf/` | HTTP-вызовы к `localhost:5000` |
| Внутренняя | `projects/08_ofd_api/bot_ofd/` | `sys.path.insert` общий модуль |
| Внутренняя | `tools/scripts/` | Общие утилиты |
| Внутренняя | `projects/05_transcript/` | Получает результаты транскрипции |

## Связи с другими проектами

| Проект | Тип связи | Детали |
|---|---|---|
| 01 Fundament RF | HTTP | Вызовы API и Sandbox |
| 08 OFD API | shared_path | `sys.path.insert` для `bot_ofd` |
| 10 MAX Bot | shared_path | Общие `tools/scripts` |
| 05 Transcript | data | Получает результаты |

## Запуск

```bash
./scripts/tg_bot.sh start
```

## Связанные KB

- [Архитектура workspace](../4-guides/architecture-overview.md)
