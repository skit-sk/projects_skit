import json
import os
import uuid
import shutil
import time
from datetime import datetime
from pathlib import Path
from models import FundObj


_storage_instance = None
_metrics_instance = None
_positions_cache = {}
_positions_cache_ts = 0.0


def get_positions_cache(ttl=10):
    global _positions_cache, _positions_cache_ts
    now = time.time()
    if now - _positions_cache_ts < ttl:
        return _positions_cache
    _positions_cache_ts = now
    _positions_cache = {}
    for obj in get_storage().list():
        lp = obj.data.get("live_position")
        if lp:
            sym = obj.data.get("emoji_entry", {}).get("symbol", "").upper()
            _positions_cache[sym] = lp
    return _positions_cache


def clear_positions_cache():
    global _positions_cache_ts
    _positions_cache_ts = 0.0


def get_storage():
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = JSONStorage()
    return _storage_instance


def get_metrics_storage():
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = MetricsStorage()
    return _metrics_instance


class JSONStorage:
    TF_EXTENSIONS = {"1D": "_1D.json", "4h": "_4h.json", "1h": "_1h.json"}

    def __init__(self, data_dir=None):
        if data_dir is None:
            self.data_dir = Path(__file__).parent / 'data'
        else:
            self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.card_dir = self.data_dir / 'card'
        self.card_dir.mkdir(exist_ok=True)

    def _card_folder(self, symbol, obj_id):
        uid5 = obj_id[:8]
        return self.card_dir / f'{symbol}_{uid5}'

    def _card_path(self, symbol, obj_id):
        return self._card_folder(symbol, obj_id) / f'{obj_id}.json'

    def _1d_path(self, symbol, obj_id):
        return self._card_folder(symbol, obj_id) / f'{obj_id}_1D.json'

    def _raw_path(self, symbol, obj_id):
        return self._card_folder(symbol, obj_id) / f'{obj_id}_RAW.json'

    def _tf_path(self, symbol, obj_id, timeframe: str):
        ext = self.TF_EXTENSIONS.get(timeframe)
        if not ext:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        return self._card_folder(symbol, obj_id) / f'{obj_id}{ext}'

    def write_timeframe(self, symbol, obj_id, timeframe: str, data: dict):
        data["updated_at"] = datetime.now().isoformat()
        self._ensure_card_folder(symbol, obj_id)
        with open(self._tf_path(symbol, obj_id, timeframe), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, default=str)

    def read_timeframe(self, symbol, obj_id, timeframe: str) -> dict:
        p = self._tf_path(symbol, obj_id, timeframe)
        if not p.exists():
            raise FileNotFoundError(f"{timeframe} data for {obj_id} not found")
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)

    def exists_timeframe(self, symbol, obj_id, timeframe: str) -> bool:
        return self._tf_path(symbol, obj_id, timeframe).exists()

    def _candles_to_legacy(self, symbol, obj_id, new_data):
        """Convert new-format 1D data dict to legacy shape (days[]/chart_data[]/summary)."""
        candles = new_data.get("candles", [])
        sym = new_data.get("symbol", symbol)
        entry_price = new_data.get("entry_price", 0)
        entry_date = new_data.get("entry_date", "")
        leverage = new_data.get("leverage", 10)
        volume = new_data.get("volume", 1)

        days = []
        chart_data = []
        profitable_count = 0
        loss_count = 0
        neutral_count = 0
        sum_roe = 0.0
        sum_volatility = 0.0
        current_roe = 0.0
        current_pnl = 0.0
        max_profit_day = None
        max_loss_day = None
        max_drawdown_pct = 0.0
        max_drawdown_usdt = 0.0
        streak_profit = 0
        streak_loss = 0
        current_streak = 0
        streak_type = None

        for i, c in enumerate(candles):
            pm = c.get("position_metrics", {})
            cm = c.get("candle_metrics", {})
            is_pre = pm.get("pre_entry", False)
            roe = pm.get("roe_pct", 0) if not is_pre else 0
            pnl = pm.get("pnl_usdt", 0) if not is_pre else 0
            profitable = pm.get("profitable", False) if not is_pre else False
            volatility = pm.get("volatility", 0)
            deviation = pm.get("deviation", {})
            day = {
                "date": c.get("date", ""),
                "day_index": i,
                "pre_entry": is_pre,
                "ohlc": {
                    "open": c.get("open", 0),
                    "high": c.get("high", 0),
                    "low": c.get("low", 0),
                    "close": c.get("close", 0),
                    "body": cm.get("body", 0),
                    "body_pct": pm.get("body_pct", 0),
                    "upper_wick": cm.get("upper_wick", 0),
                    "lower_wick": cm.get("lower_wick", 0),
                },
                "deviation": deviation,
                "roe_pct": roe,
                "pnl_usdt": pnl,
                "volatility": volatility,
                "profitable": profitable,
            }
            days.append(day)
            chart_data.append({
                "date": c.get("date", ""),
                "deviation_pct": deviation.get("from_entry_pct", 0),
                "profitable": profitable,
                "pre_entry": is_pre,
            })
            if not is_pre:
                if profitable:
                    profitable_count += 1
                if roe < 0:
                    loss_count += 1
                if roe == 0:
                    neutral_count += 1
                sum_roe += roe
                sum_volatility += volatility
                current_roe = roe
                current_pnl = pnl
                if max_profit_day is None or roe > max_profit_day["roe_pct"]:
                    max_profit_day = day
                if max_loss_day is None or roe < max_loss_day["roe_pct"]:
                    max_loss_day = day
                max_drawdown_pct = min(max_drawdown_pct, deviation.get("from_entry_pct", 0))
                max_drawdown_usdt = min(max_drawdown_usdt, deviation.get("from_entry_usdt", 0))
                if profitable:
                    if streak_type == "profit":
                        current_streak += 1
                    else:
                        current_streak = 1
                        streak_type = "profit"
                    streak_profit = max(streak_profit, current_streak)
                else:
                    if streak_type == "loss":
                        current_streak += 1
                    else:
                        current_streak = 1
                        streak_type = "loss"
                    streak_loss = max(streak_loss, current_streak)

        total_days = sum(1 for d in days if not d["pre_entry"])
        summary = {
            "total_days": total_days,
            "profitable_days": profitable_count,
            "loss_days": loss_count,
            "neutral_days": neutral_count,
            "current_roe_pct": round(current_roe, 2),
            "current_pnl_usdt": round(current_pnl, 4),
            "avg_roe_pct": round(sum_roe / total_days, 2) if total_days else 0,
            "avg_volatility": round(sum_volatility / total_days, 6) if total_days else 0,
            "max_profit_day": {
                "date": max_profit_day["date"], "roe_pct": max_profit_day["roe_pct"],
                "pnl_usdt": max_profit_day["pnl_usdt"],
            } if max_profit_day else {},
            "max_loss_day": {
                "date": max_loss_day["date"], "roe_pct": max_loss_day["roe_pct"],
                "pnl_usdt": max_loss_day["pnl_usdt"],
            } if max_loss_day else {},
            "max_drawdown_pct": round(max_drawdown_pct, 2),
            "max_drawdown_usdt": round(max_drawdown_usdt, 6),
            "streak_profit": streak_profit,
            "streak_loss": streak_loss,
        } if total_days else {}

        return {
            "id": f"{obj_id}_1D",
            "parent_id": obj_id,
            "symbol": sym.upper(),
            "entry_price": entry_price,
            "entry_date": entry_date,
            "leverage": leverage,
            "volume": volume,
            "status": "completed",
            "fetched_at": new_data.get("created_at"),
            "created_at": new_data.get("created_at"),
            "updated_at": new_data.get("updated_at"),
            "days": days,
            "chart_data": chart_data,
            "summary": summary,
        }

    def _ensure_card_folder(self, symbol, obj_id):
        folder = self._card_folder(symbol, obj_id)
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def save(self, obj: FundObj):
        obj.updated_at = datetime.now()
        symbol = obj.data.get('emoji_entry', {}).get('symbol', 'UNKNOWN')
        folder = self._ensure_card_folder(symbol, obj.id)
        with open(folder / f'{obj.id}.json', 'w', encoding='utf-8') as f:
            json.dump(obj.to_dict(), f, ensure_ascii=False, default=str)
        return obj

    def load(self, obj_id) -> FundObj:
        for f in self.card_dir.rglob(f'{obj_id}.json'):
            with open(f, 'r', encoding='utf-8') as fp:
                return FundObj.from_dict(json.load(fp))
        raise FileNotFoundError(f'Object {obj_id} not found')

    def list(self):
        objects = []
        for f in self.card_dir.rglob('*.json'):
            name = f.name
            if name.endswith('_1D.json') or name.endswith('_RAW.json') or name.endswith('_4h.json') or name.endswith('_1h.json') or name == 'metrics.json':
                continue
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    objects.append(FundObj.from_dict(json.load(fp)))
            except (KeyError, json.JSONDecodeError, TypeError):
                continue
        return sorted(objects, key=lambda x: x.created_at, reverse=True)

    def exists(self, obj_id) -> bool:
        return any(self.card_dir.rglob(f'{obj_id}.json'))

    def delete(self, obj_id):
        for f in self.card_dir.rglob(f'{obj_id}.json'):
            folder = f.parent
            shutil.rmtree(folder)
            return
        raise FileNotFoundError(f'Object {obj_id} not found')

    def save_raw(self, symbol, obj_id: str, data: dict):
        data['updated_at'] = datetime.now().isoformat()
        self._ensure_card_folder(symbol, obj_id)
        with open(self._raw_path(symbol, obj_id), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, default=str)

    def load_raw(self, symbol, obj_id: str) -> dict:
        p = self._raw_path(symbol, obj_id)
        if not p.exists():
            raise FileNotFoundError(f'RAW data for {obj_id} not found')
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)

    def delete_1d_raw(self, symbol, obj_id: str):
        for p in [self._1d_path(symbol, obj_id), self._raw_path(symbol, obj_id)]:
            if p.exists():
                p.unlink()

    def exists_raw(self, symbol, obj_id: str) -> bool:
        return self._raw_path(symbol, obj_id).exists()

    def get_card_subdirs(self):
        if not self.card_dir.exists():
            return []
        return [d for d in self.card_dir.iterdir() if d.is_dir()]

    # ── Account data (balance/orders/fills) ──

    def _account_dir(self):
        p = self.data_dir / 'account'
        p.mkdir(exist_ok=True)
        return p

    def save_balance(self, data: dict):
        with open(self._account_dir() / 'balance.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, default=str)

    def load_balance(self) -> dict:
        p = self._account_dir() / 'balance.json'
        if not p.exists():
            return {}
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_orders(self, data: dict):
        with open(self._account_dir() / 'orders.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, default=str)

    def load_orders(self) -> dict:
        p = self._account_dir() / 'orders.json'
        if not p.exists():
            return {}
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_fills(self, data: dict):
        with open(self._account_dir() / 'fills.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, default=str)

    def load_fills(self) -> dict:
        p = self._account_dir() / 'fills.json'
        if not p.exists():
            return {}
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_totals(self, data: dict):
        with open(self._account_dir() / 'totals.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, default=str)

    def load_totals(self) -> dict:
        p = self._account_dir() / 'totals.json'
        if not p.exists():
            return {}
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)


class MetricsStorage:
    def __init__(self, data_dir=None):
        if data_dir is None:
            self.data_dir = Path(__file__).parent / 'data'
        else:
            self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self._metrics_path = self.data_dir / 'metrics.json'
        self._ensure_metrics()

    def _ensure_metrics(self):
        if not self._metrics_path.exists():
            with open(self._metrics_path, 'w', encoding='utf-8') as f:
                json.dump({'records': [], 'aggregated': {'total_operations': 0, 'avg_api_ms': 0, 'avg_processing_ms': 0, 'avg_writing_ms': 0, 'avg_total_ms': 0, 'failed_count': 0, 'last_operation': None}}, f)

    def load(self) -> dict:
        try:
            with open(self._metrics_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            self._ensure_metrics()
            with open(self._metrics_path, 'r', encoding='utf-8') as f:
                return json.load(f)

    def save(self, data: dict):
        with open(self._metrics_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, default=str)

    def add_record(self, record: dict):
        data = self.load()
        record['id'] = str(uuid.uuid4())
        data['records'].insert(0, record)
        self._recalculate_aggregated(data)
        self.save(data)

    def _recalculate_aggregated(self, data: dict):
        records = data.get('records', [])
        if not records:
            return
        total = len(records)
        failed = sum(1 for r in records if r.get('result', {}).get('status') == 'failed')
        api_times = [r['duration_ms']['api_request_ms'] for r in records if 'duration_ms' in r and 'api_request_ms' in r['duration_ms']]
        proc_times = [r['duration_ms']['processing_ms'] for r in records if 'duration_ms' in r and 'processing_ms' in r['duration_ms']]
        write_times = [r['duration_ms']['writing_ms'] for r in records if 'duration_ms' in r and 'writing_ms' in r['duration_ms']]
        total_times = [r['duration_ms']['total_ms'] for r in records if 'duration_ms' in r and 'total_ms' in r['duration_ms']]
        data['aggregated'] = {
            'total_operations': total,
            'avg_api_ms': sum(api_times) / len(api_times) if api_times else 0,
            'avg_processing_ms': sum(proc_times) / len(proc_times) if proc_times else 0,
            'avg_writing_ms': sum(write_times) / len(write_times) if write_times else 0,
            'avg_total_ms': sum(total_times) / len(total_times) if total_times else 0,
            'failed_count': failed,
            'last_operation': records[0]['timestamp'] if records else None
        }

    def clear(self):
        self._ensure_metrics()
