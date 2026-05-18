# Connecting Data — Обзор

## Способы подключения данных

### 1. Напрямую через setData()

```javascript
series.setData([
  { time: '2024-01-01', value: 100 },
  { time: '2024-01-02', value: 105 },
  // ...
]);
```

### 2. UDF Compatible Datafeed

Готовый адаптер для демо-данных:
```javascript
const datafeed = new Datafeeds.UDFCompatibleDatafeed("https://demo-feed-data.tradingview.com");
new TradingView.widget({ datafeed });
```

### 3. Custom Datafeed API

Кастомная реализация `IExternalDatafeed` интерфейса.

## Форматы данных

| Series Type | Data Format |
|-------------|-------------|
| Candlestick | `{ time, open, high, low, close }` |
| Line/Area | `{ time, value }` |
| Bar | `{ time, open, high, low, close }` |
| Histogram | `{ time, value, color? }` |
| Baseline | `{ time, value }` |

## Time форматы

- `UTCTimestamp` — числовой timestamp
- `BusinessDay` — объект `{ year, month, day }`
- `string` — ISO date string `'2024-01-01'`

## Real-time updates

```javascript
// Добавление новых данных
series.update({ time: '2024-01-03', value: 110 });

// setInterval для симуляции real-time
setInterval(() => {
  series.update(getNextDataPoint());
}, 1000);
```

## Версии

Lightweight Charts™ v3.8+, v4.x, v5.x
