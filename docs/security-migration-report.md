# Security Migration Report
**Дата:** 2026-05-05
**Статус:** ✅ Выполнено

## Что было сделано

1. Создана структура `projects/` с номерными папками (01–06).
2. Перемещены все проекты: `fundament_rf`, `graphs_candle`, `demo_charts_ascii`, `tradingview-demos`, `transcript`, `screenshots_project`.
3. Перемещен `bitget_checker.py` в `projects/01_fundament_rf/`.
4. Flask-скрипты перенесены из `tools/flask/` в `scripts/` — поддержка номеров (01, 1) и автозагрузка `.env`.
5. Создан корневой `.env` с токенами (не в git).
6. Обновлен `.gitignore` (`.env`, `.env.local`).
7. Создан `.env.example` — шаблон для новых разработчиков.
8. Очищены токены из `AGENTS.md`, `L_SKILL.md`, `tasks/help_ai.md`.
9. Добавлен `load_dotenv()` в Python-скрипты (`projects/05_transcript/transcript_pipeline.py`, `projects/01_fundament_rf/app.py`).
10. Удален дубль `scripts/transcript_pipeline.py`.
11. Создан `scripts/source_env.sh` — helper для bash.
12. Созданы `docs/SECURITY_GUIDELINES.md` и этот отчет.

## Найденные утечки

| Файл | Токен | Действие |
|------|-------|----------|
| `AGENTS.md` | Vercel token | Очищен, заменен на `$VERCEL_TOKEN` |
| `L_SKILL.md` | GitHub + Vercel tokens | Очищены, заменены на переменные |
| `tasks/help_ai.md` | GitHub alt token | Очищен |
| `.git/config` (5 репо) | Embedded tokens | Заменены на `${GITHUB_TOKEN}` |

## Рекомендации

- Не хранить токены в файлах инструкций (`.md`).
- Использовать `source_env.sh` перед работой с git/vercel.
- При утечке — ротировать токены через GitHub/Vercel dashboards.
