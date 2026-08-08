# Глава 23: MidasFlow Grid 2.0 — 33 уровня Фибоначчи

> **Источник:** `data/tradeLLm/06_technical_specs/Технический регламент «MidasFlow Grid 2.0_ Полная архитектура уровней Фибоначчи и геометрический синтез».docx`

## 23.1 Обзор

**MidasFlow Grid 2.0** — это **33-уровневая сетка Фибоначчи**, распределённая в диапазоне от **-1.0 до 2.618**. Каждый уровень выполняет строго определённую роль в логике исполнения ордеров.

**Цель:** Карта следов маркет-мейкеров (Following the Money), а не коррекции ритейл-уровня.

## 23.2 Полная спецификация 33 уровней

### Зона манипуляции (отрицательные значения)

| Коэффициент | Название | Функция |
|-------------|----------|---------|
| -1.000 | **Full Hunt Target** | Expansion (Extreme Manipulation) |
| -0.886 | Deep Sweep Boundary | Manipulation Zone |
| -0.786 | Liquidity Void Edge | Manipulation Zone |
| -0.705 | **Maximum Pain Point** | Final Liquidity Trigger (Stop Run) |
| -0.618 | Hunt Expansion 0.618 | Manipulation Zone |
| -0.500 | Manipulation Midpoint | Equilibrium (Negative) |
| -0.382 | Early Fakeout Trap | Manipulation Zone |
| -0.270 | **Primary Hunt Zone** | Liquidity Grab (Retail Sweep) |
| -0.236 | Induction Level | Manipulation Zone |
| -0.118 | Pre-Range Deviation | Manipulation Zone |

### Pivot & Mitigation (нулевые и слабо-положительные)

| Коэффициент | Название | Функция |
|-------------|----------|---------|
| 0.000 | **Range Origin (Low/High)** | Pivot Point / Baseline |
| 0.118 | Shadow Induction | Early Mitigation |
| 0.236 | Retail Support/Resistance | Minor Mitigation |
| 0.382 | Secondary Mitigation | Institutional Mitigation |
| 0.500 | **Equilibrium** | Fair Value Level (Neutral) |

### OTE Zone (Institutional Entry)

| Коэффициент | Название | Функция |
|-------------|----------|---------|
| 0.618 | **OTE Start (Golden Ratio)** | Institutional Entry |
| 0.705 | **OTE Mid (Sniper Entry)** | Institutional Entry (Sweet Spot) |
| 0.786 | **OTE Deep (Last Stand)** | Institutional Entry |
| 0.886 | Deep Mitigation | Institutional Entry (Extreme) |
| 1.000 | **Invalidation Level** | Idea Cancellation / MSS |

### Expansion Zone (выше единицы)

| Коэффициент | Название | Функция |
|-------------|----------|---------|
| 1.128 | Early Deviation Target | Expansion (Initial) |
| 1.236 | Expansion 1.236 | Expansion Zone |
| 1.272 | Harmonic Extension | Expansion Zone |
| 1.414 | Volatility Extension | Expansion Zone |
| 1.500 | Expansion Midpoint | Expansion Zone |
| 1.618 | **Whale Trap Alpha** | Deep Expansion (Distribution Magnet) |
| 1.786 | Deep Extension 1.786 | Expansion Zone |
| 2.000 | Cycle Double Target | Expansion Zone |
| 2.118 | Hyper Extension 2.118 | Expansion Zone |
| 2.272 | Hyper Extension 2.272 | Expansion Zone |
| 2.382 | Hyper Extension 2.382 | Expansion Zone |
| 2.414 | Hyper Extension 2.414 | Expansion Zone |
| 2.618 | **Whale Trap Beta** | Extreme Expansion (Exhaustion) |

## 23.3 Зона OTE (0.618 - 0.786)

**OTE (Optimal Trade Entry)** — основная зона институционального входа.

```
0.618 = OTE Start (Golden Ratio)    — начало зоны
0.705 = OTE Mid (Sniper Entry)     — Sweet Spot (медиана)
0.786 = OTE Deep (Last Stand)      — последний шанс входа
```

**Sweet Spot (0.705)** — расчётное медианное значение, представляющее точку максимального институционального интереса для минимизации просадки.

## 23.4 Hunt Zones (отрицательные значения)

**Hunt Zones** — зоны активного захвата ликвидности.

```
-0.270 = Primary Hunt Zone (Retail Sweep)  — основная зона сбора стопов
-0.705 = Maximum Pain Point (Stop Run)     — финальный ликвидационный триггер
-1.000 = Full Hunt Target (Extreme)         — экстремальное расширение манипуляции
```

## 23.5 Expansion Zones (выше 1.0)

**Whale Trap Alpha (1.618)** — глубокое расширение, магнит для дистрибуции.

**Whale Trap Beta (2.618)** — экстремальное расширение, зона истощения.

## 23.6 Математическое обоснование

```
Sniper Entry (0.705) = (0.618 + 0.786) / 2 = 1.404 / 2 = 0.702 ≈ 0.705
```

Sweet Spot вычисляется как **медиана OTE-зоны**.

## 23.7 Практическое применение

### Алгоритм входа

```python
def mf_entry_zone(swing_low, swing_high):
    range_ = swing_high - swing_low

    ote_start = swing_low + range_ * 0.618  # 0.618
    ote_mid = swing_low + range_ * 0.705    # Sniper
    ote_deep = swing_low + range_ * 0.786   # Last Stand
    invalidation = swing_low + range_ * 1.0 # MSS level

    return {
        'entry_start': ote_start,
        'sweet_spot': ote_mid,
        'last_stand': ote_deep,
        'invalidation': invalidation,
    }
```

### Алгоритм TP (Take Profit)

```python
def mf_tp_levels(swing_low, swing_high, current):
    range_ = swing_high - swing_low

    targets = {
        'tp1_1236': swing_low + range_ * 1.236,  # Conservative
        'tp2_1618': swing_low + range_ * 1.618,  # Whale Trap Alpha
        'tp3_2000': swing_low + range_ * 2.000,  # Cycle Double
        'tp4_2618': swing_low + range_ * 2.618,  # Whale Trap Beta
    }
    return targets
```

## 23.8 Сравнение с классической сеткой Fibo

| Классическая | MidasFlow Grid 2.0 |
|--------------|---------------------|
| 13 уровней (0.0 - 2.618) | **33 уровня** (-1.0 - 2.618) |
| Только коррекция | Коррекция + Манипуляция + Expansion |
| Без манипуляционных зон | **10 зон манипуляции** (отрицательные) |
| Без Sniper Entry | **0.705 — Sniper Entry** (медиана OTE) |
| Стандартный | **Displacement + BOS фильтры** |

## 23.9 Кейс: BTC Feb 2026

**Данные:** Импульс BTC от $60,000 (Low) до $90,000 (High).

**Расчёт уровней:**
```
Range = $30,000
0.618 (OTE Start) = $60,000 + $30,000 × 0.618 = $78,540
0.705 (Sniper)    = $60,000 + $30,000 × 0.705 = $81,150
0.786 (Last)      = $60,000 + $30,000 × 0.786 = $83,580
1.000 (Invalid)   = $90,000
1.618 (Whale Alpha) = $60,000 + $30,000 × 1.618 = $108,540
```

## 23.10 Синтез с Ганном

**Gann angles** интегрируются в MidasFlow через:
- **Конфлюэнция углов:** пересечение горизонтальных Fibo с наклонными (1x1, 2x1, 1x2)
- **Диагональная ликвидность:** Trendline Liquidity в зонах Sweep

## 23.11 Что дальше

- **Глава 24:** Fractal Mechanics + IPDA (как эти уровни применяются на разных TF)
- **Глава 25:** Position Engineering (Scaling In/Out на уровнях OTE)
