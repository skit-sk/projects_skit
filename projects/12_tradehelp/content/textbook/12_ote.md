# Глава 12: OTE и зоны ликвидности

## 12.1 PD Arrays (Premium vs Discount)

Торговый диапазон делится на зоны:
- **Premium Zone:** Выше 50% диапазона — зона для продаж
- **Discount Zone:** Ниже 50% диапазона — зона для покупок

**Аксиома:** Продажи разрешены только в Premium, покупки — только в Discount.

## 12.2 OTE (Optimal Trade Entry)

**Формула:**
```
OTE = Fib(62%) до Fib(79%) коррекции
Sweet Spot = 70.5%
```

**Расчёт на примере BTC ($60K → $70K):**
- 62% = $63,800
- 79% = $62,100
- Sweet Spot = $62,950

**Институциональная логика:** Вход в OTE обеспечивает наилучшее RR, стоп за 100% (начало импульса).

## 12.3 IRL vs ERL

- **IRL (Internal Range Liquidity):** FVGs и Order Blocks внутри диапазона
- **ERL (External Range Liquidity):** Внешние экстремумы — PDH (Previous Day High), PDL (Previous Day Low)

## 12.4 Магниты ликвидности

**EQH (Equal Highs) / EQL (Equal Lows):**
- Поиск зон, где разница между соседними экстремумами < 0.05% × Price
- Магниты для цены — при подходе ожидается Sweep

**DOL (Draw on Liquidity):** Внешняя ликвидность (PDH/PDL) — главный ценовой магнит.
