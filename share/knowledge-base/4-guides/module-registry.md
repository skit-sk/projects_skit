# Module Registry

Реестр ключевых модулей и сервисов workspace.

## 01 Fundament RF

| Модуль | Путь | Назначение | Потребители |
|---|---|---|---|
| Flask factory | `app.py` | Регистрация blueprint'ов, запуск приложения | 01 |
| JSONStorage | `storage.py` | Хранение карточек сделок | 01 |
| BitgetAccountClient | `account/api_client.py` | Private API Bitget | 01 |
| Bitget WS | `api/bitget_ws.py` | WebSocket рынка | 01 |
| DashboardKPI | `infographics/kpi.py` | KPI-дашборд | 01 |
| EquityAnalyzer | `infographics/equity.py` | Equity curve, drawdown | 01 |
| TradeAnalyzer | `infographics/trade_analyzer.py` | Индикаторы и сигналы | 01 |
| Sandbox UI | `routes/sandbox.py` | UI песочницы | 01 |
| Proxy | `routes/proxy.py` | Reverse proxy к satellite | 02, 03 |
| HTML Patcher | `services/proxy_html_patcher.py` | Патчинг ссылок в proxy | 01 |
| Health Aggregator | `services/health_aggregator.py` | Сбор статусов проектов | 01 |
| Market Data Provider | `services/market_data_provider.py` | Поставка рыночных данных | 01 |
| TradingView Playground | `services/tv_playground.py` | TradingView интеграция | 01 |
| Code Sandbox | `services/code_sandbox.py` | Песочница кода | 01 |
| Med Life Loader | `services/med_life_loader.py` | Загрузка мед. данных | 01 |
| Med Life Routes | `routes/med_life.py` | Атлас и паспорт состояния | 01 |

## 02 Graphs Candle

| Модуль | Путь | Назначение | Потребители |
|---|---|---|---|
| Flask app | `main.py` | Entry point | 02 |
| Graphics routes | `routes/graphics.py` | Plotly/SVG графики | 02 |

## 03 Demo Charts ASCII

| Модуль | Путь | Назначение | Потребители |
|---|---|---|---|
| Chart generators | `generators/*.py` | asciichart, plotext, termgraph, summary | 03 |
| ASCII models | `charts.py` | 14 моделей инфографики | 03 |
| Data loader | `app.py` | Fallback на 01/data/card/ | 03 |

## 04 TradingView Demos

| Модуль | Путь | Назначение | Потребители |
|---|---|---|---|
| Widget generator | `fix_widgets.py` | Регенерация preview/full | 04 |
| Full-page generator | `update_widgets.py` | Генерация `widgets-full/*.html` | 04 |

## 07 / 10 Bots

| Модуль | Путь | Назначение | Потребители |
|---|---|---|---|
| Shared tools | `tools/scripts/` | Общие утилиты | 07, 10 |
| OFD bot module | `projects/08_ofd_api/bot_ofd/` | OFD для ботов | 07 |

## 09 Model Catalog

| Модуль | Путь | Назначение | Потребители |
|---|---|---|---|
| models_catalog.json | `models_catalog.json` | Реестр AI-моделей | 05, 07, 10, 01 |

## Связанные KB

- [Архитектура workspace](architecture-overview.md)
- [Матрица связей](project-links-matrix.md)
