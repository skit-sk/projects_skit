import json
from flask import Blueprint, request, jsonify, render_template
from viz_lab.services.model_catalog import get_catalog

bp = Blueprint('ai_models', __name__, url_prefix='/ai-models')

@bp.route('/')
def index():
    return render_template('ai_models/index.html')


@bp.route('/api/catalog')
def api_catalog():
    force = request.args.get('force', '').lower() == 'true'
    cat = get_catalog().get_catalog(force_refresh=force)
    return jsonify(cat)


@bp.route('/api/refresh/json', methods=['POST'])
def refresh_json():
    cat = get_catalog().refresh_from_json()
    return jsonify({'status': 'ok', 'updated': cat.get('updated', ''),
                    'stats': cat.get('stats', {})})


@bp.route('/api/refresh/online', methods=['POST'])
def refresh_online():
    data = request.get_json() or {}
    provider_id = data.get('provider_id')
    results = get_catalog().refresh_online(provider_id=provider_id)
    return jsonify({'status': 'completed', 'results': results})


@bp.route('/api/providers')
def api_providers():
    providers = get_catalog().get_providers()
    return jsonify({'providers': providers, 'count': len(providers)})


@bp.route('/api/providers/<provider_id>')
def api_provider(provider_id):
    p = get_catalog().get_provider(provider_id)
    if not p:
        return jsonify({'error': 'Provider not found'}), 404
    return jsonify(p)


@bp.route('/api/providers/test', methods=['POST'])
def api_test_provider():
    data = request.get_json() or {}
    url = data.get('url', '')
    api_key = data.get('api_key', '')
    result = get_catalog().test_connection(url, api_key)
    return jsonify(result)


@bp.route('/api/providers/sync', methods=['POST'])
def api_sync_provider():
    config = request.get_json() or {}
    if not config.get('id'):
        return jsonify({'error': 'provider id required'}), 400
    result = get_catalog().sync_custom_provider(config)
    return jsonify(result)


@bp.route('/api/models')
def api_models():
    provider_id = request.args.get('provider_id')
    model_type = request.args.get('type')
    search = request.args.get('search', '')
    limit = int(request.args.get('limit', 100))
    models = get_catalog().get_models(provider_id=provider_id,
                                       model_type=model_type,
                                       search=search)
    return jsonify({'models': models[:limit], 'total': len(models),
                    'returned': min(limit, len(models))})


@bp.route('/api/stats')
def api_stats():
    stats = get_catalog().get_stats()
    return jsonify(stats)
