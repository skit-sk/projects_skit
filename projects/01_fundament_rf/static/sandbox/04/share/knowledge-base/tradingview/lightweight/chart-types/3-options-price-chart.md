# 3. Options Price Chart (Price-Based)

## Когда использовать

Для визуализации **option chains** (цепочек опционов), price distributions или любых данных, где **цена** является более релевантной метрикой, чем время. X-ось = числовые значения цены.

## Ключевые параметры

```javascript
const chart = createOptionsChart(container, {
  layout: {
    background: { type: 'solid', color: '#ffffff' },
    textColor: '#333333',
  },
  width: 800,
  height: 400,
});
```

## Функция

```javascript
createOptionsChart(container, options)
```

## Особенности

- Горизонтальная шкала — **числовая (price)**, не временная
- Идеально для опционных цепочек, где важна цена исполнения (strike price)
- Можно использовать любые числовые данные

## Данные

```javascript
// time = числовое значение (цена), value = какое-то значение
for (let i = 0; i < 1000; i++) {
  data.push({
    time: i * 0.25,           //数值цены
    value: Math.sin(i / 100) + i / 500,
  });
}
```

## Полный рабочий пример

См. `/tradingview-demos/chart-types/3-options-price-chart/index.html`

## Версии

Lightweight Charts™ v4.0+

## Ресурсы

- [Документация](https://tradingview.github.io/lightweight-charts/docs/chart-types#options-chart-price-based)
