# Bar Series

## Когда использовать

Для отображения данных в формате **OHLC баров** — альтернатива свечам.

## Ключевые параметры

```javascript
const series = chart.addSeries(BarSeries, {
  upColor: '#26a69a',     // цвет восходящего бара
  downColor: '#ef5350',   // цвет нисходящего бара
});
```

## Data Format

```typescript
BarData {
  time: Time,
  open: number,
  high: number,
  low: number,
  close: number,
}
```

## Полный рабочий пример

См. `/tradingview-demos/series-types/bar/index.html`

## Версии

Lightweight Charts™ v3.8+, v4.x, v5.x

## Ресурсы

- [Документация](https://tradingview.github.io/lightweight-charts/docs/series-types#bar)
