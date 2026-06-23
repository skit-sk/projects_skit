# 03 — Demo Charts ASCII

**ID:** 03
**Расположение:** `projects/03_demo_charts_ascii/`
**Тип:** Flask
**Порт:** 5003
**Запуск:** `./scripts/flask.sh start 03 5003`

## Назначение

Демонстрация ASCII-графиков, Plotly, Chart.js и Deck.gl на данных торговых сделок.

## Стек

- Flask
- asciichart / plotext / termgraph
- Chart.js / Plotly / Deck.gl
- numpy

## Архитектура

```
projects/03_demo_charts_ascii/
├── app.py                       # Flask routes
├── ascii_charts.py              # ASCII-рендереры
├── ascii_visuals.py
├── charts.py                    # Генератор 14 моделей инфографики
├── indicators.py
├── generators/                  # asciichart_gen, plotext_gen, termgraph_gen, summary_gen
├── data/                        # Локальные карточки
├── outputs/                     # Сгенерированные ASCII-инфографики
├── templates/
└── static/
```

## Entry points

- Главная / файловое дерево: `/`
- ASCII-инфографика: `/infographics/<symbol>`
- ASCII-new (все модели): `/ascii-new/<symbol>`
- Plotly: `/interactive/<symbol>`
- Chart.js: `/chartjs/<symbol>`
- Deck.gl: `/deckgl/<symbol>`
- API данных: `/api/data/<symbol>`

## Зависимости

| Тип | Зависимость | Описание |
|---|---|---|
| Внутренняя | `projects/01_fundament_rf/data/card/` | Fallback-источник данных |

## Связи с другими проектами

| Проект | Тип связи | Детали |
|---|---|---|
| 01 Fundament RF | proxy / данные | `/proxy/03/` + live данные из `01/data/card/` |

## Запуск

```bash
./scripts/flask.sh start 03 5003
```

## Примечания

- Для предгенерации всех ASCII-outputs используется `generate_all_outputs.py`.
- Данные читаются напрямую из `01_fundament_rf/data/card/` (fallback), без копирования.

## Связанные KB

- [URL/Port карта](../4-guides/url-port-map.md)
