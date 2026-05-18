from flask import Blueprint, jsonify, render_template, abort
from storage import get_storage
from infographics.trade_analyzer import TradeAnalyzer
from infographics.charts import DashboardCharts

bp = Blueprint('trade_analytics', __name__, template_folder='../templates', url_prefix='/trade-analytics')

charts_engine = DashboardCharts()


def _find_obj():
    storage = get_storage()
    objs = storage.list()
    for obj in objs:
        symbol = obj.data.get('emoji_entry', {}).get('symbol', '')
        if symbol and storage.exists_1d(symbol, obj.id) and storage.exists_raw(symbol, obj.id):
            return obj
    for obj in objs:
        symbol = obj.data.get('emoji_entry', {}).get('symbol', '')
        if symbol and storage.exists_1d(symbol, obj.id):
            return obj
    return objs[0] if objs else None


@bp.route('/')
def index():
    obj = _find_obj()
    if not obj:
        return '<h2>No trade data found</h2>'
    symbol = obj.data.get('emoji_entry', {}).get('symbol', '')
    objects_list = _get_objects_list()
    return render_template('trade_analytics.html', obj=obj, symbol=symbol, objects=objects_list)


@bp.route('/dashboard/<obj_id>')
def dashboard(obj_id):
    storage = get_storage()
    try:
        obj = storage.load(obj_id)
    except FileNotFoundError:
        abort(404)
    symbol = obj.data.get('emoji_entry', {}).get('symbol', '')
    objects_list = _get_objects_list()
    return render_template('trade_analytics.html', obj=obj, symbol=symbol, objects=objects_list)


def _get_objects_list():
    storage = get_storage()
    objs = storage.list()
    result = []
    for obj in objs:
        d = obj.data.get('emoji_entry', {})
        result.append({
            'id': obj.id,
            'name': obj.name,
            'symbol': d.get('symbol', '?'),
            'has_1d': storage.exists_1d(d.get('symbol', ''), obj.id) if d.get('symbol') else False,
            'has_raw': storage.exists_raw(d.get('symbol', ''), obj.id) if d.get('symbol') else False,
        })
    return result


@bp.route('/api/list')
def api_list():
    return jsonify(_get_objects_list())


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

    if not storage.exists_1d(symbol, obj_id) or not storage.exists_raw(symbol, obj_id):
        return jsonify({'error': '1D or RAW data not found for this object'}), 404

    analyzer = TradeAnalyzer(storage)
    try:
        report = analyzer.generate_report(symbol, obj_id)
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
