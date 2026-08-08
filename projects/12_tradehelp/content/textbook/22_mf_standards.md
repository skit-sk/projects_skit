# Глава 22: MidasFlow Matrix v4.0 — Операционные стандарты

> **Источник:** `data/tradeLLm/06_technical_specs/SYSTEM MANDATE_ MidasFlow Matrix v4.0 Operational Standards.docx`

## 22.1 Что такое MidasFlow Matrix v4.0

MidasFlow Matrix — это **институциональная торговая система**, объединяющая:

- **Smart Money Concepts (SMC)** — BOS, CHoCH, MSS, OB, FVG
- **Microstructure Analysis** — Order Flow, DOM, Footprint
- **Predictive Liquidity** — IPDA (Institutional Price Delivery Algorithm)
- **CRP (Cluster Risk Projection)** — динамический риск-менеджмент
- **33-уровневая Fibо Grid 2.0** — расширенная сетка Фибоначчи

## 22.2 Протоколы именования торговых зон

| Термин | Сокращение | Определение |
|--------|-----------|-------------|
| **Order Block** | OB | Зона консолидации институциональных лимитных ордеров перед импульсом |
| **Breaker Block** | BB | Реверсивный OB, пробитый импульсом. Зеркальный вход после сбора стопов |
| **Fair Value Gap** | FVG | Зона неэффективного ценообразования (Inefficient Price Delivery) |
| **Liquidity** | LQ | Buy-side (BSL) / Sell-side (SSL) — пулы лимитных заявок за экстремумами |
| **MSS** | — | Market Structure Shift — силовой слом с displacement |
| **CHoCH** | — | Change of Character — первичный сигнал смены тренда |
| **BOS** | — | Break of Structure — подтверждение продолжения |

## 22.3 Иерархия структурных сдвигов

**Подтверждение пробоя** — только **закрытие телом свечи** (Body Close Rule):

```
BOS (Break of Structure):
  - Подтверждение текущей экспансии
  - Close > High(предыдущий Higher High) для long
  - Close < Low(предыдущий Lower Low) для short
  - Пробои только фитилем (wick) — НЕ считаются

CHoCH (Change of Character):
  - Первичный сигнал истощения тренда
  - Пробой последнего значимого экстремума
  - Без подтверждения объёмом/displacement

MSS (Market Structure Shift):
  - Силовой слом с обязательным displacement
  - Body_Size > 1.5 × ATR(14)
  - Требует подтверждения объёмом + Footprint
```

## 22.4 Алгоритм фильтрации шума BOS/CHoCH

5 уровней фильтрации:

1. **Body Close Rule** — только закрытие телом (не фитилём)
2. **Displacement Filter** — `Body > 1.5 × ATR(14)`
3. **Last BOS Rule** — валидный CHoCH пробивает только экстремум, приведший к финальному BOS
4. **Timeframe Locking** — структура на H1, исполнение на M15/M5
5. **Volume + Microstructure** — всплеск объёма + Stacked Imbalance в сторону пробоя

## 22.5 Ключевые правила v4.0

### Body Close Rule
```
BOS_VALID = (Candle.Close > Swing_High.High) AND (Candle.Body_Size > 0)
           [для бычьего пробоя]
```

### Displacement Threshold
```
MSS_VALID = (BOS_VALID) AND (Body_Size > 1.5 × ATR(14))
           AND (Volume > 1.5 × Avg_Volume_20)
```

### Swing High/Low Validation (5-свечный фрактал)
```
Swing_High = (
    High[i] > High[i-1] AND
    High[i] > High[i-2] AND
    High[i] > High[i+1] AND
    High[i] > High[i+2]
)
```

## 22.6 Naming Convention (версия 4.0)

| Объект | Формат ID | Пример |
|--------|-----------|--------|
| Order Block | `OB_{TF}_{id}_{date}_{time}` | `OB_H1_a7f2_24052026_14:30` |
| FVG | `FVG_{TF}_{id}_{date}` | `FVG_H4_b3e1_24052026` |
| BOS | `BOS_{TF}_{id}_{date}_{time}` | `BOS_H1_b2e1_24052026_15:00` |
| MSS | `MSS_{TF}_{id}_{date}_{time}` | `MSS_D1_c5f2_24052026` |
| Liquidity Pool | `LP_{type}_{level}_{date}` | `LP_BSL_82500_24052026` |
| Killzone | `KZ_{name}_{date}` | `KZ_LONDON_OPEN_24052026` |

## 22.7 Сравнение версий

| Версия | Особенность |
|--------|-------------|
| v1.0 | Базовая SMC: BOS/CHoCH/OB/FVG |
| v2.0 | + Displacement, 5-candle fractal |
| v3.0 | + Microstructure, DOM Level 2 |
| **v4.0** | **+ MidasFlow Grid 2.0 (33 уровня), IPDA, CRP, JSON-протокол** |

## 22.8 Эпистемологическая позиция

> "Классические индикаторы (RSI, MACD) — третичные математические производные от исторических цен. Они страдают от **Indicator Redundancy** — избыточности, создающей ложную иллюзию подтверждения."

**MidasFlow Matrix v4.0** — это переход к **первичным данным** (микроструктура, Order Flow) и **институциональной логике** (IPDA, Shadow DOM).

## 22.9 Top-Down Protocol

```
D1 / H4 — Macro context (Bias, ERL)
   ↓
H1 — Structure (BOS, MSS, IRL)
   ↓
M15 / M5 / M1 — Execution (Footprint, FVG, OB retest)
```

**Правило:** Если структура H4 противоречит D1 Bias — **пропустить торговый день**.

## 22.10 Что дальше

- **Глава 23:** MidasFlow Grid 2.0 — 33 уровня Fibo
- **Глава 24:** Fractal Mechanics + IPDA
- **Глава 25:** Position Engineering (Scaling In/Out)
- **Глава 26:** Микроструктурный детектив (CRP + Shadow DOM)
