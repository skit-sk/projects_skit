# Fundament RF — Трекер сделок и визуализация

Веб-приложение для учёта торговых сделок с графиками, аналитикой и интеграцией с биржей Bitget (REST + WebSocket).

## Структура проекта

```
01_fundament_rf/
├── app.py                          # Flask factory — 9 blueprints
├── models.py                       # FundObj dataclass
├── storage.py                      # JSONStorage (card/ subdir) + MetricsStorage
├── flask_runner.py                 # Watchdog автоперезапуск
├── bitget_checker.py               # CLI проверка позиций Bitget (HMAC-SHA256)
├── migrate_to_card.py              # Миграция data/* → data/card/
│
├── account/                        # Bitget private API (HMAC-SHA256)
│   ├── __init__.py                 # re-exports
│   ├── models.py                   # AssetBalance, Position, Order, Fill, AccountOverview
│   └── api_client.py               # BitgetAccountClient (8 методов)
│
├── api/                            # API-клиенты
│   ├── bitget_ws.py                # WebSocket Bitget (ticker, orderbook, OHLC, trades)
│   └── ma_data.py                  # CCXT загрузчик + кэширование
│
├── infographics/                   # Движки визуализации
│   ├── kpi.py                      # DashboardKPI (PnL, win-rate, distribution)
│   ├── equity.py                   # EquityAnalyzer (equity curve, drawdown)
│   ├── calendar.py                 # CalendarHeatmap (дневная разбивка)
│   ├── charts.py                   # DashboardCharts (Plotly)
│   ├── svg.py                      # SVGDashboard (inline SVG donut, KPI)
│   └── trade_analyzer.py           # TradeAnalyzer (8 MA, 7 стратегий, сигналы)
│
├── routes/                         # 9 Blueprint'ов
│   ├── __init__.py                 # Импорт всех routes
│   ├── api.py                      # Blueprint api — CRUD объектов, парсинг эмодзи
│   ├── web.py                      # Blueprint web — главная, карточка, range_demo
│   ├── graphics.py                 # Blueprint graphics — графики отклонения
│   ├── processor_1d.py             # Blueprint processor_1d — дневной OHLC + PnL
│   ├── dashboard.py                # Blueprint dashboard — KPI, equity, heatmap
│   ├── trade_analytics.py          # Blueprint trade-analytics — индикаторы
│   ├── ma_analytics.py             # Blueprint ma-analytics — MA backtesting
│   ├── ccxt_api.py                 # Blueprint ccxt-api — универсальный CCXT proxy
│   └── account_api.py              # Blueprint account-api — балансы, позиции, fills
│
├── templates/                      # 15+ шаблонов
│   ├── base.html                   # Базовый шаблон + навигация
│   ├── index.html                  # Главная (список объектов)
│   ├── card.html                   # Карточка сделки
│   ├── dashboard.html              # Dashboard (KPI, equity, heatmap, calendar)
│   ├── metrics.html                # Метрики процессора 1D
│   ├── trade_analytics.html        # Trade analyzer (RSI, MACD, EMA, pivots)
│   ├── ma_analytics.html           # MA backtesting
│   ├── ccxt_api.html               # CCXT API explorer
│   ├── range_variants_demo.html    # Демо вариантов range bar
│   ├── account/                    # 5 partial: overview, balance, positions, orders, fills
│   └── graphics/all.html           # Все графики
│
├── static/css/
│   ├── style.css                   # Базовая тема (light/dark)
│   ├── dashboard.css               # Dashboard
│   ├── ccxt_api.css                # CCXT explorer
│   ├── trade_analytics.css         # Trade analytics
│   └── range_variants_demo.css     # Range demo
│
├── data/
│   └── card/SYMBOL_HASH8/         # Карточки сделок (FundObj + 1D + RAW)
│
├── docs/
│   ├── account_full_plan.md        # План Account v2 (storage, analyzer)
│   └── account_ccxt_plan.md        # План Account через CCXT
│
└── AGENTS.md, structure.md, CARD_STRUCTURE.md, README.md
```

## Карта API

### 📄 Основные страницы

| Метод | URL | Blueprint | Описание |
|-------|-----|-----------|----------|
| GET | `/` | web | Главная (список объектов) |
| GET | `/card/<id>` | web | Карточка сделки |
| GET | `/delete/<id>` | web | Удаление (⚠️ GET) |
| GET | `/range_variants_demo` | web | Демо вариантов range bar |

### 🔧 API JSON

| Метод | URL | Blueprint | Описание |
|-------|-----|-----------|----------|
| POST | `/api/objects/from-emoji` | api | Создать из эмодзи-строки |
| GET | `/api/objects` | api | Список объектов |
| POST | `/api/objects` | api | Создать (JSON) |
| DELETE | `/api/objects/<id>` | api | Удалить |

### 📈 Графики

| Метод | URL | Blueprint | Описание |
|-------|-----|-----------|----------|
| GET | `/graphics/all` | graphics | Все графики |
| GET | `/graphics/chart/<id>` | graphics | JSON: OHLC + deviation |

### 📊 Dashboard

| Метод | URL | Blueprint | Описание |
|-------|-----|-----------|----------|
| GET | `/dashboard/` | dashboard | Dashboard страница |
| GET | `/dashboard/api/calendar` | dashboard | JSON календаря |

### 📐 Trade Analytics

| Метод | URL | Blueprint | Описание |
|-------|-----|-----------|----------|
| GET | `/trade-analytics/` | trade_analytics | Страница аналитики |
| GET | `/trade-analytics/api/<id>` | trade_analytics | JSON аналитики |
| GET | `/trade-analytics/dashboard/<id>` | trade_analytics | Страница для объекта |

### 📉 MA Analytics

| Метод | URL | Blueprint | Описание |
|-------|-----|-----------|----------|
| GET | `/ma-analytics/` | ma_analytics | MA backtesting |
| GET | `/ma-analytics/api/<id>` | ma_analytics | JSON MA анализа |

### 🌐 CCXT Proxy

| Метод | URL | Blueprint | Описание |
|-------|-----|-----------|----------|
| GET | `/ccxt-api/` | ccxt_api | CCXT explorer |
| GET | `/ccxt-api/api/exchanges` | ccxt_api | Список бирж |
| GET | `/ccxt-api/api/methods/<exchange>` | ccxt_api | Методы биржи |
| POST | `/ccxt-api/api/execute` | ccxt_api | Выполнить метод |
| GET | `/ccxt-api/api/env-keys` | ccxt_api | Ключи из .env |
| GET | `/ccxt-api/api/ws-stream` | ccxt_api | WebSocket SSE |

### 🔐 Account (Bitget Private API)

| Метод | URL | Blueprint | Описание |
|-------|-----|-----------|----------|
| GET | `/account-api/` | account_api | Страница аккаунта |
| GET | `/account-api/api/status` | account_api | Статус API ключей |
| GET | `/account-api/api/overview` | account_api | Equity + сводка |
| GET | `/account-api/api/balance` | account_api | Спот + фьючерсы |
| GET | `/account-api/api/positions` | account_api | Открытые позиции |
| GET | `/account-api/api/orders` | account_api | Ордера |
| GET | `/account-api/api/fills` | account_api | Сделки |
| GET | `/account-api/partial/*` | account_api | HTMX partials |

## Формат входных данных (эмодзи-строка)

```
🏗️[number] 🚏[symbol] 🔼/🔽 🧾[entry_price] 📆[entry_date] 🕒[days] 🧱[volume] 📈[pnl_percent] 🫧[pnl_usdt] 📦[result]
```

| Эмодзи | Поле | Описание |
|--------|------|----------|
| 🏗️ | number | Номер сделки |
| 🚏 | symbol | Торговая пара |
| 🔼/🔽 | hold_side | Long / Short |
| 🧾 | entry_price | Цена входа |
| 📆 | entry_date | Дата входа (YYYY-MM-DD) |
| 🕒 | entry_time | Дней в сделке |
| 🧱 | volume | Объём |
| 📈/📉 | pnl_percent | PnL в % |
| 🫧 | pnl_usdt | PnL в USDT |
| 📦 | result | 🟢 / 🔴 |

## Запуск

```bash
source scripts/source_env.sh           # загрузить .env
source venv/bin/activate               # активировать venv
./scripts/flask.sh start 01            # запуск на :5000
./scripts/flask.sh restart 01          # перезапуск
```

## Зависимости

- Flask 3.x
- CCXT (Bitget API)
- requests, websocket-client
- plotly, numpy, scipy
- htmx.org (JS, CDN)
