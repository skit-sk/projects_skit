import datetime
import json
import re
import time
from collections import defaultdict
from flask import Blueprint, jsonify, render_template, request

from account import BitgetAccountClient

bp = Blueprint('account_api', __name__, url_prefix='/account-api')


def _get_client():
    return BitgetAccountClient()


def _fmt_time(ts):
    if not ts:
        return '-'
    return datetime.datetime.fromtimestamp(ts / 1000).strftime('%Y-%m-%d %H:%M')


def _fmt_dt(ts):
    if not ts:
        return '-'
    return datetime.datetime.fromtimestamp(ts / 1000).strftime('%Y-%m-%d')


def _fmt_num(v, decimals=2):
    try:
        return f"{v:,.{decimals}f}"
    except (ValueError, TypeError):
        return str(v)


SINCE_OPTIONS = {
    '7d': 7,
    '30d': 30,
    '90d': 90,
    '180d': 180,
    '365d': 365,
}


def _parse_since(since_str):
    if not since_str or since_str == 'all':
        return None
    days = SINCE_OPTIONS.get(since_str)
    if days:
        return int((time.time() - days * 86400) * 1000)
    return None


def _extract_schema(raw_response):
    data = raw_response.get('data', [])
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list) and v:
                data = v
                break
    if not isinstance(data, list) or not data:
        return []
    item = data[0] if data else {}
    return [{'field': k, 'type': type(v).__name__, 'sample': str(v)[:40]} for k, v in item.items()]


def _build_debug(client, endpoints):
    debug = []
    for ep, params in endpoints:
        raw = client.get_raw(ep, params)
        debug.append({'endpoint': ep, 'params': params, 'raw': raw, 'schema': _extract_schema(raw)})
    return debug


@bp.route('/')
def index():
    return render_template('account/index.html')


@bp.route('/api/status')
def api_status():
    client = _get_client()
    status = client.test_auth()
    return jsonify({
        'connected': status.connected,
        'server_time': status.server_time,
        'latency_ms': status.latency_ms,
        'error': status.error,
        'has_keys': client.has_credentials,
    })


@bp.route('/api/overview')
def api_overview():
    client = _get_client()
    if not client.has_credentials:
        return jsonify({'error': 'API keys not configured'}), 400
    overview = client.get_overview()
    return jsonify({
        'total_equity_usdt': overview.total_equity_usdt,
        'spot_total_usdt': overview.spot_total_usdt,
        'futures_equity_usdt': overview.futures_equity_usdt,
        'futures_unrealized_pl': overview.futures_unrealized_pl,
        'open_positions_count': overview.open_positions_count,
        'spot_assets': [{'coin': a.coin, 'total': a.total, 'available': a.available, 'frozen': a.frozen} for a in overview.spot_assets],
        'mix_accounts': [{'margin_coin': m.margin_coin, 'equity': m.equity, 'usdt_equity': m.usdt_equity, 'unrealized_pl': m.unrealized_pl} for m in overview.mix_accounts],
    })


@bp.route('/api/balance')
def api_balance():
    client = _get_client()
    if not client.has_credentials:
        return jsonify({'error': 'API keys not configured'}), 400
    spot = client.get_spot_assets()
    mix = client.get_mix_accounts()
    return jsonify({
        'spot': [{'coin': a.coin, 'total': a.total, 'available': a.available, 'frozen': a.frozen, 'locked': a.locked} for a in spot],
        'futures': [{'margin_coin': m.margin_coin, 'equity': m.equity, 'usdt_equity': m.usdt_equity, 'available': m.available, 'locked': m.locked, 'unrealized_pl': m.unrealized_pl, 'margin_mode': m.margin_mode} for m in mix],
    })


@bp.route('/api/positions')
def api_positions():
    client = _get_client()
    if not client.has_credentials:
        return jsonify({'error': 'API keys not configured'}), 400
    positions = client.get_positions()
    
    # fill_counts
    fill_data = client.fetch_all_fills(market='futures')
    fill_counts = {}
    for f in fill_data['fills']:
        fill_counts[f.symbol] = fill_counts.get(f.symbol, 0) + 1
    
    # order_counts
    order_counts = {}
    for o in client.get_mix_orders():
        order_counts[o.symbol] = order_counts.get(o.symbol, 0) + 1
    
    return jsonify({
        'positions': [{
            'number': i + 1,
            'symbol': p.symbol,
            'ticker': p.ticker,
            'margin_size': p.margin_size,
            'open_price_avg': p.open_price_avg,
            'current_price': p.current_price,
            'unrealized_pl': p.unrealized_pl,
            'pl_percent': p.pl_percent,
            'leverage': p.leverage,
            'liquidation_price': p.liquidation_price,
            'risk_to_liquidation': p.risk_to_liquidation,
            'profitable': p.is_profitable,
            'hold_side': p.hold_side,
            'days_open': p.days_open,
            'open_date': p.open_date,
        } for i, p in enumerate(positions)],
        'fill_counts': fill_counts,
        'order_counts': order_counts,
        'total_pl': sum(p.unrealized_pl for p in positions),
        'count': len(positions),
    })


@bp.route('/api/computed')
def api_computed():
    """Позиции с computed-полями (из хранения карточек)."""
    client = _get_client()
    if not client.has_credentials:
        return jsonify({'error': 'API keys not configured'}), 400
    from storage import get_storage
    from calculator import load_aggregate

    positions = client.get_positions()
    cards = get_storage().list()
    computed_map = {}
    for obj in cards:
        c = obj.data.get('computed', {})
        entry = obj.data.get('emoji_entry', {})
        sym = entry.get('symbol', '')
        if c and sym:
            computed_map[sym.upper()] = c

    result = []
    for p in positions:
        raw = {
            'symbol': p.symbol,
            'ticker': p.ticker,
            'margin_size': p.margin_size,
            'open_price_avg': p.open_price_avg,
            'current_price': p.current_price,
            'unrealized_pl': p.unrealized_pl,
            'pl_percent': p.pl_percent,
            'leverage': p.leverage,
            'liquidation_price': p.liquidation_price,
            'profitable': p.is_profitable,
            'hold_side': p.hold_side,
            'days_open': p.days_open,
            'open_date': p.open_date,
        }
        raw.update(computed_map.get(p.ticker.upper(), {}))
        result.append(raw)

    return jsonify({
        'positions': result,
        'totals': load_aggregate(),
        'count': len(result),
    })


@bp.route('/api/orders')
def api_orders():
    client = _get_client()
    if not client.has_credentials:
        return jsonify({'error': 'API keys not configured'}), 400
    spot_orders = client.get_spot_orders()
    mix_orders = client.get_mix_orders()
    return jsonify({
        'spot': [{
            'order_id': o.order_id,
            'symbol': o.symbol,
            'ticker': o.ticker,
            'price': o.price,
            'quantity': o.quantity,
            'order_type': o.order_type,
            'side': o.side,
            'status': o.status,
            'c_time': o.c_time,
            'filled_qty': o.filled_qty,
        } for o in spot_orders],
        'futures': [{
            'order_id': o.order_id,
            'symbol': o.symbol,
            'ticker': o.ticker,
            'price': o.price,
            'quantity': o.quantity,
            'order_type': o.order_type,
            'side': o.side,
            'status': o.status,
            'c_time': o.c_time,
            'filled_qty': o.filled_qty,
        } for o in mix_orders],
        'total_count': len(spot_orders) + len(mix_orders),
    })


@bp.route('/api/fills')
def api_fills():
    client = _get_client()
    if not client.has_credentials:
        return jsonify({'error': 'API keys not configured'}), 400
    since_str = request.args.get('since', 'all')
    market = request.args.get('market', 'all')
    limit = int(request.args.get('limit', 100))
    since = _parse_since(since_str)
    result = client.fetch_all_fills(market=market, since=since)
    return jsonify({
        'fills': [{
            'order_id': f.order_id,
            'symbol': f.symbol,
            'ticker': f.ticker,
            'price': f.price,
            'quantity': f.quantity,
            'filled_qty': f.filled_qty,
            'fee_ccy': f.fee_ccy,
            'fee_detail': f.fee_detail,
            'side': f.side,
            'c_time': f.c_time,
            'total_value': f.total_value,
            'market': f.market,
        } for f in result['fills'][:limit]],
        'spot_total': result['spot_total'],
        'futures_total': result['futures_total'],
        'grand_total': result['grand_total'],
    })


SORT_KEY_MAP = {
    'time': lambda f: f.c_time,
    'symbol': lambda f: f.symbol,
    'side': lambda f: f.side,
    'price': lambda f: f.price,
    'qty': lambda f: f.filled_qty,
    'value': lambda f: f.total_value,
    'profit': lambda f: f.profit,
    'fee': lambda f: f.fee_detail,
    'market': lambda f: f.market,
}


@bp.route('/partial/overview')
def partial_overview():
    from storage import get_storage
    cards = get_storage().list()
    total_pnl = 0
    open_pos = 0
    for obj in cards:
        lp = obj.data.get('live_position')
        if lp and lp.get('hold_side'):
            open_pos += 1
            total_pnl += lp.get('unrealized_pl', 0)

    balance_data = get_storage().load_balance()
    spot_assets = balance_data.get('spot', [])
    mix_accounts = balance_data.get('futures', [])
    spot_total = sum(a.get('total', 0) for a in spot_assets)
    futures_equity = sum(m.get('usdt_equity', m.get('equity', 0)) for m in mix_accounts)
    total_equity = spot_total + futures_equity

    return render_template('account/partials/overview.html', error='',
        status={'connected': True, 'server_time': datetime.datetime.now().isoformat(), 'latency_ms': 0, 'error': ''},
        overview={
            'open_positions_count': open_pos,
            'total_equity_usdt': total_equity,
            'spot_total_usdt': spot_total,
            'futures_equity_usdt': futures_equity,
            'futures_unrealized_pl': total_pnl,
            'spot_assets': spot_assets,
            'mix_accounts': mix_accounts,
        },
        fmt_num=_fmt_num, fmt_dt=_fmt_dt, debug=[])


@bp.route('/partial/balance')
def partial_balance():
    from storage import get_storage
    from collections import namedtuple

    SpotAsset = namedtuple('SpotAsset', ['coin', 'available', 'frozen', 'locked', 'total'])
    FuturesAccount = namedtuple('FuturesAccount', ['margin_coin', 'equity', 'usdt_equity', 'available', 'locked', 'unrealized_pl', 'unrealized_pl_ratio', 'margin_mode'])

    data = get_storage().load_balance()
    if not data:
        return render_template('account/partials/balance.html', error='Нажми "Sync Exchange" для загрузки баланса', spot=None, futures=None, debug=[])
    spot = [SpotAsset(**{k: a[k] for k in SpotAsset._fields if k in a}) if isinstance(a, dict) else a for a in data.get('spot', [])]
    futures = [FuturesAccount(**{k: m[k] for k in FuturesAccount._fields if k in m}) if isinstance(m, dict) else m for m in data.get('futures', [])]
    return render_template('account/partials/balance.html', error='', spot=spot, futures=futures, fmt_num=_fmt_num, debug=[])


def _load_fill_order_stats():
    """Load fill_counts, last_trade_days, order_counts from storage."""
    from storage import get_storage
    from collections import defaultdict

    fills_data = get_storage().load_fills()
    fill_counts = {}
    last_trade_days = {}
    if fills_data and fills_data.get('fills'):
        sym_fills = defaultdict(list)
        for f in fills_data['fills']:
            sym_fills[f.get('symbol', '')].append(f)
        for sym, symf in sym_fills.items():
            fill_counts[sym] = len(symf)
            symf.sort(key=lambda x: x.get('c_time', 0), reverse=True)
            if len(symf) >= 2:
                t1 = symf[0].get('c_time', 0)
                t2 = symf[1].get('c_time', 0)
                if t1 and t2:
                    last_trade_days[sym] = (t1 - t2) / 86400000
            elif symf:
                last_trade_days[sym] = None

    orders_data = get_storage().load_orders()
    order_counts = {}
    if orders_data:
        for o in orders_data.get('futures', []):
            sym = o.get('symbol', '')
            order_counts[sym] = order_counts.get(sym, 0) + 1
        for o in orders_data.get('spot', []):
            sym = o.get('symbol', '')
            order_counts[sym] = order_counts.get(sym, 0) + 1

    return fill_counts, last_trade_days, order_counts


@bp.route('/partial/positions')
def partial_positions():
    from storage import get_storage
    cards = get_storage().list()
    fill_counts, last_trade_days, order_counts = _load_fill_order_stats()
    positions = []
    position_card_data = []
    for obj in cards:
        entry = obj.data.get('emoji_entry', {})
        lp = obj.data.get('live_position')
        if not lp or not lp.get('hold_side'):
            continue
        ticker = entry.get('symbol', '')
        positions.append({
            "ticker": ticker,
            "symbol": ticker + 'USDT',
            "hold_side": lp.get('hold_side'),
            "leverage": lp.get('leverage', 10),
            "margin_size": lp.get('margin_size', 0),
            "total_coin": lp.get('total_coin', lp.get('margin_size', 0)),
            "unrealized_pl": lp.get('unrealized_pl', 0),
            "pl_percent": lp.get('pl_percent', 0),
            "mark_price": lp.get('mark_price', 0),
            "current_price": lp.get('mark_price', 0),
            "open_price_avg": entry.get('entry_price', 0),
            "days_open": lp.get('days_open', 0),
            "liquidation_price": lp.get('liquidation_price', 0),
            "risk_to_liquidation": lp.get('risk_to_liquidation', 0),
            "open_date": entry.get('entry_date', ''),
            "position_value_usdt": lp.get('position_value_usdt', lp.get('margin_size', 0) * float(lp.get('mark_price', 0))),
            "achieved_profits": entry.get('achieved_profits', lp.get('achieved_profits', 0)),
            "total_fee": entry.get('total_fee', lp.get('total_fee', 0)),
            "has_sl": bool(entry.get('sl_price') or lp.get('stop_loss_price', 0) > 0),
            "sl_distance_pct": lp.get('sl_distance_pct', 0),
            "has_tp": bool(entry.get('tp_price') or lp.get('take_profit_price', 0) > 0),
            "tp_distance_pct": lp.get('tp_distance_pct', 0),
        })
        position_card_data.append({
            "number": entry.get('number', ''),
            "symbol": entry.get('symbol', ''),
            "deviation_pct": obj.data.get('deviation_pct', []),
            "entry_price": entry.get('entry_price', ''),
            "entry_date": entry.get('entry_date', ''),
            "entry_time": entry.get('entry_time', 0),
            "volume": entry.get('volume', 0),
            "pnl_percent": entry.get('pnl_percent', 0),
            "pnl_usdt": entry.get('pnl_usdt', 0),
            "result": entry.get('result', ''),
            "close_prices": obj.data.get('close_prices', []),
        })
    return render_template('account/partials/positions.html', error='', positions=positions,
        fill_counts=fill_counts, last_trade_days=last_trade_days, order_counts=order_counts,
        position_card_data=position_card_data, fmt_num=_fmt_num, debug=[])


@bp.route('/partial/positions_live')
def partial_positions_live():
    """Live positions from Bitget exchange (for Live mode)."""
    import time as _t
    _t_start = _t.time()
    try:
        client = _get_client()
        fill_counts, last_trade_days, order_counts = _load_fill_order_stats()
        positions = client.get_positions()
        _t_api = _t.time()
        positions_raw = [{
            "symbol": p.symbol,
            "ticker": p.ticker,
            "hold_side": p.hold_side,
            "margin_size": p.margin_size,
            "total_coin": p.total_coin,
            "open_price_avg": p.open_price_avg,
            "mark_price": p.mark_price,
            "current_price": p.mark_price,
            "unrealized_pl": p.unrealized_pl,
            "pl_percent": p.pl_percent,
            "leverage": p.leverage,
            "liquidation_price": p.liquidation_price,
            "risk_to_liquidation": p.risk_to_liquidation,
            "position_value_usdt": p.position_value_usdt,
            "achieved_profits": p.achieved_profits,
            "total_fee": p.total_fee,
            "has_sl": p.stop_loss_price > 0,
            "sl_distance_pct": abs((p.current_price - p.stop_loss_price) / p.current_price * 100) if p.stop_loss_price > 0 else 0,
            "has_tp": p.take_profit_price > 0,
            "tp_distance_pct": abs((p.take_profit_price - p.current_price) / p.current_price * 100) if p.take_profit_price > 0 else 0,
            "days_open": p.days_open,
            "open_date": p.open_date or '',
        } for p in positions]
        card_data = [{
            "number": i + 1,
            "symbol": p.symbol,
            "deviation_pct": [],
            "entry_price": p.open_price_avg,
            "entry_date": "",
            "volume": p.margin_size,
        } for i, p in enumerate(positions)]
        _t_render = _t.time()
        timings = {
            "api_ms": int((_t_api - _t_start) * 1000),
            "render_ms": int((_t_render - _t_api) * 1000),
            "total_ms": int((_t_render - _t_start) * 1000),
        }
        return render_template('account/partials/positions.html', error='',
            positions=positions_raw, position_card_data=card_data,
            fill_counts=fill_counts, last_trade_days=last_trade_days, order_counts=order_counts,
            fmt_num=_fmt_num, debug=[], timings=timings)
    except Exception as e:
        import traceback
        return render_template('account/partials/positions.html', error=f'Live error: {e}',
            positions=None, position_card_data=None,
            fill_counts={}, last_trade_days={}, order_counts={},
            fmt_num=_fmt_num, debug=traceback.format_exc())


@bp.route('/partial/orders')
def partial_orders():
    from storage import get_storage
    from collections import namedtuple

    SpotOrder = namedtuple('SpotOrder', ['order_id', 'symbol', 'ticker', 'price', 'quantity', 'order_type', 'side', 'status', 'c_time', 'filled_qty'])
    MixOrder = namedtuple('MixOrder', ['order_id', 'symbol', 'price', 'quantity', 'order_type', 'side', 'status', 'c_time', 'filled_qty'])

    data = get_storage().load_orders()
    if not data:
        return render_template('account/partials/orders.html', error='Нажми "Sync Exchange" для загрузки ордеров', spot=None, futures=None, debug=[])
    spot = [SpotOrder(**{k: o[k] for k in SpotOrder._fields if k in o}) if isinstance(o, dict) else o for o in data.get('spot', [])]
    futures = [MixOrder(**{k: o[k] for k in MixOrder._fields if k in o}) if isinstance(o, dict) else o for o in data.get('futures', [])]
    return render_template('account/partials/orders.html', error='', spot=spot, futures=futures, fmt_num=_fmt_num, fmt_time=_fmt_time, debug=[])


@bp.route('/partial/fills')
def partial_fills():
    symbol = request.args.get('symbol', '')
    market = request.args.get('market', 'all')
    since = request.args.get('since', 'all')
    limit = int(request.args.get('limit', 100))
    sort_by = request.args.get('sort_by', 'time')
    sort_dir = request.args.get('sort_dir', 'desc')
    trade_side = request.args.get('trade_side', 'all')

    # Load from JSON storage (synced by "Sync Exchange" button)
    from storage import get_storage
    stored = get_storage().load_fills()
    if stored and stored.get('fills'):
        from account.models import Fill
        fills_raw = [Fill(**f) for f in stored['fills']]
        all_fills = list(fills_raw)
        spot_total = stored.get('spot_total', 0)
        futures_total = stored.get('futures_total', 0)
        grand_total = stored.get('grand_total', 0)
    else:
        client = _get_client()
        if not client.has_credentials:
            return render_template('account/partials/fills.html', error='API keys not configured', fills=None, debug=[])
        start_time = _parse_since(since)
        result = client.fetch_all_fills(market='all', since=start_time)
        fills_raw = result['fills']
        all_fills = list(fills_raw)
        spot_total = result['spot_total']
        futures_total = result['futures_total']
        grand_total = result['grand_total']

    if symbol:
        all_fills = [f for f in all_fills if f.symbol == symbol]
    if market == 'spot':
        all_fills = [f for f in all_fills if f.market == 'spot']
    elif market == 'futures':
        all_fills = [f for f in all_fills if f.market == 'futures']
    if trade_side == 'open':
        all_fills = [f for f in all_fills if f.trade_side == 'open']
    elif trade_side == 'close':
        all_fills = [f for f in all_fills if f.trade_side == 'close']

    key_fn = SORT_KEY_MAP.get(sort_by, SORT_KEY_MAP['time'])
    all_fills.sort(key=key_fn, reverse=(sort_dir == 'desc'))

    total_filtered = len(all_fills)
    displayed = all_fills[:limit]

    unique_symbols = sorted(set(f.symbol for f in fills_raw))

    now_ms = int(time.time() * 1000)
    duration_map = {}
    pnl_pct_map = {}

    fills_by_sym = {}
    for f in fills_raw:
        fills_by_sym.setdefault(f.symbol, []).append(f)
    for sym, sym_fills in fills_by_sym.items():
        sym_fills.sort(key=lambda x: x.c_time)
        last_open_ts = None
        for f in sym_fills:
            if f.trade_side == 'open':
                last_open_ts = f.c_time
            elif f.trade_side == 'close' and last_open_ts:
                duration_map[(sym, f.c_time)] = f.c_time - last_open_ts
                if f.quote_volume:
                    pnl_pct_map[(sym, f.c_time)] = (f.profit / f.quote_volume) * 100

    if stored and stored.get('fills'):
        debug = []
    else:
        debug = _build_debug(client, [
            ('/api/v2/mix/order/fills', {'productType': 'USDT-FUTURES', 'limit': '100'}),
            ('/api/v2/spot/trade/fills', {'limit': '100'}),
        ])

    DEFAULT_LEVERAGE = 10
    margin_usdt_map = {}

    agg = defaultdict(lambda: {'count': 0, 'buys': 0, 'sells': 0,
        'total_qty': 0.0, 'total_value': 0.0, 'total_quote_volume': 0.0,
        'total_margin_usdt': 0.0,
        'total_profit': 0.0, 'total_fee': 0.0, 'price_sum': 0.0,
        'total_duration_ms': 0, 'pnl_pct_sum': 0.0, 'pnl_pct_count': 0})

    for f in all_fills:
        key = f.ticker
        mu = f.quote_volume / DEFAULT_LEVERAGE
        margin_usdt_map[(f.symbol, f.c_time)] = mu
        agg[key]['count'] += 1
        if f.side == 'buy':
            agg[key]['buys'] += 1
        else:
            agg[key]['sells'] += 1
        agg[key]['total_qty'] += f.filled_qty
        agg[key]['total_value'] += f.total_value
        agg[key]['total_quote_volume'] += f.quote_volume
        agg[key]['total_margin_usdt'] += mu
        agg[key]['total_profit'] += f.profit
        agg[key]['total_fee'] += f.fee_detail
        agg[key]['price_sum'] += f.price
        dur = duration_map.get((f.symbol, f.c_time))
        if dur:
            agg[key]['total_duration_ms'] += dur
        pp = pnl_pct_map.get((f.symbol, f.c_time))
        if pp is not None:
            agg[key]['pnl_pct_sum'] += pp
            agg[key]['pnl_pct_count'] += 1

    for k, v in agg.items():
        v['avg_price'] = v['price_sum'] / v['count'] if v['count'] else 0
        v['avg_pnl_pct'] = v['pnl_pct_sum'] / v['pnl_pct_count'] if v['pnl_pct_count'] else None

    agg_total = {
        'count': sum(v['count'] for v in agg.values()),
        'buys': sum(v['buys'] for v in agg.values()),
        'sells': sum(v['sells'] for v in agg.values()),
        'total_qty': sum(v['total_qty'] for v in agg.values()),
        'total_value': sum(v['total_value'] for v in agg.values()),
        'total_quote_volume': sum(v['total_quote_volume'] for v in agg.values()),
        'total_margin_usdt': sum(v['total_margin_usdt'] for v in agg.values()),
        'total_profit': sum(v['total_profit'] for v in agg.values()),
        'total_fee': sum(v['total_fee'] for v in agg.values()),
        'total_duration_ms': sum(v['total_duration_ms'] for v in agg.values()),
        'avg_pnl_pct': sum(v['pnl_pct_sum'] for v in agg.values()) / max(sum(v['pnl_pct_count'] for v in agg.values()), 1),
    }

    return render_template('account/partials/fills.html',
        fills=displayed,
        spot_total=spot_total,
        futures_total=futures_total,
        grand_total=grand_total,
        total_filtered=total_filtered,
        unique_symbols=unique_symbols,
        duration_map=duration_map,
        pnl_pct_map=pnl_pct_map,
        margin_usdt_map=margin_usdt_map,
        aggregated=dict(agg),
        agg_total=agg_total,
        request_params=request.args.to_dict(),
        sort_by=sort_by, sort_dir=sort_dir,
        error='',
        fmt_num=_fmt_num,
        fmt_time=_fmt_time,
        debug=debug,
    )
