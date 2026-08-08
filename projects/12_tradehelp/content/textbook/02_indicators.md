# Глава 2: Классические индикаторы

## 2.1 MACD (Moving Average Convergence Divergence)

```
MACD Line = EMA₁₂(C) − EMA₂₆(C)
Signal Line = EMA₉(MACD Line)
MACD Histogram = MACD Line − Signal Line
```

**Применение:**
- Пересечение MACD/Signal = сигнал
- Гистограмма = ускорение/замедление тренда
- Дивергенция: цена ↑, MACD ↓ = ослабление тренда

## 2.2 Stochastic Oscillator

```
%K = ((C − L₁₄) / (H₁₄ − L₁₄)) × 100
%D = SMA₃(%K)
```

**Применение:**
- %K > 80 = перекупленность
- %K < 20 = перепроданность
- Пересечение %K и %D
- Дивергенции

## 2.3 RSI (Relative Strength Index)

```
RSI = 100 − (100 / (1 + RS))
RS = Average Gain / Average Loss (за 14 периодов)
```

**Применение:**
- RSI > 70 = перекупленность
- RSI < 30 = перепроданность
- Regular / Hidden Divergences

## 2.4 VWAP (Volume-Weighted Average Price)

```
VWAP = Σ(Pᵢ × Vᵢ) / ΣVᵢ
```

**Применение:**
- Anchored VWAP — закреплён на значимом экстремуме
- Цена > VWAP = бычий уклон
- Отскок от VWAP = институциональная поддержка
