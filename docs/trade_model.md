# Модель данных сделки — Fundament RF

---

## Часть 1. Визуальное описание структуры

---

### 1.1 Схема объекта Сделка

```
┌─────────────────────────────────────────────────────────────────────┐
│                         СДЕЛКА (Trade)                             │
├─────────────────────────────────────────────────────────────────────┤
│  id                  │ UUID сделки                                 │
│  obj_type            │ "сделка"                                   │
│  name                │ "ETC #10"                                   │
│  created_at          │ Timestamp создания                          │
│  updated_at          │ Timestamp обновления                         │
├─────────────────────────────────────────────────────────────────────┤
│  data                                                            │
│  ├── emoji_entry     │ Параметры входа (статичные)                 │
│  ├── emoji_upd      │ Текущее состояние (динамические)              │
│  ├── ohlc           │ Свечные данные (high/low/body/wick)          │
│  ├── stats          │ Статистика по дням                          │
│  └── chart_updated  │ Timestamp обновления графика                │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 1.2 Визуальная схема страницы Card

```
┌──────────────────────────────────────────────────────────────┐
│                     HEADER / NAV                            │
│  Главная │ Dashboard │ Все графики │ Метрики    │ 🌙        │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    ETC #10  🔄                               │
├──────────────────────────────────────────────────────────────┤
│  #block1-position    │  Position (краткая сводка)              │
│                      │  Low: 7.77 | High: 9.78                │
│                      │  Entry: 8.0995 | Current: 8.44         │
│                      │  PnL: +0.71 USDT (+42.04%)             │
│                      │  Leverage: 10x                         │
├──────────────────────┼──────────────────────────────────────┤
│  #block2-range       │  Price Range Bar                       │
│                      │  [Low] ████████████████ [High]        │
│                      │        │_ENTRY│     │_CURRENT_│        │
├──────────────────────┼──────────────────────────────────────┤
│  emoji-summary       │  🏗️10 🚏ETC 🧾8.0995 📆2026-02-19     │
│  (строка 1)         │  🕒69дн 🧱1.68 🫧35.97 🪙0.6 📦🟢 ⬆️10  │
│  emoji-summary       │  🏗️10 🚏ETC 🧾8.44 📆2026-05-02        │
│  (строка 2)         │  🕒72дн 🧱1.68 🫧42.04 🪙0.71 📦🟢 ⬆️10 │
├──────────────────────┼──────────────────────────────────────┤
│  #block3-distribution│  Days Distribution Bar                │
│                      │  [---dp=66---|dn=6---] [da=72]       │
├──────────────────────┼──────────────────────────────────────┤
│  #current_candle_ohlc│  (hidden)                             │
├──────────────────────┼──────────────────────────────────────┤
│  #block5-critical    │  Critical Levels (hidden)             │
│                      │  Таблица критических уровней          │
├──────────────────────┼──────────────────────────────────────┤
│  #dvcContainer       │  График отклонения цены (Canvas)     │
│                      │  deviation_chart                      │
├──────────────────────┼──────────────────────────────────────┤
│  #ohlcChartContainer │  OHLC Chart (Canvas)                 │
│                      │  Свечной график                        │
└──────────────────────┴──────────────────────────────────────┘
```

---

### 1.3 Блоки карточки Card

| ID | Блок | Описание |
|----|------|----------|
| `block1-position` | **Position** | Краткая сводка: Low/High/Entry/Current/PnL/Leverage |
| `block2-range` | **Range Bar** | Визуальная шкала диапазона цен с маркерами entry и current |
| `emoji-summary` (x2) | **Emoji Summary** | Две строки с эмодзи-краткой (вход и текущее) |
| `block3-distribution` | **Distribution** | Столбчатая диаграмма дней: dp (зелёный) vs dn (красный) |
| `current_candle_ohlc` | **OHLC Data** | Скрытый блок с данными текущей свечи |
| `block5-critical` | **Critical Levels** | Таблица критических ценовых уровней |
| `dvcContainer` | **Deviation Chart** | Canvas-график отклонения цены от входа |
| `ohlcChartContainer` | **OHLC Chart** | Canvas-свечной график |

---

### 1.4 Схема Range Bar

```
[7.77]███████████████████████████████[9.78]
        │ENTRY│              │CURRENT│
        Low                         High
```

---

### 1.5 Схема Distribution Bar

```
[6]███████████████████████████████[66]  (72 дня)
 dn                              dp      da
```

---

## Часть 2. Техническое описание

---

### 2.1 Верхнеуровневые поля JSON

| Поле | Тип | Описание | Источник |
|------|-----|---------|----------|
| `id` | string (UUID) | Уникальный идентификатор сделки | Генерируется при создании |
| `obj_type` | string | Тип объекта | Константа `"сделка"` |
| `name` | string | Название сделки | `"<SYMBOL> #<NUMBER>"` |
| `created_at` | string (timestamp) | Дата создания записи | `datetime.now()` |
| `updated_at` | string (timestamp) | Дата последнего обновления | Обновляется при изменении |

---

### 2.2 `data.emoji_entry` — Входные параметры (статичные)

| Поле | Тип | Описание | Источник |
|------|-----|---------|----------|
| `number` | int | Порядковый номер сделки по символу | Счётчик сделок символа |
| `symbol` | string | Символ актива | BITGET API |
| `entry_price` | float | Цена входа | BITGET API |
| `entry_date` | string | Дата входа | BITGET API |
| `entry_time` | int | Время входа (минуты от начала дня) | BITGET API |
| `volume` | float | Объём позиции (USDT) | Пользовательский ввод |
| `pnl_percent` | float | PnL в % на момент входа | Вычисляется |
| `pnl_usdt` | float | PnL в USDT на момент входа | Вычисляется |
| `result` | string | Результат (эмодзи) | `"🟢"` или `"🔴"` |
| `status` | string | Статус | `"green"` или `"red"` |

---

### 2.3 `data.emoji_upd` — Текущее состояние (динамичные)

| Поле | Тип | Описание | Источник |
|------|-----|---------|----------|
| `current_price` | float | Текущая цена | BITGET API |
| `entry_time` | int | Время входа | Копия из `emoji_entry` |
| `pnl_percent` | float | Текущий PnL в % | Вычисляется |
| `pnl_usdt` | float | Текущий PnL в USDT | Вычисляется |
| `roe_usdt` | float | ROE в USDT | Вычисляется |
| `result` | string | Текущий результат (эмодзи) | Вычисляется |
| `status` | string | Текущий статус | Вычисляется |
| `last_updated` | string | Время последнего обновления | `datetime.now()` |

---

### 2.4 `data.ohlc` — Свечные данные (OHLC)

#### `ohlc.current` — Текущая свеча

| Поле | Тип | Описание | Источник |
|------|-----|---------|----------|
| `high` | float | High свечи | BITGET API |
| `low` | float | Low свечи | BITGET API |
| `body` | float | Body свечи | Вычисляется |
| `body_pct` | float | Body в % | Вычисляется |
| `upper_wick` | float | Upper wick | Вычисляется |
| `lower_wick` | float | Lower wick | Вычисляется |
| `pct` | float | Изменение в % | Вычисляется |
| `pct_x` | float | Изменение в % с плечом | Вычисляется |

#### `ohlc.max` — Максимумы за период

| Поле | Тип | Описание | Источник |
|------|-----|---------|----------|
| `price` | float | Максимальная цена | BITGET API |
| `pct` | float | Макс. % от входа | Вычисляется |
| `pct_x` | float | Макс. % с плечом | Вычисляется |
| `volatility` | float | Волатильность | Вычисляется |

#### `ohlc.min` — Минимумы за период

| Поле | Тип | Описание | Источник |
|------|-----|---------|----------|
| `price` | float | Минимальная цена | BITGET API |
| `pct` | float | Мин. % от входа | Вычисляется |
| `pct_x` | float | Мин. % с плечом | Вычисляется |
| `volatility` | float | Волатильность | Вычисляется |

---

### 2.5 `data.stats` — Статистика по дням

| Поле | Тип | Описание | Формула |
|------|-----|---------|---------|
| `dn` | int | Days Negative — дни с отрицательным результатом | Счётчик где `close < open` |
| `dp` | int | Days Positive — дни с положительным результатом | Счётчик где `close > open` |
| `dn_equal` | int | Days Equal — дни без изменения | Счётчик где `close == open` |
| `da` | int | Days Active — всего дней активности | `dn + dp + dn_equal` |

---

## Часть 3. Формулы расчёта

---

| Метрика | Формула | Пример |
|---------|---------|--------|
| **PnL %** | `((current_price - entry_price) / entry_price) * 100` | `((8.44 - 8.0995) / 8.0995) * 100 = 4.2%` |
| **PnL USDT** | `volume * pnl_percent / 100` | `1.68 * 4.2 / 100 = 0.071` |
| **ROE %** | `pnl_percent * leverage` | `4.2 * 10 = 42%` |
| **Body** | `\|close - open\|` | `\|8.44 - 8.10\| = 0.34` |
| **Upper Wick** | `high - max(open, close)` | `9.78 - 8.44 = 1.34` |
| **Lower Wick** | `min(open, close) - low` | `8.10 - 7.77 = 0.33` |
| **Days Active** | `dn + dp + dn_equal` | `6 + 66 + 0 = 72` |

---

## Часть 4. Источники данных

---

| Данные | Источник | Обновляется |
|--------|----------|-------------|
| `emoji_entry.*` | BITGET API (момент открытия) | Нет |
| `emoji_upd.current_price` | BITGET API | Да |
| `emoji_upd.pnl_*` | Вычисляется | Да |
| `ohlc.current` | BITGET API (1D свечи) | Да |
| `ohlc.max/min` | BITGET API | Да |
| `stats.*` | История цен (1D свечи) | Да |
| `created_at` | `datetime.now()` | Нет |
| `updated_at` | `datetime.now()` | Да |

---

## Часть 5. HTML-структура страницы Card

---

```html
<div class="card" id="cardData" data-obj-id="<uuid>">

    <!-- Block 1: Position -->
    <div id="block1-position" class="block-position"></div>

    <!-- Block 2: Range Bar -->
    <div id="block2-range" class="block-range">
        <div class="range-labels-top">...</div>
        <div class="range-bar-wrapper">
            <div class="range-fill-bg" id="rangeFillBg"></div>
            <div class="range-candles" id="rangeCandles"></div>
            <div class="range-markers" id="rangeMarkers">
                <div class="marker-entry" id="markerEntry">...</div>
                <div class="marker-current" id="markerCurrent">...</div>
            </div>
        </div>
        <div class="range-meta" id="rangeMeta"></div>
    </div>

    <!-- Emoji Summary (x2) -->
    <div class="emoji-summary"><span>🏗️10 🚏ETC ...</span></div>
    <div class="emoji-summary"><span>🏗️10 🚏ETC ...</span></div>

    <!-- Block 3: Distribution -->
    <div id="block3-distribution" class="block-distribution">
        <span class="dn-label" id="dnLabel"></span>
        <div class="dist-bar-wrapper">
            <div class="dist-dn" id="distDn"></div>
            <div class="dist-dp" id="distDp"></div>
            <span class="da-label" id="daLabel"></span>
        </div>
        <span class="dp-label" id="dpLabel"></span>
    </div>

    <!-- Hidden OHLC data -->
    <div id="current_candle_ohlc" style="display:none;"></div>

    <!-- Critical Levels (hidden) -->
    <div id="block5-critical" class="block-critical" style="display:none;">
        <table class="critical-table">...</table>
    </div>

    <!-- Deviation Chart -->
    <div id="dvcContainer">
        <canvas id="dvcChart"></canvas>
    </div>

    <!-- OHLC Chart -->
    <div id="ohlcChartContainer">
        <canvas id="ohlcChart"></canvas>
    </div>
</div>
```

---

## Часть 6. Пример данных (ETC #10)

---

```json
{
  "id": "d1b35262-3b28-423a-ab34-f0ab5f719c57",
  "obj_type": "сделка",
  "name": "ETC #10",

  "data": {
    "emoji_entry": {
      "number": 10,
      "symbol": "ETC",
      "entry_price": 8.0995,
      "entry_date": "2026-02-19",
      "entry_time": 69,
      "volume": 1.68,
      "pnl_percent": 35.97,
      "pnl_usdt": 0.6,
      "result": "🟢",
      "status": "green"
    },

    "emoji_upd": {
      "current_price": 8.44,
      "entry_time": 72,
      "pnl_percent": 42.04,
      "pnl_usdt": 0.71,
      "roe_usdt": 0.42,
      "result": "🟢",
      "status": "green",
      "last_updated": "2026-05-02 00:56"
    },

    "ohlc": {
      "current": {
        "high": 9.78,
        "low": 7.77,
        "body": 0.34,
        "body_pct": 4.2,
        "upper_wick": 1.34,
        "lower_wick": 0.33,
        "pct": 4.2,
        "pct_x": 42.04
      },
      "max": {
        "price": 9.78,
        "pct": 20.75,
        "pct_x": 207.48,
        "volatility": 2.01
      },
      "min": {
        "price": 7.77,
        "pct": -4.07,
        "pct_x": -40.68,
        "volatility": 2.01
      }
    },

    "stats": {
      "dn": 6,
      "dp": 66,
      "dn_equal": 0,
      "da": 72
    },

    "chart_updated": "2026-05-02 00:56"
  },

  "created_at": "2026-04-30 03:59:09.018328",
  "updated_at": "2026-05-02 00:56:27.135321"
}
```

---

## Часть 7. Сводка метрик

---

| Метрика | Вход | Текущее |
|---------|------|---------|
| **Цена** | 8.0995 | 8.44 (+4.2%) |
| **PnL %** | ~0% | 42.04% |
| **PnL USDT** | ~0 | 0.71 |
| **Leverage** | 10x | 10x |
| **Days Active** | 0 | 72 |
| **High** | 8.0995 | 9.78 (+20.75%) |
| **Low** | 8.0995 | 7.77 (-4.07%) |

---

## Путь к файлу

**Сохранено:** `/home/user_aioc/workspace/docs/trade_model.md`

---

## Часть 8. Dashboard — исправления и улучшения

---

### 8.1 PnL Distribution — текст внутри бара

**Проблема:** Текст обрезался при `textposition='outside'`

**Файл:** `infographics/charts.py`

**Решение:**
```python
fig.add_trace(go.Bar(
    textposition='inside',  # вместо 'outside'
    insidetextanchor='middle',
    textfont=dict(color='white', size=8)
))
```

---

### 8.2 Performance Heatmap — hover с ROE% и PnL USDT

**Проблема:** Hover показывал только дату, без полезной информации

**Файл:** `routes/dashboard.py` — функция `generate_stacked_heatmap_html()`

**Решение:**
```html
<div class="stacked-segment"
     style="background:{color}"
     title="{day_str}: ROE {roe:+.1f}%, PnL {pnl:+.2f} USDT">
</div>
```

**Формат hover:** `2026-04-15: ROE +42.0%, PnL 0.71 USDT`

---

### 8.3 Calendar Heatmap — текст на светлых bar'ах

**Проблема:** Белый текст плохо читался на светло-зелёном фоне (`#bbf7d0`)

**Файл:** `static/css/dashboard.css` — класс `.calendar-trade-text`

**Решение:**
```css
.calendar-trade-text {
    color: white;
    text-shadow:
        -1px -1px 0 #000,
        1px -1px 0 #000,
        1px 1px 0 #000,
        -1px 1px 0 #000,
        0 0 4px rgba(0,0,0,0.9);
}
```

**Эффект:** Тёмная обводка вокруг текста для контраста

---

### 8.4 Dashboard URL

**Доступен по:** http://localhost:5000/dashboard/
