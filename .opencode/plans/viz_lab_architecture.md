# 🧪 Visualization Lab — Архитектура

## Назначение

Blueprint в `01_fundament_rf` — среда для анализа данных, подбора моделей визуализации,
сравнения результатов от разных провайдеров, генерации видео/презентаций,
с замерами времени, токенов и стоимости.

## Трёхпанельный UI

```
┌─────────────────────┬──────────────────────────────┬──────────────────────────┐
│    LEFT (280px)      │        CENTER (flex)          │     RIGHT (340px)        │
├─────────────────────┼──────────────────────────────┼──────────────────────────┤
│ ┌─────────────────┐ │  ┌────────────────────────┐  │  ╔══ Model Responses ╗    │
│ │ INCOMING DATA    │ │  │  Message Input          │  │  ┌────────────────────┐ │
│ │ [upload files]   │ │  │  ┌────────────────────┐ │  │  │ Gemini 2.5 Flash   │ │
│ │ Drag & drop      │ │  │  │ "Построй график    │ │  │  │ 📐 OHLC + Bollinger│ │
│ │ CSV / JSON / PNG │ │  │  │  BTCUSDT по этим   │ │  │  │ 📜 chart_gemini.py │ │
│ │ .xlsx / .txt     │ │  │  │  данным, сравни    │ │  │  │ ⏱ 1.2s │ 450 ток │ │
│ └─────────────────┘ │  │  │  с RSI и MACD"      │ │  │  │ 📊 preview →       │ │
│                      │  │  └────────────────────┘ │  │  └────────────────────┘ │
│ ┌─────────────────┐  │  │  [🤖 Gemini] [🤖 Claude]│  │  ┌────────────────────┐ │
│ │ PROJECT TREE     │  │  │  [🤖 GPT] [🎨 TV] [+] │  │  │ Claude 4 Opus      │ │
│ │ 📁 workspace/    │  │  ├────────────────────────┤  │  │ 📐 Line + SMA       │ │
│ │  ├─ projects/    │  │  │     PREVIEW GALLERY    │  │  │ 📜 chart_claude.py  │ │
│ │  │ ├─ 01_fund..  │  │  │                       │  │  │ ⏱ 3.5s │ 1200 ток  │ │
│ │  │ ├─ 02_graphs  │  │  │  ┌─────┐ ┌─────┐     │  │  │ 📊 preview →       │ │
│ │  │ ├─ 03_ascii   │  │  │  │P1 P2│ │P1 P2│     │  │  └────────────────────┘ │
│ │  │ └─ ...        │  │  │  │Plot │ │SVG  │     │  │  ┌────────────────────┐ │
│ │  ├─ data/        │  │  │  └─────┘ └─────┘     │  │  │ GPT-4o             │ │
│ │  ├─ scripts/     │  │  │  ┌─────┐ ┌─────┐     │  │  │ 📐 ASCII chart      │ │
│ │  └─ tools/       │  │  │  │TV   │ │GIF  │     │  │  │ 📜 chart_gpt.py     │ │
│ │                   │  │  │  │Scrn │ │Anim │     │  │  │ ⏱ 0.8s │ 220 ток  │ │
│ │ Current:          │  │  │  └─────┘ └─────┘     │  │  │ 📊 preview →       │ │
│ │  data/card/BTC_.. │  │  │                       │  │  └────────────────────┘ │
│ └─────────────────┘  │  │  [📦 Скачать всё]       │  │                        │
│                      │  └────────────────────────┘  │  [🧹 Clear] [📥 Export] │
└─────────────────────┴──────────────────────────────┴──────────────────────────┘
```

## Структура модуля

```
projects/01_fundament_rf/
├── viz_lab/                            ← пакет лаборатории
│   ├── __init__.py
│   ├── provider/                       ← система провайдеров
│   │   ├── __init__.py
│   │   ├── base.py                     (AbstractModelProvider)
│   │   ├── registry.py                 (регистрация + конфиги)
│   │   ├── gemini.py                   (Gemini 2.5 Flash/Pro)
│   │   ├── openai.py                   (GPT-4o, o3, DALL-E)
│   │   ├── anthropic.py                (Claude 4 Opus/Sonnet)
│   │   ├── tradingview.py              (TradingView screenshot)
│   │   ├── local.py                    (Ollama/llama.cpp)
│   │   ├── firefly.py                  (Adobe Firefly / SD)
│   │   └── custom.py                   (user-defined via JSON)
│   │
│   ├── services/
│   │   ├── analyzer.py                 (входные данные → типы, статистика)
│   │   ├── selector.py                 (контекст → список моделей)
│   │   ├── conversation.py             (управление диалогом + история)
│   │   ├── script_generator.py         (генерация кода для рендера)
│   │   ├── video_renderer.py           (PNG→ffmpeg→MP4/GIF/презентация)
│   │   └── metrics.py                  (замеры времени, токенов, стоимости)
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── session.py                  (JSON-сессия: запросы, ответы, файлы)
│   │   └── file_manager.py            (загрузка, валидация, tree index)
│   │
│   └── config/
│       ├── providers.json              (дефолтные провайдеры)
│       └── selector_rules.json         (правила выбора модели)
│
├── routes/
│   └── viz_lab.py                      ← blueprint (14 endpoints)
│
├── templates/
│   └── viz_lab/
│       ├── lab.html                    (основная 3-панельная страница)
│       └── partials/
│           ├── project_tree.html       (левая панель)
│           ├── incoming_data.html      (левая панель)
│           ├── messages.html           (правая панель)
│           ├── preview_gallery.html    (центр)
│           └── model_tile.html         (карточка модели)
│
├── static/
│   ├── css/
│   │   └── viz_lab.css                 (3-панельный layout)
│   └── js/
│       ├── viz_lab.js                  (основной контроллер)
│       ├── project_tree.js             (файловое дерево)
│       ├── conversation.js             (управление диалогом)
│       ├── preview_gallery.js          (галерея, lightbox)
│       └── video.js                    (плеер, экспорт)
│
└── data/
    └── viz_sessions/                   ← файлы сессий
```

## Система провайдеров

```python
class ModelProvider(ABC):
    name: str
    provider: str
    capabilities: set[str]       # {"chart", "image", "video", "code"}
    max_tokens: int
    cost_per_1k_input: float
    cost_per_1k_output: float

    @abstractmethod
    def generate(self, prompt, context) -> ProviderResponse: ...
    @abstractmethod
    def render(self, data, chart_type) -> ProviderResponse: ...

class ProviderResponse:
    text: str
    files: list[FileRef]
    script: str | None
    usage: TokenUsage  # input_tokens, output_tokens, duration_ms
```

## API Endpoints

| # | Метод | Путь | Описание |
|---|-------|------|----------|
| 1 | `GET` | `/viz-lab/` | Основная страница |
| 2 | `POST` | `/viz-lab/analyze` | Загрузить файлы + промпт |
| 3 | `GET` | `/viz-lab/session/<id>` | Получить сессию |
| 4 | `POST` | `/viz-lab/session/<id>/ask` | Отправить сообщение |
| 5 | `POST` | `/viz-lab/session/<id>/run` | Запустить модели |
| 6 | `GET` | `/viz-lab/session/<id>/results` | Результаты |
| 7 | `GET` | `/viz-lab/session/<id>/preview/<rid>` | Превью |
| 8 | `GET` | `/viz-lab/session/<id>/download/<f>` | Скачать файл |
| 9 | `GET` | `/viz-lab/session/<id>/download-all` | Архив |
| 10 | `POST` | `/viz-lab/session/<id>/render-video` | Видео |
| 11 | `POST` | `/viz-lab/session/<id>/export-presentation` | Презентация |
| 12 | `GET` | `/viz-lab/providers` | Список провайдеров |
| 13 | `POST` | `/viz-lab/providers/custom` | Кастомный провайдер |
| 14 | `GET` | `/viz-lab/project-tree` | Дерево проектов |

## Метрики ответа

```json
{
  "provider": "google",
  "model": "gemini-2.5-flash",
  "task": "chart_rendering",
  "context": {"files": [...], "prompt_preview": "..."},
  "metrics": {
    "duration_ms": 452,
    "input_tokens": 320,
    "output_tokens": 150,
    "cost_usd": 0.00082,
    "script_lines": 47,
    "output_size_kb": 124
  },
  "result": {"files": [...], "preview": "..."}
}
```

## Этапы реализации

1. **UI-каркас** — 3-панельный layout, blueprint, шаблоны, статика
2. **Project Tree** — файловый браузер, drag-drop загрузка
3. **Provider System** — base, registry, gemini/openai/anthropic
4. **Analyzer + Selector** — data classification, model routing
5. **Message Panel** — chrono log, model tiles, metrics
6. **Render Pipeline** — parallel model execution, script gen
7. **Preview Gallery** — thumbnails, comparison, lightbox
8. **Video Generator** — chart animation, GIF, presentation
9. **Custom Providers** — JSON config loader
10. **Export / Download** — archive, ZIP, PDF
