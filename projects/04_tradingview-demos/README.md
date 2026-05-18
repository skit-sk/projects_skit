# TradingView Lightweight Charts Demos

Демонстрационная галерея графиков TradingView Lightweight Charts v5.2.0 с реальными данными Binance.

## Структура проекта

```
tradingview-demos/
├── index.html              # Главная галерея (iframe с демо)
├── chart-types/            # Типы графиков
│   ├── 1-standard-time-chart/
│   ├── 2-yield-curve-chart/
│   ├── 3-options-price-chart/
│   ├── 4-custom-horizontal-scale/
│   ├── 5-multi-pane-chart/
│   └── README.md           # Подробная документация
├── series-types/           # Типы серий данных
│   ├── candlestick/
│   ├── line/
│   ├── area/
│   ├── histogram/
│   ├── bar/
│   ├── baseline/
│   └── README.md           # Подробная документация
├── conditions/             # Настройки и условия
│   ├── dark-theme/
│   ├── light-theme/
│   ├── fixed-size/
│   ├── multiple-series/
│   ├── overlay-price-scale/
│   ├── autosize-responsive/
│   ├── locale-i18n/
│   └── README.md           # Подробная документация
└── README.md               # Этот файл
```

## Быстрый старт

### Запуск локально

```bash
cd tradingview-demos
python3 -m http.server 8080
# Откройте http://localhost:8080
```

### Деплой на Vercel

```bash
vercel --prod
```

## Каталог демо

### Chart Types (Типы графиков)
| # | Название | Метод | Описание |
|---|----------|-------|----------|
| 1 | Standard Time Chart | `createChart()` | Стандартный временной график с UTC timestamp |
| 2 | Yield Curve Chart | `createYieldCurveChart()` | Кривая доходности облигаций (месяцы/duration) |
| 3 | Options Price Chart | `createOptionsChart()` | График опционов (Price scale) |
| 4 | Custom Horizontal Scale | `createChart()` | График с кастомной шкалой (Fibonacci) |
| 5 | Multi-Pane Chart | `createChart() + addPane()` | Несколько панелей (свечи + Volume) |

### Series Types (Типы серий)
| Название | Метод | Описание |
|----------|-------|----------|
| Candlestick | `CandlestickSeries` | Японские свечи (OHLC) |
| Line | `LineSeries` | Линейный график |
| Area | `AreaSeries` | Областной график с заливкой |
| Histogram | `HistogramSeries` | Гистограмма (объёмы) |
| Bar | `BarSeries` | Баровый график (OHLC) |
| Baseline | `BaselineSeries` | График с базовой линией |

### Conditions (Настройки)
| Название | Описание |
|----------|----------|
| Dark Theme | Тёмная тема оформления |
| Light Theme | Светлая тема оформления |
| Fixed Size | Фиксированные размеры графиков |
| Multiple Series | Несколько серий на одном графике |
| Overlay Price Scale | Volume на overlay шкале |
| AutoSize Responsive | Автоматическое изменение размера |
| Locale i18n | Локализация (ru-RU) |

## Данные

- **Источник**: [Binance API](https://api.binance.com)
- **Symbol**: BTCUSDT Perpetual
- **Interval**: 1h (1 час)
- **Limit**: 50-200 candles (зависит от демо)

## Структура каждого демо

Каждый демо содержит два файла:

### index.html (Light версия)
- Чистый график для встраивания в iframe
- Без info panel
- Минимальный размер

### full.html (Full версия)
- График + раскрывающаяся info panel
- Параметры с color swatches
- Замеры времени (fetch, chart_build, total)
- Debug data с первыми/последними значениями

## Timing (Замеры времени)

Каждый full.html показывает время выполнения:

```
timing:
  fetch: 45ms        # Загрузка библиотеки с CDN
  chart_build: 123ms # Создание графика + данные
  total: 168ms       # Полное время
```

## Цветовые коды

### Основные цвета TradingView
- `#2962FF` — синий (primary)
- `#26a69a` — зелёный (up/bullish)
- `#ef5350` — красный (down/bearish)
- `#131722` — тёмный фон
- `#1e222d` — тёмная сетка
- `#d1d4dc` — светлый текст

### RGBA варианты
- `rgba(38, 166, 154, 0.5)` — полупрозрачный зелёный
- `rgba(239, 83, 80, 0.5)` — полупрозрачный красный
- `rgba(41, 98, 255, 0.28)` — полупрозрачный синий (topColor)
- `rgba(41, 98, 255, 0.05)` — почти прозрачный (bottomColor)

## Полезные ссылки

- [Lightweight Charts Documentation](https://tradingview.github.io/lightweight-charts/)
- [TradingView GitHub](https://github.com/tradingview/lightweight-charts)
- [Binance API](https://github.com/binance/binance-official-api-docs)

## Лицензия

MIT
