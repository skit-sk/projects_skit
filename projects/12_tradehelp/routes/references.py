"""References route: track and analyze external trading tools."""
from flask import Blueprint, render_template, jsonify, request
import json
from pathlib import Path

bp = Blueprint('references', __name__, url_prefix='/references')

DATA_FILE = Path(__file__).resolve().parent.parent / 'data' / 'references.json'


def _load():
    try:
        return json.loads(DATA_FILE.read_text(encoding='utf-8'))
    except Exception:
        return []


def _save(data):
    DATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


@bp.route('/')
def index():
    return render_template('references.html')


@bp.route('/api/list')
def api_list():
    return jsonify(_load())


@bp.route('/api/add', methods=['POST'])
def api_add():
    data = _load()
    body = request.get_json(force=True)
    ref = {
        'id': body.get('id', '').strip().lower().replace(' ', '-') or str(len(data) + 1),
        'url': body.get('url', '').strip(),
        'title': body.get('title', '').strip(),
        'status': 'added',
        'category': body.get('category', 'other'),
        'priority': body.get('priority', 'P3'),
        'description': body.get('description', ''),
        'mechanism': '',
        'screenshot': '',
        'elements': [],
        'notes': ''
    }
    if not ref['url'] or not ref['title']:
        return jsonify({'error': 'url and title required'}), 400
    data.append(ref)
    _save(data)
    return jsonify(ref)


@bp.route('/api/update', methods=['POST'])
def api_update():
    data = _load()
    body = request.get_json(force=True)
    for ref in data:
        if ref['id'] == body.get('id'):
            for key in ('status', 'description', 'mechanism', 'notes', 'priority', 'category'):
                if key in body:
                    ref[key] = body[key]
            if 'elements' in body:
                ref['elements'] = body['elements']
            _save(data)
            return jsonify(ref)
    return jsonify({'error': 'not found'}), 404


@bp.route('/api/delete', methods=['POST'])
def api_delete():
    data = _load()
    body = request.get_json(force=True)
    data[:] = [r for r in data if r['id'] != body.get('id')]
    _save(data)
    return jsonify({'ok': True})
