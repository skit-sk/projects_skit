# Advanced Topics — Real-time Updates

**Версия:** Lightweight Charts v5.2

## Подходы к Real-time обновлениям

### 1. Периодическое обновление

```javascript
const candleSeries = chart.addSeries(CandlestickSeries);
candleSeries.setData(initialData);

let lastTime = initialData[initialData.length - 1].time;

// Обновление каждые 5 секунд
setInterval(() => {
    const newCandle = fetchLatestCandle();

    if (newCandle.time === lastTime) {
        // Обновляем текущую свечу
        candleSeries.update(newCandle);
    } else {
        // Новая свеча
        candleSeries.update(newCandle);
        lastTime = newCandle.time;
    }
}, 5000);
```

### 2. WebSocket Streaming

```javascript
import { createChart } from 'lightweight-charts';

const chart = createChart(container);
const candleSeries = chart.addSeries(CandlestickSeries);
candleSeries.setData(historicalData);

const ws = new WebSocket('wss://your-data-source.com/stream');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    candleSeries.update({
        time: data.time,
        open: data.open,
        high: data.high,
        low: data.low,
        close: data.close,
    });
};

ws.onclose = () => {
    console.log('Connection closed');
};
```

### 3.券商/Exchange Data Feed

```javascript
import { createChart } from 'lightweight-charts';
import { Datafeeds } from 'lightweight-charts';

class MyDataFeed {
    constructor() {
        this.bars = [];
    }

    getBars(symbolInfo, range, callback) {
        // Fetch historical data
        const bars = fetchHistoricalBars(symbolInfo, range);
        callback(bars);
    }

    subscribeBars(symbolInfo, period, callback) {
        // Subscribe to real-time updates
        const unsubscribe = exchange.onTick(symbolInfo, (tick) => {
            callback({
                time: tick.timestamp,
                open: tick.open,
                high: tick.high,
                low: tick.low,
                close: tick.close,
                volume: tick.volume,
            });
        });

        return unsubscribe;
    }
}

const datafeed = new MyDataFeed();
const chart = new TradingView.widget({
    symbol: 'BTCUSD',
    interval: '1D',
    datafeed: datafeed,
});
```

## Best Practices

### ✅ Делайте

```javascript
// Используйте update() для последней точки
series.update(newPoint);

// Обновляйте чаще, но с разумным интервалом (1-5 сек)
setInterval(() => {
    series.update(getLatestPoint());
}, 2000);
```

### ❌ Не делайте

```javascript
// НЕ используйте setData() для обновлений — это медленно!
setInterval(() => {
    series.setData(allData); // ❌ ПЕРЕСОЗДАЁТ ВЕСЬ ГРАФИК
}, 1000);

// НЕ обновляйте слишком часто (CPU нагрузка)
setInterval(() => {
    series.update(point);
}, 100); // ❌ 100ms слишком часто
```

## Настройки для Real-time

```javascript
const chart = createChart(container, {
    // Отключите анимации для производительности
    layout: {
        animation: false,
    },

    // Оптимизируйте для обновлений
    timeScale: {
        fixLeftEdge: true,
        lockVisibleTimeRangeOnResize: true,
    },
});

// Подписка на видимый диапазон
chart.timeScale().subscribeVisibleTimeRangeChange(() => {
    // Загрузить больше данных если пользователь скроллит
});
```

## Примеры

- [Real-time Demo](https://tradingview.github.io/lightweight-charts/tutorials/demos/realtime-updates)
- [Whitespaces](https://tradingview.github.io/lightweight-charts/tutorials/demos/whitespaces)
- [Infinite History](https://tradingview.github.io/lightweight-charts/tutorials/demos/infinite-history)

## Версии

Lightweight Charts™ v3.8+, v4.x, v5.x
