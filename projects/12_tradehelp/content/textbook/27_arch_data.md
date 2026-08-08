# Глава 27: Архитектура данных — 3 Tier

> **Источник:** `data/tradeLLm/06_technical_specs/Технический отчет по архитектуре данных торговой системы_ от микроструктуры до рыночных структур.docx`

## 27.1 Эпистемологический сдвиг

Современное проектирование HFT-платформ требует архитектурного перехода от **классических лагающих индикаторов** (RSI, MACD) к анализу **микроструктуры рынка** и **высокочастотных потоков заказов**.

| Подход | Природа данных | Временной лаг | Цель |
|--------|----------------|----------------|------|
| **Классический TA** (Retail) | Производные от OHLC | Сильное запаздывание | Статистическая вероятность |
| **Микроструктура** (SMC) | Прямая запись транзакций | Реальное время / Опережение | Намерения маркет-мейкеров |

## 27.2 Трёхуровневая архитектура (3 Tier)

### Tier 1: Raw Data (Нормализованные сырые данные)

**Содержание:**
- Потоковые данные тикового уровня (Tick-by-tick)
- Лента сделок (Time & Sales)
- Обновления стакана (DOM L2)

**Этап:** **Нормализация** — приведение разнородных биржевых форматов к единому стандарту данных.

```python
# Tier 1 пример: нормализованный тик
{
    "timestamp": 1716561000000,
    "symbol": "API3USDT",
    "exchange": "BINANCE",
    "price": 0.2992,
    "volume": 100.0,
    "side": "BUY",
    "is_buyer_maker": false,
    "trade_id": "123456789"
}
```

### Tier 2: Derived Microstructure (Производная микроструктура)

**Метрики реального времени:**

| Метрика | Описание | Источник |
|---------|----------|----------|
| **Delta** | V(ask) − V(bid) | Tier 1 |
| **CVD** | Cumulative Volume Delta | Кумулятивная Delta |
| **Imbalance** | Ask/Bid ratio | DOM L2 |
| **VP (Volume Profile)** | POC, VAH, VAL, HVN, LVN | Тики |
| **Stacked Imbalance** | ≥3 уровней > 300% | Footprint |

### Tier 3: Complex Structural Patterns (Сложные структурные паттерны)

**Высший уровень абстракции:**

| Паттерн | Требует | TF |
|---------|---------|-----|
| **BOS / CHoCH / MSS** | Swing-points (5-candle fractal) | H1 |
| **Order Blocks (OB)** | Displacement + BOS | H1, H4 |
| **Fair Value Gaps (FVG)** | Три свечи (gap) | M15, H1 |
| **Breaker Blocks (BB)** | Mitigated OB | H1 |
| **MidasFlow Grid 2.0** | 33 уровня Fibo | D1, H4, H1 |

**Top-down синхронизация обязательна.**

## 27.3 Классификация лагающих и опережающих метрик

### Проблема Indicator Redundancy

Использование инструментов одного математического класса:
```
RSI + Stochastic = одна и та же формула импульса, разные масштабы
MACD + Bollinger Bands = та же EMA, разные σ
```

### Решение: комплементарные метрики + ADX-фильтр

| ADX | Режим | Допустимые инструменты |
|-----|-------|------------------------|
| < 30 | Mean Reversion | Stochastic, Bollinger Bounce |
| > 30 | Тренд | MACD, SMC (BOS/CHoCH), Volume Profile |

## 27.4 Матрица данных MidasFlow

8 функциональных категорий:

| # | Категория | Параметры |
|---|-----------|-----------|
| 1 | **Raw** | OHLC, Ticks, Sessions |
| 2 | **Microstructure** | Delta, CVD |
| 3 | **Order Flow** | DOM, Market/Limit Orders |
| 4 | **SMC** | BOS, CHoCH, MSS, OB, FVG |
| 5 | **AMT (Auction)** | POC, VAH/VAL, HVN/LVN, TPO |
| 6 | **Liquidity Heatmap** | BSL, SSL, EQH/EQL, Trendline |
| 7 | **Geometry** | OTE (62%, 70.5%, 79%), Equilibrium |
| 8 | **Risk Recovery** | Mitigation Blocks, CRP |

## 27.5 Стек технологий (Backend)

| Слой | Технология | Обоснование |
|------|-----------|-------------|
| **API** | FastAPI (ASGI) | Минимальные задержки, WebSocket |
| **Обработка** | Polars | Быстрее Pandas, эффективнее память |
| **JIT** | Numba | Ускорение Fibonacci Grid (O(n)) |
| **WebSocket** | ASGI WS | Live-данные в реальном времени |
| **Storage** | InfluxDB / TimescaleDB | Time-series оптимизация |
| **Cache** | Redis | Реал-тайм стримы |
| **Visualization** | Plotly + Datashader | Heatmap для миллионов тиков |
| **Render** | WebGL / Canvas | 60 FPS на Footprint |

## 27.6 Pipeline обработки

```
Tier 1 (Raw Ticks)
    ↓ [Normalization]
Tier 2 (Microstructure: Delta, CVD, VP)
    ↓ [Pattern Recognition]
Tier 3 (Structural: BOS, MSS, OB, FVG)
    ↓ [Grid 2.0 Application]
Geometry (33 Fibo levels, OTE, Equilibrium)
    ↓ [Risk Engine]
CRP / Recovery Module
    ↓ [Visualization]
Plotly + Datashader + WebGL
```

## 27.7 Polars-based Engine

```python
import polars as pl

def calc_indicators_polars(df: pl.DataFrame) -> pl.DataFrame:
    """
    Быстрый расчёт индикаторов через Polars.
    df должен иметь колонки: time, open, high, low, close, volume
    """
    return df.with_columns([
        # EMA(12) и EMA(26)
        pl.col('close').ewm_mean(span=12).alias('ema_12'),
        pl.col('close').ewm_mean(span=26).alias('ema_26'),

        # MACD
        (pl.col('close').ewm_mean(span=12) - pl.col('close').ewm_mean(span=26))
            .alias('macd'),

        # ATR(14)
        pl.col('high').rolling_mean(14).alias('atr_14'),

        # VWAP
        ((pl.col('close') * pl.col('volume')).cumsum() /
         pl.col('volume').cumsum()).alias('vwap'),
    ]).with_columns([
        # MACD Signal
        pl.col('macd').ewm_mean(span=9).alias('macd_signal'),
        pl.col('macd') - pl.col('macd_signal').alias('macd_hist'),
    ])
```

## 27.8 JSON-протокол MidasFlow (обзор)

```json
{
  "matrix_metadata": {
    "protocol_version": "1.1.0",
    "timestamp": "2026-05-15T14:30:00.001Z",
    "symbol": "ES_U26",
    "timeframe": "M15",
    "active_killzone": "LONDON_OPEN"
  },
  "market_structure": {
    "bias": "Bullish",
    "last_break": "MSS",
    "displacement_magnitude": "High",
    "dealing_range": {"high": 5450.00, "low": 5400.00}
  },
  "active_zones": [...],
  "crp_ribbons": {...},
  "liquidity_pools": {...},
  "volume_profile_metrics": {...}
}
```

## 27.9 Сравнение с Pandas

| Операция | Pandas | Polars | Ускорение |
|----------|--------|--------|-----------|
| Чтение 1M строк | 850ms | 95ms | **9×** |
| EMA расчёт | 320ms | 18ms | **18×** |
| Group by | 410ms | 32ms | **13×** |
| Memory | 380 MB | 75 MB | **5×** |

## 27.10 Tier 3: Top-Down синхронизация

```python
def tier3_structure(candles_by_tf):
    """
    Применяет Tier 3 паттерны ко всем TF с синхронизацией.
    """
    structure = {}

    # Macro: D1 / H4
    d1 = candles_by_tf['D1']
    structure['D1_bias'] = determine_bias(d1)
    structure['D1_ERL'] = find_erl(d1)

    # Medium: H1
    h1 = candles_by_tf['H1']
    structure['H1_structure'] = find_bos_choch_mss(h1)

    # Micro: M15
    m15 = candles_by_tf['M15']
    structure['M15_fvgs'] = find_fvg(m15)
    structure['M15_obs'] = find_order_blocks(m15)

    return structure
```

## 27.11 Что дальше

- **Глава 28:** Backend реализация (FastAPI + WebSocket + Numba)
- **Глава 29:** Frontend (WebGL + Datashader)
