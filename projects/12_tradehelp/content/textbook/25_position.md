# Глава 25: Position Engineering — Scaling In/Out

> **Источник:** `data/tradeLLm/05_analytical_reports/Аналитический отчет_ Модуль 13. Позиционный инжиниринг и алгоритмы восстановления капитала.docx`

## 25.1 Концепция

**Position Engineering** — математика управления капиталом и алгоритм динамического входа/выхода. Это не поиск паттернов, а **дешифровка институционального следа** и анализ **потока ордеров**.

## 25.2 Scaling In: Прогрессивный вход (1/8 → 4/1)

### Этап 1: Первичный вход (1/8 объёма)

**Условие:** Подтверждение MSS (Market Structure Shift)

```
MSS_VALID = (
    displacement_present AND
    body_size > 1.5 × ATR(14) AND
    volume_spike > 1.5 × avg_volume_20
)
```

Без displacement MSS = ложный сигнал.

### Этап 2: Набор основной позиции — OTE зона

**Условие:** Возврат цены в OTE (62% - 79%)

```
OTE_TEST = (
    price_in_range[0.618, 0.786] OR
    price_at_mean_threshold (50% of OB) OR
    first_fvg_test
)
```

**Mean Threshold (50% OB)** — точка максимальной эффективности.

### Этап 3: Финальная загрузка (до 4/1)

**Условие:** Подтверждение BOS (Break of Structure)

```
BOS_VALID = (
    candle.body_close > last_swing_high AND
    NOT wick_only  # Body Close Rule
)
```

BOS подтверждается **только закрытием тела** (не фитилем).

## 25.3 Пропорции Scaling In

| Этап | Условие | Доля |
|------|---------|------|
| 1 | MSS + Displacement | **1/8** (12.5%) |
| 2 | OTE зона (62-79%) | **2/8** (25%) |
| 3a | BOS подтверждение | **3/8** (37.5%) |
| 3b | Max load (max допустимая) | **4/1** (100% — leverage) |

## 25.4 Scaling Out: Фиксация прибыли

**Цель (Target)** = **DOL (Draw on Liquidity)** — зоны внешней ликвидности, магниты для IPDA.

### Уровни фиксации

| Уровень | Цель (Grid 2.0) | Доля фиксации |
|---------|------------------|---------------|
| TP1 | 1.236 (Early Deviation) | 1/4 (25%) |
| TP2 | 1.618 (Whale Trap Alpha) | 2/4 (50%) |
| TP3 | 2.000 (Cycle Double) | 3/4 (75%) |
| TP4 | 2.618 (Whale Trap Beta) | 4/4 (100%) |

## 25.5 Smart Recovery (восстановление капитала)

**Проблема:** API3 #1 — leverage 10, margin 2.50 USDT, pnl -218%. Убыток превышает маржу.

**Решение:** Алгоритм восстановления через **Breaker Blocks**.

### Логика Recovery

```python
def smart_recovery(position, ob_zones):
    """
    Если убыток > маржи, использовать Breaker Blocks
    для выхода в безубыток при ретесте.
    """
    if abs(position.unrealized_pl) > position.margin_size:
        # Найти бывший OB, ставший Breaker
        breaker = find_breaker_blocks(ob_zones)
        if breaker and price_retests(breaker):
            return {
                'action': 'CLOSE_AT_BREAKER',
                'level': breaker.distal_line,
                'rationale': 'Митигация позиции через failed OB'
            }
    return None
```

## 25.6 CRITICAL_RECOVERY Flag

**Триггер:** `|unrealized_pl| > margin_size`

**Действие:** Немедленная активация модуля восстановления.

```python
def check_recovery_flag(position):
    if abs(position.unrealized_pl) > position.margin_size:
        return ['CRITICAL_RECOVERY', 'PnL -218%']
    return []
```

## 25.7 Risk Flags

| Flag | Условие | Приоритет |
|------|---------|-----------|
| `PnL -100%` | Убыток = 100% маржи | 🔴 HIGH |
| `PnL -200%` | Убыток = 200% маржи | 🔴 CRITICAL |
| `CRITICAL_RECOVERY` | \|PL\| > Margin | 🔴 URGENT |
| `MARGIN_WARNING` | Used margin > 70% | 🟡 MEDIUM |
| `FUNDING_DRAG` | Funding > 0.05% / day | 🟡 MEDIUM |

## 25.8 Кейс: API3 #1

**Параметры:** Leverage 10, Margin 2.5008, PnL -218.26%

**Анализ:**
```
abs(unrealized_pl) = 5.45 USDT
margin_size = 2.50 USDT
ratio = 5.45 / 2.50 = 2.18  (> 1.0 → CRITICAL_RECOVERY)
```

**Действие:** Активировать модуль восстановления → искать Breaker Block для mitigation.

## 25.9 Алгоритм Breaker Block Recovery

```python
def find_recovery_breaker(candles, position):
    """Найти бывший OB, ставший Breaker Block."""
    # 1. Найти все OB за последние N баров
    obs = find_order_blocks(candles)

    # 2. Определить, какие OB были пробиты (стали Breaker)
    breakers = []
    for ob in obs:
        if candle_close_below(ob.distal_line) and not ob.mitigated:
            breakers.append(ob)

    # 3. Дождаться ретеста и закрыть позицию
    for breaker in breakers:
        if price_retests(breaker):
            return {
                'exit_price': breaker.distal_line,
                'rationale': 'Breaker Block mitigation',
                'expected_outcome': 'Reduced loss / breakeven'
            }
    return None
```

## 25.10 Draw on Liquidity (DOL) Targets

**DOL** — зоны внешней ликвидности, куда стремится цена:

```
DOL = {
    'BSL_target': equal_highs_pool,
    'SSL_target': equal_lows_pool,
    'PWH_target': previous_week_high,
    'PWL_target': previous_week_low,
    'PMH_target': previous_month_high,
    'PML_target': previous_month_low
}
```

**Правило:** TP ставится не "по красивым числам", а **на зоне ликвидности**.

## 25.11 Система усреднений

**НЕ делать martingale!** Усреднение только по протоколу Position Engineering.

| Этап | Условие | Действие |
|------|---------|----------|
| MSS | Displacement | 1/8 |
| OTE | 62-79% | 2/8 |
| BOS | Подтверждение | 3/8 |
| Среднее | **Только структурное** | 4/8 |

## 25.12 Пропорции усреднения (таблица)

| Шаг | Условие | Доля от макс. объёма |
|-----|---------|---------------------|
| 1 | MSS + Displacement | 1/8 |
| 2 | OTE 62-79% | +2/8 (итого 3/8) |
| 3 | BOS подтверждение | +3/8 (итого 6/8) |
| 4 | Max load | +2/8 (итого 8/8) |

## 25.13 Что дальше

- **Глава 26:** Микроструктурный детектив (CRP + Shadow DOM)
- **Глава 27:** Архитектура данных (3 Tier)
