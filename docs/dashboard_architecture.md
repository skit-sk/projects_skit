# Архитектура дашборда API3 #4

## Источники данных

| Файл | Содержание |
|------|-----------|
| `data/{id}.json` | CARD — сделка: entry_price, leverage, volume, stats |
| `data/card/{symbol}_{id}/{id}_1D.json` | 134 дня: roe_pct, pnl_usdt, volatility, deviation, ohlc |
| `data/card/{symbol}_{id}/{id}_RAW.json` | OHLCV свечи: open/high/low/close/volume |

## Движок аналитики (`infographics/trade_analyzer.py`)

```
TradeAnalyzer
├── load_data(symbol, obj_id)
│   ├── storage.load_1d(symbol, obj_id) → days[134]
│   └── storage.load_raw(symbol, obj_id) → candles[134]
├── compute_rsi(prices, 14)
├── compute_macd(prices, 12, 26, 9)
├── compute_ema(prices, period)
├── compute_ema_3_zones(prices) → ema9, ema21, ema55
├── compute_liquidation_zones(entry, leverage, candles)
│   └── liq_price = entry / (1 - 1/leverage)
│   └── days_where low < liq_price → risk markers
├── compute_open_interest(volumes) → OI simulated
└── find_pivot_points(data, column, window)
    └── scipy.signal.argrelextrema → all local extrema
```

## Структура дашборда (HTML + Plotly)

```
┌─────────────────────────────────────────────────────┐
│ БЛОК 1: KPI (7 карточек)                            │
│ Entry: 0.2992 | ROE: 280% | PnL: +1.01             │
│ Leverage: 10x | Volatility: 2.75% | Win: 60% | 134d│
├─────────────────────────────────────────────────────┤
│ БЛОК 2: ОСНОВНОЙ ГРАФИК (Plotly make_subplots)     │
│ ┌─────────────────────────────────────────────────┐ │
│ │ ████ Vertical Liquidation Bars (top inside)     │ │
│ ├─────────────────────────────────────────────────┤ │
│ │ 📊 OHLC Candles (background)                    │ │
│ │ ─── ROE line (right axis, gradient color)       │ │
│ │ ··· Volatility % (dashed)                       │ │
│ │ ═══ Liquidation ~0.2693 (red heatmap line)      │ │
│ │ ═══ Entry 0.2992 (purple)                       │ │
│ │ ═══ Max 0.54 / Min 0.25 (green/red)            │ │
│ ├─────────────────────────────────────────────────┤ │
│ │ ██ Volume (histogram, right scale)              │ │
│ └─────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────┤ │
│ БЛОК 3: ИНДИКАТОРЫ (Plotly, synced X axis)        │
│ ┌─────────────────────────────────────────────────┐ │
│ │ RSI(14) ─── blue line, zones 30/70 shaded      │ │
│ ├─────────────────────────────────────────────────┤ │
│ │ MACD histogram (green/red) + signal (orange)   │ │
│ ├─────────────────────────────────────────────────┤ │
│ │ EMA9 ─── cyan / EMA21 ── yellow / EMA55 pink   │ │
│ │ OI ······ purple dotted                         │ │
│ └─────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────┤
│ БЛОК 4: ТАБЛИЦА ЭКСТРЕМУМОВ                        │
│ Date | Price | ROE | Volume | Volatility | Type    │
└─────────────────────────────────────────────────────┘
```

## Поток данных

```
RAW.Close → RSI(14), MACD(12,26,9), EMA(9,21,55)
RAW.Volume → OI(simulated), Volume histogram
RAW.High/Low → Liquidation zones, Pivot points

1D.roe_pct → ROE line, Pivot points
1D.volatility → Volatility line (%)
1D.pnl_usdt → KPI, Streaks analysis
1D.ohlc.body/upper_wick/lower_wick → Wick analysis

CARD.entry_price → Liquidation price = entry / (1 - 1/leverage)
CARD.leverage → Risk calculations
CARD.stats → Win/Loss distribution
```

## Маршруты

| Endpoint | Описание |
|----------|----------|
| `GET /trade-analytics/api/<obj_id>` | JSON со всеми индикаторами |
| `GET /trade-analytics/dashboard/<obj_id>` | Полный HTML дашборд |

## Зависимости

- `plotly` — визуализация
- `numpy` — RSI, MACD, EMA
- `scipy.signal.argrelextrema` — поиск пивотов
- `json`, `datetime` — стандартные
