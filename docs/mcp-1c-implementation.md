# MCP 1С — инструкция по развёртыванию

> Двусторонний канал AI ↔ 1С для тестирования и отладки генерируемого кода.
> Цель: AI пишет BSL-код → 1С исполняет → AI получает результат/ошибку → исправляет.

---

## 1. Архитектура развёртывания

```
┌─────────────────────────────────────┐    ┌──────────────────────────────────────┐
│  IP_A: Windows Server               │    │  IP_B: Ubuntu 22.04+                │
│                                     │    │                                      │
│  Apache 2.4 + 1С:Предприятие 8.3+   │    │  OpenCode / Claude / Cursor         │
│                                     │    │                                      │
│  ┌───────────────────────────────┐  │    │  ┌────────────────────────────────┐  │
│  │  mcp-1c (расширение .cfe)    │──┼────┼──│  mcp-1c (Go-бинарник)          │  │
│  │  HTTP-сервис /hs/mcp-1c      │  │    │  │  stdio → HTTP к IP_A           │  │
│  └───────────────────────────────┘  │    │  └────────────────────────────────┘  │
│                                     │    │                                      │
│  ┌───────────────────────────────┐  │    │  ┌────────────────────────────────┐  │
│  │  1c-mcp-toolkit (обработка    │──┼────┼──│  OpenCode MCP-клиент           │  │
│  │  .epf), встроенный HTTP       │  │    │  │  (streamable-http)             │  │
│  │  порт 6003                    │  │    │  └────────────────────────────────┘  │
│  └───────────────────────────────┘  │    │                                      │
│                                     │    │  ┌────────────────────────────────┐  │
│  ┌───────────────────────────────┐  │    │  │  bsl-mcp (Python)             │  │
│  │  1С:Бухгалтерия / ERP / ...   │  │    │  │  проверка синтаксиса BSL      │  │
│  └───────────────────────────────┘  │    │  └────────────────────────────────┘  │
│                                     │    │                                      │
└─────────────────────────────────────┘    └──────────────────────────────────────┘
```

### Порты

| Откуда | Куда | Протокол | Порт | Назначение |
|--------|------|----------|------|------------|
| IP_B | IP_A | HTTP | 80/443 | mcp-1c HTTP-сервис через Apache |
| IP_A | — | HTTP | 6003 | 1c-mcp-toolkit встроенный сервер |
| IP_B | — | — | — | bsl-mcp локальный (stdio) |

---

## 2. Пререквизиты

### IP_A (Windows Server)

| Компонент | Версия | Проверка |
|-----------|--------|----------|
| Windows Server | 2019+ | `systeminfo` |
| Apache 2.4 | 2.4.x | `httpd -v` |
| 1С:Предприятие | 8.3.20+ | `"C:\Program Files\1cv8\common\1cEnterpriseVersion.ini"` |
| Публикация базы | http://IP_A/buh | Открыть в браузере /buh |
| PowerShell 5.1+ | — | `$PSVersionTable` |

### IP_B (Ubuntu)

| Компонент | Команда проверки |
|-----------|------------------|
| Ubuntu 22.04+ | `lsb_release -a` |
| Python 3.10+ | `python3 --version` |
| Go 1.21+ | `go version` |
| curl | `curl --version` |
| OpenCode | `opencode --version` |

---

## 3. Установка MCP-серверов

### 3.1 mcp-1c (feenlace)

Самый простой старт. Один Go-бинарник на IP_B, одно расширение .cfe на IP_A.

#### Шаг 1. IP_A — установка расширения .cfe

```powershell
# От имени администратора
# 1. Скачать MCP_Сервер.cfe с https://github.com/feenlace/mcp-1c/releases
# 2. Открыть Конфигуратор → Расширения → Добавить → выбрать .cfe
# 3. Обновить конфигурацию базы
# 4. Конфигуратор → Администрирование → Публикация на веб-сервере
# 5. Отметить HTTP-сервис "mcp-1c"
# 6. Перезапустить Apache
iisreset  # если IIS
# или
httpd -k restart  # если Apache
```

**Проверка на IP_A:**
```powershell
curl http://localhost/buh/hs/mcp-1c/ping
# Ожидаемый ответ: {"result":"pong"}
```

#### Шаг 2. IP_B — установка бинарника

```bash
# Скачать последний релиз
wget https://github.com/feenlace/mcp-1c/releases/latest/download/mcp-1c-linux-amd64
chmod +x mcp-1c-linux-amd64
sudo mv mcp-1c-linux-amd64 /usr/local/bin/mcp-1c

# Проверить
mcp-1c version
```

#### Шаг 3. IP_B — проверка связности

```bash
mcp-1c --base "http://IP_A/buh/hs/mcp-1c" --ping
# Ожидаемый ответ: pong
```

**Если ошибка:** проверить доступность IP_A с IP_B:
```bash
curl http://IP_A/buh/hs/mcp-1c/ping
```

---

### 3.2 1c-mcp-toolkit (ROCTUP)

Внешняя обработка .epf — **не требует изменения конфигурации**. Самый важный сервер для отладки (execute_code).

#### Шаг 1. IP_A — запуск обработки

```powershell
# 1. Скачать MCP_Toolkit.epf с https://github.com/ROCTUP/1c-mcp-toolkit/releases
# 2. Открыть в 1С: Файл → Открыть → выбрать MCP_Toolkit.epf
# 3. Выбрать режим "Встроенный сервер"
# 4. Указать порт 6003
# 5. Нажать "Запустить сервер"
```

**Проверка на IP_A:**
```powershell
curl http://localhost:6003/mcp/ping
# Ожидаемый ответ: pong
```

#### Шаг 2. IP_B — проверка связности

```bash
curl http://IP_A:6003/mcp/ping
# Ожидаемый ответ: pong
```

**Если порт 6003 закрыт:** открыть в firewall на IP_A:
```powershell
netsh advfirewall firewall add rule name="MCP Toolkit" dir=in action=allow protocol=TCP localport=6003
```

---

### 3.3 bsl-mcp (проверка синтаксиса BSL)

Локально на IP_B. Нужен для проверки кода ДО отправки в 1С.

```bash
# Установить Python-пакет
pip install mcp-bsl-ls

# Проверить
python3 -m mcp_bsl_ls --version
```

**Если mcp-bsl-ls не в pip:** установить вручную:
```bash
git clone https://github.com/phsin/mcp-bsl-ls
cd mcp-bsl-ls
pip install -r requirements.txt
```

---

## 4. Проверка связности (healthcheck)

Скрипт проверки на IP_B:

```bash
#!/bin/bash
# healthcheck.sh — проверка всех MCP-серверов

IP_A="192.168.1.100"  # заменить на реальный IP

echo "=== MCP 1С Healthcheck ==="

echo -n "1. mcp-1c (feenlace): "
if mcp-1c --base "http://${IP_A}/buh/hs/mcp-1c" --ping 2>/dev/null; then
  echo "✅"
else
  echo "❌"
fi

echo -n "2. 1c-mcp-toolkit (порт 6003): "
if curl -s "http://${IP_A}:6003/mcp/ping" | grep -q pong; then
  echo "✅"
else
  echo "❌"
fi

echo -n "3. bsl-mcp: "
if python3 -m mcp_bsl_ls --version 2>/dev/null; then
  echo "✅"
else
  echo "❌"
fi

echo "=== Done ==="
```

---

## 5. Цикл «генерация → проверка → исполнение → отладка»

### 5.1 Prompt-шаблон для AI-агента

```markdown
## Задача
Сгенерировать BSL-код для обработки 1С.

## Контекст
- База: {название_базы}, платформа {версия}
- Метаданные: используй tools mcp-1c для получения структуры
- Справка: используй bsl-mcp для проверки синтаксиса

## Порядок работы
1. Прочитай метаданные через mcp-1c: `get_metadata_tree`
2. Получи структуру объекта: `get_object_structure`
3. Напиши BSL-код
4. Проверь синтаксис через bsl-mcp
5. Исполни код через 1c-mcp-toolkit: `execute_code`
6. Прочитай результат/ошибку через `get_event_log`
7. Если ошибка — исправь и повтори с шага 3
```

### 5.2 Пример: сгенерировать и исполнить обработку

**Шаг 1. Получить контекст метаданных**

Вызов AI-агента к MCP:
```
mcp-1c.get_metadata_tree()
```

**Шаг 2. Запросить справку по API**

```
mcp-bsl-platform-context.search_platform_context("Справочники.Контрагенты")
```

**Шаг 3. Написать BSL-код**

```bsl
Процедура СоздатьКонтрагента(Наименование, ИНН) Экспорт
    НовыйЭлемент = Справочники.Контрагенты.СоздатьЭлемент();
    НовыйЭлемент.Наименование = Наименование;
    НовыйЭлемент.ИНН = ИНН;
    НовыйЭлемент.Записать();
    Возврат НовыйЭлемент.Ссылка;
КонецПроцедуры
```

**Шаг 4. Проверить синтаксис (bsl-mcp)**

```json
// Tools: analyze_text
{
  "text": "Процедура СоздатьКонтрагента(Наименование, ИНН) Экспорт\n    НовыйЭлемент = Справочники.Контрагенты.СоздатьЭлемент();\n    НовыйЭлемент.Записать();\n    Возврат НовыйЭлемент.Ссылка;\nКонецПроцедуры"
}
```

**Шаг 5. Исполнить в 1С (1c-mcp-toolkit)**

```json
// Tools: execute_code
{
  "code": "Процедура СоздатьКонтрагента(Наименование, ИНН) Экспорт\n    НовыйЭлемент = Справочники.Контрагенты.СоздатьЭлемент();\n    НовыйЭлемент.Наименование = Наименование;\n    НовыйЭлемент.ИНН = ИНН;\n    НовыйЭлемент.Записать();\n    Возврат НовыйЭлемент.Ссылка;\nКонецПроцедуры\n\nРезультат = СоздатьКонтрагента(\"ООО Тест\", \"7701234567\");\nВозврат Результат;",
  "timeout": 30
}
```

**Шаг 6. Прочитать результат**

```
mcp-1c.get_event_log(level="Error", limit=5)
```

### 5.3 Автоматизация цикла

Агент должен выполнять цикл:

```
while есть_ошибки:
    if ошибка in result:
        прочитать лог
        исправить код
        проверить синтаксис
        исполнить снова
    else:
        успех → сохранить результат
```

---

## 6. Конфиг OpenCode

### 6.1 Минимальный (3 сервера)

```json
{
  "mcpServers": {
    "1c": {
      "command": "/usr/local/bin/mcp-1c",
      "args": ["--base", "http://IP_A/buh/hs/mcp-1c"]
    },
    "1c-toolkit": {
      "url": "http://IP_A:6003/mcp",
      "transport": "streamable-http"
    },
    "bsl-mcp": {
      "command": "python3",
      "args": ["-m", "mcp_bsl_ls"]
    }
  }
}
```

### 6.2 Полный (с тестами и справкой)

```json
{
  "mcpServers": {
    "1c": {
      "command": "/usr/local/bin/mcp-1c",
      "args": ["--base", "http://IP_A/buh/hs/mcp-1c"]
    },
    "1c-toolkit": {
      "url": "http://IP_A:6003/mcp",
      "transport": "streamable-http"
    },
    "bsl-lint": {
      "command": "python3",
      "args": ["-m", "mcp_bsl_ls"]
    },
    "1c-test-runner": {
      "command": "java",
      "args": ["-jar", "/opt/mcp/mcp-onec-test-runner.jar"]
    },
    "1c-help": {
      "command": "java",
      "args": ["-jar", "/opt/mcp/mcp-bsl-platform-context.jar"]
    }
  }
}
```

---

## 7. Чеклист запуска

### IP_A (Windows)

- [ ] Установлено расширение mcp-1c (.cfe)
- [ ] Опубликован HTTP-сервис /hs/mcp-1c в Apache
- [ ] Apache перезапущен
- [ ] curl http://localhost/buh/hs/mcp-1c/ping → pong
- [ ] Запущена обработка 1c-mcp-toolkit (.epf)
- [ ] Порт 6003 открыт в firewall
- [ ] curl http://localhost:6003/mcp/ping → pong
- [ ] Настроена публикация базы (/buh доступен из браузера)

### IP_B (Ubuntu)

- [ ] mcp-1c скачан и помещён в /usr/local/bin/
- [ ] mcp-1c --ping → pong
- [ ] curl IP_A:6003/mcp/ping → pong
- [ ] bsl-mcp установлен (python3 -m mcp_bsl_ls --version)
- [ ] OpenCode установлен (opencode --version)
- [ ] Конфиг `.opencode.json` или `opencode.json` настроен

---

## 8. Типовые проблемы и их решение

| Проблема | Причина | Решение |
|----------|---------|---------|
| `connection refused` на порт 6003 | Firewall на IP_A блокирует порт | `netsh advfirewall firewall add rule ...` |
| `404` на /buh/hs/mcp-1c/ping | HTTP-сервис не опубликован | Переопубликовать базу в Apache |
| `401 Unauthorized` | BasicAuth на Apache | Добавить исключение для /hs/ в .htaccess |
| mcp-1c: `exec format error` | Не тот бинарник (ARM vs AMD64) | Скачать правильную архитектуру |
| execute_code: `Ошибка выполнения` | Синтаксическая ошибка в BSL | Проверить через bsl-mcp ДО отправки |
| bsl-mcp: `JRE not found` | Не установлена Java | `apt install default-jre` |
| медленный ответ | База большая / нет индексов | Оптимизировать запросы, добавить таймауты |

### Быстрая диагностика

```bash
# IP_B: проверить все сервисы одной командой
echo "mcp-1c: $(mcp-1c --base http://IP_A/buh/hs/mcp-1c --ping)" && \
echo "toolkit: $(curl -s http://IP_A:6003/mcp/ping)" && \
echo "bsl-mcp: $(python3 -m mcp_bsl_ls --version 2>&1)"
```

---

## Приложение A. Структура конфига OpenCode

```
~/.config/opencode/
├── opencode.json          # глобальный конфиг
└── projects/
    └── 1c/
        └── opencode.json  # проектный конфиг (рекомендуется)
```

Проектный конфиг (положить в корень проекта 1С):
```json
{
  "mcpServers": {
    "1c": {
      "command": "/usr/local/bin/mcp-1c",
      "args": ["--base", "http://IP_A/buh/hs/mcp-1c"]
    },
    "1c-toolkit": {
      "url": "http://IP_A:6003/mcp",
      "transport": "streamable-http"
    },
    "bsl-lint": {
      "command": "python3",
      "args": ["-m", "mcp_bsl_ls"]
    }
  }
}
```

---

## Приложение B. Сценарии использования

### B1. Отладка кода (основной сценарий)

```
AI пишет код → bsl-mcp проверяет синтаксис → 1c-mcp-toolkit исполняет
→ mcp-1c читает лог ошибок → AI исправляет → повтор
```

### B2. Генерация тестовых данных

```
AI → 1c-mcp-toolkit.execute_code (создание документов)
→ mcp-1c.execute_query (SELECT для проверки)
```

### B3. Анализ существующего кода

```
mcp-1c.search_code → bsl-mcp.analyze → AI выдаёт рекомендации
```
