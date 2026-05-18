# Архитектура модуля «База MA»

## 1. Схема связей

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                     СТРАТЕГИЯ «БАЗА MA»: СХЕМА ИНТЕГРАЦИИ                     │
│         Moving Average Backtest & Signal Engine для Bitget трекера           │
└──────────────────────────────────────────────────────────────────────────────┘

Внешние источники                     Внутреннее хранение
┌──────────────────┐                ┌──────────────────────────────┐
│   CCXT (Bitget)  │               │    JSONStorage               │
│   fetch_klines()  │───────────────│   data/                     │
│   timeframe=1d   │  save_raw()   │   ├── {obj_id}.json         │
│   limit=500-1000 │               │   ├── card/{sym}_{id}/       │
└──────────────────┘               │   │   ├── {id}.json (card)  │
                                   │   │   ├── {id}_1D.json      │
                                   │   │   └── {id}_RAW.json     │
                                   │   └── ma_backtest/           │
                                   │       └── {run_id}.json      │
                                   └──────────────┬───────────────┘
                                                  │
                    ┌─────────────────────────────┴─────────────────────────────┐
                    │                    TradeAnalyzer                          │
                    │  ┌───────────────────────────────────────────────────┐   │
                    │  │ compute_ma(type, period)                         │   │
                    │  │  ├─ sma()  ── np.mean                           │   │
                    │  │  ├─ ema()  ── экспоненциальное                   │   │
                    │  │  ├─ wma()  ── линейно-взвешенное                 │   │
                    │  │  ├─ hma()  ── Hull (двойное WMA + sqrt)        │   │
                    │  │  ├─ dema() ── двойное EMA                       │   │
                    │  │  ├─ tema() ── тройное EMA                       │   │
                    │  │  ├─ kama() ── Kaufman адаптивное                │   │
                    │  │  └─ zlema() ── EMA со сдвигом                   │   │
                    │  │                                                  │   │
                    │  │ backtest_strategy_X(close, params)              │   │
                    │  │  ├─ single_ma(df, type, period)     [A]        │   │
                    │  │  ├─ crossover(df, fast, slow)       [B]        │   │
                    │  │  ├─ buffer_zone(df, ma, buf)        [C]        │   │
                    │  │  ├─ confirmation(df, ma, days)      [C]        │   │
                    │  │  ├─ triple_ma(df, periods)          [D]        │   │
                    │  │  ├─ with_filters(df, ...)           [E]        │   │
                    │  │  ├─ trailing_stop(df, ...)          [F]        │   │
                    │  │  ├─ golden_cross(df, ...)           [G]        │   │
                    │  │  └─ decade_breakdown(df, strat)     [I]        │   │
                    │  │                                                  │   │
                    │  │ BacktestMetrics                                 │   │
                    │  │  ├─ calc_cagr(equity_curve)                    │   │
                    │  │  ├─ calc_max_dd(equity_curve)                  │   │
                    │  │  ├─ calc_sharpe(returns)                       │   │
                    │  │  ├─ calc_win_rate(trades)                      │   │
                    │  │  └─ to_dict() → {cagr, maxdd, sharpe, ...}    │   │
                    │  │                                                  │   │
                    │  │ ma_signal_generator(df, prices)                │   │
                    │  │  └─→ {composite_signal, confidence, filters}   │   │
                    │  └──────────────────────────────────────────────────┘   │
                    └───────────────────────┬─────────────────────────────────┘
                                            │
                    ┌───────────────────────┴─────────────────────────────────┐
                    │                     routes                              │
                    │  ┌──────────────────────────────────────────────────┐   │
                    │  │ ma_analytics.py  (/ma-analytics)                │   │
                    │  │  ├─ GET /<obj_id>          → шаблон             │   │
                    │  │  ├─ GET /api/<obj_id>      → JSON all data      │   │
                    │  │  ├─ GET /api/<id>/backtest → JSON backtest res  │   │
                    │  │  └─ GET /screener          → JSON all signals   │   │
                    │  │                                                  │   │
                    │  │ processor_1d.py                                  │   │
                    │  │  └─ process() → добавляет MA-анализ в 1D        │   │
                    │  └──────────────────────────────────────────────────┘   │
                    └───────────────────────┬─────────────────────────────────┘
                                            │
                    ┌───────────────────────┴─────────────────────────────────┐
                    │                   templates                             │
                    │  ┌──────────────────────────────────────────────────┐   │
                    │  │ ma_analytics.html                               │   │
                    │  │  ├─ Section 1: MA Lines (Plotly)                │   │
                    │  │  ├─ Section 2: Signals Table                    │   │
                    │  │  ├─ Section 3: Backtest Results                 │   │
                    │  │  ├─ Section 4: Heatmap (Plotly)                 │   │
                    │  │  └─ Section 5: Screener                         │   │
                    │  │                                                  │   │
                    │  │ trade_analytics.html  (добавлена кнопка)        │   │
                    │  │  └─ → «MA анализ» → /ma-analytics/<id>         │   │
                    │  └──────────────────────────────────────────────────┘   │
                    └─────────────────────────────────────────────────────────┘
```

---

## 2. Поток данных (data flow)

### 2.1 Загрузка исторических данных

```
CCXT.fetch_ohlcv(symbol, '1d', since=...)  →  list of [ts, open, high, low, close, volume]
        │
        ▼
ma_data.py: fetch_and_save(symbol, obj_id, limit=500)
        │
        ├──→ storage.save_raw(symbol, obj_id, raw_data)
        └──→ storage.save_1d(symbol, obj_id, processed_days)
```

### 2.2 Генерация MA-аналитики

```
storage.load_1d(symbol, obj_id)
        │
        ▼
TradeAnalyzer.compute_ma('sma', 200)  →  list[float]
TradeAnalyzer.compute_ma('ema', 50)   →  list[float]
TradeAnalyzer.compute_ma('wma', 100)  →  list[float]
...
        │
        ▼
TradeAnalyzer.ma_signal_generator(prices, ma_lines)
        │
        ├──→ price > sma_200? → trend_signal = {direction, confidence}
        ├──→ ema_13 > sma_50? → crossover_signal
        ├──→ rsi > 50?        → filter_passed
        └──→ composite_signal
```

### 2.3 Бэктест

```
TradeAnalyzer.backtest_crossover(close, 'ema', 50, 'sma', 250)
        │
        ├──→ массив сделок (entry_date, exit_date, entry_price, exit_price, pnl)
        ├──→ equity_curve (daily equity)
        ├──→ drawdown_curve
        └──→ BacktestMetrics {CAGR, MaxDD, Sharpe, WinRate, ...}
```

### 2.4 Вывод на фронт

```
GET /ma-analytics/api/<obj_id>
        │
        ▼
JSON Response:
{
    meta: {symbol, current_price, total_days},
    prices: {close, high, low, open, volume},
    ma_lines: {
        sma_50: [...],
        sma_100: [...],
        sma_200: [...],
        ema_50: [...],
        ema_100: [...],
        ema_200: [...],
        ...,
        wma_100: [...],
        hma_50: [...]
    },
    signals: [
        {type, direction, source, confidence, filters_passed}
    ],
    backtest: {
        'single_ma': {best: [...], all: [...], heatmap: {...}},
        'crossover': {best: [...], all: [...], heatmap: {...}},
        'golden_cross': {...},
        'buffer_zone': {...}
    },
    indicators: {rsi: [...], macd: {...}},
    filtered: {
        buffer_zone_5pct: {...},
        confirmation_3d: {...},
        rsi_filter: {...},
        volume_filter: {...}
    }
}
```

---

## 3. Таблица модулей и ответственности

| Модуль | Файл | Ответственность |
|--------|------|----------------|
| TradeAnalyzer | `infographics/trade_analyzer.py` | MA вычисления, все стратегии A-I, метрики, генератор сигналов |
| DashboardCharts | `infographics/charts.py` | Plotly-графики: MA линии, тепловая карта, equity/drawdown |
| MA Data | `api/ma_data.py` | CCXT загрузка истории, кэширование, конвертация в 1D |
| MA Routes | `routes/ma_analytics.py` | Blueprint `/ma-analytics/`, API-ендпоинты, скринер |
| Processor 1D | `routes/processor_1d.py` | Обогащение 1D-данных MA-анализом при обработке |
| Шаблон | `templates/ma_analytics.html` | Фронт: 5 секций, Plotly.js, таблицы |
| Шаблон (кнопка) | `templates/trade_analytics.html` | Ссылка на MA-аналитику |

---

## 4. Зависимости между файлами

```
docs/ma_base_strategy.md          (документация, без зависимостей)
docs/ma_base_architecture.md      (документация, без зависимостей)
docs/ma_base_frontend.md          (документация, без зависимостей)

infographics/trade_analyzer.py    ← numpy, scipy
infographics/charts.py            ← plotly
api/ma_data.py                    ← ccxt, storage
routes/ma_analytics.py            ← flask, storage, trade_analyzer, charts, ma_data
routes/processor_1d.py            ← trade_analyzer
templates/ma_analytics.html       ← plotly.js (CDN)
```

---

## 5. Формат хранения результатов бэктеста

Файл: `data/ma_backtest/{run_id}.json`

```json
{
    "run_id": "uuid",
    "symbol": "BTCUSDT",
    "created_at": "2026-05-10T12:00:00",
    "config": {
        "strategies": ["single_ma", "crossover", "golden_cross"],
        "ma_types": ["sma", "ema", "wma"],
        "periods": [50, 100, 200]
    },
    "results": {
        "single_ma": {
            "best_by_cagr": {"ma_type": "sma", "period": 200, "metrics": {...}},
            "all": [{"ma_type": "sma", "period": 50, "metrics": {...}}, ...]
        },
        "crossover": {
            "best_by_cagr": {"fast": "ema_50", "slow": "sma_250", "metrics": {...}},
            "all": [...]
        }
    }
}
```
