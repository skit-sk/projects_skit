# 04 — TradingView Demos

**ID:** 04
**Расположение:** `projects/04_tradingview-demos/`
**Тип:** static_mount
**Порт:** —
**Запуск:** Статические файлы через Sandbox `/static/sandbox/04/`

## Назначение

Галерея виджетов TradingView и демо Lightweight Charts v5.2.

## Стек

- HTML / CSS / JS
- TradingView Widgets (web components + iframe)
- TradingView Lightweight Charts™ v5.2

## Архитектура

```
projects/04_tradingview-demos/
├── index.html                      # Главная галерея
├── widgets/                        # Превью виджетов для галереи
│   ├── charts/
│   ├── watchlists/
│   ├── tickers/
│   ├── heatmaps/
│   ├── screeners/
│   ├── symbol-details/
│   ├── news/
│   ├── calendars/
│   └── economics/
├── widgets-full/                   # Полноразмерные страницы виджетов
├── chart-types/                    # Lightweight Charts: типы графиков
├── series-types/                   # Lightweight Charts: типы серий
├── conditions/                     # Lightweight Charts: условия/темы
├── update_widgets.py               # Генератор full-страниц
├── fix_widgets.py                  # Регенерация превью
└── share/knowledge-base/tradingview/  # Документация
```

## Entry points

- Галерея: `/static/sandbox/04/index.html`
- Mini Chart: `/static/sandbox/04/widgets-full/mini-chart.html`
- Advanced Chart: `/static/sandbox/04/widgets-full/advanced-chart.html`
- Economic Map: `/static/sandbox/04/widgets-full/economic-map.html`

## Зависимости

| Тип | Зависимость | Описание |
|---|---|---|
| Внешняя | TradingView CDN | Виджеты и графики |

## Связи с другими проектами

| Проект | Тип связи | Детали |
|---|---|---|
| 01 Fundament RF | static mount | `/static/sandbox/04/` |

## Запуск

Файлы отдаются статически из Sandbox 01:

```bash
./scripts/flask.sh start 01
# затем открыть http://localhost:5000/static/sandbox/04/index.html
```

## Примечания

- Рабочие виджеты используют либо web components (`tv-mini-chart`, `tv-economic-map`), либо динамический iframe к `https://www.tradingview-widget.com/embed-widget/`.
- Скрипт `fix_widgets.py` перегенерирует все preview и full-страницы.

## Связанные KB

- [TradingView Playground](../tradingview/playground-guide.md)
