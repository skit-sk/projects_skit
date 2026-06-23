# 11 — Med Life

**ID:** 11
**Расположение:** `projects/11_med_life/`
**Тип:** atlas (интегрирован в 01 как blueprint)
**Порт:** 5000 (внутри 01)
**Запуск:** `./scripts/flask.sh start 01`

## Назначение

Атлас человека и паспорт состояния пациента. Медицинская визуализация и таймлайн показателей.

## Стек

- Flask blueprint
- SVG / HTML / CSS
- JSON-данные пациентов

## Архитектура

```
projects/11_med_life/
├── README.md
├── data/                  # Данные пациентов
├── model/                 # Модели/схемы
├── scripts/               # Утилиты
└── templates/             # Шаблоны атласа

projects/01_fundament_rf/routes/med_life.py    # Blueprint в хабе
projects/01_fundament_rf/services/med_life_loader.py
projects/01_fundament_rf/templates/med_life/
```

## Entry points

- Атлас систем: `/med-life/atlas/<user_id>`
- Паспорт состояния: `/med-life/passport/<user_id>`
- Таймлайн: `/med-life/timeline/<user_id>`

## Зависимости

| Тип | Зависимость | Описание |
|---|---|---|
| Внутренняя | `projects/01_fundament_rf/app.py` | Регистрация blueprint |

## Связи с другими проектами

| Проект | Тип связи | Детали |
|---|---|---|
| 01 Fundament RF | blueprint | `/med-life/` |

## Запуск

```bash
./scripts/flask.sh start 01
```

## Связанные KB

- [URL/Port карта](../4-guides/url-port-map.md)
