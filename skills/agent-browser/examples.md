# agent-browser Examples

Практические примеры использования agent-browser для AI-агентов.

---

## Пример 1: Логин на сайт

```bash
# 1. Открыть страницу логина
agent-browser open https://example.com/login

# 2. Получить элементы
agent-browser snapshot -i
# → textbox "Email" [ref=e1], password "Password" [ref=e2], button "Sign In" [ref=e3]

# 3. Заполнить и отправить
agent-browser fill @e1 "admin@example.com"
agent-browser fill @e2 "password123"
agent-browser click @e3
```

---

## Пример 2: Поиск на Habr

```bash
# 1. Открыть Habr
agent-browser open https://habr.com

# 2. Snapshot
agent-browser snapshot -i
# → textbox "Поиск" [ref=e1], link "Все потоки" [ref=e2], ...

# 3. Клик на поиск и ввод запроса
agent-browser click @e1
agent-browser fill @e1 "AI agents"
agent-browser press @e1 Enter
```

---

## Пример 3: Навигация по статьям

```bash
# 1. Открыть статью
agent-browser open https://habr.com/ru/articles/1029704/

# 2. Snapshot
agent-browser snapshot -i
# → link "Комментарии" [ref=e42], button "Поделиться" [ref=e43], ...

# 3. Клик на комментарии
agent-browser click @e42
```

---

## Пример 4: Автономный дебаг React-компонента

```bash
# 1. Открыть локальный dev-сервер
agent-browser open --enable react-devtools http://localhost:3000

# 2. Интроспекция React
agent-browser react tree                    # дерево компонентов
agent-browser react inspect <fiberId>       # props, hooks, state

# 3. Скриншот с аннотациями
agent-browser screenshot --annotate debug.png
```

---

## Пример 5: Batch execution (избегаем overhead)

```bash
agent-browser batch \
  "open https://example.com" \
  "find role button click --name 'Get Started'" \
  "snapshot -i" \
  "fill @e2 \"test@test.com\"" \
  "screenshot signup.png"
```

---

## Пример 6: Проверка фронтенда с Diff

```bash
# Baseline snapshot
agent-browser open https://example.com
agent-browser snapshot -i > baseline.txt

# После изменений - сравнить
agent-browser open https://example.com
agent-browser diff snapshot --baseline baseline.txt
```

---

## Пример 7: Использование профиля Chrome

```bash
# Использовать существующий логин Chrome
agent-browser --profile "Default" open https://gmail.com
# Или
agent-browser --profile ~/.myapp-profile open https://app.example.com
```

---

## Пример 8: Работа с multiple tabs

```bash
# Открыть основной сайт
agent-browser open https://example.com

# Новый таб для документации
agent-browser tab new --label docs https://docs.example.com

# Переключаться между табами
agent-browser tab docs           # перейти к docs
agent-browser tab t1             # перейти к первому табу

# Закрыть таб
agent-browser tab close docs
```

---

## Пример 9: Перехват и блокировка запросов

```bash
agent-browser batch \
  "open https://example.com" \
  "network route '*' --abort --resource-type script" \
  "navigate https://example.com"
```

---

## Пример 10: Интеграция в Python-скрипт

```python
import subprocess

def run_agent_browser(cmd):
    result = subprocess.run(
        f'agent-browser {cmd}',
        shell=True,
        capture_output=True,
        text=True
    )
    return result.stdout

# Использование
snapshot = run_agent_browser('open https://example.com && snapshot -i')
print(snapshot)
```

---

## Workflow-скрипты

Вместо ручного ввода команд можно использовать:

```bash
./tools/agent-browser/workflows/basic.sh https://example.com
./tools/agent-browser/workflows/snapshot.sh https://example.com
./tools/agent-browser/workflows/screenshot.sh https://example.com output.png
./tools/agent-browser/workflows/chat.sh "open google.com and search for cats"
./tools/agent-browser/workflows/batch.sh https://example.com "snapshot -i" "click @e1"
```

---

## Быстрый snapshot через утилиту

```bash
# Snapshot текущей страницы
./tools/agent-browser/bin/quick-snapshot.sh

# Snapshot с открытием URL
./tools/agent-browser/bin/quick-snapshot.sh https://example.com

# Сохранить в файл
./tools/agent-browser/bin/quick-snapshot.sh https://example.com snapshot.txt
```