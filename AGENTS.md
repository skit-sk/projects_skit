# AGENTS.md

## Проекты

| # | Директория | Назначение | Вход |
|---|------------|-----------|------|
| 01 | `projects/01_fundament_rf/` | Трекер сделок Bitget | `app.py` |
| 02 | `projects/02_graphs_candle/` | Свечные графики Plotly | `main.py` |
| 03 | `projects/03_demo_charts_ascii/` | ASCII-графики | `app.py` |
| 04 | `projects/04_tradingview-demos/` | TradingView виджеты | `update_widgets.py` |
| 05 | `projects/05_transcript/` | Транскрипция | `transcript_pipeline.py` |
| 06 | `projects/06_screenshots_project/` | Каталог скриншотов | `catalog.html` |
| 07 | `projects/07_tg_bot_aiforguest/` | Telegram bot proxy → opencode | `bot/main.py` |

## Структура

```
workspace/
├── projects/              # проекты по номерам
├── scripts/               # скрипты + Flask
├── tools/                 # agent-browser
├── skills/
│   └── instructions/      # 👈 рабочие инструкции
├── docs/                  # документация
├── sessions/              # сессионные заметки
├── venv/                  # корневой venv
├── .env                   # секреты (не коммитить)
└── AGENTS.md              # этот файл
```

## ⚡ Router — при запросе прочитай соответствующий skill

| Ключевые слова | Файл инструкции |
|----------------|-----------------|
| `git`, `github`, `commit`, `push` | `skills/instructions/git.md` |
| `vercel`, `deploy` | `skills/instructions/vercel.md` |
| `flask`, `server`, `порт`, `5000` | `skills/instructions/flask.md` |
| `graphify`, `граф` | `skills/instructions/graphify.md` |
| `browser`, `скриншот` | `skills/instructions/browser.md` |
| `token`, `secret`, `.env` | `skills/instructions/security.md` |
| `venv`, `pip`, `python-dotenv` | `skills/instructions/python-env.md` |
| `tg_bot`, `telegram`, `бот`, `tg` | `skills/instructions/tg_bot.md` |
| `sc`, `скрин`, `screenshot` | — встроенные скриншоты TradingView (bot/screenshot_*.py) |

## ⚠️ Flask — СТРОГОЕ ПРАВИЛО

**Все Flask-проекты запускать/перезапускать ТОЛЬКО через `scripts/flask.sh`.**

```bash
# Запуск (по умолчанию порт 5000 для всех проектов)
./scripts/flask.sh start 01              # fundament_rf
./scripts/flask.sh start 02              # graphs_candle
./scripts/flask.sh start 03              # demo_charts_ascii

# Переопределить порт (3-й аргумент)
./scripts/flask.sh start 02 5002
./scripts/flask.sh restart fundament_rf
./scripts/flask.sh restart graphs_candle 5002

# Остановка и статус
./scripts/flask.sh stop 03
./scripts/flask.sh status demo_charts_ascii
```

❌ **НИКОГДА** не запускать `python app.py` или `python main.py` напрямую —
процесс может зависнуть, не отвязаться от терминала и не перехватить сигналы.

## ⚠️ TG Bot — СТРОГОЕ ПРАВИЛО

**Telegram bot запускать/перезапускать ТОЛЬКО через `scripts/tg_bot.sh`.**

```bash
./scripts/tg_bot.sh start              # запуск
./scripts/tg_bot.sh stop               # остановка
./scripts/tg_bot.sh restart            # перезапуск
./scripts/tg_bot.sh status             # статус
./scripts/tg_bot.sh logs               # tail -f лога
```

❌ **НИКОГДА** не запускать `python bot/main.py` напрямую.

## Quick Start

```bash
source scripts/source_env.sh   # загрузить .env
source venv/bin/activate       # активировать venv
```

## 🖥 System info — формат вывода

При любом запросе о процессах/состоянии системы выводить в этом формате:

```
uptime: 25d 22h59  load: 0.34 0.37 0.39
MEM: 3.8G total · 1.8G used · 1.3G free · 1.0G cache
SWAP: 511M · 280M used · 231M free
PROCESSES: 37 total
NET: RX 19.6 GB · TX 11.1 GB
DISK: READ 180.5 GB · WRITE 283.0 GB

  COMMAND                   CNT  %CPU  %MEM
  opencode                    3  77.9  32.4
  python3                     5  18.6   6.7
  agent-browser-linux-x64     1   0.2   0.0
  bash                       21   0.0   0.2
  tail/sh/su/sort/ps/awk      7   0.0   0.1
```

Агрегировать одинаковые команды, сортировать по %CPU.

## Security

- Токены в `.env` — не коммитить
- Helper: `source scripts/source_env.sh`
- Guidelines: `docs/SECURITY_GUIDELINES.md`
