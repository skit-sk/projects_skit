# agent-browser

Browser automation CLI for AI agents. Быстрый нативный Rust CLI от Vercel Labs.

**Статус:** АКТИВЕН
**Обновлено:** 2026-05-01
**Ссылка:** https://github.com/vercel-labs/agent-browser

---

## Установка

### Автоматическая (рекомендуется)
```bash
./tools/agent-browser/install.sh
```

### Вручную
```bash
npm install -g agent-browser
agent-browser install
```

### Другие способы
```bash
# Homebrew (macOS)
brew install agent-browser

# Cargo (Rust)
cargo install agent-browser

# Из исходников
git clone https://github.com/vercel-labs/agent-browser
cd agent-browser
pnpm install && pnpm build && pnpm build:native
pnpm link --global
agent-browser install
```

### Linux
```bash
agent-browser install --with-deps
```

---

## Быстрый старт для AI-агента

```bash
# 1. Открыть страницу
agent-browser open https://example.com

# 2. Получить интерактивные элементы (компактный snapshot)
agent-browser snapshot -i

# 3. Клик по референсу (без CSS-селекторов!)
agent-browser click @e1

# 4. Заполнить поле
agent-browser fill @e2 "text@example.com"
```

---

## Workflow-скрипты

| Скрипт | Команда | Назначение |
|--------|---------|------------|
| Базовый | `./tools/agent-browser/workflows/basic.sh <url>` | Open → Snapshot → готов к взаимодействию |
| Snapshot | `./tools/agent-browser/workflows/snapshot.sh <url>` | Snapshot с оптимизацией для AI |
| Screenshot | `./tools/agent-browser/workflows/screenshot.sh <path>` | Screenshot с аннотациями |
| Chat | `./tools/agent-browser/workflows/chat.sh "<instruction>"` | Естественный язык → команды |
| Batch | `./tools/agent-browser/workflows/batch.sh <url> <cmd1> <cmd2>...` | Пакетное выполнение |

---

## Ключевые команды

### Навигация
```bash
agent-browser open <url>           # открыть URL
agent-browser back                 # назад
agent-browser forward             # вперед
agent-browser reload               # перезагрузить
```

### Snapshot (для AI)
```bash
agent-browser snapshot             # полное accessibility tree
agent-browser snapshot -i          # только интерактивные элементы
agent-browser snapshot -i --urls  # + URL ссылок
agent-browser snapshot -c          # компактный
agent-browser snapshot -d 3       # глубина 3 уровня
```

### Взаимодействие через референсы
```bash
agent-browser click @e2            # клик по референсу
agent-browser fill @e3 "text"      # заполнить поле
agent-browser hover @e1            # hover
agent-browser focus @e2            # фокус
```

### Семантические локаторы
```bash
agent-browser find role button click --name "Submit"
agent-browser find text "Sign In" click
agent-browser find label "Email" fill "test@test.com"
agent-browser find testid my-id click
```

### Скриншоты
```bash
agent-browser screenshot                    # простой
agent-browser screenshot --annotate         # с метками элементов
agent-browser screenshot --full            # полная страница
agent-browser screenshot page.png           # в файл
```

### Cookies и Storage
```bash
agent-browser cookies                  # получить cookies
agent-browser cookies set <n> <v>      # установить cookie
agent-browser storage local             # localStorage
agent-browser storage session           # sessionStorage
```

### Табы
```bash
agent-browser tab new <url>           # новый таб
agent-browser tab <t2>                # переключиться
agent-browser tab close <t2>          # закрыть
```

### Сессии (изоляция)
```bash
agent-browser --session agent1 open site-a.com
agent-browser --session agent2 open site-b.com
agent-browser session list
```

---

## Оптимизация для AI (экономия токенов)

| Флаг | Эффект |
|------|--------|
| `-i` | Только интерактивные элементы |
| `-c` | Компактный вывод (без пустых элементов) |
| `-d N` | Ограничить глубину дерева |
| `--urls` | Включить URL ссылок |
| `--max-output N` | Лимит символов в выводе |

**Пример оптимизированного snapshot:**
```bash
agent-browser snapshot -i -c -d 5 --urls
```

---

## Конфигурация

### Файл конфигурации
```bash
# Расположение: ~/.agent-browser/config.json или ./agent-browser.json
{
  "headed": false,
  "screenshotDir": "./screenshots",
  "sessionName": "default"
}
```

### Флаги
```bash
--headed              # показать браузер
--session <name>      # изолированная сессия
--profile <name>      # Chrome profile reuse
--json                # JSON output
--debug               # debug output
```

---

## Безопасность

```bash
# Разрешенные домены
--allowed-domains "example.com,*.example.com"

# Лимит вывода
--max-output 50000

# Boundary markers для LLM
--content-boundaries
```

---

## Интеграция со скиллами

См. [../../skills/agent-browser/](../../skills/agent-browser/) для AI-агента.

---

## Прямые ссылки

| Ресурс | Ссылка |
|--------|--------|
| GitHub | https://github.com/vercel-labs/agent-browser |
| npm | https://www.npmjs.com/package/agent-browser |
| Docs | https://agent-browser.dev |

---

## Troubleshooting

```bash
# Диагностика
agent-browser doctor

# Исправление
agent-browser doctor --fix

# Offline диагностика
agent-browser doctor --offline --quick

# Обновление
agent-browser upgrade
```