# Dark Theme

## Когда использовать

Для интеграции графиков в **тёмный интерфейс** приложения. Стандартный цвет для TradingView-подобных тем.

## Ключевые параметры

```javascript
const chart = createChart(container, {
  layout: {
    background: { type: 'solid', color: '#131722' },
    textColor: '#d1d4dc',
  },
  grid: {
    vertLines: { color: '#1e222d' },
    horzLines: { color: '#1e222d' },
  },
  crosshair: {
    vertLine: { color: '#787b86', labelBackgroundColor: '#2962ff' },
    horzLine: { color: '#787b86', labelBackgroundColor: '#2962ff' },
  },
  width: 800,
  height: 400,
});
```

## Цветовая палитра

| Элемент | Цвет | Описание |
|---------|------|----------|
| background | `#131722` | Основной фон |
| text | `#d1d4dc` | Текст |
| grid | `#1e222d` | Сетка |
| crosshair | `#787b86` | Перекрестие |

## Полный рабочий пример

См. `/tradingview-demos/conditions/dark-theme/index.html`

## Версии

Lightweight Charts™ v3.8+, v4.x, v5.x
