# Heatmap Widgets

## Stock Heatmap

**Демо:** https://www.tradingview.com/widget-docs/widgets/heatmaps/stock-heatmap/

Тепловая карта акций по секторам/странам.

```html
<div id="stock-heatmap-widget"></div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
new TradingView.widget({
    "width": "100%",
    "height": 500,
    "locale": "en",
    "darkMode": true,
    "dataSource": "stocks_us",
    "group": "sector",
    "showSymbolLabel": true,
    "showVolume": true,
    "isTransparent": false
});
</script>
```

### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `dataSource` | string | "stocks_us", "stocks_uk", "stocks_eu" |
| `group` | string | "sector", "country", "market_cap" |
| `showSymbolLabel` | boolean | Показывать название |

---

## Crypto Coins Heatmap

**Демо:** https://www.tradingview.com/widget-docs/widgets/heatmaps/crypto-heatmap/

Тепловая карта криптовалют.

```html
<div id="crypto-heatmap-widget"></div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
new TradingView.widget({
    "width": "100%",
    "height": 500,
    "locale": "en",
    "darkMode": true,
    "dataSource": "crypto_total",
    "group": "market_cap",
    "showSymbolLabel": true,
    "isTransparent": false
});
</script>
```

---

## ETF Heatmap

**Демо:** https://www.tradingview.com/widget-docs/widgets/heatmaps/etf-heatmap/

Тепловая карта ETF.

```html
<div id="etf-heatmap-widget"></div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
new TradingView.widget({
    "width": "100%",
    "height": 500,
    "locale": "en",
    "darkMode": true,
    "dataSource": "etf_us",
    "group": "type",
    "showSymbolLabel": true,
    "showVolume": true,
    "isTransparent": false
});
</script>
```

---

## Forex Cross Rates

**Демо:** https://www.tradingview.com/widget-docs/widgets/heatmaps/forex-cross-rates/

Кросс-курсы валют.

```html
<div id="forex-cross-rates-widget"></div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
new TradingView.widget({
    "width": "100%",
    "height": 400,
    "locale": "en",
    "darkMode": true,
    "currencies": ["EUR", "USD", "JPY", "GBP", "CHF", "AUD", "CAD"],
    "isTransparent": false
});
</script>
```

---

## Forex Heatmap

**Демо:** https://www.tradingview.com/widget-docs/widgets/heatmaps/forex-heatmap/

Тепловая карта форекс.

```html
<div id="forex-heatmap-widget"></div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
new TradingView.widget({
    "width": "100%",
    "height": 400,
    "locale": "en",
    "darkMode": true,
    "currencies": ["EUR", "USD", "JPY", "GBP"],
    "isTransparent": false
});
</script>
```

---

## Демо в проекте

См. `/home/user_aioc/workspace/tradingview-demos/widgets/heatmaps/`
