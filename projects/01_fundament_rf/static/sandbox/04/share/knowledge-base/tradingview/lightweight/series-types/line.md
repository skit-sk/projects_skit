# Line Series

## Когда использовать

Для простого **линейного графика** — отображение изменения цены/значения во времени.

## Ключевые параметры

```javascript
const series = chart.addSeries(LineSeries, {
  color: '#2962FF',        // цвет линии
  lineWidth: 2,            // толщина линии
  lineStyle: LineStyle.Solid, // стиль линии
  crosshairMarkerVisible: true, // маркер в точке перекрестия
});
```

## Data Format

```typescript
LineData {
  time: Time,
  value: number,
}
```

## Полный рабочий пример

См. `/tradingview-demos/series-types/line/index.html`

## Версии

Lightweight Charts™ v3.8+, v4.x, v5.x

## Ресурсы

- [Документация](https://tradingview.github.io/lightweight-charts/docs/series-types#line)
