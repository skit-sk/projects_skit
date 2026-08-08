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
| 08 | `projects/08_ofd_api/` | OFD API (Blueprint в 01) | `routes.py` |
| 09 | `projects/09_model_catalog/` | Каталог моделей AI | `models_catalog.json` |
| 10 | `projects/10_max_bot/` | MAX bot (сателлит Telegram бота) | `main.py` |
| 11 | `projects/11_ut11_loader/` | Загрузчик УТ 10.3 → УТ 11.5 (оптовик) | `_work/README.md` |
| 13 | `projects/13_BPbazeMagistrDBF/` | Загрузчик DBF Магистр → БП 3.0 (внешняя обработка) | `output/ЗагрузкаМагистрDBF.epf` |
| 14 | `projects/14_ExpImpUPBP/` | Выгрузка УП → Загрузка БП (внешняя обработка) | `_work/src/ВыгрузкаЗагрузкаУПБП.xml` |
| — | `/shared/1c_ut11` | 🗄️ Реальная конфигурация УТ 11.5 (MCP: `1c_ut11`) | `Configuration.xml` |
| VizLab | `projects/01_fundament_rf/viz_lab/` | 🧪 Visualization Lab (Blueprint в 01) | `/viz-lab/` |

## Структура

```
workspace/
├── projects/              # проекты по номерам
├── /shared/               # общие ресурсы (вне workspace): 1c_ut11 (MCP), 1c_traktir, 1c_shared
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
| `max_bot`, `max`, `platform-api` | `skills/instructions/max_bot.md` |
| `sc`, `скрин`, `screenshot` | — встроенные скриншоты TradingView (bot/screenshot_*.py) |
| `viz_lab`, `лаборатория`, `lab`, `визуализация` | `skills/instructions/viz_lab.md` |
| `1c_ut11`, `mcp`, `bsl`, `rlm_projects`, `rlm_start` | `/shared/1c_ut11` (MCP-проект `1c_ut11`) — реальная конфигурация УТ 11.5 |
| `preflight`, `релиз`, `epf`, `формат потока` | `skills/instructions/epf_release.md` |
| `trade`, `трейдинг`, `smc`, `wyckoff`, `order flow`, `fvg`, `ликвидация`, `обучение трейдингу`, `институциональный`, `sweep`, `bos`, `choch`, `mss`, `elliot`, `volume profile`, `footprint`, `microstructure`, `свечн`, `candle`, `паттерн`, `doji`, `hammer`, `engulf`, `head and shoulders`, `флаг`, `клин`, `треугольник`, `настроение`, `sentiment`, `fear`, `greed`, `страх`, `жадность`, `onchain`, `on-chain`, `кит`, `whale`, `mvrv`, `sopr`, `nvt`, `exchange flow`, `биржевой`, `дериватив`, `oi`, `open interest`, `funding`, `фандинг`, `heatmap`, `анализ`, `обучение`, `индикатор` | `skills/instructions/trading.md` |
| `12_tradehelp`, `tradehelp`, `learn`, `viz`, `tools`, `journal`, `checklist`, `risk`, `score`, `confluence` | `projects/12_tradehelp/README.md` |
| `midasflow`, `mf grid`, `33 levels`, `crp`, `shadow dom`, `3-tier`, `position engineering`, `ipda`, `json protocol` | `projects/12_tradehelp/docs/MidasFlow_JSON_Schema.md` |
| `sandbox`, `playground`, `registry`, `health aggregator`, `12 в sandbox`, `proxy 12` | `projects/01_fundament_rf/routes/sandbox.py` |

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

## ⚠️ MAX Bot — СТРОГОЕ ПРАВИЛО

**MAX bot запускать/перезапускать ТОЛЬКО через `scripts/max_bot.sh`.**

```bash
./scripts/max_bot.sh start              # запуск
./scripts/max_bot.sh stop               # остановка
./scripts/max_bot.sh restart            # перезапуск
./scripts/max_bot.sh status             # статус
./scripts/max_bot.sh logs               # tail -f лога
./scripts/max_bot.sh webhook <url>      # установка webhook
```

❌ **НИКОГДА** не запускать `python main.py` напрямую.

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

## ⚠️ EPF (1С 8.3 УТ 10.3) — строгие правила сборки

Обработка `ВыгрузкаКонтрагентов_v1.epf` живёт в `projects/11_ut11_loader/_work/`.  
Сборочный каталог: `projects/11_ut11_loader/_work/epf3_контрагенты/build/`.

### 🔥 Ошибка формата потока — что НЕЛЬЗЯ делать

| Действие | Результат |
|----------|-----------|
| `json.load` + `json.dump` на `Form.elem.json` | ✅ **Безопасно** ТОЛЬКО для правки верхнеуровневых `props[]`, `tree[]`, `data[]` (удаление/добавление элементов формы) |
| `json.load` + `json.dump` на `raw[2][1][7]` | ❌ **Ломает формат** — команды кнопок (`raw[2][1][7][5]`, `raw[2][1][7][9]`) нельзя трогать через `json.load/dump` |
| Редактировать `Form.elem.json` через Python regex (`re.sub` с `re.DOTALL`) | ❌ **Ломает структуру** — `.*?` «съедает» границы вложенных блоков |
| Писать `НоваяКнопка.Заголовок` | ❌ Свойство называется **`Текст`**, не `Заголовок` |
| `Колонки[Имя].Заголовок` | ❌ Свойство называется **`ТекстШапки`**, не `Заголовок` |
| `ЭлементыФормы.ОсновныеДействияФормы.Обновить()` | ❌ Метод не существует/ошибка |
| `ГоризонтальноеПоложениеЭлементов` у `КоманднаяПанель` | ❌ Свойство не существует |

### ✅ Рабочие рецепты

1. **Правка имён/текста** (`Выполнить` → `Заполнить`, синонимы) → только `sed` на сыром тексте:
   ```bash
   sed -i 's/\\"Выполнить\\"/\\"Заполнить\\"/g' Form/Форма/Form.elem.json
   ```
2. **Удаление реквизитов/элементов формы** → `json.load/dump` на `props`/`tree`/`data` (НЕ трогать `raw[2][1][7]`):
   ```python
   d = json.load(open('Form.elem.json'))
   d['props'] = [p for p in d['props'] if ...]     # безопасно
   d['tree'] = [t for t in d['tree'] if ...]        # безопасно
   d['data'].pop(key)                                 # безопасно
   json.dump(d, open('Form.elem.json','w'), indent=2)
   ```
3. **Добавление кнопки** → только **программно** в модуле формы (через Попытка/Исключение):
   ```bsl
   Попытка
       Кнп = ЭлементыФормы.ОсновныеДействияФормы.Кнопки;
       Если Кнп.Найти("Кнопка") = Неопределено Тогда
           НК = Кнп.Добавить("Кнопка");
           НК.Текст = "Текст кнопки";
           НК.Действие = Новый Действие("Обработчик");
       КонецЕсли;
   Исключение
   КонецПопытки;
   ```
4. **Создание таблицы** → программно в модуле с Попытка:
   ```bsl
   ТП = ЭлементыФормы.Добавить(Тип("ТабличноеПоле"), "Имя");
   ТП.Значение = МояТаблица; ТП.СоздатьКолонки(); ТП.ТолькоПросмотр = Истина;
   ```
5. **Вызов модуля объекта из формы** → напрямую по имени (как в epf1):
   ```bsl
   ВыполнитьВыгрузку(Парам1, Парам2);  // без префикса, Экспорт в модуле объекта
   ```
6. **Передача таблицы на выгрузку** → параметром (не через `Перем` модуля — путается с реквизитом формы):
   ```bsl
   ЗаписатьКонтрагентовВXML(ИмяФайла, МояТаблица)
   ```

### Сборка
```bash
source venv/bin/activate
v8unpack -B build ВыгрузкаКонтрагентов_v1.epf
```
Проверка: `v8unpack -E ВыгрузкаКонтрагентов_v1.epf _work/.tmp/check` — должна распаковаться без ошибок.

## ⚠️ Preflight — СТРОГОЕ ПРАВИЛО ПЕРЕД РЕЛИЗОМ EPF

**Перед выдачей любого `.epf` выполнить:**

```bash
./scripts/preflight.sh build_v200 ЗагрузкаДанныхИзXML_V021_UT11_v2.02.epf
```

Preflight проходит 7 этапов:
1. `verify_elem_strict.py` — статический анализ Form.elem.json
2. `v8unpack -B` — сборка EPF
3. `v8unpack -E` — распаковка (ловит «Ошибка формата потока»)
4. `verify_elem_strict.py` на распакованном
5. **Roundtrip diff** — пересборка распакованного, сравнение Form
6. `verify_epf.py` — проверка паттернов и регрессий
7. Сигнатура `ff ff ff 7f`

❌ **Если preflight завершился с ошибкой — релиз НЕ ВЫПУСКАТЬ.**

## ⚠️ 1C/EPF — СТРОГОЕ ПРАВИЛО ВРЕМЕННЫХ ДИРЕКТОРИЙ

Все временные файлы операций с 1С EPF (распаковка, сборка, верификация)
создавать ТОЛЬКО в:

```
projects/11_ut11_loader/_work/.tmp/
```

❌ **ЗАПРЕЩЕНО** использовать глобальную `/tmp/` для любых операций 1С EPF.

✅ `scripts/preflight.sh` и `_work/verify_epf.py` уже настроены на `_work/.tmp/`.
   При ручном запуске v8unpack для проверки указывать ту же директорию:

```bash
v8unpack -E ЗагрузкаДанныхИзXML_V021_UT11_v2.02.epf _work/.tmp/check
```

Очистка: `.tmp/` удаляется при каждом запуске preflight/verify.  
Принудительно: `rm -rf projects/11_ut11_loader/_work/.tmp/`.

## Security

- Токены в `.env` — не коммитить
- Helper: `source scripts/source_env.sh`
- Guidelines: `docs/SECURITY_GUIDELINES.md`

## ⚠️ Бэкап сессий — после пересоздания контейнера

Контейнер пересоздаётся без сохранения `~/.local/share/opencode/` — все сессии
теряются безвозвратно (случилось 07.08.2026). Персистентный каталог — `workspace/sessions/`.

```bash
./scripts/backup_opencode.sh              # экспорт всех сессий → workspace/sessions/
./scripts/backup_opencode.sh --clean-old  # + удаление устаревших exports
```

- Запускать после каждого значимого диалога.
- Экспортированный файл: `workspace/sessions/session-ses_<ID>.json`.
- `opencode session list` показывает сессии только из текущей БД — после
  пересоздания контейнера старые ID не видны, но exports в `sessions/` остаются.

## 🔌 MCP-сервер rlm-tools-bsl (порт 9000)

- Исходники: `tools/rlm-tools-bsl/` (установлен в корневой venv, версия 1.32.0).
- Конфиг: `~/.local/share/rlm-tools-bsl/service.json` (+ `projects.json` — список
  проектов 1С: `1c_ut11`, `1c_ut10`, `1c_UPArmada`, `BPMagistr`; `RLM_CONFIG_FILE` → этот файл).
- Запуск:
  ```bash
  export RLM_CONFIG_FILE=$HOME/.local/share/rlm-tools-bsl/service.json
  nohup venv/bin/rlm-tools-bsl --transport streamable-http --host 127.0.0.1 --port 9000 >> server.log 2>&1 &
  ```
- Проверка: `curl http://127.0.0.1:9000/health` → 200.
- `mcp.1c` (8080) отключён (`enabled: false` в `.opencode/opencode.json`) — 1С живёт
  на внешней машине, включить после восстановления доступа.
