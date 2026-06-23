# TradingView Knowledge Base

База знаний по TradingView продуктам и библиотекам.

**Версия:** v1.1 (2026-04-30)

---

## Структура

```
share/knowledge-base/tradingview/
├── lightweight/          # Lightweight Charts™ (open-source)
├── widgets/             # TradingView Widgets (iframe/Web Component)
├── advanced/            # Advanced Charts (private repo)
├── terminal/           # Trading Platform
└── resources/           # Ссылки и ресурсы
```

---

## Продукты TradingView

| Продукт | Описание | Данные | Лицензия |
|---------|---------|--------|----------|
| [Lightweight Charts™](lightweight/) | Open-source библиотека, 35KB | Свои данные | Apache 2.0 |
| [TradingView Widgets](widgets/) | Готовые виджеты для встраивания | Встроены от TV | Бесплатно |
| [Advanced Charts](advanced/) | Полная библиотека TradingView | Свои данные | Commercial |
| [Trading Platform](terminal/) | Торговая платформа | Свои данные | Commercial |

---

## Lightweight Charts™ (основной раздел)

### Chart Types — Типы графиков

| # | Тип | Функция | Шкала |
|---|-----|---------|-------|
| 1 | [Standard Time Chart](lightweight/chart-types/1-standard-time-chart.md) | `createChart()` | Time |
| 2 | [Yield Curve Chart](lightweight/chart-types/2-yield-curve-chart.md) | `createYieldCurveChart()` | Linear |
| 3 | [Options Price Chart](lightweight/chart-types/3-options-price-chart.md) | `createOptionsChart()` | Price |
| 4 | [Custom Horizontal Scale](lightweight/chart-types/4-custom-horizontal-scale.md) | `createChartEx()` | Custom |
| 5 | [Multi-Pane Chart](lightweight/chart-types/5-multi-pane-chart.md) | `createChart()` + `addPane()` | Time + Panes |

### Series Types — Типы серий

| Тип | Series Definition | Data Format |
|-----|------------------|-------------|
| [Candlestick](lightweight/series-types/candlestick.md) | `CandlestickSeries` | `CandlestickData` |
| [Line](lightweight/series-types/line.md) | `LineSeries` | `LineData` |
| [Area](lightweight/series-types/area.md) | `AreaSeries` | `SingleValueData` |
| [Bar](lightweight/series-types/bar.md) | `BarSeries` | `BarData` |
| [Histogram](lightweight/series-types/histogram.md) | `HistogramSeries` | `HistogramData` |
| [Baseline](lightweight/series-types/baseline.md) | `BaselineSeries` | `SingleValueData` |
| [Custom Plugin](lightweight/series-types/custom-plugin.md) | `ICustomSeriesPaneView` | Custom |

### Conditions — Условия

| Демо | Описание |
|------|----------|
| [Dark Theme](lightweight/conditions/dark-theme.md) | Тёмная тема |
| [Light Theme](lightweight/conditions/light-theme.md) | Светлая тема |
| [AutoSize Responsive](lightweight/conditions/autosize-responsive.md) | Адаптивный размер |
| [Fixed Size](lightweight/conditions/fixed-size.md) | Фиксированные размеры |
| [Multiple Series](lightweight/conditions/multiple-series.md) | Несколько серий |
| [Overlay Price Scale](lightweight/conditions/overlay-price-scale.md) | Overlay scale для Volume |
| [Locale i18n](lightweight/conditions/locale-i18n.md) | Локализация |

### Advanced — Продвинутые темы

| Раздел | Описание |
|--------|----------|
| [Plugins](lightweight/plugins/intro.md) | Custom series, primitives |
| [Tutorials](lightweight/tutorials/how-to.md) | Пошаговые руководства |
| [API Reference](lightweight/api/IChartApi.md) | IChartApi, ISeriesApi |
| [Performance](lightweight/advanced/performance.md) | Оптимизация |
| [Real-time](lightweight/advanced/realtime.md) | Live обновления |

### Connecting Data

| Файл | Описание |
|------|----------|
| [Data Formats](lightweight/connecting-data/data-formats.md) | Форматы данных, time types |

---

## TradingView Widgets

Готовые виджеты для встраивания. см. [widgets/index.md](widgets/index.md)

### Категории виджетов

- **Charts** — Advanced Chart, Symbol Overview, Mini Chart
- **Watchlists** — Market Summary, Market Overview, Stock Market
- **Tickers** — Ticker Tape, Single Ticker, Ticker
- **Heatmaps** — Stock, Crypto, ETF, Forex heatmaps
- **Screeners** — Screener, Crypto Market
- **Symbol Details** — Symbol Info, Technical Analysis, Fundamental Data
- **News** — Top Stories
- **Calendars** — Economic Calendar

---

## Advanced Charts

Полная библиотека TradingView. см. [advanced/index.md](advanced/index.md)

⚠️ Требует доступа к private repository TradingView.

---

## Trading Platform

Торговая платформа. см. [terminal/index.md](terminal/index.md)

---

## Resources — Ресурсы

| Ресурс | Путь |
|--------|------|
| [GitHub Issues](resources/github-issues.md) | Ссылки на issues |
| [External Links](resources/external-links.md) | Внешняя документация |

---

## Версии

| Продукт | Версия |
|---------|--------|
| Lightweight Charts™ | v5.2 |
| Advanced Charts | v30+ |
| Widgets | current |

---

## Источники

- [TradingView Lightweight Charts](https://tradingview.github.io/lightweight-charts/) — основная документация
- [Advanced Charts Documentation](https://www.tradingview.com/charting-library-docs/) — Advanced Charts
- [TradingView Widgets](https://www.tradingview.com/widget/) — каталог виджетов
- [Trading Platform Demo](https://trading-terminal.tradingview-widget.com/) — демо платформы
- [GitHub Issues](https://github.com/tradingview/charting_library/issues) — баг-репорты
