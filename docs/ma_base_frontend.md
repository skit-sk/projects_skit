# Фронтенд модуля «База MA»

## 1. Новый шаблон `templates/ma_analytics.html`

Расширяет `base.html`. Всего 5 секций.

### 1.1 Хедер

```html
<h2>📊 База MA: {{ symbol }}</h2>
<div class="ma-meta">
    <span>Цена: ${{ current_price }}</span>
    <span>Дней: {{ total_days }}</span>
    <span>Сигнал: <strong class="signal-{{ composite }}">{{ composite_label }}</strong></span>
    <span>Уверенность: {{ confidence }}%</span>
</div>
```

### 1.2 Section 1 — MA Lines Chart (Plotly)

**Тип:** `Plotly Chart`

**Данные:** OHLC свечи + до 6 MA линий.

**MA линии (конфигурируемые через чекбоксы):**
- SMA 50, 100, 200
- EMA 50, 100, 200
- WMA 100 (опционально)
- HMA 50 (опционально)

**Интерактивность:**
- Чекбоксы: показать/скрыть каждую MA
- Переключатель: свечи / линия
- Range slider по датам

**Chart config:**

```javascript
Plotly.newPlot('maChart', traces, layout, {responsive: true, displayModeBar: true});
```

**Traces:**
```javascript
const traces = [
    {x: dates, close: close, type: 'candlestick', name: 'OHLC'},
    {x: dates, y: sma50, type: 'scatter', name: 'SMA 50', line: {color: '#f59e0b'}},
    {x: dates, y: sma100, type: 'scatter', name: 'SMA 100', line: {color: '#3b82f6'}},
    {x: dates, y: sma200, type: 'scatter', name: 'SMA 200', line: {color: '#ef4444'}},
    {x: dates, y: ema50, type: 'scatter', name: 'EMA 50', line: {color: '#10b981', dash: 'dot'}},
    {x: dates, y: ema100, type: 'scatter', name: 'EMA 100', line: {color: '#8b5cf6', dash: 'dot'}},
    {x: dates, y: ema200, type: 'scatter', name: 'EMA 200', line: {color: '#ec4899', dash: 'dot'}},
];
```

---

### 1.3 Section 2 — Signals Table

**Тип:** HTML-таблица

**Данные:** все активные сигналы из JSON.

| Столбец | Описание |
|---------|----------|
| Тип | `trend`, `crossover`, `filter` |
| Направление | `bullish 🔵` / `bearish 🔴` / `neutral ⚪` |
| Источник | `price > SMA 200`, `EMA 13 × SMA 50`, `RSI > 50` |
| Уверенность | 0-100% с цветовой шкалой |
| Фильтры | иконки пройденных фильтров ✓ / ✗ |

**Дизайн:**
```css
.confidence-high { background: #22c55e; }
.confidence-mid  { background: #f59e0b; }
.confidence-low  { background: #ef4444; }
```

---

### 1.4 Section 3 — Backtest Results

**Тип:** Tabs (вкладки) + таблицы

**Вкладки:**
| Вкладка | Стратегия | Что показываем |
|---------|-----------|---------------|
| A | Single MA | Топ-5 по Sharpe: MA тип, период, CAGR, MaxDD, Sharpe |
| B | Crossover | Топ-5: быстрая, медленная, CAGR, MaxDD, Sharpe |
| C | Buffer Zone | Буфер 1/3/5%, подтверждение 3/5д |
| G | Golden Cross | Классический, контрарный, задержка |
| I | Decades | CAGR/MaxDD по декадам + кризисам |

**Формат таблицы (одинаков для всех вкладок):**

```
| # | Параметры          | CAGR   | MaxDD  | Sharpe | Сделок |
|---|-------------------|--------|--------|--------|--------|
| 1 | SMA 50 / SMA 250  | 6.24%  | 61.94% | 0.373  | 15     |
```

---

### 1.5 Section 4 — Heatmap (Plotly)

**Тип:** Plotly Heatmap

**Данные:** матрица `period × ma_type`, значение = Sharpe или CAGR.

```javascript
const heatmap = {
    z: [
        [0.15, 0.18, 0.12, ...],  // period=5
        [0.22, 0.25, 0.20, ...],  // period=10
        ...
    ],
    x: ['SMA', 'EMA', 'WMA', 'HMA', 'DEMA', 'TEMA', 'KAMA', 'ZLEMA'],
    y: [5, 10, 15, 20, 25, 30, 34, 40, 50, 55, 75, 89, 100, 125, 150, 175, 200, 210, 233, 250, 270, 289, 300],
    type: 'heatmap',
    colorscale: 'RdBu_r',
    zmid: 0
};
```

---

### 1.6 Section 5 — Screener

**Тип:** HTML-таблица

**Данные:** все открытые сделки с MA-сигналами.

| Столбец | Описание |
|---------|----------|
| Символ | BTCUSDT |
| Цена | $65,432 |
| Сигнал | bullish 🔵 |
| Уверенность | 75% |
| SMA 200 | above ✅ |
| Кроссовер | EMA 13 > SMA 50 |
| Фильтры | 4/6 пройдено |
| Действие | `→ Анализ` (ссылка) |

---

## 2. JavaScript-логика

`/static/js/ma_analytics.js`:

```javascript
// Загрузка данных
async function loadMA(symbol, objId) { ... }

// Построение MA-графика
function renderMAChart(data) { ... }

// Переключение видимости MA линий
function toggleMALine(type, period) { ... }

// Построение тепловой карты
function renderHeatmap(data) { ... }

// Рендер таблицы сигналов
function renderSignals(signals) { ... }

// Рендер бэктест-таблиц (по вкладкам)
function renderBacktestTab(tab, data) { ... }

// Скринер
async function loadScreener() { ... }
```

---

## 3. CSS

`/static/css/ma_analytics.css`:

Основные классы:

| Класс | Назначение |
|-------|-----------|
| `.ma-dashboard` | Контейнер |
| `.ma-header` | Хедер с мета-информацией |
| `.ma-section` | Секция с заголовком |
| `.ma-chart-container` | Контейнер Plotly графика |
| `.ma-table` | Таблица сигналов/бэктеста |
| `.ma-tabs` | Вкладки стратегий |
| `.ma-heatmap` | Тепловая карта |
| `.ma-screener` | Скринер |
| `.signal-bullish` | 🔵 |
| `.signal-bearish` | 🔴 |
| `.signal-neutral` | ⚪ |

---

## 4. API контракты

### `GET /ma-analytics/api/<obj_id>`

```json
{
    "meta": {"symbol": "BTCUSDT", "current_price": 65432, "total_days": 365},
    "prices": {"close": [...], "high": [...], "low": [...], "open": [...], "volume": [...]},
    "ma_lines": {
        "sma_50": [...],
        "sma_100": [...],
        "sma_200": [...],
        "ema_50": [...],
        "ema_100": [...],
        "ema_200": [...]
    },
    "signals": [
        {"type": "trend", "direction": "bullish", "source": "price_above_sma_200", "confidence": 85}
    ],
    "backtest": {
        "single_ma": {"best_by_sharpe": {...}, "all": [...]},
        "crossover": {"best_by_sharpe": {...}, "all": [...]},
        "golden_cross": {...},
        "buffer_zone": {...},
        "decades": {...}
    },
    "indicators": {"rsi": [...], "macd": {"macd": [...], "signal": [...], "histogram": [...]}},
    "filtered": {
        "rsi_above_50": true,
        "volume_above_avg": true,
        "slope_positive": false
    }
}
```

### `GET /ma-analytics/screener`

```json
[
    {
        "symbol": "BTCUSDT",
        "obj_id": "...",
        "current_price": 65432,
        "composite_signal": "bullish",
        "confidence": 75,
        "price_above_sma200": true,
        "ema13_above_sma50": true,
        "filters_passed": 4,
        "filters_total": 6
    },
    ...
]
```
