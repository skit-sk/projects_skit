# 1C MCP — интеграция с AI-ассистентами

## Топология

```
IP_A (Windows Server)          IP_B (Ubuntu AI Agent)
─────────────────────          ──────────────────────────────
Apache + 1С Платформа          OpenCode + MCP бинарники
     │                              │
     │  HTTP: http://IP_A/<pub>/hs/*│
     │◄─────────────────────────────┤
     │                              │
     │                    Локальные MCP-серверы
     │                    подключаются к IP_A
```

---

## Сравнение серверов

| Сервер | Режим | Модифицирует конфигурацию | Нужен Apache | Свой порт | Язык | Инструментов |
|--------|-------|---------------------------|--------------|-----------|------|--------------|
| **mcp-1c** (feenlace) | Online | ✅ .cfe расширение | ✅ да | ❌ | Go | 9 |
| **1c-mcp-toolkit** (ROCTUP) | Online | ❌ .epf внешняя | ❌ нет | ✅ 6003 | Python | 13 |
| **vladimir-kharin/1c_mcp** | Online | ✅ .cfe расширение | ✅ да | Python прокси | 1C+Python | фреймворк |
| **1c-mcp-metacode** (ROCTUP) | Offline | ❌ не требуется | ❌ | ✅ 6001+Neo4j | Go | 3 |
| **1c-buddy** (ROCTUP) | Online | ❌ не требуется | ❌ | ✅ 6005 | JS | 3 |

---

## Детальное описание серверов

### 1. mcp-1c (feenlace) — первый этап

Базовый MCP-сервер. Один Go-бинарник, 9 готовых инструментов.

**Архитектура:**
```
AI (IP_B)                 1С (IP_A)
─────────────────         ───────────────────
mcp-1c (бинарник) ──►    .cfe расширение
     │                       │
     │  HTTP к /hs/mcp-1c    │  HTTP-сервис на Apache
     ▼                       ▼
               База 1С
```

**Инструменты (9):**
- `get_metadata_tree` — дерево метаданных
- `get_object_structure` — реквизиты, ТЧ, измерения
- `get_form_structure` — структура формы
- `get_configuration_info` — имя, версия, платформа
- `search_code` — полнотекстовый поиск (BM25/regex/exact)
- `bsl_syntax_help` — справка по BSL
- `execute_query` — выполнение SELECT
- `validate_query` — проверка синтаксиса запроса
- `get_event_log` — журнал регистрации

**Установка .cfe — 2 варианта:**

**Вариант А: Автоустановка (с IP_B)**
```bash
# Linux (IP_B) устанавливает расширение в базу на Windows
# требуется доступ к файловой базе или клиент-сервер
mcp-1c --install "\\\\IP_A\\путь\\к\\базе" --platform "C:\\Program Files\\1cv8\\8.3.XX.XXXX\\bin\\1cv8.exe"
```

**Вариант Б: Ручная на IP_A**
1. Скачать `MCP_Сервер.cfe` из https://github.com/feenlace/mcp-1c/releases
2. Конфигуратор → Расширения → Добавить → указать .cfe
3. Обновить конфигурацию БД
4. Конфигуратор → Администрирование → Публикация на веб-сервере
5. Отметить HTTP-сервис `mcp-1c`, опубликовать

**Запуск на IP_B (Ubuntu):**
```bash
wget https://github.com/feenlace/mcp-1c/releases/latest/download/mcp-1c-linux-amd64
chmod +x mcp-1c-linux-amd64
sudo mv mcp-1c-linux-amd64 /usr/local/bin/mcp-1c

# тест
mcp-1c --base "http://IP_A/buh/hs/mcp-1c"
```

**Конфиг OpenCode:**
```json
{
  "mcpServers": {
    "1c": {
      "command": "/usr/local/bin/mcp-1c",
      "args": ["--base", "http://IP_A/buh/hs/mcp-1c"]
    }
  }
}
```

---

### 2. 1c-mcp-toolkit (ROCTUP) — второй этап

Внешняя обработка .epf, НЕ расширение. Не меняет конфигурацию. 13 инструментов.

**Архитектура — встроенный сервер (рекомендуется):**
```
AI (IP_B) ◄── HTTP MCP/REST ──► .epf (IP_A)
                                    │
                               HTTP-сервер
                               внутри обработки
                               порт 6003
                               ▼
                          База 1С
```

**Инструменты (13):**
- `execute_query` — запросы на языке 1С
- `execute_code` — выполнение произвольного кода BSL
- `get_metadata` — метаданные базы
- `get_event_log` — журнал регистрации
- `get_object_by_link` / `get_link_of_object` — навигационные ссылки
- `find_references_to_object` — поиск ссылок на объект
- `get_access_rights` — права доступа
- `get_bsl_syntax_help` — справка по BSL
- `get_screenshot` — скриншот (только Windows)
- `restart_1c_session` / `close_1c_session` — управление сессией
- `submit_for_deanonymization` — деанонимизация

**Установка IP_A:**
1. Скачать `build/MCP_Toolkit.epf` из https://github.com/ROCTUP/1c-mcp-toolkit
2. Открыть в 1С: Файл → Открыть → выбрать .epf
3. В форме выбрать «Встроенный сервер»
4. Нажать «Запустить сервер»
5. HTTP-сервер запустится на порту 6003

**Запуск Python прокси на IP_B (опционально):**
```bash
python3 -m venv ~/venv/mcp-toolkit
source ~/venv/mcp-toolkit/bin/activate
pip install -r requirements.txt
python -m onec_mcp_toolkit_proxy --port 6003
```

**Конфиг OpenCode:**
```json
{
  "mcpServers": {
    "1c-toolkit": {
      "url": "http://IP_A:6003/mcp",
      "transport": "streamable-http"
    }
  }
}
```

---

### 3. vladimir-kharin/1c_mcp — третий этап (кастомные инструменты)

Фреймворк-расширение для создания СВОИХ MCP-инструментов внутри 1С.

**Архитектура:**
```
AI (IP_B) ◄── MCP ──► Python прокси ◄── HTTP ──► .cfe расширение
                                                       │
                                                 HTTP-сервис
                                                 на Apache
                                                 /hs/mcp/APIBackend
                                                       ▼
                                                  База 1С
```

**Когда развивать:**
- Нужны кастомные инструменты под свою конфигурацию
- Появилась повторяющаяся бизнес-задача → вынести в tool
- Требуется безопасность (логика внутри 1С, не в Python/Go)
- Нужны Resources (статический контекст) или Prompts (шаблоны)

**Структура разработки:**
```
Расширение MCP_Сервер.cfe
├── Подсистема mcp_КонтейнерыИнструментов
│   ├── Обработка1 (ваш инструмент)
│   │   ├── ДобавитьИнструменты()   ← описание tools
│   │   └── ВыполнитьИнструмент()    ← логика
│   └── Обработка2 (другой инструмент)
```

**Установка:**
```bash
# Python прокси на IP_B
python3 -m venv ~/venv/1c-mcp
source ~/venv/1c-mcp/bin/activate
pip install -r requirements.txt
python -m mcp_proxy \
  --onec-url "http://IP_A/buh/hs/mcp/APIBackend" \
  --port 6004
```

**Конфиг OpenCode:**
```json
{
  "mcpServers": {
    "1c-custom": {
      "url": "http://localhost:6004/mcp",
      "transport": "streamable-http"
    }
  }
}
```

---

### 4. 1c-buddy (ROCTUP) — четвёртый этап

Интеграция с 1С:Напарник (API code.1c.ai).

**Инструменты:**
- `ask_1c_ai` — общие вопросы по 1С
- `explain_1c_syntax` — объяснение объектов и синтаксиса
- `check_1c_code` — проверка кода на ошибки

**Установка на IP_B (без Docker — Node.js):**
```bash
git clone https://github.com/ROCTUP/1c-buddy
cd 1c-buddy
npm install
ONEC_BUDDY_TOKEN=your_token node dist/index.js
```

**С Docker:**
```bash
docker run -d \
  --name 1c-buddy \
  -p 6005:6005 \
  -e ONEC_BUDDY_TOKEN=your_token \
  roctup/1c-buddy
```

**Конфиг OpenCode:**
```json
{
  "mcpServers": {
    "1c-buddy": {
      "url": "http://localhost:6005/mcp",
      "transport": "streamable-http"
    }
  }
}
```

---

### 5. 1c-mcp-metacode (ROCTUP) — пятый этап (офлайн)

Загрузка метаданных в Neo4j для графового анализа конфигурации без подключения к базе.

**Архитектура:**
```
IP_B (Ubuntu)
┌─────────────────────────────┐
│ 1c-mcp-metacode :6001       │
│    │                        │
│    ├── Neo4j :7474/:7687    │
│    └── MCP сервер           │
│         │                   │
│         ▼                   │
│   ./data/prj1/              │
│   ├── metadata/*.txt        │
│   └── code/*.xml            │
└─────────────────────────────┘
```

**Подготовка файлов на IP_A:**
1. Конфигурация → Отчет по конфигурации → текстовый файл (Вся конфигурация)
2. Конфигурация → Выгрузить конфигурацию в файлы (XML)

**Установка на IP_B:**
```yaml
# docker-compose.yml
version: '3'
services:
  neo4j:
    image: neo4j:latest
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/password
    volumes:
      - neo4j_data:/data

  metacode:
    image: roctup/1c-mcp-metacode
    ports:
      - "6001:6001"
    depends_on:
      - neo4j
    environment:
      - NEO4J_HOST=neo4j
      - NEO4J_PASSWORD=password
      - PROJECT_NAME=buh
    volumes:
      - ./data:/data

volumes:
  neo4j_data:
```

```bash
mkdir -p data/prj1/metadata data/prj1/code
# скопировать файлы с IP_A в data/prj1/
docker compose up -d
```

**Требования:**
- RAM: 4 ГБ Neo4j + 6 ГБ на базу
- Загрузка: ~30 мин для типовой Бухгалтерии

**Инструменты (3):**
- `search_metadata` — поиск по структурным свойствам и связям
- `search_metadata_by_description` — семантический поиск по описаниям
- `search_code` — поиск процедур/функций по описаниям

**Конфиг OpenCode:**
```json
{
  "mcpServers": {
    "1c-metacode": {
      "url": "http://localhost:6001/mcp",
      "transport": "streamable-http"
    }
  }
}
```

---

## Сводная таблица по режимам

| Режим | Сервер | Транспорт | Зависимости |
|-------|--------|-----------|-------------|
| **Online** (живая база) | mcp-1c | stdio+HTTP (через Go) | .cfe + Apache |
| **Online** (живая база) | 1c-mcp-toolkit | HTTP встроенный | .epf + ничего |
| **Online** (живая база) | vladimir-kharin/1c_mcp | HTTP+Python прокси | .cfe + Apache |
| **Online** | 1c-buddy | HTTP | Токен code.1c.ai |
| **Offline** (файлы) | 1c-mcp-metacode | HTTP | Neo4j + данные с IP_A |

---

## Подготовка с IP_A (Windows)

| Для сервера | Что сделать |
|-------------|-------------|
| **mcp-1c** | Установить .cfe, опубликовать `/hs/mcp-1c` |
| **1c-mcp-toolkit** | Открыть .epf, запустить встроенный сервер |
| **1c-mcp-metacode** | Выгрузить ОтчетПоКонфигурации.txt + XML выгрузку |
| **1c-buddy** | Получить токен code.1c.ai |

---

## Порядок развертывания (от малого)

| Этап | Сервер | Зачем | Время |
|------|--------|-------|-------|
| 1 | **mcp-1c** | 9 базовых tools, быстрый старт | 30 мин |
| 2 | **1c-mcp-toolkit** | execute_code, скриншоты, права доступа | 15 мин |
| 3 | **vladimir-kharin/1c_mcp** | Кастомные инструменты под свои задачи | по необходимости |
| 4 | **1c-buddy** | 1С:Напарник | 10 мин |
| 5 | **1c-mcp-metacode** | Офлайн-анализ, граф метаданных | 1 час с загрузкой |

---

## Итоговый конфиг OpenCode

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
    "1c-custom": {
      "url": "http://localhost:6004/mcp",
      "transport": "streamable-http"
    },
    "1c-buddy": {
      "url": "http://localhost:6005/mcp",
      "transport": "streamable-http"
    },
    "1c-metacode": {
      "url": "http://localhost:6001/mcp",
      "transport": "streamable-http"
    }
  }
}
```
