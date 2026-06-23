import json
import subprocess
from flask import Blueprint, render_template, jsonify, abort, request, Response
from services.health_aggregator import check_all, tail_log, load_registry

bp = Blueprint('sandbox', __name__, url_prefix='/sandbox')


# ── Command whitelist for start/stop/restart ────────────────────────
PROJECT_COMMANDS = {
    '02': {
        'start':   ['./scripts/flask.sh', 'start', '02', '5005'],
        'stop':    ['./scripts/flask.sh', 'stop', '02'],
        'restart': ['./scripts/flask.sh', 'restart', '02', '5005'],
    },
    '03': {
        'start':   ['./scripts/flask.sh', 'start', '03', '5003'],
        'stop':    ['./scripts/flask.sh', 'stop', '03'],
        'restart': ['./scripts/flask.sh', 'restart', '03', '5003'],
    },
    '07': {
        'start':   ['./scripts/tg_bot.sh', 'start'],
        'stop':    ['./scripts/tg_bot.sh', 'stop'],
        'restart': ['./scripts/tg_bot.sh', 'restart'],
    },
    '10': {
        'start':   ['./projects/10_max_bot/scripts/max_bot.sh', 'start'],
        'stop':    ['./projects/10_max_bot/scripts/max_bot.sh', 'stop'],
        'restart': ['./projects/10_max_bot/scripts/max_bot.sh', 'restart'],
    },
}


@bp.route('/')
def index():
    registry = load_registry()
    projects = registry.get('projects', {})
    return render_template('sandbox/index.html', projects=projects)


@bp.route('/project/<project_id>/')
def project(project_id):
    registry = load_registry()
    project = registry.get('projects', {}).get(project_id)
    if not project:
        abort(404)
    return render_template('sandbox/project.html', project_id=project_id, project=project)


@bp.route('/health')
def health_page():
    return render_template('sandbox/health.html')


@bp.route('/api/health')
def api_health():
    return jsonify(check_all())


@bp.route('/api/registry')
def api_registry():
    registry = load_registry()
    return jsonify(registry)


@bp.route('/logs/<project_id>')
def logs(project_id):
    n = request.args.get('n', 50, type=int)
    if n > 500:
        n = 500
    content = tail_log(project_id, n)
    if content is None:
        abort(404)
    return Response(content, mimetype='text/plain; charset=utf-8')


# ── Project control API ─────────────────────────────────────────────

@bp.route('/api/<project_id>/start', methods=['POST'])
def start_project(project_id):
    return _run_control(project_id, 'start')


@bp.route('/api/<project_id>/stop', methods=['POST'])
def stop_project(project_id):
    return _run_control(project_id, 'stop')


@bp.route('/api/<project_id>/restart', methods=['POST'])
def restart_project(project_id):
    return _run_control(project_id, 'restart')


def _run_control(project_id: str, action: str):
    if project_id == '01':
        return jsonify({'error': 'Cannot control the host project (01)'}), 403

    commands = PROJECT_COMMANDS.get(project_id, {})
    cmd = commands.get(action)
    if not cmd:
        return jsonify({'error': f'Action {action} not available for project {project_id}'}), 400

    try:
        result = subprocess.run(
            cmd,
            cwd='/home/user_aioc/workspace',
            capture_output=True,
            text=True,
            timeout=30
        )
        return jsonify({
            'status': 'ok',
            'action': action,
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        })
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Command timed out'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── TradingView Playground routes ───────────────────────────────────

@bp.route('/tv-playground/')
def tv_playground():
    from services.tv_playground import get_default_params, DEFAULT_WIDGET
    widget = request.args.get('widget') or DEFAULT_WIDGET
    defaults = get_default_params(widget)
    return render_template('sandbox/tv_playground.html', widget=widget, defaults=defaults)


@bp.route('/api/tv-playground/config', methods=['POST'])
def tv_playground_config():
    from services.tv_playground import render_widget
    data = request.get_json() or {}
    widget = data.get('widget', '')
    params = data.get('params', {})
    result = render_widget(widget, params)
    return jsonify(result)


@bp.route('/tv-playground/preview')
def tv_playground_preview():
    """Return rendered preview HTML for iframe src."""
    from services.tv_playground import render_widget, DEFAULT_WIDGET
    widget = request.args.get('widget') or DEFAULT_WIDGET
    params = {
        'symbol': request.args.get('symbol', 'BTCUSDT'),
        'interval': request.args.get('interval', '1D'),
        'theme': request.args.get('theme', 'dark'),
        'seriesType': request.args.get('seriesType', 'candlestick'),
        'active_sources': request.args.getlist('active_sources') or ['binance', 'bitget', 'yahoo', 'synthetic'],
        'limit': request.args.get('limit', 200, type=int),
    }
    result = render_widget(widget, params)
    if result.get('error'):
        return result['error'], 404
    return Response(result['html'], mimetype='text/html')


@bp.route('/api/tv-playground/data')
def tv_playground_data():
    from services.market_data_provider import fetch_ohlcv
    symbol = request.args.get('symbol', 'BTCUSDT')
    interval = request.args.get('interval', '1D')
    limit = request.args.get('limit', 200, type=int)
    active_sources = request.args.getlist('source') or ['binance', 'bitget', 'yahoo', 'synthetic']
    result = fetch_ohlcv(symbol, interval, limit, active_sources)
    return jsonify(result)


@bp.route('/api/tv-playground/execute', methods=['POST'])
def tv_playground_execute():
    from services.code_sandbox import execute_code
    data = request.get_json() or {}
    code = data.get('code', '')
    libraries = data.get('libraries', [])
    result = execute_code(code, libraries)
    return jsonify(result)
