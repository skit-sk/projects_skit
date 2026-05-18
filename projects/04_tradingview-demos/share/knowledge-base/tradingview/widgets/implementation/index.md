# Widget Implementation Guide

## Способы интеграции

### 1. iframe (классический)

```html
<div id="widget-container"></div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
new TradingView.widget({
    // параметры виджета
});
</script>
```

### 2. Web Component (современный)

```html
<!-- Подключите Web Component library -->
<script src="https://unpkg.com/@tradingview/widgets-core@1.0.0/dist/widgets.core.umd.js"></script>

<!-- Используйте виджет как HTML элемент -->
<tv-advanced-chart symbol="BTCUSD" width="100%" height="500"></tv-advanced-chart>
```

### 3. Lazy Loading

```html
<!-- Отложенная загрузка для производительности -->
<div id="widget-container" data-src="https://www.tradingview.com/widget/"></div>

<script>
const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const container = entry.target;
            const script = document.createElement('script');
            script.src = 'https://s3.tradingview.com/tv.js';
            script.onload = () => {
                new TradingView.widget({
                    container: container,
                    // ... параметры
                });
            };
            document.head.appendChild(script);
            observer.unobserve(container);
        }
    });
});
observer.observe(document.getElementById('widget-container'));
</script>
```

## Параметры темы

```javascript
// Dark theme
{
    "theme": "dark",
    "darkMode": true
}

// Light theme
{
    "theme": "light",
    "darkMode": false
}
```

## Размеры

```javascript
// Фиксированные размеры
{
    "width": 800,
    "height": 500
}

// Адаптивные размеры
{
    "width": "100%",
    "height": 500,
    "autosize": true
}
```

## Локализация

```javascript
{
    "locale": "en"      // English
    "locale": "ru"      // Русский
    "locale": "de"      // Deutsch
    "locale": "ja"      // 日本語
    "locale": "zh"      // 中文
}
```

## Прозрачность

```javascript
{
    "isTransparent": true,  // Прозрачный фон
    "backgroundColor": "transparent"
}
```

## Symbol формат

| Тип | Пример |
|-----|--------|
| Stocks US | `"NASDAQ:AAPL"` |
| Stocks UK | `"LSE:VOD"` |
| Forex | `"OANDA:EURUSD"` |
| Crypto | `"BITSTAMP:BTCUSD"` |
| Indices | `"OANDA:SPX500USD"` |

## Частые ошибки

### ❌ Неправильно

```javascript
// Забыли container_id
new TradingView.widget({
    symbol: "BTCUSD"  // Нет container_id!
});

// Несуществующий символ
new TradingView.widget({
    symbol: "INVALID:SYMBOL"
});
```

### ✅ Правильно

```javascript
new TradingView.widget({
    symbol: "BITSTAMP:BTCUSD",
    container_id: "widget-container"
});
```

## Проверка работоспособности

1. Откройте страницу в браузере
2. Проверьте консоль на ошибки
3. Убедитесь что виджет загружается
4. Проверьте на разных устройствах

## Ресурсы

- [TradingView Widget Demos](https://www.tradingview.com/widget-docs/widgets/)
- [Available Markets](https://www.tradingview.com/widget-docs/markets/)
- [FAQs](https://www.tradingview.com/widget-docs/faq/general)
