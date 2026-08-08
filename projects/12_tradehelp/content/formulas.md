# Все формулы (сводный блок — 60+ формул)

## Индикаторы

```
1.  MACD Line = EMA₁₂(C) − EMA₂₆(C)
2.  Signal Line = EMA₉(MACD Line)
3.  Stochastic %K = ((C − L₁₄) / (H₁₄ − L₁₄)) × 100
4.  Stochastic %D = SMA₃(%K)
5.  Bollinger Middle = SMA₂₀(C)
6.  Bollinger Upper = SMA₂₀(C) + 2σ
7.  Bollinger Lower = SMA₂₀(C) − 2σ
8.  VWAP = Σ(Pᵢ × Vᵢ) / ΣVᵢ
9.  Anchored VWAP = Σ_{t=t₀}^{T} (Pₜ × Vₜ) / Σ_{t=t₀}^{T} Vₜ
10. True Range = max(H−L, |H−Cₚ|, |L−Cₚ|)
11. ATR(14) = EMA₁₄(TR)
12. Normalized ATR = ATR(14) / Close × 100
13. Chaikin Vol = ((EMA₁₀(HL) − EMA₁₀(HL)₋₁) / EMA₁₀(HL)₋₁) × 100
14. Historical Vol = σ(ln(Cᵢ/Cᵢ₋₁)) × √252
15. Volatility Ratio = TR / ATR(14)
16. RSI = 100 − (100 / (1 + avg_gain / avg_loss))
17. ADX = 100 × EMA(DX, period)
18. DI+ = 100 × EMA(+DM, period) / ATR(period)
19. DI- = 100 × EMA(-DM, period) / ATR(period)
20. DX = 100 × |DI+ − DI-| / (DI+ + DI-)
```

## SMC / Wyckoff

```
21. Displacement Filter = Body_Size > 1.5 × ATR(14)
22. FVG (Bullish) = Low[i-2] > High[i]
23. FVG (Bearish) = High[i-2] < Low[i]
24. CE = FVG_bottom + (FVG_top − FVG_bottom) × 0.5
25. Spring = Price < SC_Low (wick) + Close > SC_Low
26. MSS = CHoCH + Body > 1.5 × ATR
27. EQH/EQL = |High[i] − High[i-1]| < 0.05% × Price
28. Body Close Rule: BOS_VALID = (Close > Swing_High) AND (Body_Size > 0)
29. 5-candle Fractal High: H[i] > H[i±1], H[i±2]
30. 5-candle Fractal Low: L[i] < L[i±1], L[i±2]
```

## OTE / PD Arrays

```
31. OTE 62% = SwingLow + Range × (1 − 0.62)
32. OTE 79% = SwingLow + Range × (1 − 0.79)
33. Sweet Spot (70.5%) = SwingLow + Range × (1 − 0.705)
34. Premium = price > 50% of range
35. Discount = price < 50% of range
36. IRL = FVGs + OB inside range
37. ERL = external extremes (PDH/PDL)
38. Mean Threshold (50% OB) = (proximal_line + distal_line) / 2
```

## MidasFlow Grid 2.0 (33 уровня)

```
39.  Level 33 = SwingLow + Range × (-1.000)   # Full Hunt Target
40.  Level 30 = SwingLow + Range × (-0.705)   # Maximum Pain Point
41.  Level 28 = SwingLow + Range × (-0.500)   # Manipulation Mid
42.  Level 25 = SwingLow + Range × (-0.270)   # Primary Hunt Zone
43.  Level 22 = SwingLow + Range × 0.000     # Range Origin
44.  Level 27 = SwingLow + Range × 0.500     # Equilibrium
45.  Level 29 = SwingLow + Range × 0.618     # OTE Start
46.  Level 30 = SwingLow + Range × 0.705     # Sniper Entry (Sweet Spot)
47.  Level 31 = SwingLow + Range × 0.786     # OTE Deep
48.  Level 33 = SwingLow + Range × 1.000     # Invalidation
49.  Level 36 = SwingLow + Range × 1.236     # Early Deviation
50.  Level 40 = SwingLow + Range × 1.618     # Whale Trap Alpha
51.  Level 44 = SwingLow + Range × 2.000     # Cycle Double
52.  Level 45 = SwingLow + Range × 2.618     # Whale Trap Beta
```

**Sweet Spot Formula:**
```
Sniper Entry (0.705) = (0.618 + 0.786) / 2 = 0.702 ≈ 0.705
```

## Order Flow

```
53. Order Book Imbalance = (BidVol − AskVol) / (BidVol + AskVol)
54. BAVR = Ask / (Ask + Bid)
55. Aggressive Imbalance = Ask(price) / Bid(price−1) > 3.0
56. Iceberg = T&S Vol > 5 × DOM Vol (static DOM)
57. Stacked Imbalance = ≥3 levels with Ask/Bid > 300%
58. CVD = Σ(AskVol − BidVol)
59. Delta = V(ask) − V(bid)
60. CRP POC Position:
    - Lower_Third: (POC - Low) / Range < 0.33
    - Upper_Third: (POC - Low) / Range > 0.67
    - Middle_Third: 0.33 ≤ (POC - Low) / Range ≤ 0.67
61. Value Area (VA) = 68.2% of total volume (sorted)
62. D-Shape: lower_vol > upper_vol × 1.5
63. P-Shape: upper_vol > lower_vol × 1.5
64. HVN Threshold: vol > avg_vol × 1.5
65. LVN: vol < avg_vol × 0.5
```

## Derivatives

```
66. Lp (LONG) = Entry × (1 − 1/Leverage)
67. Lp (SHORT) = Entry × (1 + 1/Leverage)
68. Funding Drag = FundingRate × 3 × Days × Leverage
69. Elliott Expanded Flat B = 105–138% × A
70. Elliott Expanded Flat C = 162% × A
```

## Risk Management

```
71. Position Size = (Equity × Risk%) / StopDistance × 100
72. Kelly % = (RR × WinRate − (1 − WinRate)) / RR
73. Half-Kelly = Kelly / 2
74. Quarter-Kelly = Kelly / 4
75. ATR Stop (1×) = Entry − ATR(14)
76. ATR Stop (2×) = Entry − 2 × ATR(14)
77. Max Consecutive Losses = log(0.5) / log(1 − Risk%)
78. Sharpe = (avg_return − risk_free) / std_dev
79. Sortino = (avg_return − risk_free) / downside_dev
80. Profit Factor = Σ Wins / Σ Losses
81. Expectancy = (WinRate × AvgWin) − (LossRate × AvgLoss)
82. CRITICAL_RECOVERY: |unrealized_pl| > margin_size
```

## Position Engineering (Scaling)

```
83. Entry 1/8 = MSS + Displacement
84. Entry 2/8 = OTE zone (62-79%)
85. Entry 3/8 = BOS + Body Close
86. Max 8/8 = All confirmed
87. TP 1/4 = 1.236 (Early Deviation)
88. TP 2/4 = 1.618 (Whale Trap Alpha)
89. TP 3/4 = 2.000 (Cycle Double)
90. TP 4/4 = 2.618 (Whale Trap Beta)
```

## IPDA (Institutional Price Delivery)

```
91. Look-back Short = 20 (days)
92. Look-back Mid = 40
93. Look-back Long = 60
94. Tier 1 → Tier 2: Normalization
95. Tier 2 → Tier 3: Pattern Recognition
96. Tier 3 → Geometry: Fibo Grid Application
```

## Volume Profile

```
97. DynamicStep = ATR(14) × 0.2
98. POC = argmax(price_volumes)
99. VAH/VAL = max/min(prices in 68.2% cumulative volume)
100. HVN = level.volume > 1.5 × avg_volume
101. LVN = level.volume < 0.5 × avg_volume
```

## On-Chain

```
102. MVRV = Market Cap / Realized Cap
103. SOPR = Σ(Spent Value USD) / Σ(Cost Basis USD)
104. NVT = Network Cap / Daily Transaction Volume
```

## Backtesting

```
105. OOS Sharpe = Sharpe on out-of-sample data
106. Calmar = CAGR / Max Drawdown
107. Expectancy = Avg Win × WinRate − Avg Loss × LossRate
```

## MidasFlow Risk Flags

```
108. PnL -100%: unrealized_pl = -100% × margin
109. PnL -200%: unrealized_pl = -200% × margin
110. CRITICAL_RECOVERY: |PL| > margin
111. MARGIN_WARNING: used_margin > 70% × equity
112. FUNDING_DRAG: funding > 0.05% / day
```

## JSON Protocol

```
113. matrix_metadata.protocol_version = "1.1.0"
114. crp_ribbons.phase ∈ {Accumulation, Manipulation, Distribution, Re-entry}
115. market_structure.bias ∈ {Bullish, Bearish, Neutral}
116. market_structure.last_break ∈ {BOS, CHoCH, MSS, None}
117. liquidity_pools.current_cycle ∈ {ERL_to_IRL, IRL_to_ERL, None}
```

## 3-Tier Architecture

```
118. Tier 1 (Raw): Normalized ticks, OHLCV
119. Tier 2 (Microstructure): Delta, CVD, Imbalance, VP
120. Tier 3 (Structural): BOS, MSS, OB, FVG, Grid
```

## Top-Down Protocol

```
121. D1/H4 → Macro Bias, ERL
122. H1 → Structure, BOS, CHoCH, MSS, IRL
123. M15/M5 → FVG, OB retest
124. M1 → Tape reading
```

## Swift Entry / Stop Levels

```
125. Sniper Entry = 0.705 × Range from Low
126. Last Stand = 0.786 × Range from Low
127. Invalidation = 1.000 × Range from Low (MSS level)
128. TP Conservative = 1.236 × Range
129. TP Aggressive = 1.618 × Range
130. TP Cycle = 2.000 × Range
131. TP Max = 2.618 × Range
```

## AI-манифест: визуализация промптов

См. `docs/Иллюстрации_AI_manifest.md` — готовые промпты для DALL-E 3, Flux 2, Veo 3.1.
