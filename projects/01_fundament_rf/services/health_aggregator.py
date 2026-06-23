import os
import time
import json
import yaml
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import requests

REGISTRY_PATH = Path('/home/user_aioc/workspace/docs/sandbox/SANDBOX_REGISTRY.yaml')


def load_registry() -> Dict[str, Any]:
    if not REGISTRY_PATH.exists():
        return {'projects': {}}
    with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {'projects': {}}


def _check_pid(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def _read_pidfile(pidfile: str) -> Optional[int]:
    try:
        with open(pidfile, 'r', encoding='utf-8') as f:
            return int(f.read().strip())
    except Exception:
        return None


def _check_bot(project: Dict[str, Any]) -> Dict[str, Any]:
    pidfile = project.get('pidfile')
    pid = _read_pidfile(pidfile) if pidfile else None
    if pid and _check_pid(pid):
        return {'status': 'up', 'pid': pid}
    # fallback: pgrep by project name
    try:
        name = project.get('name', '')
        result = subprocess.run(
            ['pgrep', '-f', name],
            capture_output=True, text=True, timeout=2
        )
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            return {'status': 'up', 'pid': int(pids[0])}
    except Exception:
        pass
    return {'status': 'down'}


def _check_http(url: str, timeout: int = 3) -> Dict[str, Any]:
    try:
        resp = requests.get(url, timeout=timeout)
        return {
            'status': 'up' if resp.status_code == 200 else 'degraded',
            'http_code': resp.status_code,
            'response_ms': int(resp.elapsed.total_seconds() * 1000)
        }
    except Exception as e:
        return {'status': 'down', 'error': str(e)}


def _check_data(project: Dict[str, Any]) -> Dict[str, Any]:
    path = project.get('source_path') or project.get('path')
    if not path:
        return {'status': 'unknown'}
    p = Path(path)
    if not p.exists():
        return {'status': 'down', 'error': 'path not found'}
    if p.is_dir():
        files = list(p.rglob('*'))
        if not files:
            return {'status': 'down', 'error': 'empty directory'}
        latest = max((f.stat().st_mtime for f in files if f.is_file()), default=0)
        return {
            'status': 'up',
            'files': len(files),
            'last_modified': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(latest))
        }
    return {'status': 'up'}


def check_project(project_id: str, project: Dict[str, Any]) -> Dict[str, Any]:
    ptype = project.get('type', 'unknown')
    result = {'id': project_id, 'name': project.get('name', project_id), 'type': ptype}

    if ptype in ('flask', 'static_mount', 'atlas', 'blueprint'):
        health_url = project.get('health_url') or project.get('entry_url')
        if health_url:
            if health_url.startswith('/'):
                # internal path - convert to full URL
                health_url = f'http://localhost:5000{health_url}'
            result.update(_check_http(health_url))
        else:
            result['status'] = 'unknown'
    elif ptype == 'bot':
        result.update(_check_bot(project))
    elif ptype == 'cli':
        result.update(_check_bot(project))
    elif ptype == 'data':
        result.update(_check_data(project))
    else:
        result['status'] = 'unknown'

    result['embeddable'] = project.get('embeddable', False)
    result['entry_url'] = project.get('entry_url')
    return result


def check_all() -> Dict[str, Any]:
    registry = load_registry()
    projects = registry.get('projects', {})
    results = {}
    for pid, project in projects.items():
        results[pid] = check_project(pid, project)
    return {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'projects': results
    }


def tail_log(project_id: str, n: int = 50) -> Optional[str]:
    registry = load_registry()
    project = registry.get('projects', {}).get(project_id, {})
    log_path = project.get('log_path')
    if not log_path:
        return None
    p = Path(log_path)
    if not p.exists():
        return f'Log file not found: {log_path}'
    try:
        result = subprocess.run(
            ['tail', '-n', str(n), str(p)],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout
    except Exception as e:
        return f'Error reading log: {e}'
