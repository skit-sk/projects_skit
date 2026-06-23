# 08 — OFD API

**ID:** 08
**Расположение:** `projects/08_ofd_api/`
**Тип:** blueprint
**Порт:** 5000 (внутри 01)
**Запуск:** `./scripts/flask.sh start 01`

## Назначение

OFD API Explorer — интеграция с ОФД (контрольно-кассовая техника) внутри Fundament RF.

## Стек

- Flask blueprint
- OFD API

## Архитектура

```
projects/08_ofd_api/
├── routes.py              # Flask blueprint
├── bot_ofd/               # Общий модуль для ботов
├── templates/
└── static/
```

## Entry points

- OFD API: `/ofd-api/`
- OFD Abonent: `/ofd_abonent/`

## Зависимости

| Тип | Зависимость | Описание |
|---|---|---|
| Внутренняя | `projects/01_fundament_rf/app.py` | Регистрация blueprint |

## Связи с другими проектами

| Проект | Тип связи | Детали |
|---|---|---|
| 01 Fundament RF | blueprint | Импорт в `app.py` |
| 07 TG Bot AIForGuest | shared_path | `bot_ofd` используется ботом |

## Запуск

```bash
./scripts/flask.sh start 01
```

## Связанные KB

- [URL/Port карта](../4-guides/url-port-map.md)
