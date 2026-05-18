# Сравнение структуры трёх JSON-файлов карточки

На примере **SKYAI #4** (`45e39003-9fe7-43c1-9fca-996ff92cf56a`)

---

## 1. Файлы

| Файл | Назначение | Путь |
|------|-----------|------|
| `{id}.json` | Основная карточка (FundObj) | `data/card/{symbol}_{uid8}/{id}.json` |
| `{id}_1D.json` | Обработанные дни + аналитика | `data/card/{symbol}_{uid8}/{id}_1D.json` |
| `{id}_RAW.json` | Сырые свечи с Bitget | `data/card/{symbol}_{uid8}/{id}_RAW.json` |

---

## 2. Совпадающие поля (есть во всех трёх)

| Поле | main.json | _1D.json | _RAW.json | Значение совпадает? |
|------|-----------|----------|-----------|-------------------|
| `id` | `45e39…` | `45e39…_1D` | `45e39…_RAW` | **НЕТ** — у каждого свой суффикс |
| `created_at` | `2026-05-11 22:07:59` | `2026-05-11T22:08:57` | `2026-05-11T22:08:57` | **НЕТ** — форматы разные (main без `T`) |
| `updated_at` | `2026-05-11 22:08:57` | `2026-05-11T22:08:57` | `2026-05-11T22:08:57` | **НЕТ** — форматы разные |

> Три файла **не имеют ни одного поля с совпадающим значением** — их общие ключи (`id`, `created_at`, `updated_at`) различаются по содержанию.

---

## 3. Поля в D1 + RAW (нет в main) — связующие

| Поле | _1D.json | _RAW.json |
|------|----------|-----------|
| `parent_id` | `45e39…` | `45e39…` |
| `symbol` | `SKYAI` | `SKYAI` |
| `fetched_at` | `2026-05-11T22:08:57` | `2026-05-11T22:08:57` |

Эти три поля связывают файлы с основной карточкой.

---

## 4. Уникальные поля каждого файла

### 4.1. main.json — агрегированная аналитика (сводка)

```
data.emoji_entry         — входные данные из emoji-строки
  number, symbol, entry_price, entry_date, entry_time,
  volume, pnl_percent, pnl_usdt, result, status

data.emoji_upd           — последнее обновление цены
  current_price, entry_time, pnl_percent, pnl_usdt,
  roe_usdt, result, status, last_updated

data.leverage             — плечо (10)

data.ohlc.current        — OHLC последнего дня
  high, low, body, body_pct, upper_wick, lower_wick, pct, pct_x

data.ohlc.max            — максимум за всё время
  price, pct, pct_x, volatility

data.ohlc.min            — минимум за всё время
  price, pct, pct_x, volatility

data.stats               — счётчик дней
  dn (loss), dp (profit), dn_equal, da (total)

data.ranges.*            — 6 ценовых диапазонов × 4 параметра = 24 поля
  entry_current, entry_low, entry_high,
  current_low, current_high, low_high
  Каждый: pct, prc, days, shortest_days

data.*_datetime          — entry/current/low/high datetime
data.chart_updated       — метка времени обновления
```

### 4.2. _1D.json — посекундная аналитика (детали)

```
days[N].ohlc             — OHLC свечи
  open, high, low, close, body, body_pct, upper_wick, lower_wick

days[N].deviation        — отклонения
  from_entry_usdt, from_entry_pct, from_open_usdt, from_open_pct

days[N].roe_pct          — ROE с плечом (leverage × from_entry_pct)
days[N].pnl_usdt         — PnL в USDT (roe_pct × volume / 100)
days[N].volatility       — волатильность дня (high - low)
days[N].profitable       — boolean
days[N].day_index        — индекс дня

summary.*                — 15 полей статистики
  total_days, profitable_days, loss_days, neutral_days,
  current_roe_pct, current_pnl_usdt, avg_roe_pct, avg_volatility,
  max_profit_day {date, roe_pct, pnl_usdt},
  max_loss_day {date, roe_pct, pnl_usdt},
  max_drawdown_pct, max_drawdown_usdt,
  streak_profit, streak_loss

chart_data[N]            — данные для графика
  date, deviation_pct, profitable
```

### 4.3. _RAW.json — сырые данные (источник)

```
granularity              — "1day"
source                   — "bitget"

candles[N]               — сырые свечи с биржи
  date                   — строка
  timestamp_ms           — таймстемп в миллисекундах
  open, high, low, close — цены
  volume                 — объём торгов (не путать с volume позиции!)

total_candles            — количество свечей
```

---

## 5. День-в-день: как данные перетекают RAW → 1D

Свеча **2026-05-03**:

| RAW → | 1D → | Формула |
|-------|------|---------|
| `open=0.38248` | `ohlc.open=0.38248` | копия |
| `high=0.83639` | `ohlc.high=0.83639` | копия |
| `low=0.3824` | `ohlc.low=0.3824` | копия |
| `close=0.69762` | `ohlc.close=0.69762` | копия |
| — | `body=0.31514` | `\|close - open\|` |
| — | `body_pct=82.39%` | `body / open × 100` |
| — | `upper_wick=0.13877` | `high - max(open, close)` |
| — | `lower_wick=0.00008` | `min(open, close) - low` |
| — | `deviation.from_entry_usdt=0.05566` | `close - entry_price(0.64196)` |
| — | `deviation.from_entry_pct=8.67%` | `(close - entry) / entry × 100` |
| — | `roe_pct=86.7` | `8.67% × leverage(10)` |
| — | `pnl_usdt=0.9971` | `86.7 × volume(1.15) / 100` |
| — | `volatility=0.45399` | `high - low` |

**Ключевое расхождение:** `volume` в RAW — это **объём торгов** монеты (70M SKYAI), а `volume` в 1D/main — это **объём позиции** (1.15 USDT). Это РАЗНЫЕ сущности, одинаковое имя поля.

---

## 6. Производные поля — что откуда берётся

### main.json → из 1D (копия агрегатов)

| Поле в main | Источник в 1D |
|-------------|---------------|
| `data.chart_updated` | `updated_at` (проверка актуальности) |
| `data.ranges.*.pct` | `days[].ohlc.{high, low, close}` |
| `data.stats.dp` | `summary.profitable_days` |
| `data.stats.dn` | `summary.loss_days` |
| `data.stats.da` | `summary.total_days` |
| `data.ohlc.current` | `days[-1].ohlc` |
| `data.ohlc.max.price` | `max(days[].high)` |
| `data.ohlc.min.price` | `min(days[].low)` |

### _1D.json → из RAW (расчёт на каждой свече)

| Поле в 1D | Источник в RAW |
|------------|----------------|
| `days[N].ohlc.open/high/low/close` | `candles[N].open/high/low/close` |
| `days[N].volatility` | `candles[N].high - candles[N].low` |
| `days[N].date` | `candles[N].date` |

---

## 7. Сводная диаграмма данных

```
                    main.json                         _1D.json                        _RAW.json
               ┌──────────────────┐            ┌──────────────────┐            ┌──────────────────┐
  id           │ 45e39… (uuid4)   │   parent   │ 45e39…_1D        │   parent   │ 45e39…_RAW       │
               ├──────────────────┤            ├──────────────────┤            ├──────────────────┤
  metadata     │ obj_type, name   │            │ status, leverage │            │ granularity,     │
               │ created_at       │            │ volume,          │            │ source,          │
               │ updated_at       │            │ created_at,      │            │ total_candles    │
               │                  │            │ fetched_at       │            │                  │
               ├──────────────────┤            ├──────────────────┤            ├──────────────────┤
  entry data   │ emoji_entry:     │  ──copy──  │ entry_price      │            │                  │
               │  symbol,entry,   │            │ entry_date       │            │                  │
               │  volume,number   │            │                  │            │                  │
               ├──────────────────┤            ├──────────────────┤            ├──────────────────┤
  свечи        │ ohlc.current     │  ──agg──   │ days[].ohlc      │  ──copy──  │ candles[].       │
               │ ohlc.max         │            │  open/high/low/  │    4/6     │  open/high/      │
               │ ohlc.min         │            │  close + body/   │            │  low/close       │
               │                  │            │  upper/lowerwick │            │  + timestamp_ms, │
               │                  │            │                  │            │  volume(торги)   │
               ├──────────────────┤            ├──────────────────┤            │                  │
  аналитика    │ ranges.*         │  ──calc──  │ days[].deviation │            │                  │
               │ stats.dp/dn/da   │  ──calc──  │ summary.*        │            │                  │
               │ chart_updated    │  ──sync──  │ chart_data[]     │            │                  │
               └──────────────────┘            └──────────────────┘            └──────────────────┘
```

---

## 8. Расхождения (проблемные места)

| № | Проблема | Где |
|---|----------|-----|
| 1 | `volume` в main/1D = объём позиции, `volume` в RAW = объём торгов | Омонимия имён |
| 2 | `created_at`/`updated_at` в разных форматах: main без `T`, 1D/RAW с `T` | `storage.save()` vs `datetime.now().isoformat()` |
| 3 | `id` у всех трёх файлов разный (main=uuid4, 1D=`{id}_1D`, RAW=`{id}_RAW`) | Связь только через `parent_id` |
| 4 | Данные дублируются: OHLC свечи есть и в RAW, и в 1D (как close), и в main (как current/max/min) | 3 уровня копирования |
| 5 | `chart_updated` в main копируется из `updated_at` в 1D, но при force-пересчёте обновляется в разное время | Потенциальный race condition |

---

**Итог:** `_RAW.json` — неизменяемый слепок API; `_1D.json` — расчётная аналитика; `main.json` — сводка для UI. Данные текут строго **RAW → 1D → main**, без обратной связи.
