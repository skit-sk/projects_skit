from flask import Blueprint, jsonify, render_template, abort, request
from storage import get_storage
from infographics.trade_analyzer import TradeAnalyzer
from api.ma_data import load_or_fetch_candles, MADataLoader

bp = Blueprint('ma_analytics', __name__, template_folder='../templates', url_prefix='/ma-analytics')

analyzer = TradeAnalyzer()


@bp.route('/')
def index():
    storage = get_storage()
    objs = storage.list()
    if not objs:
        return '<h2>No trade data found</h2>'
    return render_template('ma_analytics.html', obj=objs[0], symbol='')


@bp.route('/<obj_id>')
def analytics_page(obj_id):
    storage = get_storage()
    try:
        obj = storage.load(obj_id)
    except FileNotFoundError:
        abort(404)
    symbol = obj.data.get('emoji_entry', {}).get('symbol', '')
    return render_template('ma_analytics.html', obj=obj, symbol=symbol)


@bp.route('/api/<obj_id>')
def api_data(obj_id):
    storage = get_storage()
    try:
        obj = storage.load(obj_id)
    except FileNotFoundError:
        return jsonify({'error': 'Object not found'}), 404

    symbol = obj.data.get('emoji_entry', {}).get('symbol', '')
    if not symbol:
        return jsonify({'error': 'Symbol not found'}), 400

    refresh = request.args.get('refresh', '0') == '1'
    if refresh or not storage.exists_raw(symbol, obj_id):
        try:
            loader = MADataLoader()
            loader.fetch_and_save(symbol, obj_id, 500)
        except Exception as e:
            return jsonify({'error': f'Data fetch failed: {e}'}), 500

    try:
        report = analyzer.compute_ma_analysis(symbol, obj_id)
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/screener')
def screener():
    storage = get_storage()
    objs = storage.list()
    results = []

    for obj in objs:
        symbol = obj.data.get('emoji_entry', {}).get('symbol', '')
        if not symbol:
            continue
        if not storage.exists_1d(symbol, obj.id) or not storage.exists_raw(symbol, obj.id):
            continue
        try:
            report = analyzer.compute_ma_analysis(symbol, obj.id)
            sig = report.get('signals', {})
            results.append({
                'symbol': symbol,
                'obj_id': obj.id,
                'current_price': sig.get('current_price', 0),
                'composite_signal': sig.get('composite', 'neutral'),
                'confidence': sig.get('overall_confidence', 0),
                'bullish_signals': sig.get('bullish_signals', 0),
                'bearish_signals': sig.get('bearish_signals', 0),
            })
        except Exception:
            pass

    return jsonify(results)


@bp.route('/fetch/<obj_id>', methods=['POST'])
def fetch_history(obj_id):
    storage = get_storage()
    try:
        obj = storage.load(obj_id)
    except FileNotFoundError:
        return jsonify({'error': 'Object not found'}), 404

    symbol = obj.data.get('emoji_entry', {}).get('symbol', '')
    if not symbol:
        return jsonify({'error': 'Symbol not found'}), 400

    limit = request.json.get('limit', 500) if request.is_json else 500
    try:
        loader = MADataLoader()
        data = loader.fetch_and_save(symbol, obj_id, limit)
        return jsonify({'status': 'ok', 'candles_fetched': len(data.get('candles', []))})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
