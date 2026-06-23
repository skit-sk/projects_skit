# 02 — Graphs Candle

**ID:** 02
**Расположение:** `projects/02_graphs_candle/`
**Тип:** Flask
**Порт:** 5005
**Запуск:** `./scripts/flask.sh start 02 5005`

## Назначение

Интерактивные свечные графики (Plotly) с обнаружением паттернов и SVG-альтернативой.

## Стек

- Flask
- ccxt v4.5.50
- Plotly
- pandas / numpy

## Архитектура

```
projects/02_graphs_candle/
├── main.py              # Flask entry point
├── routes/
│   ├── api.py
│   ├── web.py
│   └── graphics.py
├── charts/              # Построение графиков
├── data/                # Кэш данных
├── templates/
└── static/
```

## Entry points

- Главная: `/`
- Plotly: `/`
- SVG: `/alt`

## Зависимости

| Тип | Зависимость | Описание |
|---|---|---|
| Внешняя | Bitget API | Через ccxt |
| Внешняя | Plotly | Интерактивные графики |

## Связи с другими проектами

| Проект | Тип связи | Детали |
|---|---|---|
| 01 Fundament RF | proxy | Доступен через `/proxy/02/` |

## Запуск

```bash
./scripts/flask.sh start 02 5005
```

## Связанные KB

- [URL/Port карта](../4-guides/url-port-map.md)
