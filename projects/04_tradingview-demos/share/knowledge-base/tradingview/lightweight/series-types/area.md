# Area Series

## Когда использовать

Для графика с **заливкой под линией** — визуально привлекательный способ показать тренд.

## Ключевые параметры

```javascript
const series = chart.addSeries(AreaSeries, {
  lineColor: '#2962FF',              // цвет линии
  topColor: 'rgba(41, 98, 255, 0.28)', // цвет заливки сверху
  bottomColor: 'rgba(41, 98, 255, 0.05)', // цвет заливки снизу (градиент)
  lineWidth: 2,                      // толщина линии
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

См. `/tradingview-demos/series-types/area/index.html`

## Версии

Lightweight Charts™ v3.8+, v4.x, v5.x

## Ресурсы

- [Документация](https://tradingview.github.io/lightweight-charts/docs/series-types#area)
