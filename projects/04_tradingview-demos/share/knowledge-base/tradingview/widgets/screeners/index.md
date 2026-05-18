# Screener Widgets

## Screener

**Демо:** https://www.tradingview.com/widget-docs/widgets/screeners/screener/

Скринер для фильтрации символов по фундаментальным и техническим показателям.

```html
<div id="screener-widget"></div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
new TradingView.widget({
    "width": "100%",
    "height": 600,
    "locale": "en",
    "darkMode": true,
    "dataSource": "stocks_us",
    "defaultFilter": "fundamental",
    "defaultScreen": "most_capitalized",
    "showToolbar": true,
    "enableScrolling": true,
    "isTransparent": false
});
</script>
```

### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `dataSource` | string | "stocks_us", "stocks_uk", "forex", "crypto" |
| `defaultFilter` | string | "fundamental", "technical" |
| `defaultScreen` | string | "most_capitalized", "gainers", "losers" |
| `showToolbar` | boolean | Показывать тулбар |

### Фильтры

- **Fundamental:** P/E, P/S, P/B, Dividend Yield, Market Cap
- **Technical:** RSI, MACD, MA Cross, Price Cross, High/Low

---

## Cryptocurrency Market Screener

**Демо:** https://www.tradingview.com/widget-docs/widgets/screeners/crypto-mkt-screener/

Крипто скринер.

```html
<div id="crypto-screener-widget"></div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
new TradingView.widget({
    "width": "100%",
    "height": 600,
    "locale": "en",
    "darkMode": true,
    "dataSource": "crypto_total",
    "defaultFilter": "market_cap",
    "defaultScreen": "most_capitalized",
    "showToolbar": true,
    "enableScrolling": true,
    "isTransparent": false
});
</script>
```

---

## Демо в проекте

См. `/home/user_aioc/workspace/tradingview-demos/widgets/screeners/`
