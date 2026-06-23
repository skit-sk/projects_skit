# Series Types — Типы серий данных

В этом разделе представлены различные типы серий данных TradingView Lightweight Charts.

## Обзор

| Тип | Серия | Описание | Данные |
|-----|-------|----------|---------|
| Candlestick | `CandlestickSeries` | Японские свечи | `{ time, open, high, low, close }` |
| Line | `LineSeries` | Линейный график | `{ time, value }` |
| Area | `AreaSeries` | Областной график | `{ time, value }` |
| Histogram | `HistogramSeries` | Гистограмма | `{ time, value, color? }` |
| Bar | `BarSeries` | Баровый график | `{ time, open, high, low, close }` |
| Baseline | `BaselineSeries` | С базовой линией | `{ time, value }` |

---

## 1. Candlestick Series

**Файл**: `series-types/candlestick/full.html`

### Описание
Японские свечи (OHLC). Отображают цену открытия, максимум, минимум и закрытие для каждого периода. Цвет свечи зависит от направления движения цены.

### Метод
`chart.addSeries(CandlestickSeries, options)`

### Параметры

| Параметр | Значение | Описание |
|----------|---------|----------|
| `upColor` | `'#26a69a'` | Цвет свечи когда close > open (бычья свеча, цена выросла) |
| `downColor` | `'#ef5350'` | Цвет свечи когда close < open (медвежья свеча, цена упала) |
| `borderVisible` | `false` | Убрать границы тела свечи (верхняя и нижняя линии). Чистый вид без контуров |
| `wickUpColor` | `'#26a69a'` | Цвет фитиля (тени) верхней части бычьей свечи |
| `wickDownColor` | `'#ef5350'` | Цвет фитиля (тени) нижней части медвежьей свечи |

### Формат данных
```typescript
interface CandlestickData {
  time: Time;        // timestamp
  open: number;       // цена открытия
  high: number;      // максимум
  low: number;        // минимум
  close: number;      // цена закрытия
}
```

### Пример
```javascript
const series = chart.addSeries(CandlestickSeries, {
  upColor: '#26a69a',
  downColor: '#ef5350',
  borderVisible: false,
  wickUpColor: '#26a69a',
  wickDownColor: '#ef5350'
});

// Из Binance klines
const candleData = klines.map(k => ({
  time: k[0] / 1000,
  open: parseFloat(k[1]),
  high: parseFloat(k[2]),
  low: parseFloat(k[3]),
  close: parseFloat(k[4])
}));

series.setData(candleData);
```

---

## 2. Line Series

**Файл**: `series-types/line/full.html`

### Описание
Линейный график. Отображает одно значение (value) для каждого времени. Используется для индикаторов, скользящих средних, трендовых линий.

### Метод
`chart.addSeries(LineSeries, options)`

### Параметры

| Параметр | Значение | Описание |
|----------|---------|----------|
| `color` | `'#2962FF'` | Цвет линии графика. Синий цвет по умолчанию в TradingView |
| `lineWidth` | `2` | Толщина линии в пикселях. 1-4px рекомендуется для чёткости |

### Формат данных
```typescript
interface LineData {
  time: Time;
  value: number;
}
```

### Пример
```javascript
const series = chart.addSeries(LineSeries, {
  color: '#2962FF',
  lineWidth: 2
});

// Close price из Binance
const lineData = klines.map(k => ({
  time: k[0] / 1000,
  value: parseFloat(k[4])  // close price
}));

series.setData(lineData);
```

---

## 3. Area Series

**Файл**: `series-types/area/full.html`

### Описание
Областной график (Area Chart). Линия + заливка под ней градиентом до нижней границы. Используется для визуализации изменения значения во времени.

### Метод
`chart.addSeries(AreaSeries, options)`

### Параметры

| Параметр | Значение | Описание |
|----------|---------|----------|
| `lineColor` | `'#2962FF'` | Цвет линии на границе области. Совпадает с topColor для визуальной согласованности |
| `topColor` | `'rgba(41, 98, 255, 0.28)'` | Цвет заливки в верхней части (у линии). Градиент от этого цвета к bottomColor |
| `bottomColor` | `'rgba(41, 98, 255, 0.05)'` | Цвет заливки в нижней части (у границы графика). Практически прозрачный |
| `lineWidth` | `2` | Толщина линии (по умолчанию 1, здесь увеличена для наглядности) |

### Градиент заливки
Цвета `topColor` и `bottomColor` создают вертикальный градиент:
- Верх (рядом с линией): `topColor` — более насыщенный
- Низ (рядом с краем графика): `bottomColor` — почти прозрачный

### Формат данных
```typescript
interface SingleValueData {
  time: Time;
  value: number;
}
```

### Пример
```javascript
const series = chart.addSeries(AreaSeries, {
  lineColor: '#2962FF',
  topColor: 'rgba(41, 98, 255, 0.28)',
  bottomColor: 'rgba(41, 98, 255, 0.05)'
});

const areaData = klines.map(k => ({
  time: k[0] / 1000,
  value: parseFloat(k[4])  // close price
}));

series.setData(areaData);
```

---

## 4. Histogram Series

**Файл**: `series-types/histogram/full.html`

### Описание
Гистограмма. Используется для отображения объёмов (Volume), распределений, частотных данных. Каждый столбец может иметь свой цвет (например, зелёный для восходящих, красный для нисходящих).

### Метод
`chart.addSeries(HistogramSeries, options)`

### Параметры (серия)

| Параметр | Значение | Описание |
|----------|---------|----------|
| `color` | `'#26a69a'` | Цвет по умолчанию для всех столбцов. Переопределяется в данных для отдельных столбцов |
| `base` | `0` | Базовая линия от которой откладываются столбцы. Столбцы выше или ниже в зависимости от значения |
| `priceFormat.type` | `'volume'` | Формат отображения цены (volume добавляет суффиксы K, M, B) |

### Параметры (per-bar colors)

| Condition | Color | Description |
|-----------|-------|-------------|
| close >= open | `'#26a69a'` | Зелёный — объём при росте цены (бычий объём) |
| close < open | `'#ef5350'` | Красный — объём при падении цены (медвежий объём) |

### Формат данных
```typescript
interface HistogramData {
  time: Time;
  value: number;
  color?: string;  // опционально, переопределяет цвет серии
}
```

### Пример
```javascript
const series = chart.addSeries(HistogramSeries, {
  color: '#26a69a',  // цвет по умолчанию
  base: 0
});

// Каждый столбец с цветом
const histData = klines.map(k => {
  const close = parseFloat(k[4]);
  const open = parseFloat(k[1]);
  return {
    time: k[0] / 1000,
    value: parseFloat(k[5]),  // volume
    color: close >= open
      ? '#26a69a'  // зелёный для бычьих
      : '#ef5350'   // красный для медвежьих
  };
});

series.setData(histData);
```

---

## 5. Bar Series

**Файл**: `series-types/bar/full.html`

### Описание
Баровый график (OHLC Bar Chart). Каждый бар отображает цену открытия, максимум, минимум и закрытие. Горизонтальная черта слева — open, справа — close.

### Метод
`chart.addSeries(BarSeries, options)`

### Параметры

| Параметр | Значение | Описание |
|----------|---------|----------|
| `upColor` | `'#26a69a'` | Цвет бара когда close > open (бычий бар, цена выросла) |
| `downColor` | `'#ef5350'` | Цвет бара когда close < open (медвежий бар, цена упала) |

### Структура бара

| Element | Description |
|---------|-------------|
| Top tick | High price (максимум периода) |
| Bottom tick | Low price (минимум периода) |
| Left tick | Open price (цена открытия) |
| Right tick | Close price (цена закрытия) |

### Формат данных
```typescript
interface BarData {
  time: Time;
  open: number;
  high: number;
  low: number;
  close: number;
}
```

### Пример
```javascript
const series = chart.addSeries(BarSeries, {
  upColor: '#26a69a',
  downColor: '#ef5350'
});

const barData = klines.map(k => ({
  time: k[0] / 1000,
  open: parseFloat(k[1]),
  high: parseFloat(k[2]),
  low: parseFloat(k[3]),
  close: parseFloat(k[4])
}));

series.setData(barData);
```

---

## 6. Baseline Series

**Файл**: `series-types/baseline/full.html`

### Описание
График с базовой линией. Области выше и ниже базовой линии заливаются разными цветами. Удобен для отображения отклонений от среднего значения.

### Метод
`chart.addSeries(BaselineSeries, options)`

### Параметры

| Параметр | Значение | Описание |
|----------|---------|----------|
| `baseValue.price` | `50000` | Базовая линия (центр) по оси Y. Значения выше — заливка topColor, ниже — bottomColor |
| `topLineColor` | `'rgba(38, 166, 154, 1)'` | Цвет верхней линии-маркера. Видна только если значение выходит за topFillColor2 |
| `bottomLineColor` | `'rgba(239, 83, 80, 1)'` | Цвет нижней линии-маркера. На графике не отображается, служит для отладки |
| `topFillColor1` | `'rgba(38, 166, 154, 0.28)'` | Первый слой градиента заливки области выше базовой линии (более насыщенный) |
| `topFillColor2` | `'rgba(38, 166, 154, 0.05)'` | Второй слой градиента заливки области выше базовой линии (более прозрачный) |
| `bottomFillColor1` | `'rgba(239, 83, 80, 0.05)'` | Первый слой градиента заливки области ниже базовой линии (более прозрачный) |
| `bottomFillColor2` | `'rgba(239, 83, 80, 0.28)'` | Второй слой градиента заливки области ниже базовой линии (более насыщенный) |

### Принцип работы
```
Цена > baseValue.price (50000)
├── Заливка: градиент от topFillColor1 до topFillColor2
└── Линия: topLineColor (если выходит за край)

Цена < baseValue.price (50000)
├── Заливка: градиент от bottomFillColor1 до bottomFillColor2
└── Линия: bottomLineColor (не отображается на графике)
```

### Градиент заливки
Область выше базовой линии:
- У линии (baseValue): `topFillColor1` (более насыщенный)
- У края графика: `topFillColor2` (более прозрачный)

Область ниже базовой линии:
- У линии (baseValue): `bottomFillColor1` (более прозрачный)
- У края графика: `bottomFillColor2` (более насыщенный)

### Формат данных
```typescript
interface SingleValueData {
  time: Time;
  value: number;
}
```

### Пример
```javascript
const series = chart.addSeries(BaselineSeries, {
  baseValue: { type: 'price', price: 50000 },
  topLineColor: 'rgba(38, 166, 154, 1)',
  topFillColor1: 'rgba(38, 166, 154, 0.28)',
  topFillColor2: 'rgba(38, 166, 154, 0.05)',
  bottomLineColor: 'rgba(239, 83, 80, 1)',
  bottomFillColor1: 'rgba(239, 83, 80, 0.05)',
  bottomFillColor2: 'rgba(239, 83, 80, 0.28)',
});

const baseData = klines.map(k => ({
  time: k[0] / 1000,
  value: parseFloat(k[4])  // close price
}));

series.setData(baseData);
```

### Применение
- Отображение отклонений от средней цены
- Индикаторы импульса (momentum)
- Спреды между активами
- Измерение относительной производительности

---

## Сравнительная таблица

| Series | OHLC | Цвета | Заливка | Использование |
|--------|------|-------|---------|---------------|
| CandlestickSeries | ✓ | up/down | Нет | Цена OHLC |
| LineSeries | Нет | один | Нет | Индикаторы, MA |
| AreaSeries | Нет | один | Да (градиент) | Тренды |
| HistogramSeries | Нет | per-bar | Нет | Volume |
| BarSeries | ✓ | up/down | Нет | Цена OHLC (альтернатива свечам) |
| BaselineSeries | Нет | два (top/bottom) | Да (градиент) | Отклонения от базы |

---

## Цветовые коды

### TradingView стандартные цвета
```javascript
const COLORS = {
  blue: '#2962FF',      // primary
  green: '#26a69a',     // up/bullish
  red: '#ef5350',       // down/bearish
  darkBg: '#131722',    // background
  darkGrid: '#1e222d',  // grid lines
  lightText: '#d1d4dc' // text
};
```

### RGBA варианты для прозрачности
```javascript
const RGBA = {
  green50: 'rgba(38, 166, 154, 0.5)',   // 50% opacity
  red50: 'rgba(239, 83, 80, 0.5)',
  blue28: 'rgba(41, 98, 255, 0.28)',     // 28% opacity (topColor)
  blue05: 'rgba(41, 98, 255, 0.05)'      // 5% opacity (bottomColor)
};
```