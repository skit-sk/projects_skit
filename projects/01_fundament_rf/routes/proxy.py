import requests
import yaml
from pathlib import Path
from flask import Blueprint, request, Response, abort
from urllib.parse import urljoin
from services.proxy_html_patcher import patch_html, patch_css, patch_location_header

bp = Blueprint('proxy', __name__, url_prefix='/proxy')

REGISTRY_PATH = Path('/home/user_aioc/workspace/docs/sandbox/SANDBOX_REGISTRY.yaml')


def _load_registry():
    if not REGISTRY_PATH.exists():
        return {}
    with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    return data.get('projects', {})


def _get_project_url(project_id: str) -> tuple:
    registry = _load_registry()
    project = registry.get(project_id)
    if not project:
        abort(404, description=f'Project {project_id} not found')
    if project.get('type') not in ('flask',):
        abort(400, description=f'Project {project_id} is not proxyable')
    url = project.get('entry_url', '')
    if not url.startswith('http://localhost:'):
        abort(400, description=f'Project {project_id} has invalid entry_url')
    base = url.rstrip('/') + '/'
    return base, project


@bp.route('/<project_id>/', defaults={'path': ''}, methods=['GET', 'POST', 'OPTIONS'])
@bp.route('/<project_id>/<path:path>', methods=['GET', 'POST', 'OPTIONS'])
def proxy(project_id: str, path: str):
    base_url, project = _get_project_url(project_id)
    target_url = urljoin(base_url, path)
    if request.query_string:
        target_url = f"{target_url}?{request.query_string.decode('utf-8')}"

    # Prepare headers
    headers = {}
    for key, value in request.headers:
        if key.lower() in ('host', 'content-length'):
            continue
        headers[key] = value
    base_port = base_url.split(':')[-1].rstrip('/').rstrip('/')
    headers['Host'] = f'localhost:{base_port}'

    try:
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=request.get_data(),
            cookies=request.cookies,
            timeout=30,
            allow_redirects=False,
            stream=True
        )
    except requests.RequestException as e:
        return Response(f'Proxy error: {e}', status=502)

    # Handle redirect
    location = resp.headers.get('Location')
    if location:
        location = patch_location_header(location, project_id, base_url)
        resp.headers['Location'] = location

    content_type = resp.headers.get('Content-Type', '')
    content = resp.content

    if 'text/html' in content_type:
        content = patch_html(content, project_id, base_url)
    elif 'text/css' in content_type:
        content = patch_css(content, project_id)
    elif 'javascript' in content_type:
        # Patch JS files too (e.g., inline fetch in bundled scripts)
        from services.proxy_html_patcher import _patch_inline_js
        try:
            content = _patch_inline_js(content.decode('utf-8'), project_id, base_url).encode('utf-8')
        except Exception:
            pass

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    response_headers = [
        (k, v) for k, v in resp.headers.items()
        if k.lower() not in excluded_headers
    ]

    return Response(
        content,
        status=resp.status_code,
        headers=response_headers
    )
