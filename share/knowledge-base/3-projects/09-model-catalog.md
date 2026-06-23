# 09 — Model Catalog

**ID:** 09
**Расположение:** `projects/09_model_catalog/`
**Тип:** blueprint + data
**Порт:** 5000 (внутри 01)
**Запуск:** `./scripts/flask.sh start 01`

## Назначение

Каталог AI-моделей. JSON-реестр + UI внутри Fundament RF.

## Стек

- Flask blueprint
- JSON

## Архитектура

```
projects/09_model_catalog/
├── models_catalog.json    # Реестр моделей
├── routes.py              # Blueprint для 01
└── templates/
```

## Entry points

- Каталог: `/ai-models/`
- JSON: `/api/ai-models/` (по реализации)

## Зависимости

| Тип | Зависимость | Описание |
|---|---|---|
| Внутренняя | `projects/01_fundament_rf/app.py` | Регистрация blueprint |

## Связи с другими проектами

| Проект | Тип связи | Детали |
|---|---|---|
| 01 Fundament RF | blueprint | `/ai-models/` |
| 05 Transcript | data | Читает `models_catalog.json` |
| 07 TG Bot AIForGuest | data | Использует каталог моделей |
| 10 MAX Bot | data | Использует каталог моделей |

## Запуск

```bash
./scripts/flask.sh start 01
```

## Связанные KB

- [URL/Port карта](../4-guides/url-port-map.md)
