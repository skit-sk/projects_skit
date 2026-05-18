import json
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from calendar import monthrange
from collections import defaultdict


class CalendarHeatmap:
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            self.data_dir = Path(__file__).parent.parent / 'data'
        else:
            self.data_dir = Path(data_dir)

    def _load_1d(self, obj_id: str) -> Optional[dict]:
        card_dir = self.data_dir / 'card'
        if card_dir.exists():
            for subdir in card_dir.iterdir():
                if subdir.is_dir():
                    p = subdir / f'{obj_id}_1D.json'
                    if p.exists():
                        try:
                            with open(p, 'r', encoding='utf-8') as f:
                                return json.load(f)
                        except:
                            pass
        p = self.data_dir / f'1D_{obj_id}.json'
        if not p.exists():
            return None
        try:
            with open(p, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None

    def _load_object(self, obj_id: str) -> Optional[dict]:
        p = self.data_dir / f'{obj_id}.json'
        if p.exists():
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        card_dir = self.data_dir / 'card'
        if card_dir.exists():
            for subdir in card_dir.iterdir():
                if subdir.is_dir():
                    p = subdir / f'{obj_id}.json'
                    if p.exists():
                        try:
                            with open(p, 'r', encoding='utf-8') as f:
                                return json.load(f)
                        except:
                            pass
        return None

    def get_month_data(self, year: int, month: int) -> Dict[str, Any]:
        objects_dir = self.data_dir
        object_files = [
            f for f in objects_dir.glob('*.json')
            if f.name not in ('metrics.json',) and not f.name.startswith('1D_') and not f.name.startswith('RAW_')
        ]
        card_dir = self.data_dir / 'card'
        if card_dir.exists():
            for subdir in card_dir.iterdir():
                if subdir.is_dir():
                    for f in subdir.glob('*.json'):
                        name = f.name
                        if name.endswith('_1D.json') or name.endswith('_RAW.json'):
                            continue
                        object_files.append(f)

        month_str = f'{year}-{month:02d}'
        days_in_month = monthrange(year, month)[1]

        day_trades = defaultdict(list)

        for f in object_files:
            try:
                obj_id = f.stem
                obj_data = self._load_object(obj_id)
                if not obj_data:
                    continue

                emoji_entry = obj_data.get('data', {}).get('emoji_entry', {})
                symbol = emoji_entry.get('symbol', 'UNKNOWN')
                name = obj_data.get('name', symbol)

                days_data = self._load_1d(obj_id)
                if not days_data or 'days' not in days_data:
                    continue

                for day in days_data['days']:
                    day_date = day.get('date', '')
                    if not day_date or not day_date.startswith(month_str):
                        continue

                    roe_pct = day.get('roe_pct', 0)
                    pnl_usdt = day.get('pnl_usdt', 0)
                    deviation_pct = day.get('deviation', {}).get('from_entry_pct', 0)
                    profitable = day.get('profitable', False)
                    volatility = day.get('volatility', 0)

                    day_trades[day_date].append({
                        'obj_id': obj_id,
                        'symbol': symbol,
                        'name': name,
                        'roe_pct': round(roe_pct, 2),
                        'pnl_usdt': round(pnl_usdt, 2),
                        'deviation_pct': round(deviation_pct, 2),
                        'profitable': profitable,
                        'volatility': round(volatility, 4)
                    })
            except Exception:
                continue

        days = {}
        for day_num in range(1, days_in_month + 1):
            day_str = f'{year}-{month:02d}-{day_num:02d}'
            days[day_str] = {
                'trades': day_trades.get(day_str, []),
                'is_empty': len(day_trades.get(day_str, [])) == 0
            }

        return {
            'year': year,
            'month': month,
            'month_str': month_str,
            'days_in_month': days_in_month,
            'days': days
        }

    def get_pnl_color(self, pnl_pct: float) -> str:
        if pnl_pct >= 5:
            return '#16a34a'
        elif pnl_pct >= 2:
            return '#22c55e'
        elif pnl_pct >= 1:
            return '#86efac'
        elif pnl_pct > -1:
            return '#9ca3af'
        elif pnl_pct > -2:
            return '#fca5a5'
        elif pnl_pct > -5:
            return '#ef4444'
        else:
            return '#dc2626'

    def get_pnl_color_class(self, pnl_pct: float) -> str:
        if pnl_pct >= 5:
            return 'profit-high'
        elif pnl_pct >= 2:
            return 'profit-medium'
        elif pnl_pct >= 1:
            return 'profit-low'
        elif pnl_pct > -1:
            return 'neutral'
        elif pnl_pct > -2:
            return 'loss-low'
        elif pnl_pct > -5:
            return 'loss-medium'
        else:
            return 'loss-high'
