# Chart Types — Типы графиков

В этом разделе представлены различные типы графиков TradingView Lightweight Charts.

## 1. Standard Time Chart

**Файл**: `1-standard-time-chart/full.html`

### Описание
Стандартный time-based график. Горизонтальная шкала — UTC timestamp. Используется для свечей, линий, баров — любых финансовых данных по времени.

### Метод
`createChart()` — базовый метод создания графика

### Параметры

| Параметр | Значение | Описание |
|----------|---------|----------|
| `layout.background` | `'#131722'` | Цвет фона графика (тёмно-синий, primary dark theme) |
| `layout.textColor` | `'#d1d4dc'` | Цвет текста на графике (подписи осей, легенда) |
| `grid.vertLines.color` | `'#1e222d'` | Цвет вертикальных линий сетки (менее контрастный, фоновый) |
| `grid.horzLines.color` | `'#1e222d'` | Цвет горизонтальных линий сетки (менее контрастный, фоновый) |
| `width` | `window.innerWidth` | Ширина графика = ширина окна браузера |
| `height` | `70vh` | Высота графика = 70% от высоты окна (30%留给 info panel) |

### Параметры серии CandlestickSeries

| Параметр | Значение | Описание |
|----------|---------|----------|
| `upColor` | `'#26a69a'` | Цвет бычьей свечи (close > open) — зелёный |
| `downColor` | `'#ef5350'` | Цвет медвежьей свечи (close < open) — красный |
| `borderVisible` | `false` | Убрать границы тела свечи для чистого вида |
| `wickUpColor` | `'#26a69a'` | Цвет фитиля (тени) верхней части бычьей свечи |
| `wickDownColor` | `'#ef5350'` | Цвет фитиля (тени) нижней части медвежьей свечи |

### Структура данных
```javascript
// Binance API klines format
[
  [开盘时间, 开盘价, 最高价, 最低价, 收盘价, 成交量, ...],
  [1699004400000, 37500.00, 37600.00, 37400.00, 37550.00, 1234.5678, ...],
  ...
]

// Преобразование в CandlestickData
{
  time: kline[0] / 1000,  // timestamp в секундах
  open: parseFloat(kline[1]),
  high: parseFloat(kline[2]),
  low: parseFloat(kline[3]),
  close: parseFloat(kline[4])
}
```

### Особенности
- Использует 200 свечей для детального отображения
- `chart.timeScale().fitContent()` — автоматически подгоняет диапазон
- Обработчик resize перерисовывает график при изменении окна

---

## 2. Yield Curve Chart

**Файл**: `2-yield-curve-chart/full.html`

### Описание
График кривой доходности для облигаций и процентных ставок. Горизонтальная шкала — линейная (месяцы/duration units). X-ось = срок погашения в месяцах.

### Метод
`createYieldCurveChart()` — специализированный метод для кривых доходности

### Параметры

| Параметр | Значение | Описание |
|----------|---------|----------|
| `yieldCurve.baseResolution` | `1` | Базовое разрешение временной шкалы (1 месяц) |
| `yieldCurve.minimumTimeRange` | `10` | Минимальный диапазон шкалы времени (месяцев) |
| `yieldCurve.startTimeRange` | `3` | Начальный диапазон времени (стартовая точка) |
| `handleScroll` | `false` | Отключить прокрутку графика (фиксированный вид) |
| `handleScale` | `false` | Отключить масштабирование графика (фиксированный вид) |

### Пример данных (US Treasury Yields)
```javascript
[
  { time: 1, value: 5.378 },   // 1 месяц
  { time: 3, value: 5.271 },   // 3 месяца
  { time: 12, value: 4.739 }, // 1 год
  { time: 60, value: 3.887 },  // 5 лет
  { time: 120, value: 4.007 }, // 10 лет
  { time: 360, value: 4.290 }  // 30 лет
]
```

### Особенности
- Специальный тип графика для финансовых инструментов с фиксированным доходом
- Временная шкала представляет duration/maturity в месяцах
- Не использует реальные данные — синтетические данные для демонстрации

---

## 3. Options Price Chart

**Файл**: `3-options-price-chart/full.html`

### Описание
График для опционов и цепных таблиц (option chains). Горизонтальная шкала — Price (числовая). X-ось = цена (страйк). Используется для распределений цен и probability modeling.

### Метод
`createOptionsChart()` — специализированный метод для опционов

### Параметры

| Параметр | Значение | Описание |
|----------|---------|----------|
| `layout.background` | `'#131722'` | Цвет фона графика |
| `layout.textColor` | `'#d1d4dc'` | Цвет текста на графике |
| `series.color` | `'#2962FF'` | Цвет линии на графике |
| `series.lineWidth` | `2` | Толщина линии |

### X-axis scale — Price levels
Горизонтальная ось представляет числовые значения цен (страйки), а не время.

### Y-axis scale — Implied Volatility
Вертикальная ось представляет подразумеваемую волатильность в процентах.

### Пример данных (sin-based simulation)
```javascript
for (let i = 0; i < 100; i++) {
  data.push({
    time: i * 0.5,                    // price level (не время!)
    value: Math.sin(i / 10) * 10 + 100  // implied volatility
  });
}
```

---

## 4. Custom Horizontal Scale

**Файл**: `4-custom-horizontal-scale/full.html`

### Описание
Пример использования данных Fibonacci sequence для отображения на графике. Индексы Фибоначчи (0-10) по оси X, значения чисел Фибоначчи по оси Y.

### Метод
`createChart()` — стандартный метод (кастомный scale behavior удалён для совместимости)

### Параметры

| Параметр | Значение | Описание |
|----------|---------|----------|
| `layout.background` | `'#131722'` | Цвет фона графика |
| `layout.textColor` | `'#d1d4dc'` | Цвет текста |
| `grid.vertLines.color` | `'#1e222d'` | Цвет вертикальных линий сетки |
| `grid.horzLines.color` | `'#1e222d'` | Цвет горизонтальных линий сетки |
| `series.color` | `'#2962FF'` | Цвет линии графика |
| `series.lineWidth` | `2` | Толщина линии |

### Данные (Fibonacci Sequence)
```javascript
[
  { time: 0, value: 0 },
  { time: 1, value: 1 },
  { time: 2, value: 1 },
  { time: 3, value: 2 },
  { time: 4, value: 3 },
  { time: 5, value: 5 },
  { time: 6, value: 8 },
  { time: 7, value: 13 },
  { time: 8, value: 21 },
  { time: 9, value: 34 },
  { time: 10, value: 55 }
]
```

---

## 5. Multi-Pane Chart

**Файл**: `5-multi-pane-chart/full.html`

### Описание
График с несколькими панелями (мультипанельный). Верхняя панель — свечи BTCUSDT, нижняя — Volume гистограмма. API добавлен в v5.0.

### Метод
`createChart()` + `addPane()` — комбинация методов для создания нескольких панелей

### Параметры графика

| Параметр | Значение | Описание |
|----------|---------|----------|
| `addDefaultPane` | `false` | Отключить создание панели по умолчанию (создаём свои) |
| `width` | `window.innerWidth` | Ширина графика |
| `height` | `70vh` | Высота графика (70% окна) |
| `layout.background` | `'#131722'` | Цвет фона |
| `layout.textColor` | `'#d1d4dc'` | Цвет текста |

### Конфигурация панелей

| Панель | Тип | Данные | Описание |
|--------|-----|--------|----------|
| Pane 1 | `CandlestickSeries` | BTCUSDT OHLC | Главная панель с японскими свечами |
| Pane 2 | `HistogramSeries` | Volume | Дополнительная панель с объёмами |

### Пример кода
```javascript
// Создаём график без默认 pane
const chart = createChart(container, {
  addDefaultPane: false,
  // ... other options
});

// Главная панель (свечи)
const mainPane = chart.addPane(1);
mainPane.addSeries(CandlestickSeries, {
  upColor: '#26a69a',
  downColor: '#ef5350',
  // ...
}).setData(candleData);

// Панель объёмов
const volumePane = chart.addPane(2);
volumePane.addSeries(HistogramSeries, {
  color: '#26a69a'
}).setData(volumeData);
```

### Цвета серий

| Параметр | Значение | Описание |
|----------|---------|----------|
| `CandlestickSeries.upColor` | `#26a69a` | Цвет бычьей свечи |
| `CandlestickSeries.downColor` | `#ef5350` | Цвет медвежьей свечи |
| `CandlestickSeries.borderVisible` | `false` | Убрать границы тела свечи |
| `CandlestickSeries.wickUpColor` | `#26a69a` | Цвет фитиля вверх |
| `CandlestickSeries.wickDownColor` | `#ef5350` | Цвет фитиля вниз |
| `HistogramSeries.up color` | `rgba(38,166,154,0.5)` | Объём при росте цены (полупрозрачный зелёный) |
| `HistogramSeries.down color` | `rgba(239,83,80,0.5)` | Объём при падении цены (полупрозрачный красный) |

### Данные Volume
```javascript
const volumeData = klines.map(k => ({
  time: k[0] / 1000,
  value: parseFloat(k[5]),  // объём из kline[5]
  color: parseFloat(k[4]) >= parseFloat(k[1])
    ? 'rgba(38, 166, 154, 0.5)'  // зелёный если close >= open
    : 'rgba(239, 83, 80, 0.5)'    // красный если close < open
}));
```

---

## Общие параметры для всех chart types

### Layout
```javascript
layout: {
  background: { type: 'solid', color: '#131722' },
  textColor: '#d1d4dc'
}
```

### Grid
```javascript
grid: {
  vertLines: { color: '#1e222d' },
  horzLines: { color: '#1e222d' }
}
```

### Width/Height
```javascript
// Фиксированные
width: 800,
height: 400

// Или адаптивные
width: window.innerWidth,
height: window.innerHeight * 0.7

// Или autoSize
autoSize: true
```