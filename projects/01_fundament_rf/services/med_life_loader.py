import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

MED_LIFE_ROOT = Path('/home/user_aioc/workspace/projects/11_med_life')

SYSTEM_MAPPING = {
    'cardiovascular': ['АД', 'ХСЛП', 'триглицериды', 'сердце', 'артериальное давление', 'холестерин'],
    'respiratory': ['ФВД', 'ФВЦ', 'дыхание', 'лёгкие', 'SpO2'],
    'nervous': ['невролог', 'Тразодон', 'Актовегин', 'Бринтеликс', 'нервная', 'головная боль', 'невралгия'],
    'endocrine': ['TSH', 'Т4', 'T3', 'глюкоза', 'инсулин', 'витамин Д', 'эндокрин'],
    'musculoskeletal': ['ортопед', 'Ксеорокам', 'Толперизон', 'дорсопатия', 'радикулопатия', 'опорно-двигательная'],
    'digestive': ['гастроэнтеролог', 'Омез', 'Ниаспам', 'ЖКТ', 'пищеварение'],
    'urinary': ['мочевыделительная', 'почки', 'креатинин', 'мочевина', 'мочеиспускание'],
    'immune': ['аллерголог', 'фексофенадин', 'иммунитет', 'Никсар', 'аллергия'],
    'reproductive': ['уролог', 'гинеколог', 'либидо', 'тестостерон', 'репродуктивная'],
    'sensory': ['офтальмолог', 'зрение', 'слух', 'H52', 'сенсорная'],
    'psychological': ['психиатр', 'психолог', 'настроение', 'тревога', 'сон', 'энергия', 'депрессия'],
}

SYSTEM_LABELS = {
    'cardiovascular': 'Сердечно-сосудистая',
    'respiratory': 'Дыхательная',
    'nervous': 'Нервная',
    'endocrine': 'Эндокринная',
    'musculoskeletal': 'Опорно-двигательная',
    'digestive': 'Пищеварительная',
    'urinary': 'Мочевыделительная',
    'immune': 'Иммунная / аллергическая',
    'reproductive': 'Репродуктивная',
    'sensory': 'Сенсорная',
    'psychological': 'Психоэмоциональная',
}


def list_objects() -> List[Dict[str, Any]]:
    meta_dir = MED_LIFE_ROOT / 'data' / 'objects'
    if not meta_dir.exists():
        return []
    objects = []
    for p in sorted(meta_dir.iterdir()):
        meta_file = p / 'meta.json'
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text(encoding='utf-8'))
                meta['object_id'] = p.name
                objects.append(meta)
            except Exception:
                pass
    return objects


def load_object(object_id: str) -> Optional[Dict[str, Any]]:
    obj_dir = MED_LIFE_ROOT / 'data' / 'objects' / object_id
    if not obj_dir.exists():
        return None
    meta_file = obj_dir / 'meta.json'
    if not meta_file.exists():
        return None
    try:
        meta = json.loads(meta_file.read_text(encoding='utf-8'))
    except Exception:
        return None
    entries = []
    entries_dir = obj_dir / 'entries'
    if entries_dir.exists():
        for entry_path in sorted(entries_dir.glob('*.json')):
            try:
                entries.append(json.loads(entry_path.read_text(encoding='utf-8')))
            except Exception:
                pass
    return {'meta': meta, 'entries': entries, 'object_id': object_id}


def load_drug(drug_id: str) -> Optional[Dict[str, Any]]:
    if not drug_id:
        return None
    path = MED_LIFE_ROOT / 'data' / 'drug_reference' / drug_id / 'meta.json'
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None


def load_prices(drug_id: str) -> Optional[Dict[str, Any]]:
    if not drug_id:
        return None
    path = MED_LIFE_ROOT / 'data' / 'price_tracker' / f'{drug_id}.json'
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None


def _entry_text(entry: Dict[str, Any]) -> str:
    """Flatten entry to text for keyword matching."""
    parts = [
        entry.get('domain', ''),
        json.dumps(entry.get('specialist', {}), ensure_ascii=False),
        json.dumps(entry.get('data', {}), ensure_ascii=False),
    ]
    return ' '.join(parts).lower()


def filter_by_system(entries: List[Dict[str, Any]], system_key: str) -> List[Dict[str, Any]]:
    keywords = SYSTEM_MAPPING.get(system_key, [])
    if not keywords:
        return []
    result = []
    for entry in entries:
        text = _entry_text(entry)
        if any(kw.lower() in text for kw in keywords):
            result.append(entry)
    return result


def collect_prescriptions(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    prescriptions = []
    for entry in entries:
        data = entry.get('data', {})
        for presc in data.get('prescriptions', []):
            p = dict(presc)
            p['entry_id'] = entry.get('entry_id')
            p['date'] = entry.get('date')
            p['source'] = 'specialist'
            prescriptions.append(p)
        for presc in data.get('self_prescribed', []):
            p = dict(presc)
            p['entry_id'] = entry.get('entry_id')
            p['date'] = entry.get('date')
            p['source'] = 'self'
            prescriptions.append(p)
    return prescriptions


def collect_labs(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    labs = []
    for entry in entries:
        if entry.get('domain') == 'lab':
            data = entry.get('data', {})
            for test in data.get('tests', []):
                t = dict(test)
                t['date'] = entry.get('date')
                t['entry_id'] = entry.get('entry_id')
                labs.append(t)
    return labs


def collect_subjective(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    result = []
    for entry in entries:
        if entry.get('domain') == 'subjective':
            data = entry.get('data', {})
            data['date'] = entry.get('date')
            data['entry_id'] = entry.get('entry_id')
            result.append(data)
    return result


def build_system_scores(object_id: str) -> Dict[str, Any]:
    data = load_object(object_id)
    if not data:
        return {'object_id': object_id, 'systems': []}
    entries = data.get('entries', [])
    systems = []
    for key, label in SYSTEM_LABELS.items():
        matched = filter_by_system(entries, key)
        score = _calculate_system_score(matched, key)
        systems.append({
            'key': key,
            'name': label,
            'score': score,
            'label': _score_label(score),
            'count': len(matched)
        })
    return {'object_id': object_id, 'systems': systems}


def _calculate_system_score(entries: List[Dict[str, Any]], system_key: str) -> float:
    """Heuristic score 0-10 based on available data."""
    if not entries:
        return 0.0
    score = 5.0
    # Boost for more data
    score += min(len(entries) * 0.3, 2.0)
    # Labs with values in reference range
    for entry in entries:
        if entry.get('domain') == 'lab':
            for test in entry.get('data', {}).get('tests', []):
                ref = test.get('ref_range', {})
                val = test.get('value')
                if isinstance(val, (int, float)) and ref:
                    low = ref.get('low')
                    high = ref.get('high')
                    if low is not None and high is not None and low <= val <= high:
                        score += 0.2
                    else:
                        score -= 0.3
        # Subjective scales
        if entry.get('domain') == 'subjective':
            d = entry.get('data', {})
            for k in ['mood', 'energy', 'sleep']:
                v = d.get(k)
                if isinstance(v, (int, float)):
                    score += (v - 5) / 10.0
    return max(0.0, min(10.0, round(score, 1)))


def _score_label(score: float) -> str:
    if score >= 8: return 'excellent'
    if score >= 6: return 'good'
    if score >= 4: return 'medium'
    if score >= 2: return 'low'
    return 'very_low'
