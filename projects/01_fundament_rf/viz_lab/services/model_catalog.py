import json
import os
import subprocess
import time
from pathlib import Path
from datetime import datetime
from typing import Optional


TRANSCRIPT_DIR = Path(__file__).parent.parent.parent.parent / '09_model_catalog'
AI_PROVIDERS_DIR = TRANSCRIPT_DIR / 'ai_providers'
CATALOG_INDEX = TRANSCRIPT_DIR / 'models_catalog.json'
CACHE_DIR = Path(__file__).parent.parent.parent / 'data' / 'viz_sessions'
CACHE_PATH = CACHE_DIR / 'models_catalog.json'
CUSTOM_PROVIDERS_PATH = Path(__file__).parent.parent / 'config' / 'custom_providers.json'


class ModelCatalog:
    def __init__(self):
        self._cache: dict | None = None

    def get_catalog(self, force_refresh=False) -> dict:
        if self._cache and not force_refresh:
            return self._cache
        if CACHE_PATH.exists() and not force_refresh:
            with open(CACHE_PATH) as f:
                self._cache = json.load(f)
            return self._cache
        return self.refresh_from_json()

    def refresh_from_json(self) -> dict:
        if not CATALOG_INDEX.exists():
            return self._empty_catalog('catalog index not found')
        with open(CATALOG_INDEX) as f:
            index = json.load(f)
        providers = []
        all_models = []
        errors = []
        for p_ref in index.get('providers', []):
            pid = p_ref.get('id', '')
            cf = p_ref.get('catalog_file', '')
            pfile = AI_PROVIDERS_DIR / os.path.basename(cf) if cf else AI_PROVIDERS_DIR / f'{pid}.json'
            if pfile.exists():
                with open(pfile) as f:
                    pdata = json.load(f)
                provider_info = {
                    'id': pid,
                    'label': pdata.get('label', pid),
                    'homepage': pdata.get('homepage', ''),
                    'api_endpoint': pdata.get('api_endpoint', ''),
                    'balance': pdata.get('balance', 'unknown'),
                    'key_var': pdata.get('key_var', ''),
                    'opencode_prefix': pdata.get('opencode_prefix', ''),
                    'pricing_unit': pdata.get('pricing_unit', ''),
                    'updated': pdata.get('updated', ''),
                    'models_count': pdata.get('models_count', 0),
                    'notes': pdata.get('notes', ''),
                }
                providers.append(provider_info)
                for m in pdata.get('models', []):
                    m['provider_id'] = pid
                    m['provider_label'] = pdata.get('label', pid)
                    all_models.append(m)
            else:
                errors.append(f'provider file not found: {pid} ({pfile})')

        catalog = {
            'catalog_version': index.get('catalog_version', '1.0'),
            'updated': datetime.now().isoformat()[:10],
            'provider_catalog_dir': str(AI_PROVIDERS_DIR),
            'stats': {
                'total_models': len(all_models),
                'total_providers': len(providers),
                'by_type': self._count_by_type(all_models),
                'by_balance': self._count_by_balance(providers),
            },
            'providers': providers,
            'models': all_models,
            'errors': errors,
        }
        self._cache = catalog
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(CACHE_PATH, 'w') as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)
        return catalog

    def refresh_online(self, provider_id: Optional[str] = None) -> dict:
        results = {}
        providers = self._load_provider_configs()
        for p in providers:
            if provider_id and p['id'] != provider_id:
                continue
            try:
                if p.get('api_endpoint'):
                    result = self._fetch_from_api(p)
                elif p.get('opencode_prefix'):
                    result = self._fetch_from_opencode(p)
                else:
                    result = {'status': 'skipped', 'reason': 'no endpoint'}
                results[p['id']] = result
            except Exception as e:
                results[p['id']] = {'status': 'error', 'error': str(e)}
        self.refresh_from_json()
        return results

    def _fetch_from_api(self, provider: dict) -> dict:
        url = provider['api_endpoint']
        headers = {}
        key_var = provider.get('key_var', '')
        if key_var:
            key = os.environ.get(key_var)
            if key:
                headers['Authorization'] = f'Bearer {key}'
        try:
            import urllib.request
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode()
            data = json.loads(raw)
        except Exception as e:
            return {'status': 'error', 'error': str(e), 'url': url}

        models = self._parse_api_response(provider['id'], data)
        self._save_provider_models(provider['id'], models)
        return {'status': 'ok', 'count': len(models), 'url': url}

    def _fetch_from_opencode(self, provider: dict) -> dict:
        prefix = provider.get('opencode_prefix', '')
        try:
            result = subprocess.run(
                ['opencode', 'models'],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                return {'status': 'error', 'error': result.stderr[:200]}
            lines = result.stdout.strip().split('\n')
            filtered = [l.strip() for l in lines if l.strip().startswith(prefix)]
            models = []
            for m in filtered:
                short_id = m.replace(prefix, '', 1) if prefix else m
                models.append({
                    'id': short_id,
                    'name': short_id,
                    'type': 'llm',
                    'pricing': None,
                    'context': None,
                    'capabilities': {'text': True},
                })
            self._save_provider_models(provider['id'], models, opencode_prefix=prefix)
            return {'status': 'ok', 'count': len(models), 'source': 'opencode'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def _parse_api_response(self, provider_id: str, data) -> list[dict]:
        models = []
        if provider_id in ('routerai', 'apiyi'):
            raw = data if isinstance(data, list) else data.get('data', [])
            for m in raw:
                mid = m.get('id', '')
                models.append({
                    'id': mid,
                    'name': m.get('name', m.get('id', '')),
                    'type': self._infer_type(m),
                    'pricing': {'input_rub': None, 'output_rub': None},
                    'context': m.get('context') or m.get('max_tokens'),
                    'capabilities': {'text': True},
                })
        return models

    def _infer_type(self, model_data: dict) -> str:
        mid = (model_data.get('id') or '').lower()
        if any(k in mid for k in ('tts', 'text-to-speech')):
            return 'tts'
        if any(k in mid for k in ('audio', 'stt', 'whisper')):
            return 'audio'
        if any(k in mid for k in ('image', 'vision', 'dall-e', 'flux')):
            return 'vision'
        return 'llm'

    def _save_provider_models(self, provider_id: str, models: list[dict],
                               opencode_prefix: str = ''):
        pfile = AI_PROVIDERS_DIR / f'{provider_id}.json'
        if pfile.exists():
            with open(pfile) as f:
                existing = json.load(f)
        else:
            existing = {
                'provider': provider_id,
                'label': provider_id,
                'balance': 'unknown',
                'updated': datetime.now().isoformat()[:10],
                'models_count': 0,
                'models': [],
            }
        existing['models'] = models
        existing['models_count'] = len(models)
        existing['updated'] = datetime.now().isoformat()[:10]
        if opencode_prefix:
            existing['opencode_prefix'] = opencode_prefix
        AI_PROVIDERS_DIR.mkdir(parents=True, exist_ok=True)
        with open(pfile, 'w') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)

    def test_connection(self, url: str, api_key: str = '') -> dict:
        try:
            headers = {}
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'
            import urllib.request
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                return {'status': 'ok', 'code': resp.status, 'body': resp.read().decode()[:200]}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def sync_custom_provider(self, config: dict) -> dict:
        configs = []
        if CUSTOM_PROVIDERS_PATH.exists():
            with open(CUSTOM_PROVIDERS_PATH) as f:
                configs = json.load(f)
        existing = [c for c in configs if c.get('id') != config.get('id')]
        config['updated'] = datetime.now().isoformat()[:10]
        existing.append(config)
        CUSTOM_PROVIDERS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CUSTOM_PROVIDERS_PATH, 'w') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        return {'status': 'saved', 'provider_id': config.get('id', '')}

    def get_providers(self) -> list[dict]:
        cat = self.get_catalog()
        return cat.get('providers', [])

    def get_provider(self, provider_id: str) -> Optional[dict]:
        for p in self.get_providers():
            if p['id'] == provider_id:
                return p
        return None

    def get_models(self, provider_id: Optional[str] = None,
                   model_type: Optional[str] = None,
                   search: str = '') -> list[dict]:
        cat = self.get_catalog()
        models = cat.get('models', [])
        if provider_id:
            models = [m for m in models if m.get('provider_id') == provider_id]
        if model_type:
            models = [m for m in models if m.get('type') == model_type]
        if search:
            terms = [t.lower() for t in search.split() if t.strip()]
            models = [m for m in models if all(
                t in ' '.join(filter(None, [
                    m.get('id', ''),
                    m.get('name', ''),
                    m.get('provider_id', ''),
                    m.get('provider_label', ''),
                    m.get('type', ''),
                    ' '.join(m.get('capabilities', {}).keys()),
                ])).lower()
                for t in terms
            )]
        return models

    def get_stats(self) -> dict:
        cat = self.get_catalog()
        return cat.get('stats', {})

    def _load_provider_configs(self) -> list[dict]:
        cat = self.get_catalog()
        providers = list(cat.get('providers', []))
        if CUSTOM_PROVIDERS_PATH.exists():
            with open(CUSTOM_PROVIDERS_PATH) as f:
                custom = json.load(f)
            for c in custom:
                c['_custom'] = True
                providers.append(c)
        return providers

    def _count_by_type(self, models: list[dict]) -> dict:
        counts = {}
        for m in models:
            t = m.get('type', 'unknown')
            counts[t] = counts.get(t, 0) + 1
        return counts

    def _count_by_balance(self, providers: list[dict]) -> dict:
        counts = {}
        for p in providers:
            b = p.get('balance', 'unknown')
            counts[b] = counts.get(b, 0) + 1
        return counts

    def _empty_catalog(self, reason: str) -> dict:
        return {
            'catalog_version': '1.0',
            'updated': datetime.now().isoformat()[:10],
            'stats': {'total_models': 0, 'total_providers': 0, 'by_type': {}, 'by_balance': {}},
            'providers': [],
            'models': [],
            'errors': [reason],
        }


_catalog = ModelCatalog()


def get_catalog() -> ModelCatalog:
    return _catalog
