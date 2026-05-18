# Trading Platform

**Демо:** https://trading-terminal.tradingview-widget.com/

## Описание

TradingView Trading Platform — это готовая торговая платформа для брокеров.

## Особенности

| Категория | Особенности |
|-----------|-------------|
| **Charts** | Полные TradingView графики |
| **Order Entry** | DOM, Market/Limit/Stop ордера |
| **Portfolio** | Позиции, P&L, история |
| **Market Watch** | Watchlist, alerts |
| **News** | Интегрированные новости |

## Интеграция

Интеграция Trading Platform требует:

1. **Broker API** — Ваш брокерский API
2. **TradingView License** — Commercial лицензия
3. **Technical Integration** — Подключение к TradingView

### Architecture

```
┌─────────────────────────────────────────────┐
│         TradingView Trading Platform         │
├─────────────────────────────────────────────┤
│  Charts │ Order Entry │ Portfolio │ News   │
└─────────────────────────────────────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │   Broker Connector  │
         │   (Your Backend)    │
         └──────────────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │   Broker API         │
         │   (Your Exchange)    │
         └──────────────────────┘
```

## Ресурсы

- [Trading Platform Demo](https://trading-terminal.tradingview-widget.com/)
- [Broker Integration Docs](https://www.tradingview.com/brokerage-integration/)

## Статус

⚠️ Trading Platform — это commercial продукт для брокеров. Не доступен для direct integration без партнёрства с TradingView.
