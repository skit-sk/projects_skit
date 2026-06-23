"""Knowledge Base routes for Sandbox."""
import os
from pathlib import Path
from flask import Blueprint, render_template, abort, send_from_directory

bp = Blueprint('kb', __name__, url_prefix='/kb')

KB_DIR = Path('/home/user_aioc/workspace/share/knowledge-base')


def _list_kb_articles():
    """List all KB articles grouped by category."""
    categories = {}
    if not KB_DIR.exists():
        return categories
    for subdir in sorted(KB_DIR.iterdir()):
        if not subdir.is_dir():
            continue
        articles = []
        for f in sorted(subdir.glob('*.md')):
            articles.append({'name': f.stem, 'path': f.relative_to(KB_DIR).as_posix()})
        if articles:
            categories[subdir.name] = articles
    return categories


@bp.route('/')
def index():
    categories = _list_kb_articles()
    return render_template('sandbox/kb.html', categories=categories)


@bp.route('/view/<path:path>')
def view(path):
    file_path = KB_DIR / path
    if not file_path.exists() or not file_path.is_file():
        abort(404)
    return send_from_directory(KB_DIR, path)
