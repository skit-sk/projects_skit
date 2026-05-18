# Mermaid Diagrams

**Файл:** map_mermaid.md
**Родительский:** [map_all_small.md](./map_all_small.md)

---

## 1. Flowchart (диаграмма связей)

```mermaid
flowchart TB
    subgraph WORKSPACE["WORKSPACE"]
        subgraph PROJECTS["PROJECTS"]
            subgraph TRADING["trading"]
                FR["projects/01_fundament_rf"]
                GC["projects/02_graphs_candle"]
            end
            subgraph VISUALIZATION["visualization"]
                TVD["projects/04_tradingview-demos"]
            end
            subgraph MEDIA["media"]
                TR["projects/05_transcript"]
            end
        end

        subgraph KNOWLEDGE["KNOWLEDGE"]
            TVKB["tradingview/"]
            TVALT["tv/"]
        end

        subgraph INFRASTRUCTURE["INFRASTRUCTURE"]
            SCRIPTS["scripts/"]
            CONFIGS["configs/"]
        end

        subgraph DATA["DATA"]
            FRD["projects/01_fundament_rf/data/"]
            GCD["projects/02_graphs_candle/data/"]
        end
    end

    FR -->|uses| CCXT["ccxt / Bitget"]
    GC -->|uses| CCXT
    GC -->|uses| PLOTLY["Plotly"]
    TVD -->|uses| LW["Lightweight Charts v5"]
    TVKB -->|documents| TVD
    TVD -->|documented_by| TVKB
    FR -->|related_to| TVKB
    GC -->|related_to| TVKB
    FR <-->|trading domain| GC
```

---

## 2. Hierarchical (иерархическая диаграмма)

```mermaid
hierarchical
    WORKSPACE
        PROJECTS
            trading
                fundament_rf
                graphs_candle
            visualization
                tradingview-demos
            media
                transcript
        KNOWLEDGE
            tradingview
            tv
        INFRASTRUCTURE
            scripts
            configs
        DATA
```

---

## 3. Sequence диаграмма (зависимости проектов)

```mermaid
sequenceDiagram
    participant FR as fundament_rf
    participant GC as graphs_candle
    participant TVD as tradingview-demos
    participant KB as knowledge-base

    FR->>KB: related_to
    GC->>KB: related_to
    TVD->>KB: documents
    KB->>TVD: documented_by

    Note over FR,GC: trading domain
    FR->>GC: related_to
    GC->>FR: related_to
```

---

## 4. Pie Chart (технологии по проектам)

```mermaid
pie title Workspace Distribution
    "projects/01_fundament_rf" : 25
    "projects/02_graphs_candle" : 25
    "projects/04_tradingview-demos" : 25
    "projects/05_transcript" : 15
    "infrastructure" : 10
```
