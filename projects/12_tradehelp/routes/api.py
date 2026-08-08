"""API routes: klines proxy, live data, score, etc."""
from flask import Blueprint, jsonify, request
import json
import urllib.request
import urllib.error
import config

bp = Blueprint('api', __name__)


@bp.route('/klines')
def klines():
    """Proxy to Binance klines API for LWC (CORS bypass)."""
    symbol = request.args.get('symbol', 'BTCUSDT')
    interval = request.args.get('interval', '1d')
    limit = int(request.args.get('limit', 200))
    try:
        url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}'
        req = urllib.request.Request(url, headers={'User-Agent': 'TradeHelp/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        return jsonify(data)
    except urllib.error.URLError as e:
        return jsonify({'error': f'binance_unreachable: {e}'}), 502
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/live/balance')
def live_balance():
    return _serve_json('balance.json')


@bp.route('/live/orders')
def live_orders():
    return _serve_json('orders.json')


@bp.route('/live/fills')
def live_fills():
    return _serve_json('fills.json')


@bp.route('/live/totals')
def live_totals():
    return _serve_json('totals.json')


@bp.route('/live/journal')
def live_journal():
    """Build journal view from fills."""
    try:
        p = config.DATA_LIVE / 'fills.json'
        if not p.exists():
            return jsonify({'journal': [], 'count': 0})
        d = json.loads(p.read_text(encoding='utf-8'))
        fills = d.get('fills', [])
        journal = []
        for f in fills:
            journal.append({
                'time': f.get('c_time', ''),
                'symbol': f.get('symbol', ''),
                'side': f.get('side', ''),
                'price': float(f.get('price', 0)),
                'quantity': float(f.get('quantity', 0)),
                'pnl': float(f.get('profit', 0)),
                'order_id': f.get('order_id', ''),
            })
        return jsonify({'journal': journal, 'count': len(journal)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/score', methods=['POST'])
def score():
    """Compute Confluence Score from 10 factors."""
    data = request.get_json(silent=True) or {}
    factors = data.get('factors', {})
    # 10 factors: wyckoff, mss, sweep, va, poi, ote, heatmap, oi, footprint, rr
    keys = ['wyckoff', 'mss', 'sweep', 'va', 'poi', 'ote', 'heatmap', 'oi', 'footprint', 'rr']
    score = sum(1 for k in keys if factors.get(k))
    return jsonify({
        'score': score,
        'total': 10,
        'valid': score >= 4,
        'grade': _grade(score),
    })


def _grade(s):
    if s >= 8: return 'A+ (Confluence максимальная)'
    if s >= 6: return 'A (Хороший вход)'
    if s >= 4: return 'B (Приемлемо, но не идеально)'
    if s >= 2: return 'C (Слабый вход)'
    return 'D (Не входить)'


def _serve_json(name):
    try:
        p = config.DATA_LIVE / name
        if not p.exists():
            return jsonify({'error': 'file_not_found'}), 404
        return jsonify(json.loads(p.read_text(encoding='utf-8')))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Portfolio Metrics API ──
METRICS_JSON = config.ROOT / 'data' / 'tradeLLm' / 'candle_full_metrics_extended.json'
CARD_DIR = config.DATA_CARD  # projects/01_fundament_rf/data/card/


@bp.route('/portfolio')
def portfolio():
    """Serve full portfolio metrics (245 fields x 12 trades)."""
    try:
        if METRICS_JSON.exists():
            return jsonify(json.loads(METRICS_JSON.read_text(encoding='utf-8')))
        return jsonify({'error': 'metrics_file_not_found', 'hint': 'Run generate_metrics.py'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/portfolio/candles/<symbol>')
def portfolio_candles(symbol):
    """Serve candle history for a symbol from _1D.json."""
    try:
        if not CARD_DIR.exists():
            return jsonify({'error': 'card_dir_not_found'}), 404

        for d in CARD_DIR.iterdir():
            if not d.is_dir() or d.name.startswith('UNKNOWN') or d.name == 'ETH':
                continue
            for fname in d.iterdir():
                if fname.name.endswith('_1D.json'):
                    try:
                        data = json.loads(fname.read_text(encoding='utf-8'))
                        if data.get('symbol', '').upper() == symbol.upper():
                            return jsonify({
                                'symbol': data['symbol'],
                                'granularity': data.get('granularity', '1D'),
                                'candles': data.get('candles', []),
                                'count': data.get('count', len(data.get('candles', []))),
                            })
                    except:
                        continue
        return jsonify({'error': 'no_candles_found', 'symbol': symbol}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
