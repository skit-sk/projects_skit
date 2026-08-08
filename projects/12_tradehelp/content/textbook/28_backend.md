# Глава 28: Backend реализация — FastAPI + WebSocket + Numba

> **Источник:** `data/tradeLLm/06_technical_specs/Техническое руководство по реализации бэкенда MidasFlow Matrix.docx`

## 28.1 Стек и обоснование

| Компонент | Технология | Обоснование |
|-----------|-----------|-------------|
| **API Framework** | **FastAPI** | ASGI, async, минимальные задержки |
| **Data Processing** | **Polars** | Векторизация, эффективная память |
| **JIT Compilation** | **Numba** | Ускорение Fibonacci Grid (O(n)) |
| **Realtime** | **WebSocket** | Live-данные позиций и DOM |
| **Time-series DB** | InfluxDB / TimescaleDB | Оптимизировано для OHLCV |
| **Cache** | Redis | Реал-тайм стримы |
| **Visualization** | Plotly + Datashader | Heatmap для миллионов тиков |
| **Frontend Render** | WebGL / Canvas | 60 FPS на Footprint |

## 28.2 FastAPI Application Structure

```
midasflow_backend/
├── main.py                  # FastAPI app
├── routers/
│   ├── market_data.py       # OHLCV, T&S, DOM
│   ├── structure.py         # BOS, CHoCH, MSS, OB, FVG
│   ├── volume_profile.py    # POC, VAH, VAL
│   ├── liquidity.py         # BSL, SSL, EQH/EQL
│   ├── fibo_grid.py         # 33 levels
│   ├── crp.py               # Cluster Risk Projection
│   └── risk.py              # Position management
├── services/
│   ├── normalizer.py        # Tier 1: raw → normalized
│   ├── microstructure.py    # Tier 2: Delta, CVD, VP
│   ├── patterns.py          # Tier 3: BOS, MSS, OB, FVG
│   ├── grid.py              # 33 Fibo levels (Numba)
│   ├── crp.py               # CRP calculator
│   └── risk.py              # Risk engine
├── core/
│   ├── data_layer.py        # Polars engine
│   ├── websocket.py         # Live streaming
│   └── protocol.py          # MidasFlow JSON protocol
└── schemas/
    └── midasflow.json       # JSON Schema
```

## 28.3 FastAPI Main

```python
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import polars as pl
import asyncio

app = FastAPI(
    title="MidasFlow Matrix API",
    version="4.0.0",
    description="Institutional trading system backend"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket endpoint для live-данных
@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        # Push обновления каждую секунду
        data = await get_live_update()
        await websocket.send_json(data)
        await asyncio.sleep(1)
```

## 28.4 Tier 1: Normalizer

```python
def normalize_tick(raw, exchange):
    """
    Нормализация тиков из разных бирж к единому формату.
    """
    if exchange == "binance":
        return {
            "timestamp": raw["T"],
            "symbol": raw["s"],
            "price": float(raw["p"]),
            "volume": float(raw["q"]),
            "side": "BUY" if not raw["m"] else "SELL",
            "is_buyer_maker": raw["m"],
            "trade_id": str(raw["t"]),
            "exchange": "BINANCE"
        }
    # ... другие биржи
```

## 28.5 Tier 2: Microstructure Engine (Polars)

```python
import polars as pl
import numpy as np

def calc_microstructure_polars(ticks: pl.DataFrame) -> pl.DataFrame:
    """
    Расчёт Delta, CVD, Imbalance в реальном времени.
    """
    return ticks.with_columns([
        # Sign: +1 для покупок, -1 для продаж
        pl.when(pl.col('is_buyer_maker'))
            .then(-1)
            .otherwise(1)
            .alias('sign'),

        # Signed volume (агрессия)
        (pl.col('volume') * pl.col('sign')).alias('signed_volume'),
    ]).with_columns([
        # Delta (cumulative)
        pl.col('signed_volume').cumsum().alias('delta'),

        # CVD (cumulative volume delta)
        pl.col('signed_volume').cumsum().alias('cvd'),
    ]).with_columns([
        # Imbalance (Buy / (Buy + Sell))
        (
            pl.col('volume').filter(pl.col('sign') == 1).sum().over([...]) /
            pl.col('volume').sum().over([...])
        ).alias('imbalance')
    ])
```

## 28.6 Tier 3: Pattern Recognition

```python
def detect_bos_choch_mss(candles: pl.DataFrame, atr_period: int = 14) -> dict:
    """
    Детекция BOS, CHoCH, MSS.
    """
    # 5-candle fractal
    candles = candles.with_columns([
        pl.col('high').rolling_max(5).alias('swing_high'),
        pl.col('low').rolling_min(5).alias('swing_low'),
    ])

    # Displacement
    candles = candles.with_columns([
        (pl.col('close') - pl.col('open')).abs().alias('body_size'),
        pl.col('high').rolling_max(atr_period).alias('atr_14'),
    ]).with_columns([
        (pl.col('body_size') > 1.5 * pl.col('atr_14')).alias('displacement')
    ])

    # BOS: close > swing_high
    bos = candles.filter(pl.col('close') > pl.col('swing_high').shift(1))

    # MSS: BOS + displacement
    mss = candles.filter(
        (pl.col('close') > pl.col('swing_high').shift(1)) &
        pl.col('displacement')
    )

    return {
        'bos_count': len(bos),
        'mss_count': len(mss),
        'last_bos': bos.tail(1).to_dicts() if len(bos) > 0 else None,
        'last_mss': mss.tail(1).to_dicts() if len(mss) > 0 else None,
    }
```

## 28.7 Numba-JIT для Fibo Grid

```python
import numba as nb
import numpy as np

@nb.njit(cache=True)
def calc_fibo_grid_jit(swing_low, swing_high, levels):
    """
    JIT-компилированный расчёт 33 уровней MidasFlow Grid 2.0.
    """
    range_ = swing_high - swing_low
    n = len(levels)
    out = np.empty(n, dtype=np.float64)
    for i in nb.prange(n):
        out[i] = swing_low + range_ * levels[i]
    return out

# 33 уровня MidasFlow Grid 2.0
LEVELS = np.array([
    -1.000, -0.886, -0.786, -0.705, -0.618,
    -0.500, -0.382, -0.270, -0.236, -0.118,
    0.000, 0.118, 0.236, 0.382, 0.500,
    0.618, 0.705, 0.786, 0.886, 1.000,
    1.128, 1.236, 1.272, 1.414, 1.500,
    1.618, 1.786, 2.000, 2.118, 2.272,
    2.382, 2.414, 2.618
])
```

## 28.8 CRP WebSocket Stream

```python
@app.websocket("/ws/crp/{symbol}")
async def crp_stream(websocket: WebSocket, symbol: str):
    await websocket.accept()

    while True:
        # Получить последние 20 свечей
        candles = get_recent_candles(symbol, period=20)

        # Рассчитать CRP
        crp = calc_crp(candles, consolidation_period=20)

        # Отправить клиенту
        await websocket.send_json({
            "type": "crp_update",
            "symbol": symbol,
            "timestamp": int(time.time() * 1000),
            "data": crp
        })

        await asyncio.sleep(5)  # каждые 5 секунд
```

## 28.9 Risk Engine (CRITICAL_RECOVERY)

```python
def check_position_risk(position):
    """
    Проверка рисков позиции (MidasFlow Risk Engine).
    """
    flags = []

    # CRITICAL_RECOVERY: |PL| > Margin
    if abs(position['unrealized_pl']) > position['margin_size']:
        flags.append('CRITICAL_RECOVERY')

    # MARGIN_WARNING: used_margin > 70%
    margin_used = position['margin_size'] / position['equity']
    if margin_used > 0.7:
        flags.append('MARGIN_WARNING')

    # PnL thresholds
    pnl_pct = position['unrealized_pl'] / position['margin_size'] * 100
    if pnl_pct <= -200:
        flags.append('CRITICAL_LOSS')
    elif pnl_pct <= -100:
        flags.append('PnL -100%')
    elif pnl_pct <= -50:
        flags.append('PnL -50%')

    return {
        'position_id': position['id'],
        'flags': flags,
        'risk_level': 'CRITICAL' if 'CRITICAL' in str(flags) else
                      'HIGH' if 'PnL -100%' in flags else
                      'MEDIUM' if flags else 'LOW',
        'recommended_action': get_action(flags)
    }
```

## 28.10 Latency Targets

| Операция | Target | Метод |
|----------|--------|-------|
| Tier 1 Normalize | < 0.1ms | Numpy |
| Tier 2 Microstructure | < 1ms | Polars |
| Tier 3 Patterns | < 5ms | Numba JIT |
| Fibo Grid 33 levels | < 0.1ms | Numba JIT |
| CRP calc (20 candles) | < 2ms | Polars |
| WebSocket push | < 10ms | ASGI |
| **Total latency** | **< 25ms** | |

## 28.11 Polars Performance vs Pandas

```python
import time
import pandas as pd
import polars as pl

# Benchmark на 1M строк
n = 1_000_000
data = np.random.randn(n, 6)
df_pd = pd.DataFrame(data, columns=['o', 'h', 'l', 'c', 'v', 't'])
df_pl = pl.DataFrame(data, columns=['o', 'h', 'l', 'c', 'v', 't'])

# Pandas EMA
t0 = time.time()
df_pd['ema'] = df_pd['c'].ewm(span=12).mean()
t_pd = time.time() - t0

# Polars EMA
t0 = time.time()
df_pl = df_pl.with_columns(pl.col('c').ewm_mean(span=12).alias('ema'))
t_pl = time.time() - t0

print(f"Pandas: {t_pd*1000:.0f}ms, Polars: {t_pl*1000:.0f}ms, Speedup: {t_pd/t_pl:.0f}x")
```

## 28.12 WebSocket Protocol

```json
{
  "type": "market_update",
  "symbol": "API3USDT",
  "timestamp": 1716561000000,
  "data": {
    "price": 0.2992,
    "cvd": 1234.56,
    "delta": 45.78,
    "imbalance": 0.65,
    "ob_count": 3,
    "fvg_count": 2,
    "mss_detected": true,
    "ote_position": 0.705,
    "killzone": "LONDON_OPEN"
  }
}
```

## 28.13 Что дальше

- **Глава 29:** Frontend (WebGL + Datashader + Plotly)
- **Глава 30:** Веб-терминал (UX/архитектура)
