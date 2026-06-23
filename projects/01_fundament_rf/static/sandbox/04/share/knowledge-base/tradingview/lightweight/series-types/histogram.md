# Histogram Series

## Когда использовать

Для **гистограммы** — объём, разница значений, распределение. Каждый бар может иметь свой цвет.

## Ключевые параметры

```javascript
const series = chart.addSeries(HistogramSeries, {
  color: '#26a69a',       // базовый цвет
  base: 0,                // базовое значение (от которого откладываются бары)
  priceFormat: { type: 'volume' },
  priceScaleId: '',        // ID ценовой шкалы
});
```

## Data Format

```typescript
HistogramData {
  time: Time,
  value: number,
  color?: string,          // опциональный цвет для каждого бара
}
```

## Полный рабочий пример

См. `/tradingview-demos/series-types/histogram/index.html`

## Версии

Lightweight Charts™ v3.8+, v4.x, v5.x

## Ресурсы

- [Документация](https://tradingview.github.io/lightweight-charts/docs/series-types#histogram)
