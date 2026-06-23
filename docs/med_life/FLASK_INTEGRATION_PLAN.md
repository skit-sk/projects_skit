# План интеграции Med Life в Flask

**Цель:** сделать медицинские данные `11_med_life` доступными через веб-интерфейс `01_fundament_rf` в виде «Атласа человека» и «паспорта состояния пациента».

## 1. Подход

Создать Blueprint `med_life` внутри `01_fundament_rf`, который читает JSON-данные из `projects/11_med_life/data/`. Это соответствует существующей архитектуре (`viz_lab`, `ai_models`, `ofd_api`).

## 2. Файловая структура

```
projects/01_fundament_rf/
├── routes/
│   └── med_life.py              # Blueprint + endpoints
├── services/
│   └── med_life_loader.py       # загрузка и агрегация данных
├── templates/
│   └── med_life/
│       ├── index.html           # список пациентов
│       ├── atlas.html           # Атлас систем
│       ├── passport.html        # Паспорт состояния
│       ├── system_view.html     # одна система
│       ├── timeline.html        # таймлайн
│       └── drug_card.html       # карточка препарата
└── static/
    └── med_life/
        ├── css/
        │   └── atlas.css
        ├── js/
        │   ├── atlas.js
        │   ├── radar.js
        │   └── heatmap.js
        └── icons/
            ├── system_nervous.svg
            ├── system_cardiovascular.svg
            ├── system_respiratory.svg
            ├── system_endocrine.svg
            ├── system_musculoskeletal.svg
            ├── system_digestive.svg
            ├── system_urinary.svg
            ├── system_immune.svg
            ├── system_reproductive.svg
            ├── system_sensory.svg
            ├── system_psychological.svg
            └── system_overview.svg
```

## 3. Loader

`services/med_life_loader.py`:

```python
from pathlib import Path
import json

MED_LIFE_ROOT = Path('/home/user_aioc/workspace/projects/11_med_life')

def list_objects():
    meta_dir = MED_LIFE_ROOT / 'data' / 'objects'
    return [
        {'object_id': p.name, **json.loads((p / 'meta.json').read_text())}
        for p in meta_dir.iterdir() if (p / 'meta.json').exists()
    ]

def load_object(object_id: str):
    obj_dir = MED_LIFE_ROOT / 'data' / 'objects' / object_id
    meta = json.loads((obj_dir / 'meta.json').read_text())
    entries = [
        json.loads(entry_path.read_text())
        for entry_path in sorted((obj_dir / 'entries').glob('*.json'))
    ]
    return {'meta': meta, 'entries': entries}

def load_drug(drug_id: str):
    path = MED_LIFE_ROOT / 'data' / 'drug_reference' / drug_id / 'meta.json'
    return json.loads(path.read_text()) if path.exists() else None

def load_prices(drug_id: str):
    path = MED_LIFE_ROOT / 'data' / 'price_tracker' / f'{drug_id}.json'
    return json.loads(path.read_text()) if path.exists() else None
```

## 4. Blueprint

```python
from flask import Blueprint, render_template, jsonify, abort
from services.med_life_loader import list_objects, load_object, load_drug, load_prices

bp = Blueprint('med_life', __name__, url_prefix='/med-life')

@bp.route('/')
def index():
    return render_template('med_life/index.html', objects=list_objects())

@bp.route('/atlas/<object_id>')
def atlas(object_id):
    data = load_object(object_id)
    if not data:
        abort(404)
    return render_template('med_life/atlas.html', object_id=object_id, meta=data['meta'])

@bp.route('/passport/<object_id>')
def passport(object_id):
    data = load_object(object_id)
    if not data:
        abort(404)
    return render_template('med_life/passport.html', object_id=object_id, data=data)

@bp.route('/system/<object_id>/<system_key>')
def system_view(object_id, system_key):
    data = load_object(object_id)
    if not data:
        abort(404)
    return render_template('med_life/system_view.html',
                           object_id=object_id,
                           system_key=system_key,
                           data=data)

@bp.route('/timeline/<object_id>')
def timeline(object_id):
    data = load_object(object_id)
    if not data:
        abort(404)
    return render_template('med_life/timeline.html', object_id=object_id, data=data)

# API
@bp.route('/api/objects')
def api_objects():
    return jsonify(list_objects())

@bp.route('/api/<object_id>/entries')
def api_entries(object_id):
    return jsonify(load_object(object_id))

@bp.route('/api/<object_id>/system/<system_key>')
def api_system(object_id, system_key):
    data = load_object(object_id)
    return jsonify(filter_by_system(data['entries'], system_key))

@bp.route('/api/<object_id>/drugs')
def api_drugs(object_id):
    data = load_object(object_id)
    drugs = collect_prescriptions(data['entries'])
    for d in drugs:
        d['ref'] = load_drug(d.get('drug_id'))
        d['prices'] = load_prices(d.get('drug_id'))
    return jsonify(drugs)

@bp.route('/api/<object_id>/radar')
def api_radar(object_id):
    return jsonify(build_system_scores(object_id))

@bp.route('/api/<object_id>/timeline')
def api_timeline(object_id):
    data = load_object(object_id)
    return jsonify(sorted(data['entries'], key=lambda x: x.get('date', '')))
```

## 5. Регистрация в app.py

```python
from routes import med_life
app.register_blueprint(med_life.bp)
```

## 6. Маппинг на жизненные системы

```python
SYSTEM_MAPPING = {
    'cardiovascular': ['АД', 'ХСЛП', 'триглицериды', 'сердце', 'артериальное давление'],
    'respiratory': ['ФВД', 'ФВЦ', 'дыхание', 'лёгкие'],
    'nervous': ['невролог', 'Тразодон', 'Актовегин', 'Бринтеликс', 'нервная'],
    'endocrine': ['TSH', 'Т4', 'T3', 'глюкоза', 'инсулин', 'витамин Д'],
    'musculoskeletal': ['ортопед', 'Ксеорокам', 'Толперизон', 'дорсопатия'],
    'digestive': ['гастроэнтеролог', 'Омез', 'Ниаспам', 'ЖКТ'],
    'urinary': ['мочевыделительная', 'почки', 'креатинин', 'мочевина'],
    'immune': ['аллерголог', 'фексофенадин', 'иммунитет', 'Никсар'],
    'reproductive': ['уролог', 'гинеколог', 'либидо', 'тестостерон'],
    'sensory': ['офтальмолог', 'зрение', 'слух', 'H52'],
    'psychological': ['психиатр', 'настроение', 'тревога', 'сон', 'энергия'],
}
```

## 7. Запуск

```bash
./scripts/flask.sh start 01 5000
```

Проверка:
- `http://localhost:5000/med-life/`
- `http://localhost:5000/med-life/atlas/usr_8e498be`
