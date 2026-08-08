# Глава 19: Risk Management

## 19.1 Основы Position Sizing

### Fixed Fractional
```
Position Size = (Equity × Risk%) / StopDistance × 100
Risk% = 1-2% per trade
```

**Пример:** Equity $1000, Risk 1%, Stop distance 10% → Position $10 / 0.10 = $100

### Kelly Criterion
```
Kelly % = (RR × WinRate − (1 − WinRate)) / RR
Half-Kelly = Kelly / 2  (рекомендуется)
Quarter-Kelly = Kelly / 4  (консервативно)
```

**Пример:** RR=2, WinRate=55% → Kelly = (2×0.55 − 0.45)/2 = 0.325 = 32.5% (опасно!)
- Half-Kelly = 16.25%
- Quarter-Kelly = 8.125%

### ATR-based Stop
```
Stop (1× ATR) = Entry − ATR(14)
Stop (2× ATR) = Entry − 2×ATR(14)  ← рекомендуется
Stop (3× ATR) = Entry − 3×ATR(14)  ← для высокой волатильности
```

## 19.2 Liquidation Price

```
Lp (LONG) = Entry × (1 − 1/Leverage)
Lp (SHORT) = Entry × (1 + 1/Leverage)
```

**Пример API3 #4:** Entry 0.2992, 10x → Lp = 0.2693 (−10%)

## 19.3 Max Drawdown

### Max Consecutive Losses
```
Ruin = log(0.5) / log(1 − Risk%)
```

**Пример:** Risk 1% → max 69 убытков подряд до −50%
**Пример:** Risk 5% → max 13 убытков подряд до −50%

### Recovery Time
Чтобы восстановить −50% нужен +100%. Чтобы восстановить −20% нужен +25%.

**Правило:** фиксировать убыток быстрее, чем прибыль.

## 19.4 Portfolio Heat

```
Heat = Σ(Risk per position × Correlation)
```

**Правило:** Max heat 6% — если все позиции закроются по стопу одновременно.

## 19.5 Корреляции

Не открывать одновременно BTC LONG + ETH LONG (высокая корреляция = удвоенный риск).

**Матрица корреляций:**
| | BTC | ETH | SPX | GOLD |
|---|---|---|---|---|
| BTC | 1.0 | 0.85 | 0.30 | −0.20 |
| ETH | 0.85 | 1.0 | 0.25 | −0.10 |
| SPX | 0.30 | 0.25 | 1.0 | −0.40 |
| GOLD | −0.20 | −0.10 | −0.40 | 1.0 |

## 19.6 Funding Drag

При удержании позиции:
```
Daily funding cost = Funding × 3 × Leverage × Margin
```

**Пример:** 10x, $1000 маржи, Funding 0.05% → 0.0005 × 3 × 10 × 1000 = $15/день = 1.5% маржи.

**Правило:** при Funding > 0.05% — сокращать позицию или закрывать.
