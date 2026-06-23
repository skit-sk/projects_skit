# Workspace Knowledge Base

Единая база знаний по проектам, модулям, связям и архитектуре workspace.

## Структура

| Раздел | Описание |
|---|---|
| [3-projects/](3-projects/) | Документация по каждому из 11 проектов |
| [4-guides/](4-guides/) | Межпроектные гайды: архитектура, матрица связей, реестр модулей, URL-карта, Mermaid-диаграммы |
| [tradingview/](tradingview/) | Гайды по TradingView: Playground, Lightweight Charts, Widgets |
| [1-exchanges/](1-exchanges/) | Справочники по биржам и API |
| [2-tools/](2-tools/) | Инструменты и утилиты |

## Быстрые ссылки

- [Архитектура workspace](4-guides/architecture-overview.md)
- [Матрица связей проектов](4-guides/project-links-matrix.md)
- [Реестр модулей](4-guides/module-registry.md)
- [URL/Port карта](4-guides/url-port-map.md)
- [Mermaid-диаграммы](4-guides/mermaid-diagrams.md)

## Обновление

Для перегенерации карт выполните:

```bash
./scripts/update_knowledge_map.sh
```
