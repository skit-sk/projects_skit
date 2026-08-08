"""Main routes: dashboard, navigation."""
from flask import Blueprint, render_template, redirect, url_for
from pathlib import Path
import json
import config

bp = Blueprint('main', __name__)


def _load_live_totals():
    """Load live totals from account/totals.json."""
    try:
        p = config.DATA_LIVE / 'totals.json'
        if p.exists():
            return json.loads(p.read_text())
    except Exception:
        pass
    return {}


def _list_chapters():
    """List textbook chapters."""
    chapters = []
    textbook = config.CONTENT_DIR / 'textbook'
    if not textbook.exists():
        return chapters
    for f in sorted(textbook.glob('*.md')):
        slug = f.stem
        title = slug.split('_', 1)[1].replace('_', ' ').title() if '_' in slug else slug
        chapters.append({'slug': slug, 'title': title, 'num': slug.split('_')[0]})
    return chapters


@bp.route('/')
def index():
    totals = _load_live_totals()
    chapters = _list_chapters()
    return render_template('index.html', totals=totals, chapters=chapters)


@bp.route('/healthz')
def healthz():
    return {'status': 'ok', 'app': 'tradehelp'}


@bp.route('/favicon.ico')
def favicon():
    return '', 204
