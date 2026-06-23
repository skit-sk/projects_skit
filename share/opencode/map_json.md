# JSON Structure

**Файл:** map_json.md
**Родительский:** [map_all_small.md](./map_all_small.md)

---

## JSON-структура workspace

```json
{
  "version": "2.0",
  "updated": "2026-06-22",
  "workspace": "/home/user_aioc/workspace",
  "hub": {
    "id": "01",
    "name": "fundament_rf",
    "port": 5000,
    "entry": "projects/01_fundament_rf/app.py"
  },
  "projects": {
    "01": {"name": "fundament_rf", "type": "flask", "port": 5000},
    "02": {"name": "graphs_candle", "type": "flask", "port": 5005},
    "03": {"name": "demo_charts_ascii", "type": "flask", "port": 5003},
    "04": {"name": "tradingview-demos", "type": "static_mount"},
    "05": {"name": "transcript", "type": "cli"},
    "06": {"name": "screenshots_project", "type": "static_mount"},
    "07": {"name": "tg_bot_aiforguest", "type": "bot"},
    "08": {"name": "ofd_api", "type": "blueprint"},
    "09": {"name": "model_catalog", "type": "blueprint"},
    "10": {"name": "max_bot", "type": "bot"},
    "11": {"name": "med_life", "type": "atlas"}
  },
  "links": [
    {"from": "01", "to": "02", "type": "proxy"},
    {"from": "01", "to": "03", "type": "proxy"},
    {"from": "01", "to": "04", "type": "static_mount"},
    {"from": "01", "to": "06", "type": "static_mount"},
    {"from": "07", "to": "01", "type": "http"},
    {"from": "10", "to": "01", "type": "http"},
    {"from": "08", "to": "01", "type": "blueprint"},
    {"from": "09", "to": "01", "type": "blueprint"},
    {"from": "11", "to": "01", "type": "blueprint"},
    {"from": "03", "to": "01", "type": "data_fallback"},
    {"from": "05", "to": "09", "type": "data"},
    {"from": "07", "to": "09", "type": "data"},
    {"from": "10", "to": "09", "type": "data"}
  ]
}
```
