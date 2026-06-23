# Architecture Overview

Workspace построен вокруг центрального Flask-хаба `01_fundament_rf`, к которому подключаются satellite-проекты разными способами.

## Общая схема

```mermaid
flowchart TB
    subgraph HUB["01 Fundament RF (хаб)"]
        SANDBOX["/sandbox/"]
        KB["/kb/"]
        VIZ["/viz-lab/"]
        MED["/med-life/"]
        OFD["/ofd-api/"]
        AI["/ai-models/"]
        PROXY["/proxy/"]
        STATIC["/static/sandbox/"]
    end

    subgraph SATELLITES["Satellite проекты"]
        P02["02 Graphs Candle"]
        P03["03 Demo Charts ASCII"]
        P04["04 TradingView Demos"]
        P06["06 Screenshots Catalog"]
    end

    subgraph BOTS["Боты"]
        P07["07 TG Bot"]
        P10["10 MAX Bot"]
    end

    subgraph DATA["Данные / Catalog"]
        P05["05 Transcript"]
        P09["09 Model Catalog"]
    end

    PROXY --> P02
    PROXY --> P03
    STATIC --> P04
    STATIC --> P06
    P07 --> HUB
    P10 --> HUB
    P05 --> P09
    P07 --> P09
    P10 --> P09
```

## Типы интеграции

| Тип | Описание | Примеры |
|---|---|---|
| `proxy` | Flask reverse-proxy к satellite-сервису | 02, 03 |
| `static_mount` | Статические файлы через `01/static/sandbox/` | 04, 06 |
| `blueprint` | Flask blueprint внутри 01 | 08, 09, 11 |
| `HTTP` | Боты вызывают API хаба | 07, 10 |
| `shared_path` | Общие модули через `sys.path.insert` | 07, 10, 08 |
| `data` | Чтение/запись общих JSON-данных | 05 → 09, 03 → 01 |

## Порты и маршрутизация

- Хаб слушает `:5000`.
- Satellite Flask-проекты слушают свои порты (`02` → 5005, `03` → 5003).
- Статические проекты не требуют порта.
- Боты не открывают порт, а инициируют исходящие HTTP-запросы.

## Связанные KB

- [Матрица связей](project-links-matrix.md)
- [URL/Port карта](url-port-map.md)
