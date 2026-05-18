# Git-версионирование

## Правила

1. **Каждый коммит, изменяющий контент сайта, обязан обновлять версию в `index.html`**
2. Формат: `vMAJOR.MINOR.PATCH | YYYY-MM-DD HH:MM MSK | Описание`
3. **MAJOR** — breaking changes
4. **MINOR** — новый функционал
5. **PATCH** — багфиксы
6. Вести `CHANGELOG.md`
7. Перед push: `git diff HEAD~1..HEAD -- index.html | grep version`

## Где обновлять

| Файл | Что делать |
|------|------------|
| `index.html` | Обновить строку в футере |
| `CHANGELOG.md` | Добавить секцию `## vX.X.X (дата) — Заголовок` |
| Коммит | Включить версию: `feat(v3.0.0): описание` |

## Чеклист перед push

- [ ] Версия в `index.html` обновлена?
- [ ] `CHANGELOG.md` обновлён?
- [ ] Версия в коммит-сообщении?

## Связанные KB

- [fundament_rf](../3-projects/fundament-rf.md)
- [graphs_candle](../3-projects/graphs-candle.md)
- [Рабочие инструкции по git](../../skills/instructions/git.md)
