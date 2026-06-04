import json
import os
import uuid
import mimetypes
import asyncio
import time
from pathlib import Path
from flask import Blueprint, request, jsonify, render_template, send_file
from viz_lab.storage.session import get_store
from viz_lab.provider.registry import get_registry
from viz_lab.services.analyzer import get_analyzer, DataProfile
from viz_lab.services.selector import get_selector
from viz_lab.services.transcriber import get_transcriber
from urllib.parse import urlparse

bp = Blueprint('viz_lab', __name__, url_prefix='/viz-lab')

WORKSPACE_ROOT = Path(__file__).parent.parent.parent.parent
ALLOWED_EXTENSIONS = {'csv', 'json', 'xlsx', 'xls', 'png', 'jpg', 'jpeg', 'gif', 'svg', 'txt', 'md', 'py', 'js', 'html', 'css', 'xml', 'yaml', 'yml', 'toml', 'ini', 'cfg', 'log'}
MAX_UPLOAD_SIZE = 50 * 1024 * 1024

# Initialize providers on import
_providers_initialized = False


def _ensure_providers():
    global _providers_initialized
    if not _providers_initialized:
        get_registry().init_defaults()
        _providers_initialized = True


@bp.route('/')
def index():
    return render_template('viz_lab/lab.html')


@bp.route('/api/sessions', methods=['GET'])
def list_sessions():
    store = get_store()
    sessions = store.list_all()
    return jsonify({'sessions': sessions, 'count': len(sessions)})


@bp.route('/api/session', methods=['POST'])
def create_session():
    store = get_store()
    session_id = store.create()
    return jsonify({'session_id': session_id})


@bp.route('/api/session/<session_id>', methods=['GET', 'DELETE'])
def handle_session(session_id):
    store = get_store()
    if request.method == 'DELETE':
        ok = store.delete_session(session_id)
        if not ok:
            return jsonify({'error': 'Session not found'}), 404
        return jsonify({'status': 'deleted'})
    session = store.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    return jsonify(session)


@bp.route('/api/session/<session_id>/projects', methods=['GET'])
def list_projects(session_id):
    store = get_store()
    projects = store.list_projects(session_id)
    return jsonify({'projects': projects, 'count': len(projects)})


@bp.route('/api/session/<session_id>/project', methods=['POST'])
def create_project(session_id):
    store = get_store()
    data = request.get_json() or {}
    name = data.get('name', '')
    result = store.add_project(session_id, name)
    if not result:
        return jsonify({'error': 'Session not found'}), 404
    return jsonify(result)


@bp.route('/api/session/<session_id>/project/<project_id>', methods=['DELETE'])
def delete_project(session_id, project_id):
    store = get_store()
    ok = store.delete_project(session_id, project_id)
    if not ok:
        return jsonify({'error': 'Project not found'}), 404
    return jsonify({'status': 'deleted'})


@bp.route('/api/session/<session_id>/project/<project_id>/switch', methods=['POST'])
def switch_project(session_id, project_id):
    store = get_store()
    ok = store.set_current_project(session_id, project_id)
    if not ok:
        return jsonify({'error': 'Project not found'}), 404
    _, proj = store.get_current_project(session_id)
    return jsonify({'project_id': project_id, 'name': proj.get('name', '') if proj else ''})


@bp.route('/api/session/<session_id>/ask', methods=['POST'])
def ask_model(session_id):
    _ensure_providers()
    data = request.get_json() or {}
    prompt = data.get('prompt', '')
    models = data.get('models', [])
    files_data = data.get('files', [])
    output_types = data.get('output_types', [])
    source_files = data.get('source_files', [])

    store = get_store()
    registry = get_registry()
    transcribe_result = None

    # ── Step 1: Transcription (if audio/transcription output + URL or audio file) ──
    parsed = urlparse(prompt)
    is_url = parsed.scheme in ('http', 'https')
    is_audio_file = os.path.isfile(prompt)
    transcribe_url = ''
    do_transcribe = ('transcription' in output_types or 'audio' in output_types) and (is_url or is_audio_file)

    if do_transcribe:
        transcribe_url = prompt
        transcriber = get_transcriber()
        transcribe_result = transcriber.transcribe(
            transcribe_url, session_id=session_id, language='ru'
        )
        if transcribe_result.get('output'):
            store.add_input_file(
                session_id, transcribe_result['output'],
                source_name='transcript.md', step='transcription'
            )
            store.add_result_file(
                session_id, transcribe_result['output'],
                source_name='transcript.md'
            )
            source_files.append({
                'name': 'transcript.md',
                'path': transcribe_result['output'],
            })
            prompt = transcribe_result.get('text', prompt)[:2000]

    is_transcribe_only = do_transcribe and not (set(output_types) - {'transcription', 'audio'})

    # ── Gather context from source files ──
    context_text = ''
    if source_files or not models:
        input_files = store.get_input_files(session_id)
        for f in input_files:
            fpath = f.get('full_path', '')
            if fpath and os.path.exists(fpath):
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
                        c = fh.read(2000)
                    if c.strip():
                        context_text += f'\n--- {f["filename"]} ---\n{c[:1000]}\n'
                except Exception:
                    pass

    # ── Step 2: Auto-select models if none specified (skip if only transcribe) ──
    if not models and not is_transcribe_only:
        analyzer = get_analyzer()
        selector = get_selector()
        intent = analyzer.analyze_text(prompt)
        classification = analyzer.classify(DataProfile(), intent)
        suggestions = selector.suggest(classification, {}, intent.to_dict())
        models = [s['id'] for s in suggestions[:3]]

    # ── Step 3: Run selected models ──
    full_prompt = prompt
    if context_text:
        full_prompt = f'{prompt}\n\nContext files:\n{context_text}'

    msg = store.add_message(session_id, 'user', full_prompt, {
        'models': models, 'output_types': output_types,
        'transcribed': bool(transcribe_url),
    })

    # ── Step 3: Skip model run if only transcription ──
    if is_transcribe_only:
        msg = store.add_message(session_id, 'user', prompt, {
            'models': [], 'output_types': output_types,
            'transcribed': True,
        })
        response = {
            'status': 'completed',
            'results': [],
            'message': msg,
            'chain': {'transcribed': True, 'source_files_added': len(source_files)},
        }
        if transcribe_result:
            response['transcription'] = {
                'text': transcribe_result.get('text', '')[:10000],
                'summary': transcribe_result.get('summary', ''),
                'duration': transcribe_result.get('duration', 0),
                'model': transcribe_result.get('model', ''),
                'chain': transcribe_result.get('chain', ''),
                'language': transcribe_result.get('language', ''),
                'tokens': transcribe_result.get('tokens', 0),
                'output': transcribe_result.get('output', ''),
            }
        return jsonify(response)

    results = []
    for model_name in models:
        provider = registry.get(model_name)
        if not provider:
            results.append({
                'model': model_name,
                'error': f'Provider "{model_name}" not found',
                'metrics': {'duration_ms': 0},
            })
            continue

        start = time.time()
        try:
            resp = provider.generate(full_prompt, context=None)
            duration = (time.time() - start) * 1000
            result = {
                'model': model_name,
                'provider': provider.provider,
                'text': resp.text[:1000] if resp.text else '',
                'files': [{'name': f.name, 'path': f.path} for f in resp.files],
                'script': resp.script,
                'metrics': {
                    'duration_ms': duration,
                    'input_tokens': resp.usage.input_tokens,
                    'output_tokens': resp.usage.output_tokens,
                    'total_tokens': resp.usage.total_tokens,
                    'cost_usd': resp.usage.cost_usd,
                },
            }
            if result['files']:
                for f in result['files']:
                    store.add_input_file(
                        session_id, f['path'],
                        source_name=f['name'], step=model_name
                    )
            results.append(result)
            store.add_result(session_id, result)
        except Exception as e:
            results.append({
                'model': model_name,
                'error': str(e),
                'metrics': {'duration_ms': (time.time() - start) * 1000},
            })

    response = {
        'status': 'completed',
        'results': results,
        'message': msg,
        'chain': {
            'transcribed': bool(transcribe_result),
            'source_files_added': len(source_files),
        },
    }
    if transcribe_result:
        response['transcription'] = {
            'text': transcribe_result.get('text', '')[:10000],
            'summary': transcribe_result.get('summary', ''),
            'duration': transcribe_result.get('duration', 0),
            'model': transcribe_result.get('model', ''),
            'chain': transcribe_result.get('chain', ''),
            'language': transcribe_result.get('language', ''),
            'tokens': transcribe_result.get('tokens', 0),
            'output': transcribe_result.get('output', ''),
        }
    return jsonify(response)


@bp.route('/api/session/<session_id>/upload', methods=['POST'])
def upload_file(session_id):
    store = get_store()
    session = store.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'Empty filename'}), 400

    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({'error': f'Extension .{ext} not allowed'}), 400

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_UPLOAD_SIZE:
        return jsonify({'error': f'File too large ({size} > {MAX_UPLOAD_SIZE})'}), 400

    input_dir = store.get_input_dir(session_id)
    input_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f'{uuid.uuid4().hex[:12]}_{file.filename}'
    file_path = input_dir / safe_name
    file.save(str(file_path))

    mime = mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
    record = store.add_file(session_id, safe_name, file.filename, size, mime)
    store.add_input_file(session_id, str(file_path), file.filename, step='upload')

    return jsonify({'status': 'ok', 'file': record}), 201


@bp.route('/api/session/<session_id>/files', methods=['GET'])
def list_session_files(session_id):
    store = get_store()
    files = store.list_files(session_id)
    return jsonify({'files': files})


@bp.route('/api/session/<session_id>/input-files', methods=['GET'])
def list_input_files(session_id):
    store = get_store()
    files = store.get_input_files(session_id)
    return jsonify({'files': files})


@bp.route('/api/session/<session_id>/project/<project_id>/input-files', methods=['GET'])
def list_project_input_files(session_id, project_id):
    store = get_store()
    files = store.get_input_files(session_id, project_id)
    return jsonify({'files': files})


@bp.route('/api/session/<session_id>/history', methods=['GET'])
def list_history(session_id):
    store = get_store()
    files = store.get_history_files(session_id)
    return jsonify({'files': files})


@bp.route('/api/session/<session_id>/project/<project_id>/history', methods=['GET'])
def list_project_history(session_id, project_id):
    store = get_store()
    files = store.get_history_files(session_id, project_id)
    return jsonify({'files': files})


@bp.route('/api/session/<session_id>/results', methods=['GET'])
def list_results(session_id):
    store = get_store()
    files = store.get_results_files(session_id)
    return jsonify({'files': files})


@bp.route('/api/session/<session_id>/project/<project_id>/results', methods=['GET'])
def list_project_results(session_id, project_id):
    store = get_store()
    files = store.get_results_files(session_id, project_id)
    return jsonify({'files': files})


@bp.route('/api/session/<session_id>/files/remove-by-path', methods=['POST'])
def delete_file_by_path(session_id):
    data = request.get_json() or {}
    path = data.get('path', '')
    if not path:
        return jsonify({'error': 'path required'}), 400
    full_path = Path(path).resolve()
    if not full_path.exists():
        return jsonify({'error': 'File not found'}), 404
    try:
        full_path.unlink()
        # Also remove from session input_files so it won't appear in get_input_files
        try:
            store = get_store()
            store.remove_input_file(session_id, full_path.name)
        except Exception:
            pass
        return jsonify({'status': 'deleted', 'path': str(full_path)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/session/<session_id>/files/<filename>', methods=['DELETE'])
def delete_session_file(session_id, filename):
    store = get_store()
    ok = store.remove_file(session_id, filename)
    if not ok:
        return jsonify({'error': 'File not found'}), 404
    return jsonify({'status': 'deleted'})


@bp.route('/api/file-content')
def file_content():
    path = request.args.get('path', '')
    if not path:
        return jsonify({'error': 'No path'}), 400

    full_path = (WORKSPACE_ROOT / path).resolve()
    if not str(full_path).startswith(str(WORKSPACE_ROOT.resolve())):
        return jsonify({'error': 'Path outside workspace'}), 403
    if not full_path.exists() or not full_path.is_file():
        return jsonify({'error': 'File not found'}), 404

    ext = full_path.suffix.lower()
    previewable_text = {'.csv', '.json', '.txt', '.md', '.py', '.js', '.html', '.css', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.log', '.svg'}
    previewable_image = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}

    if ext in previewable_text:
        size = full_path.stat().st_size
        max_preview = 100 * 1024
        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read(max_preview)
        truncated = size > max_preview
        return jsonify({
            'type': 'text',
            'content': content,
            'size': size,
            'truncated': truncated,
            'lines': content.count('\n') + 1,
        })
    elif ext in previewable_image:
        return jsonify({
            'type': 'image',
            'url': f'/viz-lab/api/file-raw?path={path}',
        })
    else:
        return jsonify({
            'type': 'binary',
            'size': full_path.stat().st_size,
            'mime': mimetypes.guess_type(str(full_path))[0] or 'application/octet-stream',
        })


@bp.route('/api/file-raw')
def file_raw():
    path = request.args.get('path', '')
    if not path:
        return jsonify({'error': 'No path'}), 400

    full_path = (WORKSPACE_ROOT / path).resolve()
    if not str(full_path).startswith(str(WORKSPACE_ROOT.resolve())):
        return jsonify({'error': 'Path outside workspace'}), 403
    if not full_path.exists() or not full_path.is_file():
        return jsonify({'error': 'File not found'}), 404

    mime = mimetypes.guess_type(str(full_path))[0] or 'application/octet-stream'
    return send_file(str(full_path), mimetype=mime)


@bp.route('/api/transcribe', methods=['POST'])
def api_transcribe():
    data = request.get_json() or {}
    url = data.get('url', '')
    session_id = data.get('session_id', '')
    chain = data.get('chain', '')
    model = data.get('model', '')
    lang = data.get('language', 'ru')

    if not url:
        return jsonify({'error': 'URL or file path required'}), 400

    transcriber = get_transcriber()
    result = transcriber.transcribe(url, session_id=session_id,
                                     chain_id=chain, model=model,
                                     language=lang)
    return jsonify(result)


@bp.route('/api/transcribe/chains', methods=['GET'])
def api_transcribe_chains():
    transcriber = get_transcriber()
    chains = transcriber.get_chains()
    return jsonify({'chains': chains, 'count': len(chains)})


@bp.route('/api/analyze', methods=['POST'])
def analyze_data():
    data = request.get_json() or {}
    prompt = data.get('prompt', '')
    file_paths = data.get('files', [])

    analyzer = get_analyzer()
    selector = get_selector()

    intent = analyzer.analyze_text(prompt)

    profiles = []
    for fp in file_paths:
        full_path = str(WORKSPACE_ROOT / fp['path']) if isinstance(fp, dict) else fp
        p = analyzer.analyze_file(full_path)
        profiles.append(p.to_dict())

    profile = profiles[0] if profiles else {}
    classification = analyzer.classify(
        DataProfile(),
        intent
    )
    if profiles:
        classification.update({
            'primary_type': profile.get('data_type', 'unknown'),
            'description': 'User uploaded data: ' + profile.get('data_type', 'unknown'),
        })

    _ensure_providers()
    suggestions = selector.suggest(classification, profile, intent.to_dict())

    return jsonify({
        'intent': intent.to_dict(),
        'profile': profile,
        'classification': classification,
        'suggestions': suggestions,
    })


@bp.route('/api/providers')
def list_providers():
    _ensure_providers()
    registry = get_registry()
    return jsonify(registry.to_dict())


@bp.route('/api/project-tree')
def project_tree():
    root = WORKSPACE_ROOT
    tree = _build_tree(root, max_depth=4, max_entries=50)
    return jsonify(tree)


def _build_tree(path: Path, depth=0, max_depth=4, max_entries=50) -> dict | None:
    if depth > max_depth:
        return None
    if not path.exists():
        return None

    name = path.name
    if path.is_file():
        return {
            'name': name,
            'type': 'file',
            'path': str(path.relative_to(WORKSPACE_ROOT)),
            'size': path.stat().st_size,
        }

    entries = []
    try:
        children = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        return {'name': name, 'type': 'dir', 'path': str(path.relative_to(WORKSPACE_ROOT)), 'children': []}

    for child in children:
        if child.name.startswith('.') or child.name.startswith('__pycache__') or child.name == 'venv' or child.name == '.venv':
            continue
        sub = _build_tree(child, depth + 1, max_depth, max_entries)
        if sub:
            entries.append(sub)
        if len(entries) >= max_entries:
            break

    return {
        'name': name,
        'type': 'dir',
        'path': str(path.relative_to(WORKSPACE_ROOT)),
        'children': entries,
    }
