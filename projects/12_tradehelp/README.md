# TradeHelp v3

> Обучающая платформа по институциональному трейдингу на основе реальных данных проекта 01 (Fundament RF)

## Назначение

TradeHelp объединяет:

- **📚 Учебник** (21 глава) — от индикаторов до on-chain и психологии
- **📈 Визуализацию** в 3 режимах:
  - **Plotly** (интерактивные HTML, hover/zoom)
  - **TradingView Lightweight Charts** (мини-графики в учебнике)
  - **TradingView Embed Widgets** (полноценный TradingView: heatmap, market, calendar)
- **🔴 Live-дашборд** из `01_fundament_rf/data/account/` (balance, orders, fills, totals)
- **🛠 Инструменты:** торговый журнал, pre-trade чек-лист, Risk Calculator, Confluence Score
- **📋 Справочники:** глоссарий, формулы, чек-листы, задачник
- **🤖 AI-манифест** — готовые промпты для DALL-E 3, Flux 2, Veo 3.1

## Запуск

```bash
# Через общий скрипт
./scripts/flask.sh start 12 5012

# Или напрямую
cd projects/12_tradehelp
source ../../venv/bin/activate
python app.py
# → http://127.0.0.1:5012/
```

## Маршруты

| URL | Назначение |
|-----|------------|
| `/` | Главная — навигация по разделам |
| `/learn/` | Учебник (21 глава) |
| `/learn/<slug>` | Конкретная глава (slug = `01_intro`, `02_indicators`, ...) |
| `/viz/` | Дашборд интерактивных графиков (Plotly) |
| `/viz/candles` | Свечной график с индикаторами |
| `/viz/volume-profile` | Volume Profile (POC, VA, HVN/LVN) |
| `/viz/footprint` | Order Flow / Footprint |
| `/viz/onchain` | On-Chain метрики (MVRV, SOPR, NVT) |
| `/viz/sentiment` | Sentiment дашборд |
| `/tv/` | TradingView Widgets grid (10 виджетов) |
| `/tv/advanced` | Advanced Chart (fullscreen) |
| `/live/` | Live portfolio из `01_fundament_rf/data/account/` |
| `/tools/journal` | Торговый журнал (из fills.json) |
| `/tools/checklist` | Pre/Post-trade чек-листы |
| `/tools/risk` | Risk Calculator (Kelly, position sizing) |
| `/api/klines?symbol=...` | Прокси к Binance (для LWC) |
| `/api/live/balance\|orders\|fills\|totals` | JSON из account/ |
| `/api/score` | POST → Confluence Score |

## Источники данных

```
projects/12_tradehelp/data/
├── live/       → symlink → 01_fundament_rf/data/account/
│   ├── balance.json
│   ├── orders.json
│   ├── fills.json
│   └── totals.json
└── history/    → symlink → 01_fundament_rf/data/card/
    ├── API3_*/..._1D.json
    ├── ATOM_*/..._1D.json
    ├── ADA_*/..._1D.json
    └── ETH_*/..._1h.json
```

## Стиль: Dark + Institutional

```css
--bg-primary: #0d1117    /* GitHub dark */
--bg-elevated: #21262d
--accent-blue: #58a6ff
--accent-green: #3fb950
--accent-red: #f85149
--accent-yellow: #d29922
--accent-purple: #bc8cff
```

Шрифт: **Inter** (заголовки), **JetBrains Mono** (данные, формулы), **IBM Plex Sans** (тело).

## Стек

- **Backend:** Flask 3, Python 3.12
- **Frontend:** vanilla JS, Plotly.js (CDN), TradingView Lightweight Charts 5.2.0
- **Live polling:** JavaScript `setInterval` (30 сек) для live-дашборда
- **Storage:** JSON-файлы (account/ + card/ из проекта 01)

## Структура

```
projects/12_tradehelp/
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── routes/                   # 7 blueprint'ов
│   ├── main.py learning.py viz.py tv.py live.py tools.py api.py
├── content/                  # 21 глава + 4 справочника
├── data/                     # симлинки
├── viz/                      # интерактивные HTML
├── tools/                    # 4 скрипта генерации
├── templates/                # 10 шаблонов
├── static/                   # CSS, JS, img
├── docs/                     # Учебник, ТЗ, Risk, AI-манифест
└── tests/
```

## Источник истины

- **`data/tradeLLm/`** — 7 энциклопедий (01) + 3 ТЗ (06) + 8 спец. исследований (07) + XLSX
- **`projects/01_fundament_rf/data/`** — реальные OHLCV + account JSON
- **`projects/04_tradingview-demos/`** — паттерны Lightweight Charts и Embed Widgets

## Лицензия

Internal use.
