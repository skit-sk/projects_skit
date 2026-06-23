# Watchlist Widgets

## Market Summary

**Демо:** https://www.tradingview.com/widget-docs/widgets/watchlists/market-summary/

Общая сводка рынка.

```html
<div id="market-summary-widget"></div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
new TradingView.widget({
    "width": "100%",
    "height": 450,
    "locale": "en",
    "darkMode": true,
    "market": "stock",
    "dateRange": "1D",
    "autosize": false,
    "showToolbar": true
});
</script>
```

### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `market` | string | "stock", "forex", "crypto", "bond", "index" |
| `dateRange` | string | Диапазон |
| `showToolbar` | boolean | Показывать тулбар |

---

## Market Overview

**Демо:** https://www.tradingview.com/widget-docs/widgets/watchlists/market-overview/

Обзор рынка по категориям.

```html
<div id="market-overview-widget"></div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
new TradingView.widget({
    "width": "100%",
    "height": 600,
    "locale": "en",
    "darkMode": true,
    "groups": [
        {
            "title": "Indices",
            "symbols": [
                ["OANDA:SPX500"],
                ["OANDA:NS100"],
                ["CRYPTOCAP:BTC"],
                ["BITSTAMP:ETHUSD"]
            ],
            "showSymbolLogo": true,
            "showSymbolLabel": true
        }
    ]
});
</script>
```

### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `groups` | array | Массив групп символов |
| `groups[].title` | string | Название группы |
| `groups[].symbols` | array | Массив символов |

---

## Stock Market

**Демо:** https://www.tradingview.com/widget-docs/widgets/watchlists/stock-market/

Обзор биржи: топ gainers, losers, most active.

```html
<div id="stock-market-widget"></div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
new TradingView.widget({
    "width": "100%",
    "height": 450,
    "locale": "en",
    "darkMode": true,
    "market": "brazil",
    "showToolbar": true,
    "showGroupByExchange": true,
    "showSymbolLogo": true,
    "isTransparent": false
});
</script>
```

---

## Market Quotes

**Демо:** https://www.tradingview.com/widget-docs/widgets/watchlists/market-quotes/

Котировки выбранных инструментов.

```html
<div id="market-quotes-widget"></div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
new TradingView.widget({
    "width": "100%",
    "height": 400,
    "locale": "en",
    "darkMode": true,
    "symbols": [
        ["Apple", "NASDAQ:AAPL"],
        ["Microsoft", "NASDAQ:MSFT"],
        ["Google", "NASDAQ:GOOGL"],
        ["Amazon", "NASDAQ:AMZN"]
    ],
    "showSymbolLogo": true,
    "isTransparent": false,
    "showOverly": false
});
</script>
```

---

## Демо в проекте

См. `/home/user_aioc/workspace/tradingview-demos/widgets/watchlists/`
