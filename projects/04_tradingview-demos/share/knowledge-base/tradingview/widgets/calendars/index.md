# Calendars Widgets

## Economic Calendar

**Демо:** https://www.tradingview.com/widget-docs/widgets/calendars/economic-calendar/

Экономический календарь с событиями.

```html
<div id="economic-calendar-widget"></div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
new TradingView.widget({
    "width": "100%",
    "height": 500,
    "locale": "en",
    "darkMode": true,
    "importanceFilter": "medium,high",
    "currencyFilter": "USD,EUR,GBP",
    "isTransparent": false,
    "showFilter": true,
    "showFilterValues": true
});
</script>
```

### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `importanceFilter` | string | "low,medium,high" |
| `currencyFilter` | string | Валюты через запятую |
| `showFilter` | boolean | Показывать фильтры |
| `countryFilter` | string | Фильтр по странам |

### Важность событий

| Уровень | Описание |
|---------|----------|
| `low` | Низкая важность |
| `medium` | Средняя важность |
| `high` | Высокая важность |

---

## Демо в проекте

См. `/home/user_aioc/workspace/tradingview-demos/widgets/calendars/`
