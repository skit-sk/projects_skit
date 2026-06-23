# Links Index

**Файл:** map_links.md
**Родительский:** [map_all_small.md](./map_all_small.md)

---

## Типы связей

| Тип | Описание | Направление |
|---|---|---|
| `proxy` | Flask reverse-proxy | unidirectional |
| `static_mount` | Статические файлы | unidirectional |
| `blueprint` | Flask blueprint внутри хаба | unidirectional |
| `http` | HTTP-вызов | unidirectional |
| `data` | Общие данные | unidirectional |
| `data_fallback` | Fallback на данные другого проекта | unidirectional |

---

## Индекс связей

| От | К | Тип | Детали |
|---|---|---|---|
| 01 | 02 | proxy | `/proxy/02/` |
| 01 | 03 | proxy | `/proxy/03/` |
| 01 | 04 | static_mount | `/static/sandbox/04/` |
| 01 | 06 | static_mount | `/static/sandbox/06/` |
| 07 | 01 | http | `localhost:5000` |
| 10 | 01 | http | `localhost:5000` |
| 08 | 01 | blueprint | `/ofd-api/` |
| 09 | 01 | blueprint | `/ai-models/` |
| 11 | 01 | blueprint | `/med-life/` |
| 03 | 01 | data_fallback | `../01_fundament_rf/data/card/` |
| 05 | 09 | data | `models_catalog.json` |
| 07 | 09 | data | `models_catalog.json` |
| 10 | 09 | data | `models_catalog.json` |
| 07 | 08 | shared_path | `sys.path.insert` для `bot_ofd` |
| 07 | 10 | shared_path | Общие `tools/scripts` |
| 10 | 07 | shared_path | Общие `tools/scripts` |
