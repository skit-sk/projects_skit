# Charts Widgets

## Advanced Chart

**Демо:** https://www.tradingview.com/widget-docs/widgets/charts/advanced-chart/

Полнофункциональный интерактивный график с техническим анализом.

```html
<div id="advanced-chart-container"></div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
new TradingView.widget({
    "symbol": "NASDAQ:AAPL",
    "interval": "D",
    "container_id": "advanced-chart-container",
    "theme": "dark",
    "style": "1",
    "locale": "en",
    "toolbar_bg": "#f1f3f6",
    "enable_publishing": false,
    "allow_symbol_change": true,
    "hide_top_toolbar": false,
    "hide_legend": false,
    "save_image": false,
    " withdateranges": true,
    "hide_side_toolbar": false,
    "details": true,
    "hotlist": true
});
</script>
```

### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `symbol` | string | Символ (e.g., "NASDAQ:AAPL", "BITFINEX:BTCUSD") |
| `interval` | string | Интервал ("1", "5", "15", "30", "60", "D", "W", "M") |
| `theme` | string | "light" или "dark" |
| `toolbar_bg` | string | Цвет toolbar |
| `enable_publishing` | boolean | Разрешить сохранять изображение |
| `hide_top_toolbar` | boolean | Скрыть верхний тулбар |
| `withdateranges` | boolean | Показывать диапазоны дат |

---

## Symbol Overview

**Демо:** https://www.tradingview.com/widget-docs/widgets/charts/symbol-overview/

Компактный обзор символа: цена + мини-график.

```html
<div id="symbol-overview-widget"></div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
new TradingView.widget({
    "symbol": "BITSTAMP:BTCUSD",
    "width": "100%",
    "height": 400,
    "locale": "en",
    "colorTheme": "dark",
    "isTransparent": false,
    "autosize": true,
    "dateRange": "1M",
    "showVolume": true,
    "showMA": true,
    "hideDateRange": false,
    "hideMarketStatus": false,
    "hideSymbolLogo": false,
    "scalePosition": "right",
    "isHollowCandle": false,
    "upColor": "#26a69a",
    "downColor": "#ef5350",
    "unchangedColor": "#757575",
    "borderColor": "#S",
    "largeChartUrl": ""
});
</script>
```

### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `dateRange` | string | Диапазон ("1D", "1W", "1M", "3M", "6M", "1Y", "ALL") |
| `showVolume` | boolean | Показывать объём |
| `showMA` | boolean | Показывать Moving Average |
| `scalePosition` | string | "left" или "right" |

---

## Mini Chart

**Демо:** https://www.tradingview.com/widget-docs/widgets/charts/mini-chart/

Маленький график для компактного отображения.

```html
<tv-mini-ticker-chart
    symbol="BTCUSD"
    width="100%"
    height="200"
    locale="en"
    dateRange="1M"
    symbolUrl=""
></tv-mini-ticker-chart>
```

### Web Component параметры

| Атрибут | Тип | Описание |
|---------|-----|----------|
| `symbol` | string | Торговый символ |
| `width` | string | Ширина (e.g., "100%") |
| `height` | number | Высота в пикселях |
| `dateRange` | string | Диапазон времени |

---

## Демо в проекте

См. `/home/user_aioc/workspace/tradingview-demos/widgets/charts/`
