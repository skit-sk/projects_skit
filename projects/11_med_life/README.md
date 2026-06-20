# 11_med_life — Медицинская жизнедеятельность объекта

Система ведения хронологических записей медицинской жизнедеятельности для субъекта (объекта наблюдения).

## Концепция

Каждая запись (entry) — это JSON-файл с фиксированной структурой, описывающий одно событие/состояние/факт в привязке к:
- **объекту** (object_id: `usr_` + 7 hex)
- **дате** (YYYY-MM-DD)
- **специалисту** (кто внёс)

Все записи одного объекта хранятся хронологически в `data/objects/<object_id>/entries/`.

## Директории

```
projects/11_med_life/
├── README.md                  # этот файл
├── model/
│   ├── schema.json            # JSON Schema (Draft 2020-12)
│   └── schema.md              # человеческое описание схемы
├── templates/
│   ├── entry_template.json
│   ├── object_meta_template.json
│   ├── drug_meta_template.json
│   └── price_drug_file_template.json
├── data/
│   ├── objects/usr_*/         # объекты наблюдения
│   ├── drug_reference/        # справочник препаратов
│   │   ├── index.json
│   │   ├── d_XXXXXXXX/        # drug_id
│   │   │   ├── meta.json      # карточка препарата
│   │   │   └── analysis/      # глубокий разбор (3 .md файла)
│   │   └── ...
│   └── price_tracker/         # цены и места приобретения
│       ├── sources.json       # реестр источников (макс 10)
│       ├── index.json
│       └── d_XXXXXXXX.json    # один файл на препарат, внутри все цены
└── scripts/
    └── price_parser/          # парсер цен с маркетплейсов
        ├── main.py
        ├── config.py
        ├── models.py
        ├── base.py
        └── parsers/
            ├── megapteka.py
            ├── eapteka.py
            └── apteka_ru.py
```

### Схема связей

```
prescriptions[].drug_id ──────→ drug_reference/d_{id}/meta.json
                                       │
                                       ▼
                             price_tracker/d_{id}.json
```

## Домены данных

| Домен | Описание |
|-------|----------|
| `subjective` | Субъективное состояние: настроение, тревога, либидо, сон, аппетит, энергия |
| `medication` | Приём препарата: название, доза, эффект, побочные эффекты, adherence |
| `examination` | Осмотр специалиста: диагноз, жалобы, назначения |
| `drug_reference` | Справочная карточка препарата |
| `price_entry` | Цены и места приобретения |
| `lab` | Лабораторные анализы: показатель, значение, референс |
| `event` | События: госпитализация, смена терапии, кризис |
| `lifestyle` | Образ жизни: сон, питание, физическая активность, стресс |

## Правила

### object_id

Формат: `usr_` + 7 символов hex (первые 7 символа от UUID4, нижний регистр).

Генерация: `python3 -c "import uuid; print('usr_' + uuid.uuid4().hex[:7])"`

### Именование entry-файлов

```
YYYY-MM-DD_<seq>_<domain>.json
```

- `seq` — 3 цифры с ведущими нулями (001, 002, …)
- `domain` — один из 6 доменов латиницей

### Шкала (scale)

Числовой score 0–10 + вербальная метка (very_low / low / medium / high / very_high).

Маппинг:

| Score | label |
|-------|-------|
| 0–2 | very_low |
| 3–4 | low |
| 5–6 | medium |
| 7–8 | high |
| 9–10 | very_high |

### Нормализация frequency

Повторения всегда через `/сут`, `/нед`, `/мес`. Варианты `день`, `ночь` не используются.

| Было | Стало |
|------|-------|
| `"2×/день"` | `"2×/сут"` |

### Route (способ приёма)

Enum: `per_os`, `sublingual`, `im`, `iv`, `topical`, `rectal`, `inhalation`, `other`

Указывается в `prescriptions[].route`.

### Специалист

Запись содержит объект `{ "role": "...", "name": "..." }`. Роль из открытого списка:
`self`, `patient`, `ophthalmologist`, `psychiatrist`, `neurologist`, `endocrinologist`,
`therapist`, `psychologist`, `narcologist`, `sexologist`, `nurse`, `other`.

### AI Inference

Если `diagnosis.code` или `diagnosis.text` не указаны:

```
1. AI анализирует данные: complaints, objective_findings, prescriptions
2. Формирует предположительный диагноз (ICD-11 + текст)
3. Записывает его с полем "inferred": true
```

Пример:
```json
"diagnosis": {
  "code": "H52.0",
  "text": "Гиперметропия / Пресбиопия (предположительно)",
  "inferred": true
}
```

Поле `inferred` отличает AI-гипотезу от диагноза, поставленного врачом.

## Валидация

JSON Schema (`model/schema.json`) проверяет:
- базовую структуру entry (обязательные поля, форматы)
- дискриминацию по domain (oneOf — каждый домен имеет свою структуру data)
- типы данных, диапазоны, enum-значения

## Тестовый объект

`data/objects/usr_a1b2c3d/` — тестовый объект для отладки и разработки.

## Дорожная карта

- [x] Структура директорий
- [x] JSON Schema (все 6 доменов)
- [x] Шаблоны entry и meta
- [x] Тестовый объект usr_a1b2c3d
- [x] Первый ввод данных (examination + event, usr_8e498be)
- [x] AI Inference: авто-заполнение diagnosis
- [x] Route (способ приёма) в prescriptions
- [x] Drug Reference — 7 карточек + 21 analysis-файл
- [x] Price Tracker — 7 файлов с ценами + sources.json
- [x] Price Parser — модуль на 3 ресурса (megapteka, eapteka, apteka.ru)
- [ ] Первый ввод subjective
- [ ] Скрипты валидации и генерации
- [ ] Парсер текстовых данных
- [ ] Подключение ICD-11 (при >50 записей)
