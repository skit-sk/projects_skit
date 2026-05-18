# Tutorials — Пошаговые руководства

**Версия:** Lightweight Charts v5.2

---

## Список туториалов

| Туториал | Уровень | Описание |
|----------|---------|----------|
| [Price and Volume](#price-and-volume) | Базовый | Свечи + Volume |
| [Real-time Updates](#real-time-updates) | Базовый | Live данные |
| [Legends](#legends) | Средний | Легенды графика |
| [Tooltips](#tooltips) | Средний | Tooltips при наведении |
| [Price Line](#price-line) | Средний | Ценовые линии |
| [Watermark](#watermark) | Простой | Водяной знак |
| [Range Switcher](#range-switcher) | Продвинутый | Переключение таймфреймов |
| [Compare Multiple Series](#compare-multiple-series) | Продвинутый | Несколько серий |
| [Custom Themes](#custom-themes) | Продвинутый | Кастомные темы |

---

## Price and Volume

Базовый пример: свечи + объём в отдельной панели.

```javascript
import { createChart, CandlestickSeries, HistogramSeries } from 'lightweight-charts';

const chart = createChart(container, { layout: { addPane: true } });

const candleSeries = chart.addSeries(CandlestickSeries);
const volumeSeries = chart.addSeries(HistogramSeries, {
    priceFormat: { type: 'volume' },
    priceScaleId: '',
});

candleSeries.setData(candleData);
volumeSeries.setData(volumeData.map(v => ({
    time: v.time,
    value: v.volume,
    color: v.close > v.open ? '#26a69a' : '#ef5350',
})));
```

**Демо:** `/home/user_aioc/workspace/tradingview-demos/chart-types/5-multi-pane-chart/`

---

## Real-time Updates

Обновление графика в реальном времени.

```javascript
const candleSeries = chart.addSeries(CandlestickSeries);
candleSeries.setData(initialData);

// Обновление последней свечи
candleSeries.update({ time: '2024-01-02', open: 100, high: 105, low: 98, close: 103 });

// Добавление новой свечи
candleSeries.update({ time: '2024-01-03', open: 103, high: 110, low: 102, close: 108 });

// Периодическое обновление
setInterval(() => {
    const newData = fetchLatestCandle();
    candleSeries.update(newData);
}, 1000);
```

**Важно:** Не используйте `setData()` для обновлений — это заменяет все данные!

---

## Legends

Отображение легенды при наведении.

```javascript
const legend = document.createElement('div');
legend.style.position = 'absolute';
legend.style.top = '10px';
legend.style.left = '10px';
container.appendChild(legend);

chart.subscribeCrosshairMove(param => {
    if (!param.time || !param.seriesData.size) {
        legend.textContent = '';
        return;
    }

    const candle = param.seriesData.get(candleSeries);
    if (candle) {
        legend.textContent = `O: ${candle.open} H: ${candle.high} L: ${candle.low} C: ${candle.close}`;
    }
});
```

---

## Tooltips

### Floating Tooltip

```javascript
const tooltip = document.createElement('div');
tooltip.className = 'tooltip';
container.appendChild(tooltip);

chart.subscribeCrosshairMove(param => {
    if (!param.time) {
        tooltip.style.display = 'none';
        return;
    }

    const data = param.seriesData.get(candleSeries);
    if (data) {
        tooltip.style.display = 'block';
        tooltip.innerHTML = `
            <div>Time: ${data.time}</div>
            <div>Open: ${data.open}</div>
            <div>High: ${data.high}</div>
            <div>Low: ${data.low}</div>
            <div>Close: ${data.close}</div>
        `;
    }
});
```

---

## Watermark

```javascript
const chart = createChart(container, {
    layout: {
        watermark: {
            visible: true,
            text: 'My Watermark',
            fontSize: 24,
            color: 'rgba(200, 200, 200, 0.5)',
        },
    },
});
```

---

## Custom Themes

```javascript
const chart = createChart(container, {
    layout: {
        background: { type: 'solid', color: '#1e222d' },
        textColor: '#d1d4dc',
    },
    grid: {
        vertLines: { color: '#1e222d' },
        horzLines: { color: '#1e222d' },
    },
    crosshair: {
        vertLine: { color: '#787b86', labelBackgroundColor: '#2962ff' },
        horzLine: { color: '#787b86', labelBackgroundColor: '#2962ff' },
    },
});
```

---

## Дополнительные ресурсы

- [Официальные туториалы](https://tradingview.github.io/lightweight-charts/tutorials/)
- [Demos в workspace](/home/user_aioc/workspace/tradingview-demos/)
- [GitHub plugin-examples](https://github.com/tradingview/lightweight-charts/tree/master/plugin-examples/src/plugins)
