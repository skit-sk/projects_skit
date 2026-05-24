import json
import time
from pathlib import Path

AGGREGATE_FILE = Path(__file__).resolve().parent.parent / 'data' / 'account' / 'totals.json'


def calc_aggregate(cards: list) -> dict:
    total_margin = 0.0
    total_pl = 0.0
    total_value = 0.0
    count = 0
    for obj in cards:
        lp = obj.data.get('live_position')
        if not lp or not lp.get('hold_side'):
            continue
        m = float(lp.get('margin_size', 0))
        pl = float(lp.get('unrealized_pl', 0))
        lev = float(lp.get('leverage', 10))
        total_margin += m
        total_pl += pl
        total_value += m * lev
        count += 1
    return {
        'total_margin': round(total_margin, 6),
        'total_pl': round(total_pl, 6),
        'total_value': round(total_value, 6),
        'total_positions': count,
        'updated_at': int(time.time() * 1000),
    }


def save_aggregate(data: dict):
    AGGREGATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(AGGREGATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)


def load_aggregate() -> dict:
    if not AGGREGATE_FILE.exists():
        return {}
    with open(AGGREGATE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)