# Ticker Widgets

## Ticker Tape

**Демо:** https://www.tradingview.com/widget-docs/widgets/tickers/ticker-tape/

Бегущая строка тикеров (как на бирже).

```html
<div id="ticker-tape-widget"></div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
new TradingView.widget({
    "width": "100%",
    "height": 75,
    "locale": "en",
    "darkMode": true,
    "symbols": [
        ["BTC/USD", "BITSTAMP:BTCUSD"],
        ["ETH/USD", "BITSTAMP:ETHUSD"],
        ["S&P 500", "OANDA:SPX500USD"],
        ["EUR/USD", "OANDA:EURUSD"]
    ],
    "showSymbolLogo": true,
    "showVolume": true,
    "isTransparent": false,
    "displayMode": "adaptive"
});
</script>
```

### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `displayMode` | string | "adaptive", "fixed" |
| `showVolume` | boolean | Показывать объём |
| `showSymbolLogo` | boolean | Показывать логотип символа |

---

## Single Ticker

**Демо:** https://www.tradingview.com/widget-docs/widgets/tickers/single-ticker/

Один тикер с ценой и изменением.

```html
<div id="single-ticker-widget"></div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
new TradingView.widget({
    "width": "100%",
    "height": 100,
    "locale": "en",
    "darkMode": true,
    "symbol": "BITSTAMP:BTCUSD",
    "isTransparent": false,
    "showSymbolLogo": true,
    "showVolume": false,
    "displayMode": "compact"
});
</script>
```

### Web Component

```html
<tv-single-ticker symbol="BTCUSD" width="100%" height="80"></tv-single-ticker>
```

---

## Ticker

**Демо:** https://www.tradingview.com/widget-docs/widgets/tickers/ticker/

Компактный тикер (до 15 символов).

```html
<div id="ticker-widget"></div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
new TradingView.widget({
    "width": "100%",
    "height": 60,
    "locale": "en",
    "darkMode": true,
    "symbols": [
        ["BTCUSD", "BITSTAMP:BTCUSD|1D"],
        ["ETHUSD", "BITSTAMP:ETHUSD|1D"],
        ["SPX", "OANDA:SPX500USD|1D"]
    ],
    "showSymbolLogo": true,
    "isTransparent": false,
    "showVolume": false
});
</script>
```

---

## Демо в проекте

См. `/home/user_aioc/workspace/tradingview-demos/widgets/tickers/`
