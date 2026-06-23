# 10 — MAX Bot

**ID:** 10
**Расположение:** `projects/10_max_bot/`
**Тип:** bot
**Порт:** —
**Запуск:** `./projects/10_max_bot/scripts/max_bot.sh start`

## Назначение

Сателлит Telegram-бота (07) для платформы MAX. Проксирует запросы и использует общие модули.

## Стек

- Python
- requests
- Telegram Bot API / MAX API

## Архитектура

```
projects/10_max_bot/
├── main.py                # Entry point
├── handler.py             # Обработчики
├── config.py
├── scripts/
│   └── max_bot.sh         # Управление ботом
└── bot.log
```

## Entry points

- MAX IM / Telegram bot

## Зависимости

| Тип | Зависимость | Описание |
|---|---|---|
| Внутренняя | `projects/01_fundament_rf/` | HTTP-вызовы к `localhost:5000` |
| Внутренняя | `projects/09_model_catalog/` | Каталог моделей |
| Внутренняя | `tools/scripts/` | Общие утилиты (shared с 07) |

## Связи с другими проектами

| Проект | Тип связи | Детали |
|---|---|---|
| 01 Fundament RF | HTTP | Вызовы API/Sandbox |
| 09 Model Catalog | data | `models_catalog.json` |
| 07 TG Bot AIForGuest | shared_path | Общие `tools/scripts` |

## Запуск

```bash
./projects/10_max_bot/scripts/max_bot.sh start
```

## Связанные KB

- [Архитектура workspace](../4-guides/architecture-overview.md)
