# 06 — Screenshots Catalog

**ID:** 06
**Расположение:** `projects/06_screenshots_project/`
**Тип:** static_mount
**Порт:** —
**Запуск:** Статические файлы через Sandbox `/static/sandbox/06/`

## Назначение

Каталог скриншотов и визуальных ассетов.

## Стек

- HTML / CSS / JS
- Статические изображения

## Архитектура

```
projects/06_screenshots_project/
├── catalog.html
├── images/
└── static/
```

## Entry points

- Каталог: `/static/sandbox/06/catalog.html`

## Связи с другими проектами

| Проект | Тип связи | Детали |
|---|---|---|
| 01 Fundament RF | static mount | `/static/sandbox/06/` |

## Запуск

```bash
./scripts/flask.sh start 01
# затем открыть http://localhost:5000/static/sandbox/06/catalog.html
```

## Связанные KB

- [URL/Port карта](../4-guides/url-port-map.md)
