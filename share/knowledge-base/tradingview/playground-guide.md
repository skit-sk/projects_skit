# TradingView Playground

Интерактивная площадка для экспериментов с TradingView Widgets и Lightweight Charts™.

## Расположение

- Playground в Sandbox: `/sandbox/tv-playground`
- Исходники: `projects/01_fundament_rf/services/tv_playground.py`
- TradingView Demos: `/static/sandbox/04/index.html`

## Что доступно

| Компонент | Описание | URL |
|---|---|---|
| Widget Gallery | Галерея всех TradingView виджетов | `/static/sandbox/04/index.html` |
| Full Widget Pages | Полноразмерные страницы виджетов | `/static/sandbox/04/widgets-full/*.html` |
| Lightweight Chart Types | Демо типов графиков | `/static/sandbox/04/chart-types/` |
| Lightweight Series Types | Демо типов серий | `/static/sandbox/04/series-types/` |
| Lightweight Conditions | Темы, размеры, локализация | `/static/sandbox/04/conditions/` |

## Подходы к встраиванию виджетов

### Web Components

Используется для виджетов, официально поддерживающих кастомные элементы:

```html
<tv-mini-chart symbol="BINANCE:BTCUSDT" color-theme="dark" locale="en"></tv-mini-chart>
<script type="module" src="https://widgets.tradingview-widget.com/w/en/tv-mini-chart.js"></script>
```

### Dynamic iframe

Универсальный fallback для остальных виджетов:

```javascript
var iframe = document.createElement('iframe');
iframe.src = 'https://www.tradingview-widget.com/embed-widget/advanced-chart/?locale=en#' +
    encodeURIComponent(JSON.stringify({symbol: 'BINANCE:BTCUSDT', theme: 'dark'}));
```

## Регенерация виджетов

После изменений в TradingView API запустите:

```bash
cd projects/04_tradingview-demos
python fix_widgets.py
```

Скрипт обновит:
- `widgets/*/*/index.html` — превью для галереи
- `widgets-full/*.html` — полноразмерные страницы

## Связанные KB

- [04 TradingView Demos](../3-projects/04-tradingview-demos.md)
- [01 Fundament RF / Viz Lab](../3-projects/01-fundament-rf.md)
