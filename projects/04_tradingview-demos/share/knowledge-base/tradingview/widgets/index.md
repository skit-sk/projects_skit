# TradingView Widgets

**Документация:** https://www.tradingview.com/widget-docs/

Готовые виджеты для встраивания на сайт. Не требуют написания кода — просто скопируйте и вставьте.

## Форматы

| Формат | Описание | Пример |
|--------|----------|--------|
| **iframe** | Классический embed через `<script>` | `new TradingView.widget(...)` |
| **Web Component** | Современный `<tv-widget>` | `<tv-advanced-chart symbol="BTCUSD">` |

## Категории виджетов

| Категория | Виджеты | Раздел |
|-----------|---------|--------|
| [Charts](charts/) | Advanced Chart, Symbol Overview, Mini Chart | 3 |
| [Watchlists](watchlists/) | Market Summary, Overview, Stock Market, Quotes | 4 |
| [Tickers](tickers/) | Ticker Tape, Single Ticker, Ticker | 3 |
| [Heatmaps](heatmaps/) | Stock, Crypto, ETF, Forex heatmaps + Cross Rates | 5 |
| [Screeners](screeners/) | Screener, Crypto Market | 2 |
| [Symbol Details](symbol-details/) | Symbol Info, Technical Analysis, Fundamental Data, Company Profile | 4 |
| [News](news/) | Top Stories | 1 |
| [Calendars](calendars/) | Economic Calendar | 1 |

## Быстрый старт

### 1. Выберите виджет

Перейдите на https://www.tradingview.com/widget/ и выберите нужный виджет.

### 2. Настройте параметры

Настройте symbol, interval, theme и другие опции.

### 3. Скопируйте код

```html
<!-- iframe версия -->
<div id="widget-container"></div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
new TradingView.widget({
    "symbol": "BTCUSD",
    "interval": "D",
    "container_id": "widget-container",
    "theme": "dark"
});
</script>
```

### 4. Вставьте на сайт

```html
<!-- Web Component версия -->
<tv-mini-ticker-chart symbol="BTCUSD" width="100%" height="200"></tv-mini-ticker-chart>
```

## Преимущества Widgets

| Преимущество | Описание |
|--------------|----------|
| **Быстрая интеграция** | Copy-paste за минуты |
| **Встроенные данные** | Не нужно подключать свой datafeed |
| **Адаптивность** | Работают на desktop и mobile |
| **Локализация** | 30+ языков включено |
| **Темы** | Dark/Light темы |

## Сравнение с Lightweight Charts

| Критерий | Widgets | Lightweight Charts |
|----------|---------|-------------------|
| Код | Не нужен | JavaScript |
| Данные | Встроены TV | Свои данные |
| Кастомизация | Ограничена | Полная |
| Размер | 0 KB (iframe) | 35 KB |
| Real-time | Встроен | Своя реализация |
| Технические индикаторы | Встроены | Нужно писать |

## Демо в этом проекте

См. `/home/user_aioc/workspace/tradingview-demos/widgets/` — интерактивные демо всех виджетов.

## Ресурсы

- [Каталог виджетов](https://www.tradingview.com/widget/)
- [Документация](https://www.tradingview.com/widget-docs/)
- [Widget Demos](https://www.tradingview.com/widget-docs/widgets/)
- [Available Markets](https://www.tradingview.com/widget-docs/markets/)
