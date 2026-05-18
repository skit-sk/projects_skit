import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class TradeKPI:
    id: str
    name: str
    symbol: str
    entry_date: str
    leverage: int
    volume: float
    pnl_usdt: float
    pnl_percent: float
    roe_percent: float
    status: str
    days_active: int
    side: str = 'long'


class DashboardKPI:
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            self.data_dir = Path(__file__).parent.parent / 'data'
        else:
            self.data_dir = Path(data_dir)

    def _load_all_objects(self) -> List[dict]:
        objects = []
        for f in self.data_dir.glob('*.json'):
            name = f.name
            if name in ('metrics.json',) or name.startswith('1D_') or name.startswith('RAW_'):
                continue
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    objects.append(json.load(fp))
            except (KeyError, json.JSONDecodeError, TypeError):
                continue
        card_dir = self.data_dir / 'card'
        if card_dir.exists():
            for subdir in card_dir.iterdir():
                if subdir.is_dir():
                    for f in subdir.glob('*.json'):
                        name = f.name
                        if name.endswith('_1D.json') or name.endswith('_RAW.json'):
                            continue
                        try:
                            with open(f, 'r', encoding='utf-8') as fp:
                                objects.append(json.load(fp))
                        except:
                            continue
        return objects

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

    def get_all_trades_kpi(self) -> List[TradeKPI]:
        objects = self._load_all_objects()
        trades = []
        for obj in objects:
            data = obj.get('data', {})
            emoji_entry = data.get('emoji_entry', {})
            emoji_upd = data.get('emoji_upd', {})
            if not emoji_entry.get('symbol'):
                continue
            days_data = self._load_1d(obj['id'])
            days_active = len(days_data['days']) if days_data and 'days' in days_data else emoji_entry.get('entry_time', 0)
            side = emoji_entry.get('hold_side', 'long')
            trades.append(TradeKPI(
                id=obj['id'],
                name=obj.get('name', emoji_entry.get('symbol', 'Unknown')),
                symbol=emoji_entry.get('symbol', 'UNKNOWN'),
                entry_date=emoji_entry.get('entry_date', ''),
                leverage=emoji_entry.get('leverage', data.get('leverage', 1)),
                volume=emoji_entry.get('volume', 0),
                pnl_usdt=emoji_entry.get('pnl_usdt', emoji_upd.get('pnl_usdt', 0)),
                pnl_percent=emoji_entry.get('pnl_percent', emoji_upd.get('pnl_percent', 0)),
                roe_percent=emoji_entry.get('pnl_usdt', 0),
                status=emoji_entry.get('status', emoji_upd.get('status', 'unknown')),
                days_active=days_active,
                side=side,
            ))
        return trades

    def get_summary(self) -> Dict[str, Any]:
        trades = self.get_all_trades_kpi()
        if not trades:
            return self._empty_summary()

        total_pnl = sum(t.pnl_usdt for t in trades)
        total_pnl_percent = sum(t.pnl_percent for t in trades) / len(trades) if trades else 0
        winning = [t for t in trades if t.status in ('green', '🟢')]
        losing = [t for t in trades if t.status in ('red', '🔴')]
        win_rate = len(winning) / len(trades) * 100 if trades else 0
        active = [t for t in trades if t.days_active > 0]
        short_count = sum(1 for t in trades if t.side == 'short')
        long_count = len(trades) - short_count

        best = max(trades, key=lambda t: t.pnl_usdt) if trades else None
        worst = min(trades, key=lambda t: t.pnl_usdt) if trades else None

        return {
            'total_trades': len(trades),
            'active_trades': len(active),
            'total_pnl_usdt': round(total_pnl, 2),
            'avg_pnl_usdt': round(total_pnl / len(trades), 2) if trades else 0,
            'avg_pnl_percent': round(total_pnl_percent, 2),
            'win_count': len(winning),
            'loss_count': len(losing),
            'win_rate': round(win_rate, 1),
            'best_trade': {
                'name': best.name if best else None,
                'symbol': best.symbol if best else None,
                'pnl_usdt': round(best.pnl_usdt, 2) if best else 0,
                'pnl_percent': round(best.pnl_percent, 2) if best else 0
            } if best else None,
            'worst_trade': {
                'name': worst.name if worst else None,
                'symbol': worst.symbol if worst else None,
                'pnl_usdt': round(worst.pnl_usdt, 2) if worst else 0,
                'pnl_percent': round(worst.pnl_percent, 2) if worst else 0
            } if worst else None,
            'avg_leverage': round(sum(t.leverage for t in trades) / len(trades), 1) if trades else 0,
            'avg_days_active': round(sum(t.days_active for t in trades) / len(trades), 1) if trades else 0,
            'short_count': short_count,
            'long_count': long_count,
        }

    def _empty_summary(self) -> Dict[str, Any]:
        return {
            'total_trades': 0,
            'active_trades': 0,
            'total_pnl_usdt': 0,
            'avg_pnl_usdt': 0,
            'avg_pnl_percent': 0,
            'win_count': 0,
            'loss_count': 0,
            'win_rate': 0,
            'best_trade': None,
            'worst_trade': None,
            'avg_leverage': 0,
            'avg_days_active': 0,
            'short_count': 0,
            'long_count': 0,
        }

    def get_pnl_by_symbol(self) -> Dict[str, Dict[str, float]]:
        trades = self.get_all_trades_kpi()
        by_symbol = {}
        for t in trades:
            if t.symbol not in by_symbol:
                by_symbol[t.symbol] = {'pnl_usdt': 0, 'pnl_percent': 0, 'count': 0, 'win_count': 0, 'loss_count': 0}
            by_symbol[t.symbol]['pnl_usdt'] += t.pnl_usdt
            by_symbol[t.symbol]['pnl_percent'] += t.pnl_percent
            by_symbol[t.symbol]['count'] += 1
            if t.status in ('green', '🟢'):
                by_symbol[t.symbol]['win_count'] += 1
            else:
                by_symbol[t.symbol]['loss_count'] += 1
        for sym in by_symbol:
            cnt = by_symbol[sym]['count']
            by_symbol[sym]['avg_pnl_usdt'] = round(by_symbol[sym]['pnl_usdt'] / cnt, 2)
            by_symbol[sym]['win_rate'] = round(by_symbol[sym]['win_count'] / cnt * 100, 1)
        return by_symbol

    def get_distribution(self) -> List[Dict[str, Any]]:
        trades = self.get_all_trades_kpi()
        return [
            {
                'id': t.id,
                'name': t.name,
                'symbol': t.symbol,
                'pnl_usdt': round(t.pnl_usdt, 2),
                'pnl_percent': round(t.pnl_percent, 2),
                'status': t.status,
                'side': t.side,
            }
            for t in sorted(trades, key=lambda x: x.pnl_usdt, reverse=True)
        ]

    def get_top_trades(self, limit: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        trades = self.get_all_trades_kpi()
        sorted_trades = sorted(trades, key=lambda x: x.pnl_usdt, reverse=True)
        top = sorted_trades[:limit]
        bottom = sorted(trades, key=lambda x: x.pnl_usdt)[:limit]
        return {
            'top': [
                {
                    'id': t.id,
                    'name': t.name,
                    'symbol': t.symbol,
                    'pnl_usdt': round(t.pnl_usdt, 2),
                    'pnl_percent': round(t.pnl_percent, 2),
                    'days_active': t.days_active,
                    'side': t.side,
                } for t in top
            ],
            'bottom': [
                {
                    'id': t.id,
                    'name': t.name,
                    'symbol': t.symbol,
                    'pnl_usdt': round(t.pnl_usdt, 2),
                    'pnl_percent': round(t.pnl_percent, 2),
                    'days_active': t.days_active,
                    'side': t.side,
                } for t in bottom
            ]
        }

    def get_donut(self) -> Dict[str, int]:
        trades = self.get_all_trades_kpi()
        winning = sum(1 for t in trades if t.status in ('green', '🟢'))
        losing = sum(1 for t in trades if t.status in ('red', '🔴'))
        return {'win': winning, 'loss': losing}
