import os
import time
import json
import inspect
from flask import Blueprint, jsonify, render_template, request, Response
from api.bitget_ws import BitgetWSStream

bp = Blueprint('ccxt_api', __name__, url_prefix='/ccxt-api')

CATEGORY_RULES = [
    ('Market Data', ['ohlcv', 'ticker', 'order_book', 'trades', 'markets', 'currencies', 'price', 'kline', 'candle']),
    ('Orders', ['order', 'cancel', 'edit']),
    ('Portfolio', ['balance', 'positions', 'position']),
    ('Account', ['deposit', 'withdraw', 'account', 'transaction', 'transfer']),
    ('Funding', ['funding', 'borrow', 'loan', 'interest', 'liquidation']),
    ('Convert', ['convert']),
    ('Greeks', ['greeks', 'option']),
]

PUBLIC_PREFIXES = [
    'fetch_ohlcv', 'fetch_ticker', 'fetch_trades', 'fetch_order_book',
    'fetch_markets', 'fetch_currencies', 'fetch_funding_rate',
    'fetch_public', 'fetch_contract_ohlcv',
]

AUTH_TOKENS = [
    'balance', 'position', 'order', 'deposit', 'withdraw',
    'create_', 'cancel_', 'edit_', 'transfer', 'account',
    'transaction', 'borrow', 'loan', 'liquidation',
]


def _is_auth_required(method_name):
    if any(method_name.startswith(p) for p in PUBLIC_PREFIXES):
        return False
    if any(t in method_name for t in AUTH_TOKENS):
        return True
    return True


def _get_env_key(key):
    val = os.environ.get(key, '')
    if not val:
        val = os.environ.get('BITGET_' + key, '')
    if val.startswith('"') or val.startswith("'"):
        val = val[1:-1]
    return val


@bp.route('/')
def index():
    return render_template('ccxt_api.html')


@bp.route('/api/exchanges')
def list_exchanges():
    import ccxt
    return jsonify(sorted(ccxt.exchanges))


@bp.route('/api/env-keys')
def env_keys():
    return jsonify({
        'api_key': _get_env_key('API_KEY'),
        'secret': _get_env_key('SECRET_KEY'),
        'passphrase': _get_env_key('PASSPHRASE'),
    })


@bp.route('/api/methods/<exchange_id>')
def get_methods(exchange_id):
    import ccxt
    if exchange_id not in ccxt.exchanges:
        return jsonify({'error': f'Exchange {exchange_id} not found'}), 404

    ex_class = getattr(ccxt, exchange_id)
    all_methods = set()

    for name in dir(ex_class):
        if name.startswith('_'):
            continue
        if not name.startswith(('fetch', 'create', 'cancel', 'edit', 'withdraw', 'watch')):
            continue
        try:
            obj = getattr(ex_class, name)
            if callable(obj):
                all_methods.add(name)
        except Exception:
            pass

    all_methods = sorted(all_methods)

    categorized = {}
    categorized_all = set()
    for cat_name, keywords in CATEGORY_RULES:
        cat_methods = []
        for m in all_methods:
            if any(kw in m for kw in keywords):
                cat_methods.append({'name': m, 'auth_required': _is_auth_required(m)})
        if cat_methods:
            categorized[cat_name] = cat_methods
            categorized_all.update(m['name'] for m in cat_methods)

    remaining = sorted(set(all_methods) - categorized_all)
    if remaining:
        categorized['Other'] = [{'name': m, 'auth_required': _is_auth_required(m)} for m in remaining]

    signatures = {}
    for m in all_methods:
        try:
            sig = inspect.signature(getattr(ex_class, m))
            sig_params = []
            for pname, param in sig.parameters.items():
                if pname == 'self' or pname == 'kwargs':
                    continue
                p = {'name': pname}
                if param.default is not inspect.Parameter.empty:
                    default = param.default
                    if isinstance(default, (dict, list)):
                        p['default'] = str(default)
                    else:
                        p['default'] = default
                if param.annotation is not inspect.Parameter.empty:
                    anno = str(param.annotation)
                    if anno.startswith("<class '") and anno.endswith("'>"):
                        anno = anno[8:-2]
                    p['annotation'] = anno
                sig_params.append(p)
            signatures[m] = sig_params
        except (ValueError, TypeError):
            signatures[m] = []

    return jsonify({
        'categories': categorized,
        'signatures': signatures,
    })


@bp.route('/api/docs/<exchange>/<method>')
def method_docs(exchange, method):
    import ccxt
    if exchange not in ccxt.exchanges:
        return jsonify({'error': 'Exchange not found'}), 404
    try:
        ex_class = getattr(ccxt, exchange)
        fn = getattr(ex_class, method)
        doc = fn.__doc__ or ''
        return jsonify({'docs': doc})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/ws-stream')
def ws_stream():
    method = request.args.get('method')
    params_raw = request.args.get('params', '{}')
    try:
        params = json.loads(params_raw)
    except json.JSONDecodeError:
        params = {}

    def generate():
        stream = BitgetWSStream(method, params)
        try:
            stream.connect(timeout=10)
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            return

        yield f"data: {json.dumps({'type': 'connected', 'method': method})}\n\n"

        while True:
            msg = stream.recv(timeout=15)
            if msg is None:
                yield f"data: {json.dumps({'type': 'timeout'})}\n\n"
                break
            yield f"data: {json.dumps({'type': 'message', 'data': msg})}\n\n"

        stream.close()

    return Response(generate(), mimetype='text/event-stream',
                    headers={
                        'Cache-Control': 'no-cache',
                        'X-Accel-Buffering': 'no',
                        'Connection': 'keep-alive',
                    })


@bp.route('/api/execute', methods=['POST'])
def execute_method():
    import ccxt
    data = request.json
    exchange_id = data.get('exchange', 'bitget')
    method = data.get('method')
    raw_params = data.get('params', {})

    if not exchange_id or not method:
        return jsonify({'error': 'Missing exchange or method'}), 400

    params = {}
    for k, v in raw_params.items():
        if v == '' or v is None:
            continue
        if k == 'since' and isinstance(v, str) and v and not v.isdigit():
            try:
                from datetime import datetime
                dt = datetime.strptime(v, '%Y-%m-%d')
                params[k] = int(dt.timestamp() * 1000)
            except ValueError:
                params[k] = v
        elif k == 'params' and isinstance(v, str):
            try:
                params[k] = json.loads(v) if v.strip() else {}
            except json.JSONDecodeError:
                params[k] = v
        else:
            try:
                if v == 'true':
                    params[k] = True
                elif v == 'false':
                    params[k] = False
                elif v == 'null':
                    params[k] = None
                elif '.' in v or 'e' in v.lower():
                    params[k] = float(v)
                else:
                    params[k] = int(v)
            except (ValueError, TypeError):
                params[k] = v

    t_gen_start = time.perf_counter()

    api_key = data.get('api_key') or _get_env_key('API_KEY')
    secret = data.get('secret') or _get_env_key('SECRET_KEY')
    passphrase = data.get('passphrase') or _get_env_key('PASSPHRASE')

    config = {'enableRateLimit': True}
    if api_key:
        config['apiKey'] = api_key
    if secret:
        config['secret'] = secret
    if passphrase:
        config['passphrase'] = passphrase
        config['password'] = passphrase

    try:
        ex = getattr(ccxt, exchange_id)(config)
    except Exception as e:
        return jsonify({'error': f'Failed to create exchange instance: {e}'}), 500

    last_url = None

    def capture_url(response, *args, **kwargs):
        nonlocal last_url
        last_url = response.request.url
        return response

    ex.session.hooks['response'].append(capture_url)

    t_gen_end = time.perf_counter()
    t_rtt_start = time.perf_counter()

    try:
        result = getattr(ex, method)(**params)
    except Exception as e:
        t_rtt_end = time.perf_counter()
        try:
            ex.session.hooks['response'].remove(capture_url)
        except ValueError:
            pass
        return jsonify({
            'error': str(e),
            'request_url': last_url,
            'timing': {
                'gen_ms': round((t_gen_end - t_gen_start) * 1000, 2),
                'rtt_ms': round((t_rtt_end - t_rtt_start) * 1000, 2),
                'total_ms': round((t_rtt_end - t_gen_start) * 1000, 2),
            },
        }), 500

    t_rtt_end = time.perf_counter()
    try:
        ex.session.hooks['response'].remove(capture_url)
    except ValueError:
        pass

    return jsonify({
        'request_url': last_url,
        'timing': {
            'gen_ms': round((t_gen_end - t_gen_start) * 1000, 2),
            'rtt_ms': round((t_rtt_end - t_rtt_start) * 1000, 2),
            'total_ms': round((t_rtt_end - t_gen_start) * 1000, 2),
        },
        'response': result,
    })
