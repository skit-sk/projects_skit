# TradeLLM Skill — Институциональный трейдинг

**Статус:** РАБОТАЕТ
**Обновлено:** 2026-07-02
**Источник:** `data/tradeLLm/` (45 файлов)

## Источники в data/tradeLLm/

| Тема | Файл(ы) |
|------|---------|
| SMC / Order Blocks / FVG | `Торговая Энциклопедия 2.0.docx`, `Энциклопедия современного трейдинга.docx` |
| Wyckoff + SMC equivalence | `Энциклопедический справочник трейдера.docx` (таблица эквивалентности) |
| Volume Profile + Triple Threat | `Энциклопедический справочник трейдера.docx`, `Образовательная торговая энциклопедия 3.docx` |
| Order Flow / DOM / Tape | `Торговая Энциклопедия 2.0.docx`, `Энциклопедия современного трейдинга.docx` |
| Elliott Wave | `Энциклопедический справочник трейдера.docx` |
| OTE / PD Arrays / Killzones | `Торговая Энциклопедия 2.0.docx` |
| Алгоритмы и формулы (ТЗ) | `Для реализации вашего запроса...docx`, `Дополнение к ТЗ.docx` |
| Разбор сделок (API3, VELVET, BTC) | `Ниже представлен детальный разбор...docx` |
| Задачник OTE/Liquidation/CHoCH | `Создай практический задачник...docx` |
| Таблицы Breaker/Mitigation, микроструктура | `.xlsx` файлы (2 шт) |
| Скриншоты графиков | 18 `.jpg` (27-28 июня 2026) |

## Ключевые концепции

### ADX-фильтр
| ADX | Режим | Инструменты |
|-----|-------|-------------|
| < 30 | Mean Reversion / Боковик | Stochastic, Bollinger Bounce, осцилляторы |
| > 30 | Тренд | MACD, SMC (BOS/CHoCH), Volume Profile |

### SMC: Структурные сломы
- **BOS** = Close > High(Previous_Swing_High) — продолжение тренда
- **CHoCH** = пробой последнего структ. минимума — смена характера
- **MSS** = CHoCH + Displacement (тело свечи > 1.5 × ATR(14)) — подтверждённый разворот

### Order Block (OB)
Валиден при 3 условиях:
1. Наличие displacement (импульс)
2. Создание BOS/CHoCH
3. Является последней противоположной свечой перед импульсом

### Fair Value Gap (FVG)
- Low[i-2] > High[i] → FVG
- CE (Consequent Encroachment) = 50% заполнения FVG

### Wyckoff
- Spring: Price < SC_Low (wick) + Body Close > SC_Low
- UTAD: Upthrust After Distribution — ложный пробой вверх
- Эквивалентность: Spring = SSL Sweep, UTAD = BSL Sweep, SOS = Bullish BOS, LPS = OB Retest/OTE

### Volume Profile
- Value Area = 68.2% общего объёма
- HVN: объём > 1.5× среднего = поддержка/сопротивление
- DynamicStep = ATR(14) × 0.2

### Order Flow
- Stacked Imbalance: ≥3 уровня Ask/Bid > 300%
- Iceberg: T&S Vol > 5 × Visible DOM Vol (при статичном размере)
- Passive Absorption: лимитный ордер поглощает рыночную агрессию
- CVD дивергенция: цена ↑, CVD ↓ = скрытая дистрибуция

### OTE / PD Arrays
- Premium = выше 50%, Discount = ниже 50%
- OTE = Fib 62%–79%, Sweet Spot = 70.5%
- IRL = FVGs + OB внутри ренджа, ERL = внешние экстремумы

### OI Trend Health (4 сценария)
| Цена | OI | Funding | Сигнал |
|------|----|---------|--------|
| ↑ | ↑ | нейтр. (~0.01%) | Здоровый тренд |
| ↑↑ | ↑ | > 0.05% | Leverage Flush (риск каскада) |
| ↑ | ↓ | — | Затухание (фиксация) |
| ↓↓ | ↓↓ | — | Капитуляция (дно) |

### Ликвидации
- Lp = Entry × (1 − 1/Leverage) для LONG
- Heatmap: агрегация Lp по всем плечам (10x–100x)

### Формулы индикаторов
- MACD Line = EMA₁₂(C) − EMA₂₆(C), Signal = EMA₉(MACD)
- Stochastic %K = (C − L₁₄)/(H₁₄ − L₁₄) × 100, %D = SMA₃(%K)
- Bollinger: Middle = SMA₂₀(C), Upper/Lower = ± 2σ

### Чек-лист A+ Setup (4 из 6)
1. MSS / BOS подтверждение
2. Снятие ликвидности (Sweep)
3. POI (OB или FVG)
4. OTE зона (62–79%)
5. Подтверждение OI (здоровый тренд)
6. Footprint (Imbalance / Absorption)

### ICT Killzones (EST)
- Asia: 19:00–22:00 (аккумуляция)
- London: 02:00–05:00 (манипуляция)
- New York: 07:00–10:00 (дистрибуция)
- London Close: 10:00–12:00 (реверс)

## Полные документы

Подробная документация в `docs/trading/`:
- `Учебник_институционального_трейдинга.md` — книга (30 глав + справочник + задачник)
- `Техническое_задание.md` — ТЗ для разработчиков (архитектура, схемы, API)
- `MidasFlow_JSON_Schema.md` — JSON-протокол MidasFlow Matrix v1.1.0

## MidasFlow Matrix v4.0 (главы 22-30 учебника)

- **Глава 22:** Operational Standards v4.0
- **Глава 23:** MidasFlow Grid 2.0 (33 уровня Fibo от -1.0 до 2.618)
- **Глава 24:** Fractal Mechanics + IPDA (look-back 20/40/60)
- **Глава 25:** Position Engineering (Scaling In 1/8 → 8/8)
- **Глава 26:** CRP + Shadow DOM
- **Глава 27:** 3-Tier Architecture (Raw → Micro → Structural)
- **Глава 28:** Backend (FastAPI + Polars + Numba)
- **Глава 29:** Frontend (WebGL + Datashader)
- **Глава 30:** Веб-терминал (UX Vataga/TigerTrade)

**Генератор JSON:** TradeHelp → Tools → MidasFlow Quick Builder
