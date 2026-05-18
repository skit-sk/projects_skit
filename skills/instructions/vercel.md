# VERCEL Skill — Деплой

**Статус:** РАБОТАЕТ
**Обновлено:** 2026-05-05

## Токен

`$VERCEL_TOKEN` из `.env` (загрузить: `source scripts/source_env.sh`)

## Установка Vercel CLI

```bash
npm install -g vercel --prefix /home/user_aioc/.local --cache /tmp/npm-cache
export PATH="/home/user_aioc/.local/bin:$PATH"
```

## Деплой

```bash
export PATH="/home/user_aioc/.local/bin:$PATH"
export HOME=/tmp
export VERCEL_CACHE_DIR=/tmp/vercel-cache

cd <project_dir>
vercel --prod --yes --token $VERCEL_TOKEN
```

## Graphify deploy

```bash
cd graphify-out
HOME=/tmp vercel --prod --yes --token $VERCEL_TOKEN
```

**URL:** https://graphify-out-six.vercel.app/graph.html

## Известные проблемы

- Ошибка `EACCES: mkdir '/home/user_aioc/.cache/com.vercel.cli'` — можно игнорировать
- Решение: всегда использовать `HOME=/tmp`
