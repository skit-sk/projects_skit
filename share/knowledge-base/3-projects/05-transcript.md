# 05 — Transcript

**ID:** 05
**Расположение:** `projects/05_transcript/`
**Тип:** CLI pipeline
**Порт:** —
**Запуск:** `python transcript_pipeline.py <url_or_file>`

## Назначение

Транскрипция видео/аудио: скачивание, извлечение аудио, распознавание речи, суммаризация.

## Стек

- Python
- yt-dlp / ffmpeg
- Whisper / другие STT-модели

## Архитектура

```
projects/05_transcript/
├── transcript_pipeline.py    # Основной pipeline
├── downloaders/
├── extractors/
├── transcribers/
├── summarizers/
└── outputs/
```

## Entry points

- CLI: `python transcript_pipeline.py <url>`

## Зависимости

| Тип | Зависимость | Описание |
|---|---|---|
| Внутренняя | `projects/09_model_catalog/` | Каталог моделей для суммаризации |
| Внутренняя | `projects/07_tg_bot_aiforguest/` | Отправка результатов в Telegram |

## Связи с другими проектами

| Проект | Тип связи | Детали |
|---|---|---|
| 09 Model Catalog | data | Читает `models_catalog.json` |
| 07 TG Bot AIForGuest | data | Пишет результаты для бота |

## Запуск

```bash
cd projects/05_transcript
python transcript_pipeline.py <URL>
```

## Связанные KB

- [Архитектура workspace](../4-guides/architecture-overview.md)
