# Conditions — Настройки и условия

В этом разделе представлены различные настройки графиков: темы, размеры, масштабирование, локализация.

---

## 1. Dark Theme

**Файл**: `conditions/dark-theme/full.html`

### Описание
Тёмная тема оформления TradingView. Цвета фона и текста подобраны для комфортного просмотра графиков.

### Параметры

| Параметр | Значение | Описание |
|----------|---------|----------|
| `layout.background` | `'#131722'` | Цвет фона графика (тёмно-синий, основной цвет темы) |
| `layout.textColor` | `'#d1d4dc'` | Цвет текста на графике (светло-серый) |
| `grid.vertLines.color` | `'#1e222d'` | Цвет вертикальных линий сетки (едва заметный) |
| `grid.horzLines.color` | `'#1e222d'` | Цвет горизонтальных линий сетки (едва заметный) |
| `crosshair.vertLine.color` | `'#787b86'` | Цвет вертикальной линии перекрестия (серый) |
| `crosshair.horzLine.color` | `'#787b86'` | Цвет горизонтальной линии перекрестия (серый) |
| `crosshair.vertLine.labelBackgroundColor` | `'#2962ff'` | Цвет фона подписи вертикальной линии (синий) |
| `crosshair.horzLine.labelBackgroundColor` | `'#2962ff'` | Цвет фона подписи горизонтальной линии (синий) |

### Параметры серии

| Параметр | Значение | Описание |
|----------|---------|----------|
| `lineColor` | `'#2962FF'` | Цвет линии AreaSeries |
| `topColor` | `'rgba(41, 98, 255, 0.28)'` | Цвет заливки вверху области (полупрозрачный синий) |
| `bottomColor` | `'rgba(41, 98, 255, 0.05)'` | Цвет заливки внизу области (почти прозрачный) |

### Crosshair (перекрестие)
Перекрестие — это две линии (вертикальная и горизонтальная), которые появляются при наведении мыши на график. Они помогают определить точные значения цены и времени.

---

## 2. Light Theme

**Файл**: `conditions/light-theme/full.html`

### Описание
Светлая тема оформления. Используется белый фон с тёмным текстом и светло-серой сеткой.

### Параметры

| Параметр | Значение | Описание |
|----------|---------|----------|
| `layout.background` | `'#ffffff'` | Цвет фона графика (белый) |
| `layout.textColor` | `'#333333'` | Цвет текста на графике (тёмно-серый) |
| `grid.vertLines.color` | `'#e0e0e0'` | Цвет вертикальных линий сетки (светло-серый) |
| `grid.horzLines.color` | `'#e0e0e0'` | Цвет горизонтальных линий сетки (светло-серый) |

### Параметры серии

| Параметр | Значение | Описание |
|----------|---------|----------|
| `lineColor` | `'#2962FF'` | Цвет линии AreaSeries |
| `topColor` | `'rgba(41, 98, 255, 0.28)'` | Цвет заливки вверху области |
| `bottomColor` | `'rgba(41, 98, 255, 0.05)'` | Цвет заливки внизу области |

### CSS переменные для стилей
В light theme используются адаптированные цвета для фона страницы:
```css
body {
  background: #fff;
  color: #333;
}
.info-panel {
  background: #f5f5f5;
  border-top: 1px solid #e0e0e0;
}
```

---

## 3. Fixed Size

**Файл**: `conditions/fixed-size/full.html`

### Описание
Фиксированные размеры графиков. Не адаптируются к размеру окна. Каждый chart создаётся отдельно с фиксированными width/height.

### Три графика разных размеров

| Chart | Width | Height | Border Color | Description |
|-------|-------|--------|--------------|-------------|
| Small | `300` | `200` | `#26a69a` | Компактный график для мини-виджетов |
| Medium | `500` | `300` | `#2962ff` | Средний график для дашбордов |
| Large | `800` | `400` | `#ef5350` | Большой график для детального анализа |

### Параметры каждого графика

| Chart | Series | Color | Points |
|-------|--------|-------|--------|
| Small | `LineSeries` | `#26a69a` | 30 точек (первые 30 свечей) |
| Medium | `LineSeries` | `#2962ff` | 50 точек (первые 50 свечей) |
| Large | `LineSeries` | `#ef5350` | 80 точек (все свечи) |

### Пример кода
```javascript
// Создание трёх независимых графиков
const chartSmall = createChart(document.getElementById('container-small'), {
  layout: { background: { type: 'solid', color: '#131722' }, textColor: '#d1d4dc' },
  width: 300,
  height: 200
});
chartSmall.addSeries(LineSeries, { color: '#26a69a' }).setData(lineData.slice(0, 30));

const chartMedium = createChart(document.getElementById('container-medium'), {
  layout: { background: { type: 'solid', color: '#131722' }, textColor: '#d1d4dc' },
  width: 500,
  height: 300
});
chartMedium.addSeries(LineSeries, { color: '#2962ff' }).setData(lineData.slice(0, 50));

const chartLarge = createChart(document.getElementById('container-large'), {
  layout: { background: { type: 'solid', color: '#131722' }, textColor: '#d1d4dc' },
  width: 800,
  height: 400
});
chartLarge.addSeries(LineSeries, { color: '#ef5350' }).setData(lineData);
```

---

## 4. Multiple Series

**Файл**: `conditions/multiple-series/full.html`

### Описание
Несколько серий на одном графике. Candlestick + 2 Moving Averages (MA20, MA50). MA рассчитываются на клиенте из исторических данных.

### Серии

| # | Type | Color | Description |
|---|------|-------|-------------|
| 1 | `CandlestickSeries` | up: `#26a69a` / down: `#ef5350` | Японские свечи BTCUSDT OHLC |
| 2 | `LineSeries` | `#2962FF` | MA20 (20-периодная скользящая средняя) |
| 3 | `LineSeries` | `#ef5350` | MA50 (50-периодная скользящая средняя) |

### Формулы MA

| MA | Formula | Description |
|----|---------|-------------|
| MA20 | `sum(last 20 closes) / 20` | Краткосрочный тренд (чувствительна) |
| MA50 | `sum(last 50 closes) / 50` | Долгосрочный тренд (менее чувствительна) |

### Пример кода
```javascript
// MA20: скользящая средняя за 20 периодов
const ma20 = klines.map((k, i) => {
  let sum = 0;
  for (let j = Math.max(0, i - 19); j <= i; j++) {
    sum += parseFloat(klines[j][4]);  // close price
  }
  return {
    time: k[0] / 1000,
    value: sum / Math.min(i + 1, 20)
  };
});

// MA50: скользящая средняя за 50 периодов
const ma50 = klines.map((k, i) => {
  let sum = 0;
  for (let j = Math.max(0, i - 49); j <= i; j++) {
    sum += parseFloat(klines[j][4]);
  }
  return {
    time: k[0] / 1000,
    value: sum / Math.min(i + 1, 50)
  };
});

// Добавляем все серии на один график
chart.addSeries(CandlestickSeries, {...}).setData(candleData);
chart.addSeries(LineSeries, { color: '#2962FF' }).setData(ma20);
chart.addSeries(LineSeries, { color: '#ef5350' }).setData(ma50);
```

### Применение
- Трендовые индикаторы (MA, EMA)
- Сравнение нескольких активов
- Наложение индикаторов на цену

---

## 5. Overlay Price Scale

**Файл**: `conditions/overlay-price-scale/full.html`

### Описание
Объём (Volume) отображается на отдельной шкале с `priceScaleId: 'overlay'`. Шкала объёма располагается в верхней части графика.

### Серии

| Series | Type | Price Scale | Description |
|--------|------|-------------|-------------|
| 1 | `CandlestickSeries` | default | Цена BTCUSDT на основной шкале |
| 2 | `HistogramSeries` | `'overlay'` | Volume на overlay шкале (верхние 20%) |

### Overlay Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `volumeSeries.priceScale().scaleMargins.top` | `0.8` | Верхняя граница overlay шкалы (80% от верха) |
| `volumeSeries.priceScale().scaleMargins.bottom` | `0` | Нижняя граница overlay шкалы (0% = начинается от верха) |

### Цвета

| Series | Up Color | Down Color | Description |
|--------|----------|------------|-------------|
| CandlestickSeries | `#26a69a` | `#ef5350` | Цвета свечей |
| HistogramSeries (up) | `rgba(38,166,154,0.5)` | — | Объём при росте цены (полупрозрачный зелёный) |
| HistogramSeries (down) | — | `rgba(239,83,80,0.5)` | Объём при падении цены (полупрозрачный красный) |

### Пример кода
```javascript
// Основная серия — свечи
chart.addSeries(CandlestickSeries, {
  upColor: '#26a69a',
  downColor: '#ef5350',
  borderVisible: false
}).setData(candleData);

// Volume — histogram с overlay price scale
const volumeSeries = chart.addSeries(HistogramSeries, {
  color: '#26a69a'  // цвет по умолчанию
});

// Настраиваем overlay шкалу
volumeSeries.priceScale().applyOptions({
  scaleMargins: {
    top: 0.8,   // начинается от 80% высоты (сверху)
    bottom: 0    // до 0% (до самого верха)
  }
});

// Данные с цветом для каждого бара
volumeSeries.setData(klines.map(k => ({
  time: k[0] / 1000,
  value: parseFloat(k[5]),
  color: parseFloat(k[4]) >= parseFloat(k[1])
    ? 'rgba(38, 166, 154, 0.5)'
    : 'rgba(239, 83, 80, 0.5)'
})));
```

### Как работает overlay
```
Высота графика (100%)
├── 0% - 80% (0.8): Candlestick (цена)
└── 80% - 100%: Histogram (volume overlay)
```

---

## 6. AutoSize Responsive

**Файл**: `conditions/autosize-responsive/full.html`

### Описание
Автоматическое изменение размера графика при изменении размеров окна браузера. Использует `autoSize: true` и внутренний ResizeObserver.

### Параметры

| Parameter | Value | Description |
|-----------|-------|-------------|
| `autoSize` | `true` | Включить автоматическое изменение размера (без width/height) |
| `width` | не указывается | Не указывается — размер контролируется autoSize |
| `height` | не указывается | Не указывается — ResizeObserver управляет размером |

### Преимущества autoSize
- График автоматически заполняет контейнер
- Не нужен обработчик resize
- Встроенный ResizeObserver отслеживает изменения

### Пример кода
```javascript
const chart = createChart(document.getElementById('container'), {
  layout: {
    background: { type: 'solid', color: '#131722' },
    textColor: '#d1d4dc'
  },
  autoSize: true  // НЕ указываем width и height
});

// Не нужен window.addEventListener('resize', ...)
```

### Сравнение подходов

| Approach | Parameters | Resize Handler |
|----------|------------|----------------|
| Manual | `width: window.innerWidth, height: window.innerHeight * 0.7` | Нужен |
| autoSize | `autoSize: true` | Не нужен |

---

## 7. Locale i18n

**Файл**: `conditions/locale-i18n/full.html`

### Описание
Локализация графика: русская локаль (`ru-RU`), формат даты `dd/MM/yy`, видимое время на временной шкале.

### Параметры

| Parameter | Value | Description |
|-----------|-------|-------------|
| `localization.locale` | `'ru-RU'` | Локаль для форматирования дат (русский язык) |
| `localization.dateFormat` | `'dd/MM/yy'` | Формат даты: день/месяц/год (25/04/26) |
| `timeScale.timeVisible` | `true` | Показывать время на временной шкале |
| `timeScale.secondsVisible` | `false` | Не показывать секунды (только часы:минуты) |

### Layout & Series Colors

| Parameter | Value | Description |
|-----------|-------|-------------|
| `layout.background` | `'#131722'` | Цвет фона |
| `layout.textColor` | `'#d1d4dc'` | Цвет текста |
| `series.lineColor` | `'#2962FF'` | Цвет линии AreaSeries |
| `series.topColor` | `'rgba(41,98,255,0.28)'` | Цвет заливки вверху |
| `series.bottomColor` | `'rgba(41,98,255,0.05)'` | Цвет заливки внизу |

### Пример кода
```javascript
const chart = createChart(container, {
  layout: {
    background: { type: 'solid', color: '#131722' },
    textColor: '#d1d4dc'
  },
  // Локализация
  localization: {
    locale: 'ru-RU',
    dateFormat: 'dd/MM/yy'
  },
  // Временная шкала
  timeScale: {
    timeVisible: true,      // показывать время
    secondsVisible: false    // НЕ показывать секунды
  },
  width: window.innerWidth,
  height: window.innerHeight * 0.7
});

// Даты отображаются в формате dd/MM/yy
const firstDate = new Date(first.time * 1000).toLocaleDateString('ru-RU');
// Пример: "25/04/26"
```

### Доступные локали
- `'en-US'` — английский (США)
- `'ru-RU'` — русский
- `'de-DE'` — немецкий
- `'ja-JP'` — японский
- И многие другие

### Форматы даты
- `'dd/MM/yy'` — 25/04/26
- `'MM/dd/yyyy'` — 04/25/2026
- `'yyyy-MM-dd'` — 2026-04-25

---

## Сравнительная таблица

| Condition | Key Feature | Use Case |
|-----------|-------------|----------|
| Dark Theme | Тёмный фон | Ночная работа, AMOLED |
| Light Theme | Светлый фон | Дневная работа, читаемость |
| Fixed Size | Фиксированные px | Виджеты, API embedding |
| Multiple Series | N серий на графике | Индикаторы, сравнения |
| Overlay Price Scale | Volume сверху | Объёмы на свечах |
| AutoSize Responsive | Авто-Resize | Адаптивные лейауты |
| Locale i18n | Локализация | Не-английские пользователи |