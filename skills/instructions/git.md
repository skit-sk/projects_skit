# GIT Skill — Работа с GitHub

**Статус:** РАБОТАЕТ
**Обновлено:** 2026-05-05

## Токены

Загружаются из `.env`:
```bash
source scripts/source_env.sh
```

- GitHub Token: `$GITHUB_TOKEN`
- GitHub Alt Token: `$GITHUB_TOKEN_ALT`

## Приоритетные методы

### GitHub: CLI (основной)
```bash
HOME=/tmp GIT_CONFIG_NOSYSTEM=1 git <command>
```

### GitHub: Curl API (резервный)
```bash
curl -s -X POST https://api.github.com/user/repos \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"name","private":false}'
```

## Git workflow

```bash
# 1. Проверить remote
HOME=/tmp GIT_CONFIG_NOSYSTEM=1 git remote -v

# 2. Добавить/обновить remote
HOME=/tmp GIT_CONFIG_NOSYSTEM=1 git remote set-url origin https://${GITHUB_TOKEN}@github.com/skit-sk/<repo>.git

# 3. Добавить файлы
HOME=/tmp GIT_CONFIG_NOSYSTEM=1 git add -A

# 4. Закоммитить
HOME=/tmp GIT_CONFIG_NOSYSTEM=1 git commit -m "message"

# 5. Запушить
HOME=/tmp GIT_CONFIG_NOSYSTEM=1 git push origin main
```

## Создание нового репозитория

```bash
TOKEN=$GITHUB_TOKEN
curl -s -X POST "https://api.github.com/user/repos" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"repo-name","description":"Description","private":false}'
```

## Remote URLs

```
origin        → https://${GITHUB_TOKEN}@github.com/skit-sk/tradingview-demos.git
graphs_candle → https://${GITHUB_TOKEN}@github.com/skit-sk/graphs_candle.git
diary_trading → https://${GITHUB_TOKEN}@github.com/skit-sk/diary_trading.git
```

## Проекты и репозитории

| Проект | Репо | Статус |
|--------|------|--------|
| tradingview-demos | skit-sk/tradingview-demos | ✅ |
| graphs_candle | skit-sk/graphs_candle | ✅ |
| diary_trading | skit-sk/diary_trading | ✅ |

## Починка .gitconfig

Если `.gitconfig` стал директорией:
```bash
rm -rf /home/user_aioc/.gitconfig
echo '[user]
  email = ai@test.com
  name = AI' > /home/user_aioc/.gitconfig
```
