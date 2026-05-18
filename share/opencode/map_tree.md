# Tree View

**Файл:** map_tree.md
**Родительский:** [map_all_small.md](./map_all_small.md)

---

## Полная структура workspace

```
WORKSPACE/
│
├── PROJECTS/
│   ├── trading/
│   │   ├── projects/01_fundament_rf/
│   │   │   ├── app.py              [entry point]
│   │   │   ├── models.py           [data models]
│   │   │   ├── storage.py          [JSON storage]
│   │   │   ├── flask_runner.py     [watchdog]
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── api.py          [REST API]
│   │   │   │   ├── web.py          [web pages]
│   │   │   │   ├── processor_1d.py [1D processor]
│   │   │   │   └── graphics.py     [graphics]
│   │   │   ├── templates/
│   │   │   │   ├── base.html
│   │   │   │   ├── index.html
│   │   │   │   ├── card.html
│   │   │   │   ├── metrics.html
│   │   │   │   ├── macros.html
│   │   │   │   └── graphics/
│   │   │   │       └── all.html
│   │   │   ├── static/css/
│   │   │   │   └── style.css
│   │   │   ├── static/graphics/
│   │   │   │   ├── simple_canvas.html
│   │   │   │   └── simple_svg.html
│   │   │   └── data/               [48 JSON files]
│   │   │       ├── 1D_*.json
│   │   │       ├── RAW_*.json
│   │   │       └── metrics.json
│   │   │
│   │   └── projects/02_graphs_candle/
│   │       ├── main.py             [entry point]
│   │       ├── flask_daemon.py     [daemon]
│   │       ├── requirements.txt
│   │       ├── charts/
│   │       │   ├── __init__.py
│   │       │   ├── candlestick.py
│   │       │   ├── pnl.py
│   │       │   ├── combined.py
│   │       │   └── svg_charts.py
│   │       ├── data/
│   │       │   ├── __init__.py
│   │       │   ├── fetcher.py      [ccxt/Bitget]
│   │       │   ├── generator.py
│   │       │   └── patterns.py
│   │       ├── templates/
│   │       │   ├── index.html
│   │       │   └── alt.html
│   │       └── static/
│   │           └── style.css
│   │
│   ├── visualization/
│   │   └── projects/04_tradingview-demos/
│   │       ├── index.html         [gallery]
│   │       ├── README.md
│   │       ├── package.json
│   │       ├── vercel.json
│   │       ├── chart-types/       [5 types]
│   │       │   ├── README.md
│   │       │   ├── 1-standard-time-chart/
│   │       │   │   ├── index.html
│   │       │   │   └── full.html
│   │       │   ├── 2-yield-curve-chart/
│   │       │   ├── 3-options-price-chart/
│   │       │   ├── 4-custom-horizontal-scale/
│   │       │   └── 5-multi-pane-chart/
│   │       │
│   │       ├── series-types/     [7 types]
│   │       │   ├── README.md
│   │       │   ├── candlestick/
│   │       │   ├── line/
│   │       │   ├── area/
│   │       │   ├── bar/
│   │       │   ├── histogram/
│   │       │   └── baseline/
│   │       │
│   │       └── conditions/        [8 conditions]
│   │           ├── README.md
│   │           ├── dark-theme/
│   │           ├── light-theme/
│   │           ├── fixed-size/
│   │           ├── autosize-responsive/
│   │           ├── multiple-series/
│   │           ├── overlay-price-scale/
│   │           └── locale-i18n/
│   │
│   └── media/
│       └── projects/05_transcript/
│           ├── README.md
│           ├── transcript_pipeline.py
│           ├── playlist_transcript.py
│           ├── yt_transcript_ytdlp.py
│           └── setup_env.sh
│
├── KNOWLEDGE/
│   ├── tradingview/
│   │   ├── index.md              [main index]
│   │   ├── chart-types/         [5 files]
│   │   │   ├── 1-standard-time-chart.md
│   │   │   ├── 2-yield-curve-chart.md
│   │   │   ├── 3-options-price-chart.md
│   │   │   ├── 4-custom-horizontal-scale.md
│   │   │   └── 5-multi-pane-chart.md
│   │   │
│   │   ├── series-types/        [7 files]
│   │   │   ├── candlestick.md
│   │   │   ├── line.md
│   │   │   ├── area.md
│   │   │   ├── bar.md
│   │   │   ├── histogram.md
│   │   │   ├── baseline.md
│   │   │   └── custom-plugin.md
│   │   │
│   │   ├── conditions/          [8 files]
│   │   │   ├── dark-theme.md
│   │   │   ├── light-theme.md
│   │   │   ├── fixed-size.md
│   │   │   ├── autosize-responsive.md
│   │   │   ├── multiple-series.md
│   │   │   ├── overlay-price-scale.md
│   │   │   └── locale-i18n.md
│   │   │
│   │   └── connecting-data/
│   │       └── data-formats.md
│   │
│   └── tv/                      [8 files]
│       ├── index.md
│       ├── introduction.md
│       ├── getting-started.md
│       ├── tutorials.md
│       ├── lightweight-getting-started.md
│       ├── lightweight-tutorials.md
│       ├── lightweight-api.md
│       └── api-modules-charting-library.md
│
├── INFRASTRUCTURE/
│   ├── scripts/
│   │   ├── scripts/flask.sh              [Flask process manager]
│   │   ├── scripts/flask_manager.py      [auto-restart watchdog]
│   │   ├── git.sh                [git helper]
│   │   ├── bitget_checker.py     [Bitget API checker]
│   │   ├── update_knowledge_map.sh [map updater]
│   │   ├── remove_system_reminder_from_zips.py
│   │   ├── transcript_pipeline.py
│   │   └── yt_transcript_ytdlp.py
│   │
│   └── configs/
│       ├── AGENTS.md             [main agent instructions]
│       ├── AGENTS.md           [skills documentation]
│       └── future.md            [future plans]
│
└── DATA/
    ├── projects/01_fundament_rf/data/        [JSON storage - 48 files]
    └── projects/02_graphs_candle/data/       [Python modules]
```

---

## Краткая структура (только директории)

```
WORKSPACE/
├── projects/01_fundament_rf/
│   ├── routes/
│   ├── templates/
│   ├── static/
│   └── data/
├── projects/02_graphs_candle/
│   ├── charts/
│   ├── data/
│   ├── templates/
│   └── static/
├── projects/04_tradingview-demos/
│   ├── chart-types/
│   ├── series-types/
│   └── conditions/
├── projects/05_transcript/
├── share/
│   ├── opencode/    (эта карта)
│   │   ├── map_all_small.md
│   │   ├── map_mermaid.md
│   │   ├── map_tree.md
│   │   ├── map_json.md
│   │   ├── map_links.md
│   │   └── map_update.md
│   └── knowledge-base/
│       ├── tradingview/
│       └── tv/
└── scripts/
```
