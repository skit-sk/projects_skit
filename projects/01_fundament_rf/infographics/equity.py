import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict


class EquityAnalyzer:
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

    def get_equity_curve(self) -> Dict[str, Any]:
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

        all_days = defaultdict(list)

        for f in object_files:
            try:
                obj_id = f.stem
                obj_data = self._load_object(obj_id)
                if not obj_data:
                    continue

                emoji_entry = obj_data.get('data', {}).get('emoji_entry', {})
                symbol = emoji_entry.get('symbol', 'UNKNOWN')
                entry_date = emoji_entry.get('entry_date', '')
                name = obj_data.get('name', symbol)

                days_data = self._load_1d(obj_id)
                if not days_data or 'days' not in days_data:
                    continue

                for day in days_data['days']:
                    date = day.get('date')
                    if not date:
                        continue
                    all_days[date].append({
                        'date': date,
                        'pnl_usdt': day.get('pnl_usdt', 0),
                        'roe_pct': day.get('roe_pct', 0),
                        'deviation_pct': day.get('deviation', {}).get('from_entry_pct', 0),
                        'profitable': day.get('profitable', False),
                        'symbol': symbol,
                        'name': name,
                        'obj_id': obj_id
                    })
            except Exception:
                continue

        sorted_dates = sorted(all_days.keys())
        cumulative_pnl = 0
        equity_curve = []
        peak = 0
        max_drawdown_pct = 0
        drawdown_curve = []

        for date in sorted_dates:
            day_pnl = sum(tr['pnl_usdt'] for tr in all_days[date])
            cumulative_pnl += day_pnl
            peak = max(peak, cumulative_pnl)
            drawdown = peak - cumulative_pnl
            drawdown_pct = (drawdown / peak * 100) if peak > 0 else 0
            max_drawdown_pct = max(max_drawdown_pct, drawdown_pct)

            equity_curve.append({
                'date': date,
                'cumulative_pnl': round(cumulative_pnl, 4),
                'day_pnl': round(day_pnl, 4),
                'trades_count': len(all_days[date])
            })
            drawdown_curve.append({
                'date': date,
                'drawdown': round(drawdown, 4),
                'drawdown_pct': round(drawdown_pct, 2)
            })

        return {
            'equity_curve': equity_curve,
            'drawdown_curve': drawdown_curve,
            'max_drawdown_pct': round(max_drawdown_pct, 2),
            'final_pnl': round(cumulative_pnl, 2),
            'start_date': sorted_dates[0] if sorted_dates else None,
            'end_date': sorted_dates[-1] if sorted_dates else None,
            'total_days': len(sorted_dates)
        }

    def get_heatmap_data(self) -> Dict[str, Any]:
        objects_dir = self.data_dir
        object_files = [
            f for f in objects_dir.glob('*.json')
            if f.name not in ('metrics.json',) and not f.name.startswith('1D_') and not f.name.startswith('RAW_')
        ]

        symbol_month_pnl = defaultdict(lambda: defaultdict(list))
        symbol_month_days = defaultdict(lambda: defaultdict(list))

        for f in object_files:
            try:
                obj_id = f.stem
                obj_data = self._load_object(obj_id)
                if not obj_data:
                    continue

                emoji_entry = obj_data.get('data', {}).get('emoji_entry', {})
                symbol = emoji_entry.get('symbol', 'UNKNOWN')

                days_data = self._load_1d(obj_id)
                if not days_data or 'days' not in days_data:
                    continue

                for day in days_data['days']:
                    date = day.get('date', '')
                    if not date or len(date) < 7:
                        continue
                    year_month = date[:7]
                    roe_pct = day.get('roe_pct', 0)
                    symbol_month_pnl[symbol][year_month].append(roe_pct)
                    symbol_month_days[symbol][year_month].append({'date': date, 'roe_pct': round(roe_pct, 2)})
            except Exception:
                continue

        all_months = set()
        all_symbols = set(symbol_month_pnl.keys())
        for sym_data in symbol_month_pnl.values():
            all_months.update(sym_data.keys())
        all_months = sorted(all_months)

        if not all_months or not all_symbols:
            return {'z': [], 'x': [], 'y': [], 'symbols': [], 'cells': {}, 'symbol_min': {}, 'symbol_max': {}}

        symbol_min = {}
        symbol_max = {}
        for sym in sorted(all_symbols):
            all_roe = []
            for month in all_months:
                all_roe.extend(symbol_month_pnl[sym].get(month, []))
            if all_roe:
                symbol_min[sym] = min(all_roe)
                symbol_max[sym] = max(all_roe)
            else:
                symbol_min[sym] = 0
                symbol_max[sym] = 0

        z_data = []
        for sym in sorted(all_symbols):
            row = []
            for month in all_months:
                values = symbol_month_pnl[sym].get(month, [])
                avg = sum(values) / len(values) if values else 0
                row.append(round(avg, 1))
            z_data.append(row)

        return {
            'z': z_data,
            'x': all_months,
            'y': sorted(all_symbols),
            'symbols': sorted(all_symbols),
            'cells': {sym: {month: symbol_month_days[sym][month] for month in all_months} for sym in sorted(all_symbols)},
            'symbol_min': symbol_min,
            'symbol_max': symbol_max
        }
