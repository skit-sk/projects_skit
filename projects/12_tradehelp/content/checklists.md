# Чек-листы (MidasFlow v4.0)

## A+ Setup Checklist (6 из 6)

- [ ] MSS/BOS подтверждение
- [ ] Sweep ликвидности (BSL/SSL)
- [ ] POI (Order Block или FVG)
- [ ] OTE зона (62–79%)
- [ ] OI Trend Healthy
- [ ] Footprint (Imbalance / Absorption)

## 10-Level Entry Checklist

- [ ] 1. Макро-фаза (Wyckoff)
- [ ] 2. Слом структуры (MSS)
- [ ] 3. Снятие ликвидности
- [ ] 4. Value Area (VAH/VAL)
- [ ] 5. POI (Order Block)
- [ ] 6. OTE (Fib 70.5%)
- [ ] 7. Heatmap кластер
- [ ] 8. OI Trend Health
- [ ] 9. Footprint подтверждение
- [ ] 10. Risk/Reward > 1:2

## Pre-Trade Checklist

- [ ] Wyckoff phase определена
- [ ] MSS / BOS подтверждён
- [ ] Sweep ликвидности есть
- [ ] POI найден
- [ ] Цена в OTE
- [ ] Heatmap ликвидаций подтверждает
- [ ] OI Trend Healthy
- [ ] Footprint подтверждение
- [ ] RR ≥ 1:2
- [ ] Position size по Risk Calculator
- [ ] Стоп-лосс за OB
- [ ] Confluence Score ≥ 4

## Post-Trade Checklist

- [ ] Записать сделку в журнал
- [ ] Скриншот графика
- [ ] Confluence Score: сколько совпало?
- [ ] Что сработало / не сработало
- [ ] Эмоциональное состояние
- [ ] Соблюдал план?
- [ ] P&L зафиксирован
- [ ] Что улучшить?
- [ ] Метрики обновлены
- [ ] Margin в норме
- [ ] Funding Rate проверен
- [ ] Не вхожу из мести

## Правила дисциплины

1. Не входить без Confluence Score ≥ 4
2. Не усреднять убыточную позицию
3. Не двигать стоп-лосс дальше от входа
4. Не входить после серии убытков (cooldown 30 мин)
5. Фиксировать P&L по плану
6. Перед сделкой — дыхание 3 раза
7. После убытка — запись в журнал

## MidasFlow v4.0 Operational Checklist

### Pre-Analysis (Macro)

- [ ] Определить Bias на D1/H4
- [ ] Идентифицировать ERL (PDH/PDL, PWH/PWL)
- [ ] Подтвердить IPDA look-back период (20/40/60)
- [ ] Проверить активный Killzone (Asia/London/NY)

### Tier 1: Raw Data

- [ ] Подключение к WebSocket биржи
- [ ] Нормализация тиков (OHLCV + T&S)
- [ ] Сохранение в Time-series DB (TimescaleDB)

### Tier 2: Microstructure

- [ ] Расчёт Delta, CVD (Polars, latency < 1ms)
- [ ] Обновление Volume Profile
- [ ] Детекция Footprint (Bid/Ask > 300%)

### Tier 3: Structural

- [ ] 5-candle fractal (Swing High/Low)
- [ ] BOS / CHoCH детекция (Body Close Rule)
- [ ] MSS с displacement > 1.5×ATR
- [ ] FVG: Low[i-2] > High[i]
- [ ] Order Block (последняя противоположная свеча)
- [ ] Breaker Block (mitigated OB)

### Geometry (MidasFlow Grid 2.0)

- [ ] Построить 33 уровня Fibo
- [ ] Определить зону OTE (62-79%)
- [ ] Sweet Spot = 0.705
- [ ] Invalidation = 1.0
- [ ] Цена входа на правильном уровне

### Risk Management

- [ ] Position Size по Kelly или Fixed-Fraction
- [ ] Stop за 1.0 (MSS level)
- [ ] TP по DOL targets (1.236 / 1.618 / 2.000 / 2.618)
- [ ] Risk/Reward ≥ 1:2
- [ ] Не превышать max leverage (10x для крипто)

### Risk Flags (MidasFlow)

- [ ] `PnL -100%` — стоп и разбор
- [ ] `PnL -200%` — URGENT
- [ ] `CRITICAL_RECOVERY` — Smart Recovery активировать
- [ ] `MARGIN_WARNING` (>70%) — снизить leverage
- [ ] `FUNDING_DRAG` (>0.05%/day) — закрыть позицию

### Position Engineering (Scaling)

- [ ] **1/8** — MSS + Displacement
- [ ] **2/8** — OTE зона (62-79%)
- [ ] **3/8** — BOS + Body Close
- [ ] **Max 4/1** — все подтверждения

### Smart Recovery (если убыток > маржи)

- [ ] Найти Breaker Block (mitigated OB)
- [ ] Дождаться ретеста
- [ ] Закрыть на distal_line
- [ ] Записать в журнал
- [ ] Post-mortem анализ

## 5-candle Fractal Validation

- [ ] **High**: H[i] > H[i±1], H[i±2]
- [ ] **Low**: L[i] < L[i±1], L[i±2]
- [ ] Валидный swing → использовать для BOS/CHoCH
- [ ] Если swing internal — игнорировать

## Tier 3 → Tier 1 Sync (Top-Down)

- [ ] **D1/H4** → Bias (Long/Short/Neutral)
- [ ] **H1** → Structure (BOS/CHoCH/MSS)
- [ ] **M15** → FVG + OB
- [ ] **M5** → Entry trigger
- [ ] Если H4 ≠ D1 Bias — **SKIP TRADE**

## Timeframe Locking

- [ ] **Структура** — H1 (минимальный шум)
- [ ] **Исполнение** — M15/M5/M1
- [ ] **Контекст** — D1/H4 (Bias)
- [ ] **Не смешивать** — никогда не торговать M15 против D1

## Killzones (EST)

- [ ] **Asia**: 19:00–22:00 (аккумуляция)
- [ ] **London Open**: 02:00–05:00 (манипуляция)
- [ ] **New York Open**: 07:00–10:00 (дистрибуция)
- [ ] **London Close**: 10:00–12:00 (реверс)
