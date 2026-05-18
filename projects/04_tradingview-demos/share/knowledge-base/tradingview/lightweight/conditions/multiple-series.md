# Multiple Series

## Когда использовать

Когда нужно **несколько серий на одном графике** — сравнение активов, MA overlay, объём + цена.

## Ключевые параметры

```javascript
// Серия 1: Свечи
const candleSeries = chart.addSeries(CandlestickSeries, {
  upColor: '#26a69a',
  downColor: '#ef5350',
});

// Серия 2: Moving Average 1
const ma1Series = chart.addSeries(LineSeries, {
  color: '#2962FF',
  lineWidth: 1,
});

// Серия 3: Moving Average 2
const ma2Series = chart.addSeries(LineSeries, {
  color: '#ef5350',
  lineWidth: 1,
});
```

## Особенности

- Все серии разделяют одну временную шкалу
- Разные серии могут иметь разные типы (candlestick + line + histogram)
- Для разных диапазонов значений использовать overlay price scale

## Полный рабочий пример

См. `/tradingview-demos/conditions/multiple-series/index.html`

## Версии

Lightweight Charts™ v3.8+, v4.x, v5.x

## Ресурсы

- [Документация](https://tradingview.github.io/lightweight-charts/tutorials/demos/compare-multiple-series)
