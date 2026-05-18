# ccxt Claude Skills — установка и применение

Набор skills из официального репозитория ccxt для AI-агентов (Claude Code / OpenCode).

## Доступные навыки

| Skill | Язык | Вызов |
|-------|------|-------|
| `ccxt-python` | Python | `/ccxt-python` |
| `ccxt-typescript` | TypeScript / JS | `/ccxt-typescript` |
| `ccxt-php` | PHP | `/ccxt-php` |
| `ccxt-csharp` | C# / .NET | `/ccxt-csharp` |
| `ccxt-go` | Go | `/ccxt-go` |

## Установка

```bash
# Из корня репозитория ccxt
git clone https://github.com/ccxt/ccxt.git /tmp/ccxt
cp -r /tmp/ccxt/.claude/skills/ccxt-python ~/.opencode/skills/
cp -r /tmp/ccxt/.claude/skills/ccxt-typescript ~/.opencode/skills/
```

Или через установочный скрипт:
```bash
bash /tmp/ccxt/.claude/skills/install-skills.sh --python --typescript
```

## Что покрывает каждый skill

- ✅ Установка и импорт
- ✅ REST API (fetch_ticker, create_order и т.д.)
- ✅ WebSocket API (watch_ticker, watch_order_book)
- ✅ Аутентификация (apiKey, secret)
- ✅ Обработка ошибок
- ✅ Rate limiting
- ✅ Примеры кода

## Применение в проектах репозитория

```bash
# В fundament_rf или graphs_candle
/ccxt-python  # загружает skill с документацией и примерами
```

Skill автоматически подскажет:
- Как подключить Bitget через ccxt
- Как получить OHLCV данные
- Как создать и отменить ордер
- Как обработать ошибки API

## Ссылки

- [Репозиторий ccxt](https://github.com/ccxt/ccxt)
- [Папка skills в ccxt](https://github.com/ccxt/ccxt/tree/master/.claude/skills)
- [Документация ccxt](https://docs.ccxt.com)
