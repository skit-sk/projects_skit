# Candlestick Series

## Когда использовать

Для отображения **японских свечей** (OHLC) — наиболее популярный тип графика для трейдинга.

## Ключевые параметры

```javascript
const series = chart.addSeries(CandlestickSeries, {
  upColor: '#26a69a',           // цвет бычьей свечи
  downColor: '#ef5350',          // цвет медвежьей свечи
  borderVisible: false,          // видимость границы тела свечи
  wickUpColor: '#26a69a',        // цвет фитиля бычьей свечи
  wickDownColor: '#ef5350',      // цвет фитиля медвежьей свечи
});
```

## Data Format

```typescript
CandlestickData {
  time: Time,
  open: number,
  high: number,
  low: number,
  close: number,
}
```

## Полный рабочий пример

См. `/tradingview-demos/series-types/candlestick/index.html`

## Версии

Lightweight Charts™ v3.8+, v4.x, v5.x

## Ресурсы

- [Документация](https://tradingview.github.io/lightweight-charts/docs/series-types#candlestick)
