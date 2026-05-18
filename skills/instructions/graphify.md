# GRAPHIFY Skill — Knowledge Graph

**Статус:** РАБОТАЕТ
**Обновлено:** 2026-05-17

## Обновление графа

```bash
# Полное обновление
cd /home/user_aioc/workspace
source venv/bin/activate
graphify update . && python3 graphify-out/rename_communities.py
```

## Просмотр

- `graphify-out/graph.html` — интерактивный граф (открыть в браузере)
- `graphify-out/graph.json` — данные (2886 nodes, 7922 edges, 160 communities)
- `graphify-out/GRAPH_REPORT.md` — отчёт

## Деплой на Vercel

```bash
cd graphify-out
HOME=/tmp vercel --prod --yes --token $VERCEL_TOKEN
```

**Deployed:** https://graphify-out-six.vercel.app/graph.html

## Команды graphify

| Команда | Описание |
|---------|----------|
| `graphify update .` | Перестроить граф из кода |
| `graphify path \"A\" \"B\"` | Кратчайший путь между узлами |
| `graphify explain \"X\"` | Объяснение узла и соседей |
| `graphify add <url>` | Добавить URL в граф |
| `graphify watch .` | Следить за изменениями и авто-перестраивать |

## Структура

- **Nodes:** файлы, функции, классы
- **Edges:** вызовы, импорты, наследование
- **Communities:** кластеры связанных компонентов (именованы по проектам)

## Проекты в графе

- `01_fundament_rf` — трекер сделок
- `02_graphs_candle` — свечные графики (доминирует)
- `03_demo_charts_ascii` — ASCII-графики
- `04_tradingview-demos` — TradingView виджеты
- `05_transcript` — транскрипция
- `06_screenshots_project` — каталог скриншотов
- `07_tg_bot_aiforguest` — Telegram bot proxy
