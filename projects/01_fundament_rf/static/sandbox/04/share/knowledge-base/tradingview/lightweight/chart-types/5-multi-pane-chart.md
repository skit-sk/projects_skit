# 5. Multi-Pane Chart

## Когда использовать

Для отображения **нескольких панелей** на одном графике — например, основной график + объём + индикаторы в отдельных панелях.

## Ключевые параметры

```javascript
const chart = createChart(container, {
  addDefaultPane: false,  // отключаем стандартную панель
  layout: {
    background: { type: 'solid', color: '#ffffff' },
    textColor: '#333333',
  },
  width: 800,
  height: 500,
});

// Создаём панели вручную
const mainPane = chart.addPane(1);  // главная панель
const volumePane = chart.addPane(2); // дополнительная панель
```

## Функции

- `chart.addPane(paneIndex)` → `IPaneApi`
- `pane.addSeries(SeriesDefinition, options)` → `ISeriesApi`

## Особенности

- В v5.0+ появился API для работы с панами
- Каждая панель может содержать несколько серий
- Панели синхронизированы по времени
- Полезно для Volume, RSI, MACD и других индикаторов

## Пример

```javascript
// Главная панель: свечи
const mainPane = chart.addPane(1);
const candleSeries = mainPane.addSeries(CandlestickSeries, {
  upColor: '#26a69a',
  downColor: '#ef5350',
});
candleSeries.setData(candleData);

// Вторая панель: объём
const volumePane = chart.addPane(2);
const volumeSeries = volumePane.addSeries(HistogramSeries, {
  color: '#26a69a',
});
volumeSeries.setData(volumeData);
```

## Полный рабочий пример

См. `/tradingview-demos/chart-types/5-multi-pane-chart/index.html`

## Версии

Lightweight Charts™ v5.0+ (Pane API)

## Ресурсы

- [Документация](https://tradingview.github.io/lightweight-charts/docs/panes)
