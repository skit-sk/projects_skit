"""Terminal routes: combined chart + order book interface."""
from flask import Blueprint, render_template, jsonify, request
import urllib.request
import json
import asyncio
import sys
from pathlib import Path
_ws_root = Path(__file__).resolve().parents[3]
if str(_ws_root) not in sys.path:
    sys.path.insert(0, str(_ws_root))

bp = Blueprint('terminal', __name__, url_prefix='/terminal')


@bp.route('/')
def index():
    return render_template('terminal.html')


BITGET_API = 'https://api.bitget.com/api/v2/spot/market/orderbook'


@bp.route('/api/orderbook')
def orderbook():
    symbol = request.args.get('symbol', 'BTCUSDT').upper()
    if not symbol.endswith('USDT'):
        symbol += 'USDT'
    limit = int(request.args.get('limit', 20))
    try:
        url = f'{BITGET_API}?symbol={symbol}&type=step0&limit={limit}'
        req = urllib.request.Request(url, headers={'User-Agent': 'TradeHelp/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        if data.get('code') == '00000':
            return jsonify(data['data'])
        return jsonify({'error': data.get('msg', 'unknown')}), 502
    except urllib.error.URLError as e:
        return jsonify({'error': f'bitget_unreachable: {e.reason}'}), 502
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/orderbook/deep')
def orderbook_deep():
    """WebSocket 500-level orderbook snapshot."""
    symbol = request.args.get('symbol', 'BTCUSDT').upper()
    if not symbol.endswith('USDT'):
        symbol += 'USDT'
    try:
        from tools.scripts.formatters.orderbook import fetch_aggregated_ob_ws
        data = asyncio.run(fetch_aggregated_ob_ws(symbol, 500, 0))
        if data:
            return jsonify(data)
        return jsonify({'error': 'ws_empty'}), 502
    except Exception as e:
        return jsonify({'error': f'ws_failed: {str(e)}'}), 500
