# URL / Port Map

| Проект | ID | Порт | Entry URL | Sandbox URL | Запуск |
|---|---|---|---|---|---|
| Fundament RF | 01 | 5000 | `http://localhost:5000/` | `http://localhost:5000/` | `./scripts/flask.sh start 01` |
| Graphs Candle | 02 | 5005 | `http://localhost:5005/` | `http://localhost:5000/proxy/02/` | `./scripts/flask.sh start 02 5005` |
| Demo Charts ASCII | 03 | 5003 | `http://localhost:5003/` | `http://localhost:5000/proxy/03/` | `./scripts/flask.sh start 03 5003` |
| TradingView Demos | 04 | — | `projects/04_tradingview-demos/index.html` | `http://localhost:5000/static/sandbox/04/index.html` | Статика |
| Transcript | 05 | — | CLI | — | `python transcript_pipeline.py <url>` |
| Screenshots Catalog | 06 | — | `projects/06_screenshots_project/catalog.html` | `http://localhost:5000/static/sandbox/06/catalog.html` | Статика |
| TG Bot AIForGuest | 07 | — | — | — | `./scripts/tg_bot.sh start` |
| OFD API | 08 | 5000 | `http://localhost:5000/ofd-api/` | `http://localhost:5000/ofd-api/` | Внутри 01 |
| Model Catalog | 09 | 5000 | `http://localhost:5000/ai-models/` | `http://localhost:5000/ai-models/` | Внутри 01 |
| MAX Bot | 10 | — | — | — | `./projects/10_max_bot/scripts/max_bot.sh start` |
| Med Life | 11 | 5000 | `http://localhost:5000/med-life/` | `http://localhost:5000/med-life/` | Внутри 01 |

## Ключевые маршруты 01

| Маршрут | Описание |
|---|---|
| `/` | Главная |
| `/dashboard/` | Dashboard |
| `/sandbox/` | Sandbox UI |
| `/kb/` | Knowledge Base |
| `/viz-lab/` | Viz Lab (внутри 01) |
| `/med-life/` | Med Life Atlas |
| `/ofd-api/` | OFD API |
| `/ai-models/` | Model Catalog |
| `/ccxt-api/` | CCXT API Explorer |
| `/proxy/02/` | Proxy к Graphs Candle |
| `/proxy/03/` | Proxy к Demo Charts ASCII |
| `/static/sandbox/04/` | TradingView Demos |
| `/static/sandbox/06/` | Screenshots Catalog |

## Связанные KB

- [Архитектура workspace](architecture-overview.md)
- [Реестр модулей](module-registry.md)
