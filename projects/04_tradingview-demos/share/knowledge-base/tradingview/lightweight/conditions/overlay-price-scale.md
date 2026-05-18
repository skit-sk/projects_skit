# Overlay Price Scale

## Когда использовать

Для индикаторов типа **Volume**, где значения сильно отличаются от основной цены и не должны влиять на масштаб.

## Ключевые параметры

```javascript
// Создаём Volume серию с overlay scale
const volumeSeries = chart.addSeries(HistogramSeries, {
  color: '#26a69a',
  priceScaleId: 'overlay',  // ключевой параметр
});

// Настраиваем отступы overlay scale
volumeSeries.priceScale().applyOptions({
  scaleMargins: { top: 0.8, bottom: 0 },
});
```

## Особенности

- Overlay scale невидим в UI, но позволяет серии отображаться
- Полезно для Volume, RSI, MACD и других индикаторов
- Несколько серий могут использовать один overlay scale

## Полный рабочий пример

См. `/tradingview-demos/conditions/overlay-price-scale/index.html`

## Версии

Lightweight Charts™ v3.8+, v4.x, v5.x

## Ресурсы

- [Документация](https://tradingview.github.io/lightweight-charts/docs/price-scale#create-price-scale)
