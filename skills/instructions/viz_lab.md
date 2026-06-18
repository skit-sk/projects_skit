# 🧪 Visualization Lab

Blueprint проекта `01_fundament_rf` — `/viz-lab/`.

## Что делает
- 3-панельный UI: дерево проектов + загрузка | ввод + галерея | сообщения
- Загрузка CSV/JSON/PNG через drag-drop
- Подключение AI-моделей через `opencode CLI`
- Analyzer: определяет тип данных (OHLCV, timeseries, tabular) и намерение (chart type, indicators)
- Selector: автоматически подбирает модели под задачу
- 8 провайдеров: deepseek-free, gemini-2.5, gpt-4o, claude-4, tv-screenshot

## API Endpoints

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/viz-lab/` | Основная страница |
| POST | `/viz-lab/api/analyze` | Анализ данных + подбор моделей |
| POST | `/viz-lab/api/session` | Создать сессию |
| GET | `/viz-lab/api/session/<id>` | Получить сессию |
| POST | `/viz-lab/api/session/<id>/ask` | Отправить запрос к моделям |
| POST | `/viz-lab/api/session/<id>/upload` | Загрузить файл |
| GET | `/viz-lab/api/session/<id>/files` | Список файлов сессии |
| GET | `/viz-lab/api/providers` | Список провайдеров |
| GET | `/viz-lab/api/project-tree` | Дерево проектов |
| GET | `/viz-lab/api/file-content` | Превью файла |
| GET | `/viz-lab/api/file-raw` | Скачать файл |

## Структура

```
projects/01_fundament_rf/
├── viz_lab/           ← Python пакет (provider/ services/ storage/ config/)
├── routes/viz_lab.py  ← Blueprint
├── templates/viz_lab/ ← lab.html + partials/
├── static/            ← css/viz_lab.css + js/viz_lab.js
```

## Запуск

Через `scripts/flask.sh start 01` — blueprint доступен на `/viz-lab/`.
