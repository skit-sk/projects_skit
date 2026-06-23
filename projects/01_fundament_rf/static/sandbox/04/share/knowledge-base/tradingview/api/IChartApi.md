# API Reference — IChartApi

**Версия:** Lightweight Charts v5.2

## Основные методы IChartApi

### Создание серий

| Метод | Описание |
|-------|----------|
| `addSeries(definition, options?)` | Добавить серию |
| `removeSeries(series)` | Удалить серию |
| `getSeries()` | Получить все серии |

```javascript
const chart = createChart(container);

// Добавление серий
const candleSeries = chart.addSeries(CandlestickSeries, {
    upColor: '#26a69a',
    downColor: '#ef5350',
});

const lineSeries = chart.addSeries(LineSeries, {
    color: '#2962FF',
    lineWidth: 2,
});

// Получение серий
const allSeries = chart.getSeries(); // [candleSeries, lineSeries]

// Удаление
chart.removeSeries(candleSeries);
```

### Работа с time scale

| Метод | Описание |
|-------|----------|
| `timeScale()` | Получить ITimeScaleApi |
| `applyOptions(options)` | Применить опции к chart |

```javascript
const timeScale = chart.timeScale();

timeScale.applyOptions({
    rightOffset: 5,
    barSpacing: 12,
    fixLeftEdge: false,
    lockVisibleTimeRangeOnResize: true,
    timeScale: {
        visible: true,
        timeVisible: false,
        secondsVisible: false,
    },
});

// Подписка на изменения
timeScale.subscribeVisibleTimeRangeChange(callback);
timeScale.unsubscribeVisibleTimeRangeChange(callback);
```

### Работа с price scale

| Метод | Описание |
|-------|----------|
| `priceScale(scaleId)` | Получить IPriceScaleApi |
| `applyOptions(options)` | Применить опции |

```javascript
const priceScale = chart.priceScale('right');

priceScale.applyOptions({
    scaleMargins: {
        top: 0.1,
        bottom: 0.1,
    },
});
```

### Resize

```javascript
// Ручной resize
chart.resize(width, height);

// Автоматический (с ResizeObserver)
const resizeObserver = new ResizeObserver(entries => {
    for (const entry of entries) {
        const { width, height } = entry.contentRect;
        chart.resize(width, height);
    }
});
resizeObserver.observe(container);
```

### Утилиты

```javascript
// Удаление chart
chart.remove();

// Сериализация/десериализация
const chartState = chart.serialize();
chart.applyOptions(chartState);

// Получение bounds
const bounds = chart.getChartWidget().bounds;
```

## Полный список интерфейсов

| Интерфейс | Описание |
|-----------|----------|
| `IChartApi` | Главный API графика |
| `ISeriesApi<T>` | API серии данных |
| `ITimeScaleApi` | API временной шкалы |
| `IPriceScaleApi` | API ценовой шкалы |
| `IPaneApi` | API панелей (v5.0+) |
| `IChartApiBase` | Базовый интерфейс |

## Ресурсы

- [Full API Documentation](https://tradingview.github.io/lightweight-charts/docs/api)
- [Interfaces List](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/)
