# JSON Structure

**Файл:** map_json.md
**Родительский:** [map_all_small.md](./map_all_small.md)

---

## Полная JSON структура workspace

```json
{
  "version": "1.0",
  "updated": "2026-04-30",
  "workspace": {
    "path": "/home/user_aioc/workspace",

    "projects": {
      "projects/01_fundament_rf": {
        "path": "projects/01_fundament_rf/",
        "domain": "trading",
        "entry": "app.py",
        "type": "Flask application",
        "technologies": ["Flask", "ccxt", "Bitget", "JSON", "HTML", "CSS", "Jinja2"],
        "components": {
          "routes": ["api.py", "web.py", "processor_1d.py", "graphics.py"],
          "templates": ["base.html", "index.html", "card.html", "metrics.html"],
          "static": ["css/style.css"]
        },
        "data": {
          "location": "projects/01_fundament_rf/data/",
          "format": "JSON",
          "file_count": 48,
          "types": ["1D_*.json", "RAW_*.json", "metrics.json"]
        },
        "documentation": ["README.md", "CARD_STRUCTURE.md", "PROCESSOR_1D_PLAN.md", "structure.md"]
      },

      "projects/02_graphs_candle": {
        "path": "projects/02_graphs_candle/",
        "domain": "trading",
        "entry": "main.py",
        "type": "Flask application",
        "technologies": ["Flask", "Plotly", "ccxt", "Bitget", "pandas", "numpy"],
        "components": {
          "charts": ["candlestick.py", "pnl.py", "combined.py", "svg_charts.py"],
          "data": ["fetcher.py", "generator.py", "patterns.py"]
        },
        "data": {
          "location": "projects/02_graphs_candle/data/",
          "format": "Python modules"
        },
        "documentation": ["README.md", "PROJECT_PLAN.md"]
      },

      "projects/04_tradingview-demos": {
        "path": "projects/04_tradingview-demos/",
        "domain": "visualization",
        "entry": "index.html",
        "type": "HTML/JS demo gallery",
        "technologies": ["Lightweight Charts v5.2.0", "JavaScript", "HTML", "Binance API"],
        "subdirs": {
          "chart-types": ["1-standard-time-chart", "2-yield-curve-chart", "3-options-price-chart", "4-custom-horizontal-scale", "5-multi-pane-chart"],
          "series-types": ["candlestick", "line", "area", "bar", "histogram", "baseline"],
          "conditions": ["dark-theme", "light-theme", "fixed-size", "autosize-responsive", "multiple-series", "overlay-price-scale", "locale-i18n"]
        },
        "deployment": "Vercel",
        "documentation": ["README.md"]
      },

      "projects/05_transcript": {
        "path": "projects/05_transcript/",
        "domain": "media",
        "type": "Python pipeline",
        "technologies": ["Python", "yt-dlp", "YouTube API"],
        "components": ["transcript_pipeline.py", "playlist_transcript.py", "yt_transcript_ytdlp.py"],
        "documentation": ["README.md"]
      }
    },

    "knowledge_bases": {
      "tradingview": {
        "path": "share/knowledge-base/tradingview/",
        "topic": "TradingView Charting Library & Lightweight Charts",
        "files_count": 23,
        "sections": {
          "chart-types": {
            "count": 5,
            "files": ["1-standard-time-chart.md", "2-yield-curve-chart.md", "3-options-price-chart.md", "4-custom-horizontal-scale.md", "5-multi-pane-chart.md"]
          },
          "series-types": {
            "count": 7,
            "files": ["candlestick.md", "line.md", "area.md", "bar.md", "histogram.md", "baseline.md", "custom-plugin.md"]
          },
          "conditions": {
            "count": 8,
            "files": ["dark-theme.md", "light-theme.md", "fixed-size.md", "autosize-responsive.md", "multiple-series.md", "overlay-price-scale.md", "locale-i18n.md"]
          },
          "connecting-data": {
            "count": 1,
            "files": ["data-formats.md"]
          }
        }
      },

      "tv": {
        "path": "share/knowledge-base/tv/",
        "topic": "TradingView Alternative Knowledge Base",
        "files_count": 8,
        "topics": ["introduction", "getting-started", "tutorials", "lightweight-getting-started", "lightweight-tutorials", "lightweight-api", "api-modules-charting-library"]
      }
    },

    "infrastructure": {
      "scripts": {
        "path": "scripts/",
        "files": [
          {"name": "scripts/flask.sh", "purpose": "Flask process manager"},
          {"name": "scripts/flask_manager.py", "purpose": "auto-restart watchdog"},
          {"name": "git.sh", "purpose": "git helper"},
          {"name": "bitget_checker.py", "purpose": "Bitget API checker"},
          {"name": "update_knowledge_map.sh", "purpose": "knowledge map updater"}
        ]
      },
      "configs": {
        "files": [
          {"name": "AGENTS.md", "purpose": "main agent instructions"},
          {"name": "AGENTS.md", "purpose": "skills documentation"},
          {"name": "future.md", "purpose": "future plans"}
        ]
      }
    }
  },

  "links": {
    "project_to_domain": [
      {"project": "projects/01_fundament_rf", "domain": "trading"},
      {"project": "projects/02_graphs_candle", "domain": "trading"},
      {"project": "projects/04_tradingview-demos", "domain": "visualization"},
      {"project": "projects/05_transcript", "domain": "media"}
    ],

    "project_to_kb": [
      {"project": "projects/01_fundament_rf", "kb": "tradingview", "type": "related_to"},
      {"project": "projects/02_graphs_candle", "kb": "tradingview", "type": "related_to"},
      {"project": "projects/04_tradingview-demos", "kb": "tradingview", "type": "documents"}
    ],

    "technology_links": [
      {"project": "projects/01_fundament_rf", "technology": "ccxt/Bitget", "type": "uses"},
      {"project": "projects/02_graphs_candle", "technology": "ccxt/Bitget", "type": "uses"},
      {"project": "projects/02_graphs_candle", "technology": "Plotly", "type": "uses"},
      {"project": "projects/04_tradingview-demos", "technology": "Lightweight Charts v5", "type": "uses"}
    ],

    "cross_project": [
      {"project_a": "projects/01_fundament_rf", "project_b": "projects/02_graphs_candle", "type": "related_to", "reason": "trading domain"}
    ]
  }
}
```

---

## Упрощённый JSON для навигации

```json
{
  "navigation": {
    "projects": [
      {"id": "projects/01_fundament_rf", "name": "projects/01_fundament_rf", "path": "projects/01_fundament_rf/"},
      {"id": "projects/02_graphs_candle", "name": "projects/02_graphs_candle", "path": "projects/02_graphs_candle/"},
      {"id": "projects/04_tradingview-demos", "name": "projects/04_tradingview-demos", "path": "projects/04_tradingview-demos/"},
      {"id": "projects/05_transcript", "name": "projects/05_transcript", "path": "projects/05_transcript/"}
    ],
    "knowledge_bases": [
      {"id": "tradingview", "name": "tradingview", "path": "share/knowledge-base/tradingview/"},
      {"id": "tv", "name": "tv", "path": "share/knowledge-base/tv/"}
    ],
    "scripts": [
      {"id": "update_map", "name": "update_knowledge_map.sh", "path": "scripts/update_knowledge_map.sh"}
    ]
  }
}
```

---

## Links JSON

```json
{
  "bidirectional_links": [
    {
      "from": "projects/01_fundament_rf",
      "to": "projects/02_graphs_candle",
      "type": "related_to",
      "direction": "bidirectional",
      "reason": "trading domain"
    },
    {
      "from": "projects/04_tradingview-demos",
      "to": "share/knowledge-base/tradingview/",
      "type": "documents",
      "direction": "unidirectional",
      "inverse": "documented_by"
    }
  ],

  "unidirectional_links": [
    {"from": "projects/01_fundament_rf", "to": "ccxt/Bitget", "type": "uses"},
    {"from": "projects/02_graphs_candle", "to": "ccxt/Bitget", "type": "uses"},
    {"from": "projects/02_graphs_candle", "to": "Plotly", "type": "uses"},
    {"from": "projects/04_tradingview-demos", "to": "Lightweight Charts v5", "type": "uses"},
    {"from": "projects/01_fundament_rf", "to": "share/knowledge-base/tradingview/", "type": "related_to"},
    {"from": "projects/02_graphs_candle", "to": "share/knowledge-base/tradingview/", "type": "related_to"}
  ]
}
```
