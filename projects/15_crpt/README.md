# 🧬 Проект 15 — CRPT (Честный Знак)

Клиентская библиотека и веб-интерфейс для работы с API ГИС МТ «Честный Знак» (ЦРПТ).

**Покрытие**: Mobile API, True API, API Национального каталога, ЭДО Лайт.

---

## 🚀 Установка

```bash
cd projects/15_crpt
pip install -e .
cp .env.example .env
```

## ⚡ Быстрый старт

```bash
# Проверка кода (без авторизации)
python -m cli.main check "01046300375902232121tZxhYmJdBh"

# Проверка участника по ИНН (без авторизации)
python -m cli.main participant 7701234567

# Информация об окружении
python -m cli.main env
```

## 🌐 Веб-интерфейс

```bash
python app.py
# → http://localhost:5015/crpt
```

Веб-UI содержит интерактивный API Explorer с категоризированными эндпоинтами, формами ввода параметров и отображением результатов.

---

## 🔐 Модель аутентификации

| # | Уровень | Что нужно | Где работает | Получение |
|---|---------|-----------|-------------|-----------|
| **0** | Без авторизации | Ничего | Mobile API, публичные True API | — |
| **1** | **API Key** | Ключ из ЛК ГИС МТ | **API Национального каталога** | ЛК → Нац. каталог → Профиль → «API KEY» |
| **2** | **Динамический токен** | omsConnection из СУЗ | True API, СУЗ | СУЗ → Устройства → Идентификатор соединения |
| **3** | КЭП (ГОСТ-подпись) | Сертификат УКЭП | True API, ЭДО Lite | Аккредитованный УЦ |

**Важно**: уровни 0-2 не требуют КЭП. API Key для Национального каталога — простейший способ начать.

### Как получить API Key (Национальный каталог)

1. Войти в ЛК ГИС МТ (продуктивный контур)
2. Меню → «Национальный каталог»
3. Правый верхний угол → ФИО → «Профиль»
4. Вкладка «Данные участника» → скопировать `API KEY`
5. Записать в `.env`: `NK_API_KEY=ваш_ключ`

### Как получить omsConnection (динамический токен)

1. Авторизоваться в ГИС МТ под ролью «Администратор»
2. «Главное окно» → «Управление заказами» (СУЗ)
3. Раздел «Устройства» → скопировать `OMS ID` и `Идентификатор соединения`
4. Записать в `.env`: `CRPT_OMS_CONNECTION=ваш_connection`

---

## 📡 Базовые URL

| Окружение | True API v3 | True API v4 | Национальный каталог | ЭДО Лайт |
|-----------|-------------|-------------|---------------------|----------|
| **Sandbox** | `markirovka.sandbox.crptech.ru/api/v3/true-api` | `.../api/v4/true-api` | `api.nk.sandbox.crptech.ru` | `edo-gismt.sandbox.crptech.ru` |
| **Production** | `markirovka.crpt.ru/api/v3/true-api` | `.../api/v4/true-api` | `апи.национальный-каталог.рф` | `edo-gismt.crpt.ru` |

### Mobile API
| Окружение | URL |
|-----------|-----|
| Все | `https://mobile.api.crpt.ru/mobile/check` |

---

## 📱 Mobile API — Level 0 (публичный, без авторизации)

**Клиент**: `MobileCheckClient` (`crpt.mobile_api`)

```python
from crpt.mobile_api import MobileCheckClient
client = MobileCheckClient()
```

| # | Метод | Эндпоинт | Параметры | Назначение |
|---|-------|----------|-----------|------------|
| 1 | `check_datamatrix(code)` | `GET /mobile/check?codeType=datamatrix` | `code` — DataMatrix | Проверка КМ |
| 2 | `check_ean13(code)` | `GET /mobile/check?codeType=ean13` | `code` — 13 цифр | Проверка штрихкода |
| 3 | `check_qr(code)` | `GET /mobile/check?codeType=qr` | `code` — QR-строка | Проверка QR-чека |
| 4 | `check_receipt(code)` | `POST /mobile/check` | `code` — receipt-строка | Проверка по реквизитам чека |
| 5 | `check(code, type)` | `GET /mobile/check?codeType=...` | универсальный | Любой тип кода |

### CLI

```bash
python -m cli.main check "01046300375902232121tZxhYmJdBh"             # DataMatrix
python -m cli.main check "4630037590223" -t ean13                      # EAN-13
python -m cli.main check "t=20231203T2319&s=261.80&fn=..." -t receipt  # Чек
```

---

## 🏢 True API — публичные методы (Level 0)

**Клиент**: `TrueApiClient` (`crpt.true_api`)

```python
from crpt.true_api import TrueApiClient
client = TrueApiClient()
```

| # | Метод | Эндпоинт | Параметры | Назначение |
|---|-------|----------|-----------|------------|
| 1 | `get_participants(inn)` | `GET /participants?inns={inn}` | `inn` — ИНН | Статус, товарные группы, роли УОТ |
| 2 | `get_mods_list(inns, ...)` | `GET /mods/list` | `inns`, `product_groups`, `limit`, `page` | Список мест деятельности |
| 3 | `get_mods_info(pg, inn, kpp)` | `POST /mods/info` | `pg` — товарная группа, `inn`, `kpp` | Статус блокировки МОД (пиво) |
| 4 | `cises_public_info(cises)` | `POST /cises/public-info` | `cises` — список КИ | Общедоступная информация о КИ |

### CLI

```bash
python -m cli.main participant 7701234567           # Проверка УОТ
python -m cli.main mods --inn 7701234567            # Список МОД
python -m cli.main cises "010463..." --public       # Публичная инфо о КИ
```

---

## 🔑 True API — аутентификация (Level 2)

### Получение динамического токена

```python
from crpt.auth import DynamicTokenAuth
from crpt.true_api import TrueApiClient

# signer — функция подписи данных (base64)
def my_signer(data: str) -> str:
    # Здесь: подпись любым сертификатом, возврат base64
    ...

auth = DynamicTokenAuth(
    oms_connection="ваш-connection-из-СУЗ",
    signer=my_signer,
)

client = TrueApiClient(auth=auth)
# auth.authenticate() — получить токен
```

Без `signer` работает только для Preview-сред (если API допускает неподписанные данные).

### Использование готового токена

```python
from crpt.auth import TokenAuth
from crpt.true_api import TrueApiClient

client = TrueApiClient(auth=TokenAuth("ваш-токен"))
```

### Методы аутентификации

| # | Метод | Эндпоинт | Назначение |
|---|-------|----------|------------|
| 1 | `auth_key()` | `GET /auth/key` | Получить uuid + data для подписи |
| 2 | `auth_sign_in(uuid, data, inn)` | `POST /auth/simpleSignIn` | Получить токен сессии |

---

## 📦 True API — коды идентификации (Level 2+)

**Требуется**: токен в заголовке `Authorization: Bearer <token>`

| # | Метод | Эндпоинт | Назначение |
|---|-------|----------|------------|
| 1 | `cises_short_list(cises)` | `POST /cises/short/list` | Краткая информация (статус, владелец) |
| 2 | `cises_info(cises)` | `POST /cises/info` | Подробная информация |
| 3 | `cises_history(cises)` | `POST /cises/history` | История движения КИ |

### CLI

```bash
export CRPT_TOKEN="ваш-токен"
python -m cli.main cises "010463...abc,010463...def"          # Инфо о КИ
python -m cli.main cises "010463...abc" --history             # История движения
```

---

## 📦 True API — товары / продукты (Level 2+)

| # | Метод | Эндпоинт | Назначение |
|---|-------|----------|------------|
| 1 | `product_info(gtin)` | `GET /product/info?gtin={gtin}` | Информация о товаре |
| 2 | `products_gtin_list(inn, pg)` | `GET /products/gtin/list` | Список GTIN товаров УОТ |
| 3 | `product_group_by_gtin(gtin)` | `GET /product/group?gtin={gtin}` | Код товарной группы по GTIN |

```bash
python -m cli.main product 04630037590223
```

---

## 📄 True API — документы (Level 2+)

| # | Метод | Эндпоинт | Назначение |
|---|-------|----------|------------|
| 1 | `documents_list(...)` | `GET /documents/list` | Список загруженных документов |
| 2 | `document_info(doc_id)` | `GET /doc/{id}/info` | Содержимое документа |
| 3 | `document_cises(doc_id)` | `GET /doc/{id}/cises` | Список КИ по документу |
| 4 | `document_status(doc_id)` | `GET /document/status` | Статус обработки документа |
| 5 | `document_validate(type, doc)` | `POST /document/validate` | Предпроверка УПД |

```bash
python -m cli.main docs --limit 50                   # Список документов
python -m cli.main docs --id "doc-123"               # Содержимое
python -m cli.main docs --id "doc-123" --cises       # КИ документа
```

---

## 📊 True API — чеки ККТ (Level 2+)

| # | Метод | Эндпоинт | Назначение |
|---|-------|----------|------------|
| 1 | `checks_list(...)` | `GET /checks/list` | Список чеков ККТ |
| 2 | `check_body(check_id)` | `GET /checks/{id}/body` | Содержимое чека |

---

## 📋 True API — квитанции (Level 2+)

| # | Метод | Эндпоинт | Назначение |
|---|-------|----------|------------|
| 1 | `receipts_document(doc_id)` | `GET /receipts/{documentId}` | Квитанция по ID документа |
| 2 | `receipts_check(check_id)` | `GET /receipts/check/{checkId}` | Квитанция по ID чека |

---

## 📊 True API — выгрузки данных / Диспенсер (Level 2+)

| # | Метод | Эндпоинт | Назначение |
|---|-------|----------|------------|
| 1 | `dispenser_tasks_create(type, params)` | `POST /dispenser/tasks` | Создать задание на выгрузку |
| 2 | `dispenser_task_status(task_id)` | `GET /dispenser/tasks/{id}` | Статус задания |
| 3 | `dispenser_results(task_id)` | `GET /dispenser/results/{id}` | Результаты выгрузки |
| 4 | `dispenser_download(task_id)` | `GET /dispenser/results/{id}/file` | Скачать ZIP/CSV |

---

## 🔗 True API — ЭДО Лайт (через True API, Level 2+)

| # | Метод | Эндпоинт | Назначение |
|---|-------|----------|------------|
| 1 | `edo_abonent_id()` | `GET /edo/abonent` | ID абонента в ЭДО Лайт |
| 2 | `edo_document_zip(doc_id)` | `GET /edo/document/{id}/zip` | ZIP-архив документооборота |

---

## 🏪 API Национального каталога (Level 1 — API Key)

**Клиент**: `NkApiClient` (`crpt.nk_api`)

```python
from crpt.nk_api import NkApiClient
client = NkApiClient(api_key="ваш-api-key")
```

**Базовый URL**: `https://api.nk.sandbox.crptech.ru` (sandbox) / `https://апи.национальный-каталог.рф` (prod)

### Карточки товаров

| # | Метод | Эндпоинт | Назначение |
|---|-------|----------|------------|
| 1 | `get_product(gtin)` | `GET /v3/feed-product?gtin={gtin}` | Полная карточка своего товара |
| 2 | `get_product_by_id(good_id)` | `GET /v3/feed-product?good_id={id}` | Карточка по ID |
| 3 | `get_products(gtins)` | `GET /v3/feed-product?gtins=...` | Несколько карточек (до 25) |
| 4 | `get_public_product(gtin)` | `GET /v3/product?gtin={gtin}` | Публичная карточка |
| 5 | `get_short_product(gtin)` | `GET /v3/short-product?gtin={gtin}` | Краткая карточка |
| 6 | `get_own_products(limit, page)` | `GET /v3/feed-products` | Список своих товаров |
| 7 | `check_product_changes(gtins)` | `GET /v3/product-changes` | Проверка изменений |
| 8 | `check_markable(gtins)` | `GET /v3/product/markable` | Принадлежность к маркировке |

### Создание и редактирование

| # | Метод | Эндпоинт | Назначение |
|---|-------|----------|------------|
| 9 | `create_or_update_product(data)` | `POST /v3/feed` | Создать/обновить карточку |
| 10 | `get_feed_status(feed_id)` | `GET /v3/feed-status` | Статус обработки пакета |
| 11 | `generate_gtin(count)` | `POST /v3/generate-gtin` | Сгенерировать GTIN |
| 12 | `resize_photo(url, w, h)` | `POST /v3/resize-photo` | Изменить размер фото |
| 13 | `send_to_moderation(gtin)` | `POST /v3/moderation` | Отправить на модерацию |

### Справочники

| # | Метод | Эндпоинт | Назначение |
|---|-------|----------|------------|
| 14 | `get_categories()` | `GET /v3/dict/categories` | Дерево категорий товаров |
| 15 | `get_attributes(cat_id)` | `GET /v3/dict/attributes` | Атрибуты категории |
| 16 | `get_countries()` | `GET /v3/dict/countries` | Справочник стран |
| 17 | `get_brands(name, ...)` | `GET /v3/dict/brands` | Справочник брендов |

### Разрешительные документы

| # | Метод | Эндпоинт | Назначение |
|---|-------|----------|------------|
| 18 | `check_permit_doc(gtin, num, date)` | `GET /v3/permit-doc` | Проверка сертификата/декларации |

### Субаккаунты

| # | Метод | Эндпоинт | Назначение |
|---|-------|----------|------------|
| 19 | `get_subaccounts()` | `GET /v3/sub-accounts` | Список субаккаунтов |
| 20 | `get_accounts_codes()` | `GET /v3/accounts-codes` | Доступы субаккаунтов |

### CLI

```bash
export NK_API_KEY="ваш-ключ"
python -m cli.main nk --gtin "04630037590223"      # Карточка товара
python -m cli.main nk --categories                  # Дерево категорий
python -m cli.main nk --brands                      # Справочник брендов
python -m cli.main nk --countries                   # Справочник стран
```

---

## 🏗 Структура проекта

```
projects/15_crpt/
├── app.py                     # Flask entry point (порт 5015)
├── pyproject.toml             # Зависимости
├── .env.example               # Шаблон конфигурации
├── crpt/                      # Python-библиотека
│   ├── __init__.py
│   ├── client.py              # HttpClient (urllib, без внешних deps)
│   ├── auth.py                # AuthProvider, ApiKeyAuth, TokenAuth, DynamicTokenAuth, KEPAuth
│   ├── models.py              # Pydantic модели (Participant, CiseInfo, ProductInfo, ...)
│   ├── types.py               # ApiEnv, BASE_URLS, PRODUCT_GROUPS
│   ├── utils.py               # Парсинг DataMatrix, GS1, определение типа кода
│   ├── mobile_api/
│   │   └── check.py           # MobileCheckClient — публичная проверка
│   ├── true_api/
│   │   └── ...                # TrueApiClient — 30+ методов ГИС МТ
│   ├── nk_api/
│   │   └── ...                # NkApiClient — 20 методов Нац. каталога
│   └── web/
│       ├── routes.py          # Flask Blueprint + дерево эндпоинтов
│       └── templates/
│           └── explorer.html  # Веб-интерфейс API Explorer
├── cli/
│   └── main.py                # CLI: crpt check|participant|product|...
├── tests/
│   ├── test_utils.py          # Тесты парсинга DataMatrix
│   ├── test_models.py         # Тесты Pydantic моделей
│   ├── test_types_auth.py     # Тесты типов и аутентификации
│   └── test_mobile_api.py     # Тесты Mobile API (с моками)
└── openapi/
    ├── true-api.yaml          # OpenAPI-спека True API (из crpt-openapi)
    └── edo-light.yaml         # OpenAPI-спека ЭДО Лайт
```

---

## 🧪 Тесты

```bash
python -m pytest tests/ -v
```

---

## 📚 Источники

| Ресурс | URL |
|--------|-----|
| Официальная документация разработчиков | `https://docs.crpt.ru/gismt/Раздел_для_разработчиков/` |
| True API документация | `https://docs.crpt.ru/gismt/True_API/` |
| API Национального каталога | `https://docs.crpt.ru/gismt/API_НК/` |
| Инструкция по динамическому токену | `https://docs.crpt.ru/gismt/Инструкция_по_получению_динамического_клиентского_токена/` |
| Инструкция по работе с API | `https://docs.crpt.ru/gismt/Инструкция_по_работе_с_API/` |
| OpenAPI-спецификация (неофиц.) | `https://github.com/pravets/crpt-openapi` |
| Статья Infostart | `https://infostart.ru/1c/articles/2740983/` |
