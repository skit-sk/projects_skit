# Глава 24: Fractal Mechanics и IPDA

> **Источник:** `data/tradeLLm/05_analytical_reports/Аналитический отчет Модуль 12_ Фрактальная механика и вложенность структур ТФ.docx`

## 24.1 Фрактальная природа рынка

Рынок **фрактален** — одни и те же структуры повторяются на разных таймфреймах. Это не хаос, а **алгоритм межбанковской доставки цены** (IPDA), который оперирует конкретными параметрами для поиска ликвидности и ребалансировки неэффективностей.

## 24.2 IPDA (Institutional Price Delivery Algorithm)

**IPDA** — алгоритм доставки цены, который оперирует фиксированными ретроспективными окнами:

```
Look-back периоды: 20, 40, 60 торговых дней
```

В этих диапазонах алгоритм идентифицирует:
- Ключевые пулы ликвидности
- Неэффективности (FVG)
- Цели для текущей доставки цены

**Вывод:** Фрактальность — это не просто повторение геометрических паттернов, а **идентичность алгоритмических действий** по поиску ликвидности на разных временных отрезках.

## 24.3 Top-Down Protocol (иерархия таймфреймов)

### Макро-контекст (D1 / H4)

**Определение:**
- Общее смещение (**Bias**)
- Внешняя ликвидность (**ERL** — External Range Liquidity)
- ERL = максимумы/минимумы предыдущих периодов (PDH/PDL, PWH/PWL)

### Среднесрочная структура (H1)

**Идентификация:**
- Внутренняя ликвидность (**IRL** — Internal Range Liquidity)
- В строгом определении ICT: **IRL = FVG + OB** (не internal swings)
- Алгоритм стремится из ERL в IRL и наоборот

### Микроструктура (M15 / M5 / M1)

**Зона тактического исполнения:**
- Footprint
- DOM Level 2
- Cluster Risk Projection (CRP)

## 24.4 Золотое правило институциональной дисциплины

> **Если структура H4 противоречит D1 Bias — пропустить торговый день.**

Работа против макро-контекста резко снижает математическое ожидание сделки.

## 24.5 Валидация структурных точек (5-свечный фрактал)

### Swing High (медвежий фрактал)

```
Swing_High[i] = (
    High[i] > High[i-1] AND
    High[i] > High[i-2] AND
    High[i] > High[i+1] AND
    High[i] > High[i+2]
)
```

### Swing Low (бычий фрактал)

```
Swing_Low[i] = (
    Low[i] < Low[i-1] AND
    Low[i] < Low[i-2] AND
    Low[i] < Low[i+1] AND
    Low[i] < Low[i+2]
)
```

**5-свечный фрактал** — стандарт ICT для валидации swing-точек.

## 24.6 Подтверждение CHoCH через фракталы

```
CHoCH_VALID = (
    Current_Close < Last_Swing_Low.Low AND
    Last_Swing_Low.Fractal_Valid AND  # 5-candle
    Body_Close_Rule  # не фитиль
)
```

## 24.7 IPDA Look-back Periods

```python
def ipda_lookbacks(candles):
    lookbacks = {
        'short': 20,   # 20 торговых дней
        'mid':   40,
        'long':  60
    }
    pools = {}
    for name, period in lookbacks.items():
        window = candles[-period:]
        pools[name] = {
            'fvg': find_fvg(window),
            'ob': find_order_blocks(window),
            'liquidity': find_eqh_eql(window),
            'poc': find_poc(window)
        }
    return pools
```

## 24.8 Вложенность структур (Nesting)

Структуры на разных TF **вложены** друг в друга:

```
D1 MSS содержит:
  H4 BOS (несколько, каждый со своим OTE)
    H1 CHoCH (локальные развороты)
      M15 OB (точки входа)
        M5 FVG (микро-входы)
          M1 Tape Reading (precision entry)
```

**Правило:** Синхронизация обязательна. Нельзя торговать M15 OB против H4 Bias.

## 24.9 ERL → IRL → ERL (цикл)

```
1. Снятие ERL: импульс собирает внешнюю ликвидность (BSL sweep)
2. Откат к IRL: возврат к FVG/OB для mitigation
3. Проекция к следующему ERL: новый импульс к противоположной стороне
```

**ERL = конечные пункты назначения (цели)**
**IRL = промежуточные станции (mitigation)**

## 24.10 FVG vs Internal Swings

| Тип | Является IRL? | Почему |
|-----|---------------|--------|
| FVG (Fair Value Gap) | ✅ ДА | Зона ребалансировки, цель IPDA |
| Order Block (OB) | ✅ ДА | Точка входа институционалов |
| Internal Swing High/Low | ❌ НЕТ | Шум, не значимая цель |
| Equilibrium (50%) | ⚠️ Нейтрально | Pivot, но не цель |

## 24.11 Swing Strength Validation

```python
def swing_strength(candles, i, strength='m1_simple'):
    """Оценка силы swing-точки (5 уровней)."""
    h = candles[i].high
    l = candles[i].low
    if strength == 'm1_simple':
        # Простой: экстремум больше/меньше соседей
        if i < 2 or i > len(candles) - 3:
            return 0
        is_high = all(h > candles[i+j].high for j in [-1, -2, 1, 2])
        is_low = all(l < candles[i+j].low for j in [-1, -2, 1, 2])
        if is_high or is_low:
            return 1  # Простой swing
        return 0
    # Более сложные варианты (volume-weighted, displacement-weighted)
    ...
```

## 24.12 Кейс: BTC Feb 2026 (D1 → H4 → H1)

```
D1 (Macro): MSS вверх, Bias = Long, ERL = $90,000 (предыдущий HH)
  ↓
H4 (Structure): 
  - BOS на $75,000 → Pullback к OTE 0.705 (~$70,000)
  - Второй BOS на $82,000
  ↓
H1 (Execution):
  - CHoCH на $79,500 (локальный разворот)
  - FVG $78,000-$79,000 → точка входа
  - OB $76,500-$77,500 → страховка
```

## 24.13 Timeframe Locking

**Структура:** H1 (минимальный шум, институциональные уровни)
**Исполнение:** M15 / M5 / M1 (точный entry)
**Контекст:** D1 / H4 (Bias)

```
IF TF_Structure ≠ TF_Bias:
    SKIP_TRADE
```

## 24.14 Что дальше

- **Глава 25:** Position Engineering (Scaling In/Out на разных TF)
- **Глава 26:** Микроструктурный детектив (CRP + Shadow DOM)
