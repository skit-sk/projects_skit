# 2. Yield Curve Chart

## Когда использовать

Для визуализации **yield curves** — кривых доходности облигаций или процентных ставок. Горизонтальная ось = срок погашения в месяцах (duration units), линейно распределённая.

## Ключевые параметры

```javascript
const chart = createYieldCurveChart(container, {
  // Layout
  layout: {
    background: { type: 'solid', color: '#ffffff' },
    textColor: '#333333',
  },

  // Специфичные для Yield Curve
  yieldCurve: {
    baseResolution: 1,        // базовый интервал в месяцах
    minimumTimeRange: 10,     // минимальный диапазон
    startTimeRange: 3,        // начальный диапазон
  },

  // Отключение скролла/зума
  handleScroll: false,
  handleScale: false,

  width: 800,
  height: 400,
});
```

## Функция

```javascript
createYieldCurveChart(container, options)
```

## Особенности

- Whitespace игнорируется для crosshair и grid lines
- Специализирован для представления yield curves
- Временная шкала линейна (месяцы/duration units)

## Данные

```javascript
// time = месяцы, value = процентная ставка %
const curveData = [
  { time: 1, value: 5.378 },   // 1 месяц
  { time: 3, value: 5.271 },   // 3 месяца
  { time: 12, value: 4.739 },  // 1 год
  { time: 60, value: 3.887 },  // 5 лет
  { time: 120, value: 4.007 }, // 10 лет
];
```

## Полный рабочий пример

См. `/tradingview-demos/chart-types/2-yield-curve-chart/index.html`

## Версии

Lightweight Charts™ v4.0+

## Ресурсы

- [Документация](https://tradingview.github.io/lightweight-charts/docs/chart-types#yield-curve-chart)
