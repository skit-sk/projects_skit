import sys
import os
sys.path.insert(0, os.path.expanduser('~/.local/lib/python3.12/site-packages'))

from flask import Flask
from routes import api, web, graphics, processor_1d, dashboard, trade_analytics, ma_analytics, ccxt_api, account_api

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

app.register_blueprint(api.bp)
app.register_blueprint(web.bp)
app.register_blueprint(graphics.bp)
app.register_blueprint(processor_1d.bp)
app.register_blueprint(dashboard.bp)
app.register_blueprint(trade_analytics.bp)
app.register_blueprint(ma_analytics.bp)
app.register_blueprint(ccxt_api.bp)
app.register_blueprint(account_api.bp)
app.register_blueprint(ofd_api_bp)


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    app.run(debug=False, host="0.0.0.0", port=port)
