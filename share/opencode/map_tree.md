# Tree View

**Файл:** map_tree.md
**Родительский:** [map_all_small.md](./map_all_small.md)

---

## Структура workspace

```
WORKSPACE/
├── projects/
│   ├── 01_fundament_rf/          [hub, port 5000]
│   │   ├── app.py
│   │   ├── routes/
│   │   │   ├── sandbox.py
│   │   │   ├── proxy.py
│   │   │   ├── med_life.py
│   │   │   ├── viz_lab.py
│   │   │   ├── ai_models.py
│   │   │   ├── ofd_api.py
│   │   │   └── ...
│   │   ├── services/
│   │   ├── templates/
│   │   ├── static/
│   │   └── data/card/
│   ├── 02_graphs_candle/         [port 5005]
│   ├── 03_demo_charts_ascii/     [port 5003]
│   ├── 04_tradingview-demos/     [static]
│   ├── 05_transcript/            [cli]
│   ├── 06_screenshots_project/   [static]
│   ├── 07_tg_bot_aiforguest/     [bot]
│   ├── 08_ofd_api/               [blueprint in 01]
│   ├── 09_model_catalog/         [blueprint in 01]
│   ├── 10_max_bot/               [bot]
│   └── 11_med_life/              [atlas/blueprint in 01]
├── share/
│   ├── knowledge-base/           [KB]
│   │   ├── 3-projects/
│   │   ├── 4-guides/
│   │   └── tradingview/
│   └── opencode/                 [maps]
│       ├── map_all.md
│       ├── map_all_small.md
│       ├── map_mermaid.md
│       ├── map_tree.md
│       ├── map_json.md
│       ├── map_links.md
│       └── map_update.md
├── scripts/
│   ├── flask.sh
│   ├── tg_bot.sh
│   └── update_knowledge_map.sh
├── tools/
└── venv/
```
