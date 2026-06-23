import sys
import os
import time
sys.path.insert(0, os.path.expanduser('~/.local/lib/python3.12/site-packages'))

from flask import Flask, g
from routes import api, web, graphics, processor_1d, dashboard, trade_analytics, ma_analytics, ccxt_api, account_api, processor, viz_lab, ai_models, sandbox, proxy, med_life, kb, timeframe_api, visualizations

# Register OFD API blueprint from 08_ofd project
_ofd_dir = os.path.join(os.path.dirname(__file__), '..', '08_ofd_api')
if _ofd_dir not in sys.path:
    sys.path.insert(0, _ofd_dir)
import importlib.util
_spec = importlib.util.spec_from_file_location("ofd_routes", os.path.join(_ofd_dir, "routes.py"))
_ofd_mod = importlib.util.module_from_spec(_spec)
_sys_path_save = sys.path.copy()
sys.path.insert(0, _ofd_dir)
_spec.loader.exec_module(_ofd_mod)
sys.path = _sys_path_save
ofd_api_bp = _ofd_mod.bp

app = Flask(__name__)

app.jinja_env.cache = None

@app.before_request
def _start_timer():
    g.start_time = time.time()

@app.after_request
def _add_timing_header(response):
    if hasattr(g, 'start_time'):
        elapsed = int((time.time() - g.start_time) * 1000)
        response.headers['X-Server-Ms'] = str(elapsed)
    return response

app.register_blueprint(api.bp)
app.register_blueprint(web.bp)
app.register_blueprint(graphics.bp)
app.register_blueprint(processor_1d.bp)
app.register_blueprint(dashboard.bp)
app.register_blueprint(trade_analytics.bp)
app.register_blueprint(ma_analytics.bp)
app.register_blueprint(ccxt_api.bp)
app.register_blueprint(account_api.bp)
app.register_blueprint(processor.bp)
app.register_blueprint(ofd_api_bp)
# Register OFD Abonent blueprint
_spec2 = importlib.util.spec_from_file_location("ofd_abonent_routes", os.path.join(_ofd_dir, "routes_ofd_abonent.py"))
_ofd2_mod = importlib.util.module_from_spec(_spec2)
_sys_path_save2 = sys.path.copy()
sys.path.insert(0, _ofd_dir)
_spec2.loader.exec_module(_ofd2_mod)
sys.path = _sys_path_save2
app.register_blueprint(_ofd2_mod.bp)
app.register_blueprint(viz_lab.bp)
app.register_blueprint(ai_models.bp)
app.register_blueprint(sandbox.bp)
app.register_blueprint(proxy.bp)
app.register_blueprint(med_life.bp)
app.register_blueprint(kb.bp)
app.register_blueprint(timeframe_api.bp)
app.register_blueprint(visualizations.bp)

# ── Experimental: graphics_v2 (Bento + Compact) ─────────────────────
# Полностью изолирован: при ошибке основной проект продолжает работать.
try:
    from routes import graphics_v2
    app.register_blueprint(graphics_v2.bp)
    print('[OK] graphics_v2 loaded at /graphics/v2')
except Exception as _gv2_err:
    print(f'[skip] graphics_v2 not loaded: {_gv2_err}')


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    app.run(debug=False, host="0.0.0.0", port=port)
