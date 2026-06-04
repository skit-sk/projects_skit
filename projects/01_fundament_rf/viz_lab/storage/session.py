import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path


class SessionStore:
    def __init__(self, data_dir: str = ''):
        if not data_dir:
            data_dir = Path(__file__).parent.parent.parent / 'data' / 'viz_sessions'
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._memory: dict[str, dict] = {}

    def _migrate(self, session: dict) -> dict:
        """Migrate old sessions (no projects) to new structure."""
        if 'projects' in session:
            return session
        pid = 'default'
        proj = {
            'name': 'Project 1',
            'created_at': session.get('created_at', datetime.now().isoformat()),
            'input_files': session.get('input_files', []),
            'messages': session.get('messages', []),
            'results': session.get('results', []),
            'files': session.get('files', []),
        }
        session['current_project'] = pid
        session['projects'] = {pid: proj}
        session.pop('input_files', None)
        session.pop('messages', None)
        session.pop('results', None)
        session.pop('files', None)
        # Migrate directories
        old_base = self.get_session_dir(session['id'])
        new_base = old_base / 'projects' / pid
        for d in ['input', 'history', 'results']:
            old_d = old_base / d
            new_d = new_base / d
            if old_d.exists() and not new_d.exists():
                new_d.parent.mkdir(parents=True, exist_ok=True)
                old_d.rename(new_d)
        self._persist(session['id'])
        return session

    def create(self) -> str:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        short = uuid.uuid4().hex[:8]
        session_id = f'VIZ_LAB_{ts}_{short}'
        pid = 'default'
        proj = {
            'name': 'Project 1',
            'created_at': datetime.now().isoformat(),
            'input_files': [],
            'messages': [],
            'results': [],
            'files': [],
        }
        session = {
            'id': session_id,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'current_project': pid,
            'projects': {pid: proj},
        }
        self._memory[session_id] = session
        self._ensure_session_dir(session_id)
        self._ensure_project_dir(session_id, pid)
        self._persist(session_id)
        return session_id

    def get(self, session_id: str) -> dict | None:
        if session_id in self._memory:
            return self._memory[session_id]
        path = self._session_path(session_id)
        if path.exists():
            with open(path) as f:
                data = json.load(f)
            data = self._migrate(data)
            self._memory[session_id] = data
            return data
        return None

    def update(self, session_id: str, data: dict):
        data['updated_at'] = datetime.now().isoformat()
        self._memory[session_id] = data
        self._persist(session_id)

    def add_project(self, session_id: str, name: str = '') -> dict | None:
        session = self.get(session_id)
        if not session:
            return None
        pid = f'proj_{uuid.uuid4().hex[:8]}'
        proj = {
            'name': name or f'Project {len(session["projects"]) + 1}',
            'created_at': datetime.now().isoformat(),
            'input_files': [],
            'messages': [],
            'results': [],
            'files': [],
        }
        session['projects'][pid] = proj
        session['current_project'] = pid
        self._ensure_project_dir(session_id, pid)
        self.update(session_id, session)
        return {'project_id': pid, **proj}

    def delete_project(self, session_id: str, project_id: str) -> bool:
        session = self.get(session_id)
        if not session or project_id not in session.get('projects', {}):
            return False
        proj_dir = self.get_session_dir(session_id) / 'projects' / project_id
        if proj_dir.exists():
            shutil.rmtree(str(proj_dir))
        del session['projects'][project_id]
        # Switch to first available
        if session.get('current_project') == project_id:
            first = next(iter(session['projects']), None)
            session['current_project'] = first if first else 'default'
        self.update(session_id, session)
        return True

    def get_current_project(self, session_id: str) -> tuple[str, dict] | None:
        session = self.get(session_id)
        if not session:
            return None
        pid = session.get('current_project', 'default')
        proj = session.get('projects', {}).get(pid)
        if not proj:
            proj = session.get('projects', {}).get('default')
            if not proj:
                return None
            pid = 'default'
        return pid, proj

    def set_current_project(self, session_id: str, project_id: str) -> bool:
        session = self.get(session_id)
        if not session or project_id not in session.get('projects', {}):
            return False
        session['current_project'] = project_id
        self.update(session_id, session)
        return True

    def list_projects(self, session_id: str) -> list[dict]:
        session = self.get(session_id)
        if not session:
            return []
        return [{'id': pid, **proj} for pid, proj in session.get('projects', {}).items()]

    def add_result(self, session_id: str, result: dict, project_id: str = ''):
        _, proj = self._resolve_project(session_id, project_id)
        if proj is None:
            return
        proj.setdefault('results', []).append(result)
        session = self.get(session_id)
        if session:
            self.update(session_id, session)

    def add_result_file(self, session_id: str, source_path: str, source_name: str = '', project_id: str = ''):
        res_dir = self.get_results_dir(session_id, project_id)
        res_dir.mkdir(parents=True, exist_ok=True)
        dest = res_dir / (source_name or os.path.basename(source_path))
        shutil.copy2(source_path, str(dest))

    def add_message(self, session_id: str, role: str, content: str, metadata: dict | None = None, project_id: str = ''):
        _, proj = self._resolve_project(session_id, project_id)
        if proj is None:
            return None
        msg = {
            'id': uuid.uuid4().hex[:12],
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {},
        }
        proj.setdefault('messages', []).append(msg)
        session = self.get(session_id)
        if session:
            self.update(session_id, session)
        return msg

    def add_file(self, session_id: str, filename: str, original_name: str, size_bytes: int, mime_type: str, project_id: str = ''):
        _, proj = self._resolve_project(session_id, project_id)
        if proj is None:
            return None
        record = {
            'id': uuid.uuid4().hex[:12],
            'filename': filename,
            'original_name': original_name,
            'size_bytes': size_bytes,
            'mime_type': mime_type,
            'uploaded_at': datetime.now().isoformat(),
            'in_input': True,
        }
        proj.setdefault('files', []).append(record)
        session = self.get(session_id)
        if session:
            self.update(session_id, session)
        return record

    def remove_file(self, session_id: str, filename: str) -> bool:
        session = self.get(session_id)
        if not session:
            return False
        # Try from all projects
        for pid, proj in session.get('projects', {}).items():
            before = len(proj.get('files', []))
            proj['files'] = [f for f in proj.get('files', []) if f.get('filename') != filename]
            if len(proj['files']) < before:
                file_path = self.get_session_dir(session_id) / 'projects' / pid / 'input' / filename
                if file_path.exists():
                    file_path.unlink()
                self.update(session_id, session)
                return True
        return False

    def add_input_file(self, session_id: str, source_path: str,
                       source_name: str = '', step: str = '', project_id: str = '') -> dict | None:
        _, proj = self._resolve_project(session_id, project_id)
        if proj is None:
            return None
        pid = self._resolve_pid(session_id, project_id)
        input_dir = self.get_input_dir(session_id, pid)
        input_dir.mkdir(parents=True, exist_ok=True)
        history_dir = self.get_history_dir(session_id, pid)
        history_dir.mkdir(parents=True, exist_ok=True)

        name = source_name or os.path.basename(source_path)
        step_num = len(proj.get('input_files', [])) + 1
        prefix = f'step_{step_num:03d}'
        if step:
            prefix += f'_{step}'
        hist_name = f'{prefix}_{name}'

        try:
            shutil.copy2(source_path, str(input_dir / name))
            shutil.copy2(source_path, str(history_dir / hist_name))
        except (shutil.SameFileError, OSError):
            pass

        record = {
            'id': uuid.uuid4().hex[:12],
            'filename': name,
            'source': os.path.basename(source_path),
            'added_at': datetime.now().isoformat(),
            'step': step,
        }
        proj.setdefault('input_files', []).append(record)
        session = self.get(session_id)
        if session:
            self.update(session_id, session)
        return record

    def remove_input_file(self, session_id: str, filename: str) -> bool:
        session = self.get(session_id)
        if not session:
            return False
        for pid, proj in session.get('projects', {}).items():
            before = len(proj.get('input_files', []))
            proj['input_files'] = [f for f in proj.get('input_files', []) if f.get('filename') != filename]
            if len(proj['input_files']) < before:
                self.update(session_id, session)
                return True
        return False

    def get_input_files(self, session_id: str, project_id: str = '') -> list[dict]:
        _, proj = self._resolve_project(session_id, project_id)
        if proj is None:
            return []
        pid = self._resolve_pid(session_id, project_id)
        result = []
        for f in proj.get('input_files', []):
            fpath = self.get_input_dir(session_id, pid) / f['filename']
            f['exists'] = fpath.exists()
            f['full_path'] = str(fpath)
            result.append(f)
        return result

    def get_history_files(self, session_id: str, project_id: str = '') -> list[dict]:
        pid = self._resolve_pid(session_id, project_id)
        hist_dir = self.get_history_dir(session_id, pid)
        if not hist_dir.exists():
            return []
        return self._list_dir(hist_dir)

    def get_results_files(self, session_id: str, project_id: str = '') -> list[dict]:
        pid = self._resolve_pid(session_id, project_id)
        res_dir = self.get_results_dir(session_id, pid)
        if not res_dir.exists():
            return []
        return self._list_dir(res_dir)

    def delete_session(self, session_id: str) -> bool:
        session_dir = self.get_session_dir(session_id)
        if not session_dir.exists():
            return False
        shutil.rmtree(str(session_dir))
        self._memory.pop(session_id, None)
        json_path = self._session_path(session_id)
        if json_path.exists():
            json_path.unlink()
        return True

    def list_all(self) -> list[dict]:
        sessions = []
        for path in sorted(self.data_dir.glob('*.json')):
            with open(path) as f:
                sessions.append(json.load(f))
        return sorted(sessions, key=lambda s: s.get('created_at', ''), reverse=True)

    def get_session_dir(self, session_id: str) -> Path:
        return self.data_dir / session_id

    def _resolve_project(self, session_id: str, project_id: str = '') -> tuple[str, dict | None]:
        session = self.get(session_id)
        if not session:
            return '', None
        pid = project_id or session.get('current_project', 'default')
        proj = session.get('projects', {}).get(pid)
        if proj:
            return pid, proj
        first = next(iter(session.get('projects', {}).values()), None)
        return 'default', first

    def _resolve_pid(self, session_id: str, project_id: str = '') -> str:
        session = self.get(session_id)
        if not session:
            return 'default'
        pid = project_id or session.get('current_project', 'default')
        if pid in session.get('projects', {}):
            return pid
        first = next(iter(session.get('projects', {})), 'default')
        return first

    def get_input_dir(self, session_id: str, project_id: str = '') -> Path:
        return self.get_session_dir(session_id) / 'projects' / project_id / 'input'

    def get_history_dir(self, session_id: str, project_id: str = '') -> Path:
        return self.get_session_dir(session_id) / 'projects' / project_id / 'history'

    def get_results_dir(self, session_id: str, project_id: str = '') -> Path:
        return self.get_session_dir(session_id) / 'projects' / project_id / 'results'

    def _list_dir(self, d: Path) -> list[dict]:
        if not d.exists():
            return []
        result = []
        for f in sorted(d.iterdir()):
            if f.is_file():
                result.append({
                    'name': f.name,
                    'path': str(f),
                    'size': f.stat().st_size,
                    'modified': datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                })
        return result

    def _ensure_session_dir(self, session_id: str):
        self.get_session_dir(session_id).mkdir(parents=True, exist_ok=True)

    def _ensure_project_dir(self, session_id: str, project_id: str):
        base = self.get_session_dir(session_id) / 'projects' / project_id
        base.mkdir(parents=True, exist_ok=True)
        (base / 'input').mkdir(exist_ok=True)
        (base / 'history').mkdir(exist_ok=True)
        (base / 'results').mkdir(exist_ok=True)

    def _session_path(self, session_id: str) -> Path:
        return self.data_dir / f'{session_id}.json'

    def _persist(self, session_id: str):
        data = self._memory.get(session_id)
        if data:
            with open(self._session_path(session_id), 'w') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)


_store = SessionStore()

def get_store() -> SessionStore:
    return _store
