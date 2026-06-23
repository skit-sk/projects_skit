import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json

from storage import get_storage


class MADataLoader:
    def __init__(self, exchange_id: str = 'bitget', entry_date: str = None):
        self.storage = get_storage()
        self.exchange_id = exchange_id
        self.entry_date = entry_date
        self._ccxt = None

    @property
    def ccxt(self):
        if self._ccxt is None:
            import ccxt
            self._ccxt = getattr(ccxt, self.exchange_id)({
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'},
            })
        return self._ccxt

    def fetch_historical(self, symbol: str, limit: int = 500,
                         timeframe: str = '1d', since: Optional[str] = None) -> List[Dict]:
        since_ts = None
        if since:
            dt = datetime.strptime(since, '%Y-%m-%d')
            since_ts = int(dt.timestamp() * 1000)

        all_candles = []
        remaining = limit
        current_since = since_ts

        while remaining > 0:
            batch_size = min(200, remaining)
            try:
                ohlcv = self.ccxt.fetch_ohlcv(symbol, timeframe, since=current_since, limit=batch_size)
            except Exception as e:
                raise Exception(f"CCXT fetch error for {symbol}: {e}")

            if not ohlcv:
                break

            for c in ohlcv:
                all_candles.append({
                    'date': time.strftime('%Y-%m-%d', time.gmtime(c[0] / 1000)),
                    'timestamp_ms': c[0],
                    'open': float(c[1]),
                    'high': float(c[2]),
                    'low': float(c[3]),
                    'close': float(c[4]),
                    'volume': float(c[5]),
                })

            remaining -= len(ohlcv)
            current_since = ohlcv[-1][0] + 1
            if len(ohlcv) < batch_size:
                break

        return all_candles

    def fetch_and_save(self, symbol: str, obj_id: str, limit: int = 500) -> Dict:
        candles = self.fetch_historical(symbol, limit)
        for c in candles:
            c['pre_entry'] = (self.entry_date is not None and c.get('date', '') < self.entry_date)
        raw_data = {
            'id': f'{obj_id}_MA_RAW',
            'parent_id': obj_id,
            'symbol': symbol.upper(),
            'granularity': '1day',
            'source': self.exchange_id,
            'fetched_at': datetime.now().isoformat(),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'candles': candles,
            'total_candles': len(candles),
        }
        self.storage.save_raw(symbol, obj_id, raw_data)
        return raw_data
