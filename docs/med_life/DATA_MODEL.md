# Модель данных Med Life

## 1. Структура проекта

```
11_med_life/
├── data/objects/<patient_id>/
│   ├── meta.json                 # мета пациента
│   └── entries/
│       ├── YYYY-MM-DD_001_examination.json
│       ├── YYYY-MM-DD_002_event.json
│       └── YYYY-MM-DD_003_lab.json
├── data/drug_reference/<drug_id>/
│   ├── meta.json                 # справочник препарата
│   └── analysis/
│       ├── notes.md
│       ├── clinical_efficacy.md
│       └── pharmacodynamics.md
├── data/price_tracker/<drug_id>.json  # цены из аптек
└── data/user/users/<patient_id>/
    ├── combined_analysis.md
    ├── combined_analysis.pdf
    ├── prescriptions_prices.md
    └── prescriptions_prices.pdf
```

## 2. Мета пациента (`meta.json`)

```json
{
  "object_id": "usr_8e498be",
  "name": "Симонов А.О.",
  "birth_year": 1984,
  "sex": "male",
  "blood_type": "A+",
  "allergies": ["пыльца", "пенициллин"],
  "height_cm": 178,
  "weight_kg": 82,
  "notes": "..."
}
```

## 3. Записи (`entries/*.json`)

### Общая структура

```json
{
  "entry_id": "uuid",
  "object_id": "usr_8e498be",
  "date": "2026-06-17",
  "time": "09:00",
  "specialist": {"role": "neurologist", "name": "..."},
  "domain": "examination",
  "data": {}
}
```

### Домены

| Домен | Описание | Ключевые поля `data` |
|---|---|---|
| `examination` | Осмотр | `specialty`, `diagnosis`, `complaints`, `objective_findings`, `prescriptions` |
| `lab` | Лаборатория | `tests[].{name, value, unit, ref_range}` |
| `medication` | Приём препарата | `drug_id`, `dose`, `route`, `regimen`, `adherence`, `effect` |
| `event` | Событие | `type`, `description`, `severity` |
| `subjective` | Самочувствие | `mood`, `anxiety`, `sleep`, `energy`, `appetite` (score 0–10) |
| `lifestyle` | Образ жизни | `sleep_hrs`, `activity_min`, `stress_level`, `diet_notes` |

### Пример `examination`

```json
{
  "data": {
    "specialty": "neurologist",
    "diagnosis": {"code": "", "text": "", "inferred": true},
    "complaints": "...",
    "objective_findings": "...",
    "prescriptions": [
      {
        "drug": "Триттико",
        "drug_id": "d_79ca8af0",
        "dose": {"value": 150, "unit": "мг", "text": "150 мг (1/3 таб)"},
        "route": "per_os",
        "regimen": {"time": "21:00", "frequency": "1×/сут", "duration": "3 месяца"}
      }
    ]
  }
}
```

### Пример `lab`

```json
{
  "data": {
    "tests": [
      {
        "name": "Пролактин",
        "value": 12.5,
        "unit": "нг/мл",
        "ref_range": {"low": 4.6, "high": 21.4}
      }
    ]
  }
}
```

## 4. Справочник препаратов

```json
{
  "drug_id": "d_79ca8af0",
  "name": "Триттико",
  "generic": "Тразодон",
  "atc_code": "N06AX05",
  "drug_class": "СИОЗС / антагонист 5-HT₂A",
  "pharmacodynamics": {
    "targets": [{"receptor": "5-HT₂A", "action": "антагонист", "affinity": "высокая"}],
    "mechanism_summary": "...",
    "clinical_effect": "Анксиолитический, антидепрессивный, седативный"
  },
  "pharmacokinetics": {
    "half_life": "5–9 часов",
    "metabolism": "CYP3A4",
    "bioavailability": "65%"
  },
  "indications": ["Большое депрессивное расстройство", "Тревожные расстройства"],
  "side_effects": ["Седация", "Головокружение"],
  "linked_prescriptions": [
    {"object_id": "usr_8e498be", "entry_id": "2026-06-17_001", "date": "2026-06-17"}
  ]
}
```

## 5. Трекер цен

```json
{
  "drug_id": "d_79ca8af0",
  "drug_name": "Триттико",
  "last_updated": "2026-06-18",
  "prices": {
    "src_001": {
      "source_name": "Мегаптека",
      "dose_form": "таблетки 150 мг №20",
      "price_group": {"min": 845, "median": 867, "max": 910},
      "url": "https://...",
      "availability": "in_stock",
      "last_checked": "2026-06-18"
    }
  },
  "history": [
    {"date": "2026-06-18", "entries": ["src_001", "src_002", "src_003"]}
  ]
}
```

## 6. Отчёты

- `combined_analysis.md` — объединённый аналитический отчёт.
- `combined_analysis.pdf` — PDF-версия.
- `prescriptions_prices.md` — таблица назначений с ценами.
- `prescriptions_prices.pdf` — PDF-версия.

## 7. Готовность к визуализации

✅ Даты, единицы измерения, референсные значения.  
✅ Связи препарат → цены.  
✅ Генерация сводных отчётов.  

⚠️ Мало повторяющихся измерений.  
⚠️ Нет явной привязки к жизненным системам — требуется маппинг.  
⚠️ Нет CSV-импорта.
