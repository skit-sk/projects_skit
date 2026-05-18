# Light Theme

## Когда использовать

Для интеграции графиков в **светлый интерфейс** приложения.

## Ключевые параметры

```javascript
const chart = createChart(container, {
  layout: {
    background: { type: 'solid', color: '#ffffff' },
    textColor: '#333333',
  },
  grid: {
    vertLines: { color: '#e0e0e0' },
    horzLines: { color: '#e0e0e0' },
  },
  width: 800,
  height: 400,
});
```

## Цветовая палитра

| Элемент | Цвет | Описание |
|---------|------|----------|
| background | `#ffffff` | Основной фон |
| text | `#333333` | Текст |
| grid | `#e0e0e0` | Сетка |

## Полный рабочий пример

См. `/tradingview-demos/conditions/light-theme/index.html`

## Версии

Lightweight Charts™ v3.8+, v4.x, v5.x
