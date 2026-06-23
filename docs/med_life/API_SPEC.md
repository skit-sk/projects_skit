# API спецификация Med Life Atlas

## Базовый путь

`/med-life/`

## HTML endpoints

| Метод | Путь | Описание |
|---|---|---|
| GET | `/med-life/` | Список пациентов |
| GET | `/med-life/atlas/<object_id>` | Атлас систем пациента |
| GET | `/med-life/passport/<object_id>` | Паспорт состояния |
| GET | `/med-life/system/<object_id>/<system_key>` | Данные по одной системе |
| GET | `/med-life/timeline/<object_id>` | Таймлайн |

## JSON API

| Метод | Путь | Описание |
|---|---|---|
| GET | `/med-life/api/objects` | Список пациентов |
| GET | `/med-life/api/<object_id>/entries` | Все записи пациента |
| GET | `/med-life/api/<object_id>/system/<system_key>` | Записи по системе |
| GET | `/med-life/api/<object_id>/labs` | Лабораторные данные |
| GET | `/med-life/api/<object_id>/drugs` | Препараты с ценами |
| GET | `/med-life/api/<object_id>/radar` | Оценки систем для радара |
| GET | `/med-life/api/<object_id>/timeline` | Хронология |

### Ответ `/med-life/api/objects`

```json
[
  {
    "object_id": "usr_8e498be",
    "name": "Симонов А.О.",
    "birth_year": 1984,
    "sex": "male"
  }
]
```

### Ответ `/med-life/api/<object_id>/radar`

```json
{
  "object_id": "usr_8e498be",
  "systems": [
    {"name": "cardiovascular", "score": 5.0, "label": "medium"},
    {"name": "respiratory", "score": 7.0, "label": "good"},
    {"name": "nervous", "score": 6.5, "label": "medium"},
    {"name": "endocrine", "score": 5.5, "label": "medium"},
    {"name": "musculoskeletal", "score": 7.2, "label": "good"},
    {"name": "digestive", "score": 3.0, "label": "low"},
    {"name": "urinary", "score": 4.0, "label": "low"},
    {"name": "immune", "score": 4.0, "label": "low"},
    {"name": "reproductive", "score": 5.0, "label": "medium"},
    {"name": "sensory", "score": 2.0, "label": "very_low"},
    {"name": "psychological", "score": 6.0, "label": "medium"}
  ]
}
```

### Ответ `/med-life/api/<object_id>/drugs`

```json
[
  {
    "drug": "Триттико",
    "drug_id": "d_79ca8af0",
    "dose": {"value": 150, "unit": "мг"},
    "regimen": {"time": "21:00", "frequency": "1×/сут"},
    "ref": {"generic": "Тразодон", "atc_code": "N06AX05"},
    "prices": {
      "prices": {
        "src_001": {"price_group": {"min": 845, "median": 867, "max": 910}}
      }
    }
  }
]
```

## Системные ключи

| Ключ | Система |
|---|---|
| `cardiovascular` | Сердечно-сосудистая |
| `respiratory` | Дыхательная |
| `nervous` | Нервная |
| `endocrine` | Эндокринная |
| `musculoskeletal` | Опорно-двигательная |
| `digestive` | Пищеварительная |
| `urinary` | Мочевыделительная |
| `immune` | Иммунная / аллергическая |
| `reproductive` | Репродуктивная |
| `sensory` | Сенсорная |
| `psychological` | Психоэмоциональная |

## Коды ошибок

| Код | Значение |
|---|---|
| 404 | Пациент или система не найдены |
| 500 | Ошибка загрузки/обработки данных |
