# Baseline Series

## Когда использовать

Для графика с **базовой линией** — две области выше/ниже базового значения окрашиваются разными цветами.

## Ключевые параметры

```javascript
const series = chart.addSeries(BaselineSeries, {
  baseValue: { type: 'price', price: 100 },  // базовое значение
  topLineColor: 'rgba(38, 166, 154, 1)',      // цвет верхней линии
  topFillColor1: 'rgba(38, 166, 154, 0.28)', // верхняя заливка 1
  topFillColor2: 'rgba(38, 166, 154, 0.05)', // верхняя заливка 2
  bottomLineColor: 'rgba(239, 83, 80, 1)',    // цвет нижней линии
  bottomFillColor1: 'rgba(239, 83, 80, 0.05)', // нижняя заливка 1
  bottomFillColor2: 'rgba(239, 83, 80, 0.28)', // нижняя заливка 2
});
```

## Data Format

```typescript
SingleValueData {
  time: Time,
  value: number,
}
```

## Полный рабочий пример

См. `/tradingview-demos/series-types/baseline/index.html`

## Версии

Lightweight Charts™ v4.0+, v5.x

## Ресурсы

- [Документация](https://tradingview.github.io/lightweight-charts/docs/series-types#baseline)
