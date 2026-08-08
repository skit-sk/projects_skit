"""Tests for TradeHelp."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import config


def test_config_loads():
    assert config.PORT == 5012
    assert config.HOST
    assert config.DATA_LIVE.exists()
    assert config.DATA_HISTORY.exists()


def test_live_data():
    totals_file = config.DATA_LIVE / 'totals.json'
    if totals_file.exists():
        d = json.loads(totals_file.read_text())
        assert isinstance(d, dict)


def test_history_data():
    files = list(config.DATA_HISTORY.glob('*/*_1D.json'))
    assert len(files) > 0, "no 1D files"


def test_routes():
    from app import create_app
    app = create_app()
    client = app.test_client()
    r = client.get('/')
    assert r.status_code == 200
    r = client.get('/healthz')
    assert b'ok' in r.data
    r = client.get('/learn/')
    assert r.status_code == 200
    r = client.get('/viz/')
    assert r.status_code == 200
    r = client.get('/tv/')
    assert r.status_code == 200
    r = client.get('/tools/')
    assert r.status_code == 200
