# Глава 20: Backtesting и валидация

## 20.1 Методология Backtesting

### Типы
- **In-sample (IS):** На этих данных модель обучается
- **Out-of-sample (OOS):** Проверка на незнакомых данных
- **Walk-forward:** Окно IS → OOS → сдвиг → повтор

### Walk-Forward пример
```
Window 1: IS[2020-2022] → OOS[2023]     → score 1.5
Window 2: IS[2020-2023] → OOS[2024]     → score 1.7
Window 3: IS[2020-2024] → OOS[2025]     → score 1.4
Average score: 1.53 → стратегия валидна
```

## 20.2 Метрики

### Основные
- **Win Rate:** % прибыльных сделок (target 50-60%)
- **Profit Factor:** Σ Wins / Σ Losses (target > 1.5)
- **Sharpe Ratio:** (avg return − risk free) / std dev (target > 1.5)
- **Sortino:** как Sharpe, но только downside deviation
- **Max Drawdown:** максимальное падение equity (target < 20%)
- **Avg R:R:** средний risk/reward (target > 2.0)
- **Expectancy:** (WinRate × AvgWin) − (LossRate × AvgLoss)

### Дополнительные
- **Calmar Ratio:** Annual Return / Max Drawdown (target > 3.0)
- **Recovery Factor:** Total Profit / Max DD
- **CAGR:** Compound Annual Growth Rate
- **Consecutive Wins/Losses**

## 20.3 Ошибки Backtesting

### Overfitting (переоптимизация)
Стратегия подогнана под историю, не работает в реале.

**Противоядие:** Out-of-sample testing, walk-forward, минимальное кол-во параметров.

### Look-Ahead Bias
Использование данных, которые были бы недоступны в момент сделки.

**Противоядие:** Строгий порядок: в момент T доступны только данные до T.

### Survivorship Bias
Тестирование только на активах, которые "выжили" (не делистнулись).

**Противоядие:** Включать делистнутые/обанкротившиеся активы.

### Slippage & Fees
Игнорирование реальных транзакционных издержек.

**Типичные значения:**
- Spot: 0.1% fee
- Futures maker: 0.02%, taker: 0.04%
- Slippage: 0.05-0.5% (зависит от ликвидности)

## 20.4 Monte Carlo

Рандомизация порядка сделок для оценки:
- Распределения Max DD
- Вероятности Ruin
- 95% confidence interval для equity curve

## 20.5 Paper Trading

Перед живыми деньгами:
1. 30+ сделок на бумаге
2. Win Rate > 50%, Profit Factor > 1.3
3. 3+ месяца стабильных результатов
4. Затем переход на 0.25× от целевого размера

## 20.6 Бенчмарки

| Категория | Целевой Sharpe | Целевой Max DD |
|-----------|----------------|----------------|
| Систематический тренд | > 0.8 | < 25% |
| Mean reversion | > 1.2 | < 15% |
| SMC / Wyckoff | > 1.0 | < 20% |
| Order Flow | > 1.5 | < 12% |
| Buy & Hold BTC | ~ 0.7 | ~ 80% |
