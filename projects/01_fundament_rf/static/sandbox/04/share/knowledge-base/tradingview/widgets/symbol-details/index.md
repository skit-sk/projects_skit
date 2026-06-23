# Symbol Details Widgets

## Symbol Info

**Демо:** https://www.tradingview.com/widget-docs/widgets/symbol-details/symbol-info/

Информация о символе: цена, изменения, описание.

```html
<div id="symbol-info-widget"></div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
new TradingView.widget({
    "width": "100%",
    "height": 250,
    "locale": "en",
    "darkMode": true,
    "symbol": "NASDAQ:AAPL",
    "isTransparent": false,
    "showSymbolLogo": true,
    "showCurrencyCode": true
});
</script>
```

### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `symbol` | string | Символ |
| `showCurrencyCode` | boolean | Показывать код валюты |
| `showSymbolLogo` | boolean | Показывать логотип |

---

## Technical Analysis

**Демо:** https://www.tradingview.com/widget-docs/widgets/symbol-details/technical-analysis/

Технический анализ: осцилляторы, Moving Averages.

```html
<div id="technical-analysis-widget"></div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
new TradingView.widget({
    "width": "100%",
    "height": 450,
    "locale": "en",
    "darkMode": true,
    "symbol": "NASDAQ:AAPL",
    "isTransparent": false,
    "showIntervalUI": true,
    "showSymbolLogo": true,
    "showToolbar": true
});
</script>
```

### Отображает

- **Summary:** Общая рекомендация (Buy/Sell/Neutral)
- **Oscillators:** RSI, Stochastic, CCI, Williams %R, MACD, Momentum
- **Moving Averages:** 10 MA, 20 MA, 50 MA, 100 MA, 200 MA

---

## Fundamental Data

**Демо:** https://www.tradingview.com/widget-docs/widgets/symbol-details/fundamental-data/

Фундаментальные данные компании.

```html
<div id="fundamental-data-widget"></div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
new TradingView.widget({
    "width": "100%",
    "height": 450,
    "locale": "en",
    "darkMode": true,
    "symbol": "NASDAQ:AAPL",
    "isTransparent": false,
    "showSymbolLogo": true,
    "showTab": true,
    "showPeriodTabs": true
});
</script>
```

### Показывает

- P/E Ratio
- Market Cap
- Revenue
- EPS
- Dividend Yield
- 52-week Range
- И многое другое

---

## Company Profile

**Демо:** https://www.tradingview.com/widget-docs/widgets/symbol-details/company-profile/

Профиль компании.

```html
<div id="company-profile-widget"></div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
new TradingView.widget({
    "width": "100%",
    "height": 350,
    "locale": "en",
    "darkMode": true,
    "symbol": "NASDAQ:AAPL",
    "isTransparent": false,
    "showSymbolLogo": true
});
</script>
```

---

## Демо в проекте

См. `/home/user_aioc/workspace/tradingview-demos/widgets/symbol-details/`
