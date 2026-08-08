# Глава 11: Order Flow — поток ордеров и книга заявок

## 11.1 Глубина рынка (DOM / Level 2)

**Bid/Ask Walls:** Крупные лимитные заявки, создающие искусственные стены.

**Order Book Imbalance:**
```
Imbalance = (BidVolume − AskVolume) / (BidVolume + AskVolume)
```
- Imbalance > 0.3 = бычье давление
- Imbalance < -0.3 = медвежье давление

**Bid-Ask Volume Ratio (BAVR):**
```
BAVR = AskVolume / (AskVolume + BidVolume)
```

**Order Book Slope:** Скорость уменьшения объёма от лучшей цены. Крутой slope = мало ликвидности за уровнем.

**Cancel-Replace Velocity:** Скорость отмен/замен заявок. Высокая = спуфинг (фейковые стены).

## 11.2 Лента сделок (Time & Sales)

**Tape Speed:** Количество принтов в секунду.
- Ускорение при подходе к уровню = ритейл-паника
- Slow tape = отсутствие интереса

**Iceberg Orders:**
```
Iceberg = T&S Vol(price L, time T) > 5 × Visible DOM(price L)
при условии Visible Size не уменьшается (мгновенное обновление)
```

**The Axe:** Доминирующий маркет-мейкер или ECN, защищающий сторону стакана.

**Dark Pool Prints:** Внебиржевые блоки с кодами 'D' или 'T' (35-40% объёма США). Кластеры таких принтов = предвестники публичного движения.

## 11.3 Кластерный анализ (Footprint)

**Aggressive Imbalance:**
```
Ask(price) / Bid(price − 1 step) > 3.0 (300%)
```

**Stacked Imbalance:** Три и более последовательных уровней в одной свече с Ask/Bid > 300%.

**Passive Absorption:** Поглощение рыночной агрессии лимитной заявкой, препятствующее расширению свечи.

## 11.4 Delta и CVD

```
Delta = V(ask) − V(bid)
CVD = Σ(AskVol − BidVol)
```

**Медвежья дивергенция:** Цена растёт, CVD падает = скрытые продажи лимитами.

## 11.5 Онлайн-индикаторы Order Flow

| Индикатор | Формула | Назначение |
|-----------|---------|------------|
| Real-Time CVD | Σ(Buy − Sell) per bar | Накопительная дельта |
| Order Flow Imbalance | (Buy−Sell)/(Buy+Sell) | Давление потока |
| BAVR | Ask/(Ask+Bid) | Перекос книги |
| Tape Speed | Принты/сек | Ритейл-активность |
| DOM Liquidity Heatmap | Bid/Ask по ценам | Концентрация лимитников |
