# SECURITY Skill — Работа с секретами

**Статус:** АКТУАЛЬНО
**Обновлено:** 2026-05-05

## Быстрые правила

1. **Токены только в `.env`** — никогда в `.md`, `.py`, `.sh`
2. `.env` в `.gitignore` — всегда
3. Использовать `source scripts/source_env.sh` для загрузки

## Токены

| Переменная | Назначение |
|------------|------------|
| `GITHUB_TOKEN` | GitHub API |
| `GITHUB_TOKEN_ALT` | GitHub Alt |
| `VERCEL_TOKEN` | Vercel deploy |
| `OPENAI_API_KEY` | OpenAI API |

## Что делать при утечке

1. Отозвать токен в GitHub/Vercel dashboard
2. Сгенерировать новый
3. Обновить `.env`
4. `git-filter-repo` для очистки истории
5. `git push --force`

## Полные guidelines

См. `docs/SECURITY_GUIDELINES.md`
