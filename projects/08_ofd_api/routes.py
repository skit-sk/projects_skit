"""OFD API Explorer — Flask Blueprint."""
import os, json
from pathlib import Path
from flask import Blueprint, jsonify, render_template, request

_bp_dir = Path(__file__).resolve().parent
_providers_dir = _bp_dir / "providers"
_bot_ofd_dir = _bp_dir / "bot_ofd"

import sys
sys.path.insert(0, str(_bot_ofd_dir))
from yandex_ofd import YandexOfdClient

bp = Blueprint("ofd_api", __name__, url_prefix="/ofd-api",
               template_folder=str(_bp_dir / "templates"),
               static_folder=str(_bp_dir / "static"),
               static_url_path="/static/ofd_api")


def load_provider(name):
    path = _providers_dir / f"{name}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build_methods_tree():
    tree = {}
    provider = load_provider("yandex_ofd")
    if not provider:
        return {"Ошибка": [{"name": "—", "desc": "Файл providers/yandex_ofd.json не найден", "params": None}]}

    categories = {
        "inn":              "🔍 Проверка",
        "Check_FN":         "🔍 Проверка",
        "getCrptTicket":    "🔍 Проверка",
        "KKT_v1":           "📟 Кассы",
        "KKT_v2":           "📟 Кассы",
        "TP_v1":            "🏪 Торговые точки",
        "TP_v2":            "🏪 Торговые точки",
        "TradePoint":       "🏪 Торговые точки",
        "KKTbyTradePoint":  "🏪 Торговые точки",
        "getDocCount":      "📄 Документы",
        "documents":        "📄 Документы",
        "getFiscalDoc_v1":  "📄 Документы",
        "getFiscalDoc_v2":  "📄 Документы",
        "KKTShift_v1":      "📊 Смены",
        "KKTShift_v2":      "📊 Смены",
        "documentsShift":   "📊 Смены",
        "closeShiftReport": "📊 Смены",
        "getChequeLink_v1": "🔗 Чеки",
        "getChequeLink_v2": "🔗 Чеки",
        "getFiscalReport":  "📋 Отчёты",
    }

    for ep_name, ep_info in provider.get("endpoints", {}).items():
        cat = categories.get(ep_name, "📦 Прочее")
        if isinstance(ep_info, dict):
            method = ep_info.get("method", "")
            desc = ep_info.get("desc", ep_name.replace("_", " "))
            params = ep_info.get("params", {})
            _, path = method.split(" ", 1) if " " in method else ("POST", method)
        else:
            method, path = ep_info.split(" ", 1)
            desc = ep_name.replace("_", " ")
            params = {"fiscalDriveNumber": "...", "date": "2025-01-01"}

        if cat not in tree:
            tree[cat] = []
        tree[cat].append({
            "name": path,
            "desc": desc,
            "params": params,
        })

    return tree


METHODS = build_methods_tree()


def get_client():
    token = os.environ.get("OFD_API_TOKEN", "")
    return YandexOfdClient(token=token)


@bp.route("/")
def index():
    return render_template("ofd_api.html")


@bp.route("/api/methods")
def api_methods():
    return jsonify({"categories": METHODS})


@bp.route("/api/execute", methods=["POST"])
def api_execute():
    try:
        data = request.get_json(force=True, silent=True) or {}
        method_path = data.get("method", "")
        params = data.get("params", {})

        if not method_path:
            return jsonify({"error": "Method is required"})

        client = get_client()
        result = client.call(method_path, params)
        return jsonify({
            "response": result,
            "status": 200,
            "url": f"{client.base}/{method_path.lstrip('/')}",
            "timing": {"total_ms": 0},
        })
    except Exception as e:
        return jsonify({"error": str(e), "status": 500})
