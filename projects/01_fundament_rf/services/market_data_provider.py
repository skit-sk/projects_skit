import re
import time
import random
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


def detect_symbol_type(symbol: str) -> str:
    """Detect symbol type based on common patterns."""
    s = symbol.upper().strip()
    if ':' in s:
        return 'stock'
    if re.search(r'(USDT|BTC|ETH|BUSD|FDUSD|USDC|SOL|XRP|ADA|DOGE|AVAX|LINK|LTC|BNB)$', s):
        return 'crypto'
    if '=' in s:
        return 'commodity'
    if len(s) == 6 and s.isalpha():
        return 'forex'
    if s.isalpha() and 1 <= len(s) <= 5:
        return 'stock'
    return 'crypto'


def _format_time(ts_ms: int, interval: str) -> str:
    """Format timestamp to ISO string or date depending on interval."""
    dt = datetime.utcfromtimestamp(ts_ms / 1000)
    if interval in ('1d', '3d', '1w', '1M'):
        return dt.strftime('%Y-%m-%d')
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def _interval_to_binance(interval: str) -> str:
    mapping = {
        '1': '1m', '3': '3m', '5': '5m', '15': '15m', '30': '30m',
        '60': '1h', '120': '2h', '240': '4h', '360': '6h', '720': '12h',
        'D': '1d', '1D': '1d', 'W': '1w', '1W': '1w', 'M': '1M', '1M': '1M'
    }
    return mapping.get(interval, '1d')


def _interval_to_bitget(interval: str) -> str:
    mapping = {
        '1': '1m', '5': '5m', '15': '15m', '30': '30m',
        '60': '1H', '240': '4H', '360': '6H', '720': '12H',
        'D': '1D', '1D': '1D', 'W': '1W', '1W': '1W', 'M': '1M', '1M': '1M'
    }
    return mapping.get(interval, '1D')


def fetch_binance(symbol: str, interval: str, limit: int = 200) -> Optional[List[Dict[str, Any]]]:
    """Fetch klines from Binance public API."""
    try:
        # Normalize symbol for Binance (remove separators)
        sym = symbol.upper().replace('/', '').replace('-', '')
        tf = _interval_to_binance(interval)
        url = 'https://api.binance.com/api/v3/klines'
        params = {'symbol': sym, 'interval': tf, 'limit': limit}
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return [
            {
                'time': _format_time(item[0], interval),
                'open': float(item[1]),
                'high': float(item[2]),
                'low': float(item[3]),
                'close': float(item[4]),
                'volume': float(item[5]),
            }
            for item in data
        ]
    except Exception as e:
        print(f'Binance fetch failed for {symbol}: {e}')
        return None


def fetch_bitget(symbol: str, interval: str, limit: int = 200) -> Optional[List[Dict[str, Any]]]:
    """Fetch klines from Bitget public API."""
    try:
        sym = symbol.upper().replace('/', '')
        if not sym.endswith('USDT'):
            sym = sym + 'USDT'
        tf = _interval_to_bitget(interval)
        url = 'https://api.bitget.com/api/v2/spot/market/candles'
        params = {'symbol': sym, 'granularity': tf, 'limit': str(limit)}
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get('code') != '00000':
            return None
        rows = data.get('data', [])
        # Bitget order: [openTime, open, high, low, close, vol, quoteVol]
        rows_sorted = sorted(rows, key=lambda x: int(x[0]))
        return [
            {
                'time': _format_time(int(row[0]), interval),
                'open': float(row[1]),
                'high': float(row[2]),
                'low': float(row[3]),
                'close': float(row[4]),
                'volume': float(row[5]),
            }
            for row in rows_sorted
        ]
    except Exception as e:
        print(f'Bitget fetch failed for {symbol}: {e}')
        return None


def fetch_yahoo(symbol: str, interval: str, limit: int = 200) -> Optional[List[Dict[str, Any]]]:
    """Fetch historical data from Yahoo Finance."""
    try:
        import yfinance as yf
        # Map intervals
        tf_map = {
            '1': '1m', '5': '5m', '15': '15m', '30': '30m', '60': '60m',
            'D': '1d', '1D': '1d', 'W': '1wk', '1W': '1wk', 'M': '1mo', '1M': '1mo'
        }
        tf = tf_map.get(interval, '1d')
        period = '1y' if tf in ('1d', '1wk', '1mo') else '7d'
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=tf)
        if hist.empty:
            return None
        rows = []
        for idx, row in hist.iterrows():
            rows.append({
                'time': idx.strftime('%Y-%m-%d') if tf in ('1d', '1wk', '1mo') else idx.strftime('%Y-%m-%d %H:%M:%S'),
                'open': round(float(row['Open']), 6),
                'high': round(float(row['High']), 6),
                'low': round(float(row['Low']), 6),
                'close': round(float(row['Close']), 6),
                'volume': int(row['Volume']) if row['Volume'] == row['Volume'] else 0,
            })
        return rows[-limit:]
    except Exception as e:
        print(f'Yahoo fetch failed for {symbol}: {e}')
        return None


def generate_synthetic(symbol: str, interval: str, limit: int = 200) -> List[Dict[str, Any]]:
    """Generate realistic synthetic OHLCV data."""
    random.seed(symbol + interval)
    base_price = random.uniform(10, 50000)
    volatility = random.uniform(0.005, 0.03)
    rows = []
    
    # Determine time delta
    interval_minutes = {
        '1': 1, '5': 5, '15': 15, '30': 30, '60': 60,
        '240': 240, 'D': 1440, '1D': 1440, 'W': 10080, '1W': 10080,
        'M': 43200, '1M': 43200
    }.get(interval, 1440)
    
    now = datetime.utcnow()
    if interval in ('D', '1D', 'W', '1W', 'M', '1M'):
        now = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    for i in range(limit, 0, -1):
        t = now - timedelta(minutes=interval_minutes * i)
        change = random.uniform(-volatility, volatility)
        close = base_price * (1 + change)
        high = close * (1 + random.uniform(0, volatility * 0.5))
        low = close * (1 - random.uniform(0, volatility * 0.5))
        open_price = low + random.uniform(0, high - low)
        # ensure open/close within low-high
        open_price = min(max(open_price, low), high)
        close = min(max(close, low), high)
        volume = random.uniform(100, 10000)
        rows.append({
            'time': t.strftime('%Y-%m-%d') if interval in ('D', '1D', 'W', '1W', 'M', '1M') else t.strftime('%Y-%m-%d %H:%M:%S'),
            'open': round(open_price, 6),
            'high': round(high, 6),
            'low': round(low, 6),
            'close': round(close, 6),
            'volume': round(volume, 2),
        })
        base_price = close
    return rows


def fetch_ohlcv(symbol: str, interval: str = '1D', limit: int = 200,
                active_sources: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Fetch OHLCV data using active sources in priority order.
    active_sources: e.g. ['binance', 'bitget', 'yahoo', 'synthetic']
    """
    if active_sources is None:
        active_sources = ['binance', 'bitget', 'yahoo', 'synthetic']
    
    symbol_type = detect_symbol_type(symbol)
    result = {
        'symbol': symbol,
        'type': symbol_type,
        'interval': interval,
        'source': None,
        'data': []
    }
    
    for source in active_sources:
        data = None
        if source == 'binance' and symbol_type == 'crypto':
            data = fetch_binance(symbol, interval, limit)
        elif source == 'bitget' and symbol_type == 'crypto':
            data = fetch_bitget(symbol, interval, limit)
        elif source == 'yahoo' and symbol_type in ('stock', 'forex', 'commodity'):
            data = fetch_yahoo(symbol, interval, limit)
        elif source == 'yahoo' and symbol_type == 'crypto':
            data = fetch_yahoo(symbol, interval, limit)
        elif source == 'synthetic':
            data = generate_synthetic(symbol, interval, limit)
        
        if data:
            result['source'] = source
            result['data'] = data
            return result
    
    # Ultimate fallback
    result['source'] = 'synthetic'
    result['data'] = generate_synthetic(symbol, interval, limit)
    return result
