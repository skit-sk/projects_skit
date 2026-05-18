import json
import websocket

WS_URL = 'wss://ws.bitget.com/v2/ws/public'

CHANNEL_MAP = {
    'fetch_ticker_ws':      {'channel': 'ticker',  'instType': 'SPOT'},
    'fetch_tickers_ws':     {'channel': 'ticker',  'instType': 'SPOT'},
    'fetch_order_book_ws':  {'channel': 'books5',  'instType': 'SPOT'},
    'fetch_ohlcv_ws':       {'channel': 'candle1d','instType': 'SPOT'},
    'fetch_trades_ws':      {'channel': 'trade',   'instType': 'SPOT'},
}


def resolve_channel(method, params):
    base = CHANNEL_MAP.get(method)
    if not base:
        raise ValueError(f'Unknown WS method: {method}')

    config = dict(base)
    symbol = params.get('symbol', 'BTC/USDT').replace('/', '')

    config['instId'] = symbol

    if method == 'fetch_ohlcv_ws':
        tf_map = {
            '1m': 'candle1m', '5m': 'candle5m', '15m': 'candle15m',
            '30m': 'candle30m', '1M': 'candle1M',
        }
        tf = params.get('timeframe', '1m')
        ch = tf_map.get(tf)
        if not ch:
            raise ValueError(f'WS candle not supported for timeframe {tf}. '
                             f'Supported: {", ".join(tf_map.keys())}')
        config['channel'] = ch

    if method == 'fetch_order_book_ws':
        limit_val = params.get('limit', 5)
        try:
            limit = int(limit_val)
        except (ValueError, TypeError):
            limit = 5
        if limit <= 5:
            config['channel'] = 'books5'
        elif limit <= 15:
            config['channel'] = 'books15'
        else:
            config['channel'] = 'books'

    return config


class BitgetWSStream:
    def __init__(self, method, params):
        self.method = method
        self.params = params
        self.ws = None

    def connect(self, timeout=10):
        channel = resolve_channel(self.method, self.params)
        args = [{k: v for k, v in channel.items() if v is not None}]
        sub_msg = json.dumps({"op": "subscribe", "args": args})
        self.ws = websocket.create_connection(WS_URL, timeout=timeout)
        self.ws.send(sub_msg)
        return self

    def recv(self, timeout=30):
        if not self.ws:
            return None
        self.ws.settimeout(timeout)
        try:
            raw = self.ws.recv()
            return json.loads(raw)
        except websocket.WebSocketTimeoutException:
            return None
        except Exception:
            return None

    def close(self):
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
            self.ws = None
