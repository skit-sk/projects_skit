# Structure — Fundament RF

## Общая структура

```
01_fundament_rf/
├── app.py                          # Flask factory — 9 blueprints
├── models.py                       # FundObj dataclass
├── storage.py                      # JSONStorage (card/) + MetricsStorage
├── flask_runner.py                 # Watchdog автоперезапуск
├── bitget_checker.py               # CLI Bitget positions (HMAC-SHA256)
├── migrate_to_card.py              # Миграция data/* → data/card/
│
├── account/                        # Bitget private API
│   ├── __init__.py
│   ├── models.py                   # AssetBalance, Position, Order, Fill, ...
│   └── api_client.py               # BitgetAccountClient (HMAC-SHA256)
│
├── api/
│   ├── bitget_ws.py                # WebSocket Bitget public channels
│   └── ma_data.py                  # CCXT MADataLoader
│
├── infographics/                   # Движки визуализации
│   ├── kpi.py                      # DashboardKPI
│   ├── equity.py                   # EquityAnalyzer
│   ├── calendar.py                 # CalendarHeatmap
│   ├── charts.py                   # DashboardCharts (Plotly)
│   ├── svg.py                      # SVGDashboard
│   └── trade_analyzer.py           # TradeAnalyzer (MA, RSI, MACD, pivots)
│
├── routes/                         # 9 Blueprint'ов
│   ├── __init__.py                 # Импорт всех routes
│   ├── api.py                      # CRUD объектов, парсинг эмодзи
│   ├── web.py                      # Главная, карточка, range_demo
│   ├── graphics.py                 # Графики отклонения цены
│   ├── processor_1d.py             # Дневной OHLC + PnL
│   ├── dashboard.py                # KPI, equity, heatmap, calendar
│   ├── trade_analytics.py          # Trade analyzer
│   ├── ma_analytics.py             # MA backtesting
│   ├── ccxt_api.py                 # CCXT proxy
│   └── account_api.py              # Account overview
│
├── templates/
│   ├── base.html                   # Базовый шаблон + навигация
│   ├── index.html                  # Главная
│   ├── card.html                   # Карточка сделки
│   ├── dashboard.html              # Dashboard
│   ├── metrics.html                # Метрики
│   ├── trade_analytics.html        # Trade analyzer
│   ├── ma_analytics.html           # MA backtesting
│   ├── ccxt_api.html               # CCXT explorer
│   ├── range_variants_demo.html    # Range bar demo
│   ├── account/                    # 5 partial: overview, balance, positions, orders, fills
│   └── graphics/all.html           # Все графики
│
├── static/css/
│   ├── style.css                   # Базовая тема (light/dark)
│   ├── dashboard.css               # Dashboard
│   ├── ccxt_api.css                # CCXT
│   ├── trade_analytics.css         # Trade analytics
│   └── range_variants_demo.css     # Range demo
│
├── data/card/SYMBOL_HASH8/         # — карточки сделок
│
├── docs/
│   ├── account_full_plan.md
│   └── account_ccxt_plan.md
│
├── venv/
├── AGENTS.md, README.md, structure.md, CARD_STRUCTURE.md
└── *.log
```

## Все Blueprint'ы

### `api` (префикс `/api`)
| Маршрут | Функция | Описание |
|---------|---------|----------|
| `GET /objects` | `list_objects` | Список объектов |
| `POST /objects` | `create_object` | Создать (JSON) |
| `POST /objects/from-emoji` | `create_from_emoji` | Создать из эмодзи |
| `DELETE /objects/<id>` | `delete_object` | Удалить |

### `web` (без префикса)
| Маршрут | Функция | Описание |
|---------|---------|----------|
| `GET /` | `index` | Главная |
| `GET /obj/<id>` | `get_object` | Карточка (прямой) |
| `GET /card/<id>` | `card` | Карточка с графиком |
| `GET /delete/<id>` | `delete_object` | Удаление (⚠️ GET)|
| `GET /range_variants_demo` | `range_variants_demo` | Демо range bar |

### `graphics` (префикс `/graphics`)
| Маршрут | Функция | Описание |
|---------|---------|----------|
| `GET /all` | `all_charts` | Все графики |
| `GET /chart/<id>` | `chart` | JSON графика |

### `processor_1d` (префикс `/processor_1d`)
| Маршрут | Функция | Описание |
|---------|---------|----------|
| `GET /metrics` | `metrics_page` | Метрики |
| `POST /create/<id>` | `create_1d` | Создать 1D данные |
| `GET /status/<id>` | `status_1d` | Статус 1D |

### `dashboard` (префикс `/dashboard`)
| Маршрут | Функция | Описание |
|---------|---------|----------|
| `GET /` | `index` | Dashboard страница |
| `GET /api/calendar` | `calendar_data` | JSON календаря |

### `trade_analytics` (префикс `/trade-analytics`)
| Маршрут | Функция | Описание |
|---------|---------|----------|
| `GET /` | `index` | Страница аналитики |
| `GET /dashboard/<id>` | `dashboard` | Аналитика по объекту |
| `GET /api/<id>` | `api_data` | JSON аналитики |
| `GET /api/list` | `api_list` | Список объектов |

### `ma_analytics` (префикс `/ma-analytics`)
| Маршрут | Функция | Описание |
|---------|---------|----------|
| `GET /` | `index` | MA backtesting |
| `GET /api/<id>` | `api_data` | JSON MA анализа |

### `ccxt_api` (префикс `/ccxt-api`)
| Маршрут | Функция | Описание |
|---------|---------|----------|
| `GET /` | `index` | CCXT explorer |
| `GET /api/exchanges` | `list_exchanges` | Список бирж |
| `GET /api/methods/<exchange>` | `get_methods` | Методы биржи |
| `POST /api/execute` | `execute_method` | Выполнить метод |
| `GET /api/env-keys` | `env_keys` | Ключи из .env |
| `GET /api/ws-stream` | `ws_stream` | WebSocket SSE |

### `account_api` (префикс `/account-api`)
| Маршрут | Функция | Описание |
|---------|---------|----------|
| `GET /` | `index` | Страница аккаунта |
| `GET /api/status` | `api_status` | Статус ключей |
| `GET /api/overview` | `api_overview` | Equity + сводка |
| `GET /api/balance` | `api_balance` | Спот + фьючерсы |
| `GET /api/positions` | `api_positions` | Позиции |
| `GET /api/orders` | `api_orders` | Ордера |
| `GET /api/fills` | `api_fills` | Сделки |
| `GET /partial/*` | `partial_*` | HTMX partials |

## Модель данных

### `FundObj` (models.py)
```python
@dataclass
class FundObj:
    id: str              # UUID4
    obj_type: str        # тип (сделка)
    name: str            # название
    data: dict           # emoji_entry, emoji_upd, ohlc, stats, ranges, ...
    created_at: datetime
    updated_at: datetime
```

### `BitgetAccountClient` (account/api_client.py)
- HMAC-SHA256 подпись
- 8 методов: `get_spot_assets`, `get_mix_accounts`, `get_positions`, `get_spot_orders`, `get_mix_orders`, `get_spot_fills`, `get_mix_fills`, `fetch_all_fills`
- Поддержка пагинации (`idLessThan` cursor)

## Хранилище

### `JSONStorage` → `data/card/SYMBOL_HASH8/`
- `{uuid}.json` — FundObj
- `{uuid}_1D.json` — дневной OHLC + summary
- `{uuid}_RAW.json` — сырые свечи с Bitget

## Запуск

```bash
source scripts/source_env.sh
./scripts/flask.sh start 01        # порт 5000
./scripts/flask.sh restart 01      # перезапуск
./scripts/flask.sh stop 01         # остановка
```

## Критические замечания

| Проблема | Локация | Статус |
|----------|---------|--------|
| Path Traversal | `storage.py` | ⚠️ Не исправлено |
| CSRF на GET /delete | `web.py` | ⚠️ Не исправлено |
| sys.path.insert хрупкий | `app.py` | ⚠️ Не исправлено |
| Ключи в .env (не .gitignore) | корень workspace | ⚠️ Риск коммита |
