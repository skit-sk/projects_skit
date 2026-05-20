# Project 08 — OFD API Integration

## Цель
Получение фискальных данных (чеки, смены, ККТ) от российских ОФД-провайдеров через REST API.

## Структура

```
projects/08_ofd_api/
├── README.md              ← этот файл
├── docs/
│   ├── providers.md       ← анализ провайдеров
│   └── model.md           ← модель данных JSON
├── bot_ofd/
│   ├── ofd_config.py      ← загрузка/сохранение ofd_config.json
│   └── ofd_client.py      ← базовый HTTP клиент
└── tests/
    └── test_config.py
```

## Провайдеры

| Провайдер | Сайт | API | Аутентификация |
|-----------|------|-----|---------------|
| Первый ОФД | 1-ofd.ru | REST JSON | API key |
| Такском | taxcom.ru | REST JSON | login+pass |
| Яндекс.ОФД | ofd.yandex.ru | REST JSON | OAuth2 |
| Эвотор | evotor.ru | REST JSON | Bearer token |

## Модель хранения

`TG_ALL/tg_ofd/ofd_config.json` — организации, ККТ, провайдеры.

Подробнее: `docs/model.md`
