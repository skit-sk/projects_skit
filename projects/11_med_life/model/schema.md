# Schema — Модель данных med_life

## 1. Базовая структура entry

Каждая запись — JSON-файл в `data/objects/<object_id>/entries/YYYY-MM-DD_<seq>_<domain>.json`.

### Обязательные поля

| Поле | Тип | Формат | Описание |
|------|-----|--------|----------|
| `entry_id` | string | `UUID v4` | Уникальный идентификатор записи |
| `object_id` | string | `usr_[0-9a-f]{7}` | Идентификатор объекта |
| `date` | string | `YYYY-MM-DD` | Дата записи |
| `specialist` | object | `{ role, name }` | Кто внёс запись |
| `domain` | string | enum | Домен данных (см. ниже) |
| `data` | object | зависит от domain | Содержимое записи |

### Опциональные поля

| Поле | Тип | Описание |
|------|-----|----------|
| `time` | string `HH:MM` | Время записи |
| `timezone` | string `+/-HH:MM` | Часовой пояс |
| `attachments` | string[] | Список файлов |
| `notes` | string | Произвольный комментарий |
| `source` | enum | `manual` / `import` / `parse` |

---

## 2. Шкала scale

Оценка по двум осям: числовой score (0–10) и вербальная метка.

```
very_low │  low  │ medium │ high │ very_high
   0       1  2    3  4     5  6    7  8     9  10
```

### Маппинг score → label

| Score | label |
|-------|-------|
| 0–2 | `very_low` |
| 3–4 | `low` |
| 5–6 | `medium` |
| 7–8 | `high` |
| 9–10 | `very_high` |

Можно указать только score — label вычисляется автоматически при обработке.
Можно указать оба поля — для переопределения.

---

## 3. Специалист specialist

```json
{
  "role": "psychiatrist",
  "name": "Иванов И.И."
}
```

**Роли** (открытый список, добавляются по мере данных):

| Роль | Описание |
|------|----------|
| `self` | Самостоятельная запись объекта |
| `patient` | Запись от лица пациента |
| `psychiatrist` | Врач-психиатр |
| `neurologist` | Невролог |
| `endocrinologist` | Эндокринолог |
| `therapist` | Терапевт |
| `psychologist` | Психолог |
| `narcologist` | Нарколог |
| `ophthalmologist` | Офтальмолог |
| `sexologist` | Сексолог |
| `nurse` | Медсестра / медбрат |
| `other` | Другой специалист |

---

## 4. Домены (6 шт)

### 4.1 subjective — Субъективное состояние

Описание самочувствия, эмоций, влечения, сна.

```json
{
  "mood":          { "score": 5, "label": "medium" },
  "anxiety":       { "score": 7, "label": "high" },
  "libido":        { "score": 8, "label": "high" },
  "sleep_hrs":     5.5,
  "sleep_quality": { "score": 3, "label": "low" },
  "appetite":      { "score": 6, "label": "medium" },
  "energy":        { "score": 3, "label": "low" },
  "notes":         "тревога утром, либидо повышено"
}
```

### 4.2 medication — Приём препарата

Фиксация приёма лекарства, дозировки, эффекта и побочек.

```json
{
  "drug":          "Рисперидон",
  "dose_mg":       2,
  "dose_text":     "1 таблетка 2 мг",
  "frequency":     "1×/сут",
  "route":         "per_os",
  "effect_score":  { "score": 6, "label": "medium" },
  "side_effects":  [ "сонливость", "сухость во рту" ],
  "adherence":     100
}
```

### 4.3 examination — Осмотр специалиста

Приём врача: диагноз, жалобы, объективно, назначения.

```json
{
  "specialty": "psychiatrist",
  "diagnosis": {
    "code": "6A71",
    "text": "Рекуррентное депрессивное расстройство",
    "inferred": false
  },
  "complaints": "Сниженное настроение, тревога, нарушение сна",
  "objective_findings": "Сознание ясное, критика сохранена, тревожен",
  "prescriptions": [
    {
      "drug": "Пароксетин",
      "dose": { "value": 20, "unit": "мг", "text": "20 мг" },
      "regimen": { "time": "утро", "frequency": "1×/сут", "duration": "" }
    },
    {
      "drug": "Кветиапин",
      "dose": { "value": 25, "unit": "мг", "text": "25 мг" },
      "regimen": { "time": "на ночь", "frequency": "1×/сут", "duration": "" }
    }
  ]
}
```

### 4.4 lab — Лабораторные данные

Анализы: кровь, гормоны, биохимия.

```json
{
  "test":           "Пролактин",
  "value":          850,
  "unit":           "мМЕ/л",
  "ref_range":      { "low": 86, "high": 324 },
  "lab_name":       "Гемотест",
  "date_collected": "2026-06-15"
}
```

### 4.5 event — Событие

Ключевые медицинские события.

```json
{
  "event_type":  "hospitalization",
  "description": "Плановая госпитализация в ПНД №14 для коррекции терапии",
  "severity":    { "score": 6, "label": "medium" }
}
```

Типы событий: `hospitalization`, `regimen_change`, `crisis`, `consultation`, `procedure`, `other`.

### 4.6 lifestyle — Образ жизни

Режим дня, питание, активность, стресс.

```json
{
  "sleep_schedule": {
    "bedtime":  "23:30",
    "wake_time": "07:00",
    "notes":    "просыпался 2 раза"
  },
  "meals": [
    { "time": "08:00", "description": "завтрак: каша, чай" },
    { "time": "13:00", "description": "обед: суп, курица" },
    { "time": "19:00", "description": "ужин: рыба, овощи" }
  ],
  "physical_activity": {
    "type":         "прогулка",
    "duration_min": 30,
    "intensity":    { "score": 3, "label": "low" }
  },
  "stress_level": { "score": 7, "label": "high" }
}
```

### 4.7 drug_reference — Справочная карточка препарата

Хранится в `data/drug_reference/d_{drug_id}/meta.json`. Описывает препарат, механизм действия, фармакокинетику, эффекты.

```json
{
  "drug_id": "d_79ca8af0",
  "name": "Триттико",
  "generic": "Тразодон",
  "generic_alt": "",
  "atc_code": "N06AX05",
  "drug_class": "СИОЗС / антагонист 5-HT₂A",
  "type": "medication",
  "description": "Атипичный антидепрессант, антагонист серотониновых рецепторов",
  "pharmacodynamics": {
    "targets": [
      { "receptor": "5-HT₂A", "action": "антагонист", "affinity": "высокая" }
    ],
    "mechanism_summary": "Блокирует 5-HT₂A → ↑ норадреналин и дофамин в ПФК",
    "clinical_effect": "Анксиолитический, антидепрессивный"
  },
  "pharmacokinetics": {
    "half_life": "5–9 часов",
    "metabolism": "CYP3A4",
    "bioavailability": "65%"
  },
  "indications": ["БДР", "Тревожные расстройства"],
  "contraindications": [],
  "side_effects": ["Седация", "Головокружение"],
  "linked_prescriptions": [],
  "needs_clarification": false,
  "created": "2026-06-18",
  "updated": "2026-06-18"
}
```

### 4.8 price_entry — Цены и места приобретения

Хранится в `data/price_tracker/d_{drug_id}.json` — **один файл на препарат**, внутри все источники с ценами.

```json
{
  "drug_id": "d_79ca8af0",
  "drug_name": "Триттико",
  "last_updated": "2026-06-18",
  "prices": {
    "src_001": {
      "source_name": "Мегаптека",
      "dose_form": "таблетки 150 мг №20",
      "price_group": { "min": 845, "median": 867, "max": 910 },
      "url": "https://megapteka.ru/...",
      "availability": "in_stock",
      "last_checked": "2026-06-18"
    }
  },
  "history": [
    { "date": "2026-06-18", "entries": ["src_001"] }
  ]
}
```

Парсер цен (`scripts/price_parser/`) ищет препарат на 3–5 ресурсах и обновляет этот файл.

### 4.9 Связь между объектами

```
prescriptions[].drug_id ──────→ drug_reference/d_{id}/meta.json
                                        │
                                        ▼
                              price_tracker/d_{id}.json
```

---

## 5. Правила именования entry-файлов

```
YYYY-MM-DD_<seq>_<domain>.json
```

Где:
- `seq` — трёхзначный номер с ведущими нулями (001, 002, …)
- `domain` — один из 6 доменов

Примеры:
- `2026-06-18_001_subjective.json`
- `2026-06-18_002_medication.json`
- `2026-06-19_001_lab.json`

---

## 6. Генерация entry_id

`entry_id` = UUID v4 (например `a1b2c3d4-e5f6-7890-abcd-ef1234567890`).

Генерируется при создании записи.

---

## 7. Генерация object_id

Формат: `usr_` + первые 7 символов hex от UUID4 (нижний регистр).

Пример: `usr_a1b2c3d`
