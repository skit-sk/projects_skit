# News Widgets

## Top Stories

**Демо:** https://www.tradingview.com/widget-docs/widgets/news/top-stories/

Новости рынков.

```html
<div id="top-stories-widget"></div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
new TradingView.widget({
    "width": "100%",
    "height": 500,
    "locale": "en",
    "darkMode": true,
    "feedMode": "symbol",
    "symbol": "NASDAQ:AAPL",
    "isTransparent": false,
    "showSymbolLogo": true,
    "showArticleHotlist": false
});
</script>
```

### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `feedMode` | string | "symbol", "market", "all" |
| `symbol` | string | Символ для новостей |
| `showArticleHotlist` | boolean | Показывать горячие статьи |

### Режимы feedMode

| Режим | Описание |
|-------|----------|
| `symbol` | Новости только по выбранному символу |
| `market` | Новости всего рынка |
| `all` | Все новости |

---

## Демо в проекте

См. `/home/user_aioc/workspace/tradingview-demos/widgets/news/`
