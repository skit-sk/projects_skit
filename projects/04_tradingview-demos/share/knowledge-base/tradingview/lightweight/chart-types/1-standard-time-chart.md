# 1. Standard Time-Based Chart

## Когда использовать

Стандартный график для отображения финансовых данных (свечи, линии, бары) во времени. Использует `createChart()` — основную функцию библиотеки.

## Ключевые параметры

```javascript
const chart = createChart(container, {
  // Layout
  layout: {
    background: { type: 'solid', color: '#ffffff' },
    textColor: '#333333',
  },

  // Grid
  grid: {
    vertLines: { color: '#e0e0e0' },
    horzLines: { color: '#e0e0e0' },
  },

  // Размеры
  width: 800,
  height: 400,
  // или autoSize: true
});
```

## Функция

```javascript
createChart(container, options)
```

- **container**: `HTMLElement` или `string` (id)
- **options**: `TimeChartOptions` (опционально)

## Возвращает

`IChartApi` — интерфейс для управления графиком

## Типичный код

```javascript
const chart = createChart(document.getElementById('container'), options);

const candlestickSeries = chart.addSeries(CandlestickSeries, {
  upColor: '#26a69a',
  downColor: '#ef5350',
  borderVisible: false,
  wickUpColor: '#26a69a',
  wickDownColor: '#ef5350',
});

candlestickSeries.setData([
  { time: '2024-01-01', open: 100, high: 105, low: 98, close: 103 },
  // ...
]);

chart.timeScale().fitContent();
```

## Полный рабочий пример

См. `/tradingview-demos/chart-types/1-standard-time-chart/index.html`

## Горизонтальная шкала

Time (UTC timestamp) — стандартная временная шкала.

## Версии

Lightweight Charts™ v3.8+, v4.x, v5.x

## Ресурсы

- [Документация](https://tradingview.github.io/lightweight-charts/docs/chart-types#standard-time-based-chart)
- [Getting Started](https://tradingview.github.io/lightweight-charts/docs)
