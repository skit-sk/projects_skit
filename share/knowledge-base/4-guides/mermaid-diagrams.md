# Mermaid Diagrams

Коллекция Mermaid-диаграмм, описывающих архитектуру, связи и потоки данных workspace.

## 1. Общая архитектура

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

## 2. Потоки данных

```mermaid
flowchart LR
    BITGET[Bitget API] --> |REST/WebSocket| F01[01 Fundament RF]
    F01 --> |JSON| DCARD[data/card/]
    DCARD --> |fallback| P03[03 Demo Charts ASCII]
    DCARD --> |pipeline| P05[05 Transcript]
    P05 --> |models_catalog.json| P09[09 Model Catalog]
    P09 --> |read| P07[07 TG Bot]
    P09 --> |read| P10[10 MAX Bot]
    P09 --> |blueprint| F01
    F01 --> |HTTP response| P07
    F01 --> |HTTP response| P10
```

## 3. Sandbox → Satellite

```mermaid
flowchart TD
    USER[Пользователь] --> |/sandbox/| S01[01 Sandbox UI]
    S01 --> |/proxy/02/| P02[02 Graphs Candle]
    S01 --> |/proxy/03/| P03[03 Demo Charts ASCII]
    S01 --> |/static/sandbox/04/| P04[04 TradingView Demos]
    S01 --> |/static/sandbox/06/| P06[06 Screenshots Catalog]
    S01 --> |/viz-lab/| VIZ[Viz Lab]
    S01 --> |/med-life/| P11[11 Med Life]
    S01 --> |/med-life/| MED[Med Life Atlas]
    S01 --> |/kb/| KB[Knowledge Base]
```

## 4. Mindmap доменов

```mermaid
mindmap
  root((WORKSPACE))
    Trading
      01 Fundament RF
      02 Graphs Candle
      03 Demo Charts ASCII
    Visualization
      04 TradingView Demos
      11 Med Life
      Viz Lab (в 01)
    Media / AI
      05 Transcript
      09 Model Catalog
    Automation
      07 TG Bot AIForGuest
      10 MAX Bot
      08 OFD API
    Assets
      06 Screenshots Catalog
    Knowledge
      Knowledge Base
```

## 5. Bot ↔ Hub interactions

```mermaid
sequenceDiagram
    participant U as User
    participant B07 as 07 TG Bot
    participant B10 as 10 MAX Bot
    participant F01 as 01 Fundament RF
    participant P09 as 09 Model Catalog

    U->>B07: Команда /prompt
    B07->>F01: GET /api/...
    F01-->>B07: JSON
    B07-->>U: Ответ

    U->>B10: Запрос
    B10->>P09: Читает models_catalog.json
    P09-->>B10: Данные моделей
    B10->>F01: POST /api/...
    F01-->>B10: Результат
    B10-->>U: Ответ
```

## Связанные KB

- [Архитектура workspace](architecture-overview.md)
- [Матрица связей](project-links-matrix.md)
