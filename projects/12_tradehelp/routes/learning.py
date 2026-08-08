"""Learning routes: textbook chapters."""
from flask import Blueprint, render_template, abort, redirect, url_for
from pathlib import Path
import re
import config

bp = Blueprint('learning', __name__)


def _list_chapters():
    textbook = config.CONTENT_DIR / 'textbook'
    chapters = []
    if not textbook.exists():
        return chapters
    for f in sorted(textbook.glob('*.md')):
        slug = f.stem
        # parse "NN_title" pattern
        m = re.match(r'^(\d+)_(.+)$', slug)
        if m:
            num, rest = m.group(1), m.group(2)
            title = rest.replace('_', ' ').title()
        else:
            num, title = '00', slug
        # try to extract H1 from file
        first_line = ''
        try:
            with open(f) as fh:
                for line in fh:
                    line = line.strip()
                    if line.startswith('# '):
                        first_line = line[2:].strip()
                        break
        except Exception:
            pass
        if first_line:
            title = first_line
        chapters.append({'slug': slug, 'title': title, 'num': num})
    return chapters


@bp.route('/')
def index():
    chapters = _list_chapters()
    return render_template('learn.html', chapters=chapters)


@bp.route('/<slug>')
def chapter(slug):
    textbook = config.CONTENT_DIR / 'textbook'
    fpath = textbook / f'{slug}.md'
    if not fpath.exists() or not fpath.is_file():
        abort(404)
    try:
        content = fpath.read_text(encoding='utf-8')
    except Exception:
        abort(404)
    # extract title (first H1)
    title = slug
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('# '):
            title = line[2:].strip()
            break
    chapters = _list_chapters()
    cur_idx = next((i for i, c in enumerate(chapters) if c['slug'] == slug), 0)
    prev_ch = chapters[cur_idx - 1] if cur_idx > 0 else None
    next_ch = chapters[cur_idx + 1] if cur_idx < len(chapters) - 1 else None
    return render_template('learn_chapter.html',
                           slug=slug, title=title, content=content,
                           chapters=chapters, cur_idx=cur_idx,
                           prev_ch=prev_ch, next_ch=next_ch)
