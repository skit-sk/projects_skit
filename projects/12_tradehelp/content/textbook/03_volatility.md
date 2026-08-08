# Глава 3: Индикаторы волатильности

## 3.1 ATR (Average True Range)

```
True Range = max(H − L, |H − C_prev|, |L − C_prev|)
ATR(14) = EMA₁₄(TR)
```

**Применение:**
- **Displacement Filter:** Body > 1.5 × ATR(14) = валидный MSS
- **DynamicStep** = ATR(14) × 0.2 (шаг Volume Profile)
- **Стоп-лосс:** 1.5–2 × ATR от точки входа

## 3.2 Bollinger Bands

```
Middle = SMA₂₀(C)
Upper = SMA₂₀(C) + 2σ
Lower = SMA₂₀(C) − 2σ
```

**Применение:**
- Squeeze → предвестник импульса
- Bounce от границ при ADX < 30
- Пробой при ADX > 30 = усиление тренда

## 3.3 Keltner Channels

```
Middle = EMA₂₀(C)
Upper = EMA₂₀(C) + ATR(14) × 2
Lower = EMA₂₀(C) − ATR(14) × 2
```

## 3.4 Historical Volatility (HV)

```
HV = σ(ln(Cᵢ / Cᵢ₋₁)) × √252
```

## 3.5 Chaikin Volatility

```
Chaikin Vol = ((EMA₁₀(HL) − EMA₁₀(HL)₋₁) / EMA₁₀(HL)₋₁) × 100
```

## 3.6 Normalized ATR

```
NATR = ATR(14) / Close × 100
```

Позволяет сравнивать волатильность активов с разной ценой.

## 3.7 Volatility Ratio (VR)

```
VR = TR / ATR(14)
```

VR > 3 = экстремальная свеча (возможный разворот).
