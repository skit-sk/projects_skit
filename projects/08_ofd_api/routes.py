"""OFD API Explorer — Flask Blueprint."""
import os, json, time
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

_providers_cache = {}
_cache_ttl = 30
_cache_ts = 0


def _list_providers():
    files = sorted(_providers_dir.glob("*.json"))
    result = []
    for f in files:
        if f.name == "schema.json":
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            result.append({
                "id": f.stem,
                "name": data.get("provider", f.stem),
                "version": data.get("version", ""),
                "auth_type": data.get("auth_type", ""),
                "base_url": data.get("base_url", ""),
            })
        except Exception:
            pass
    return result


def _load_provider(name):
    global _providers_cache, _cache_ts
    now = time.time()
    if now - _cache_ts < _cache_ttl and name in _providers_cache:
        return _providers_cache[name]
    path = _providers_dir / f"{name}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    _providers_cache[name] = data
    _cache_ts = now
    return data


def _build_tree(provider_name):
    provider = _load_provider(provider_name)
    if not provider:
        return {"Ошибка": [{"name": "—", "desc": f"Провайдер {provider_name} не найден", "params": None}]}

    category_map = provider.get("category_map", {})
    if not category_map:
        # Hardcoded fallback for yandex_ofd
        category_map = {
            "inn": "🔍 Проверка", "Check_FN": "🔍 Проверка", "getCrptTicket": "🔍 Проверка",
            "KKT_v1": "📟 Кассы", "KKT_v2": "📟 Кассы",
            "TP_v1": "🏪 Торговые точки", "TP_v2": "🏪 Торговые точки",
            "TradePoint": "🏪 Торговые точки", "KKTbyTradePoint": "🏪 Торговые точки",
            "getDocCount": "📄 Документы", "documents": "📄 Документы",
            "getFiscalDoc_v1": "📄 Документы", "getFiscalDoc_v2": "📄 Документы",
            "KKTShift_v1": "📊 Смены", "KKTShift_v2": "📊 Смены",
            "documentsShift": "📊 Смены", "closeShiftReport": "📊 Смены",
            "getChequeLink_v1": "🔗 Чеки", "getChequeLink_v2": "🔗 Чеки",
            "getFiscalReport": "📋 Отчёты",
        }

    tree = {}
    for ep_name, ep_info in provider.get("endpoints", {}).items():
        cat = category_map.get(ep_name, "📦 Прочее")
        method_str = ep_info.get("method", "POST /")
        _, path = method_str.split(" ", 1) if " " in method_str else ("POST", method_str)
        params_meta = ep_info.get("params", {})
        normalized = {}
        for pk, pv in params_meta.items():
            if isinstance(pv, dict):
                normalized[pk] = pv
            else:
                normalized[pk] = {"type": "string", "required": False, "desc": "", "example": str(pv)}
        if cat not in tree:
            tree[cat] = []
        tree[cat].append({
            "key": ep_name,
            "name": path,
            "desc": ep_info.get("desc", ep_name.replace("_", " ")),
            "method": method_str.split(" ")[0] if " " in method_str else "POST",
            "params": normalized,
            "docs": ep_info.get("docs", ""),
        })
    return tree


@bp.route("/")
def index():
    return render_template("ofd_api.html")


@bp.route("/api/providers")
def api_providers():
    return jsonify(_list_providers())


@bp.route("/api/methods/<provider_name>")
def api_methods(provider_name):
    tree = _build_tree(provider_name)
    return jsonify({"categories": tree})


@bp.route("/api/docs/<provider_name>/<method_key>")
def api_docs(provider_name, method_key):
    provider = _load_provider(provider_name)
    if not provider:
        return jsonify({"error": "Provider not found"}), 404
    ep = provider.get("endpoints", {}).get(method_key, {})
    return jsonify({
        "docs": ep.get("docs", ""),
        "desc": ep.get("desc", ""),
    })


@bp.route("/api/execute", methods=["POST"])
def api_execute():
    try:
        data = request.get_json(force=True, silent=True) or {}
        provider_name = data.get("provider", "yandex_ofd")
        method_path = data.get("method", "")
        params = data.get("params", {})
        ui_token = data.get("token", "")

        if not method_path:
            return jsonify({"error": "Method is required"})

        provider = _load_provider(provider_name)
        if not provider:
            return jsonify({"error": f"Provider '{provider_name}' not found"}), 404

        base_url = provider.get("base_url", "")
        auth_type = provider.get("auth_type", "")
        env_token_name = provider.get("env_token", "")

        # Priority: UI token → env var
        token = ui_token or os.environ.get(env_token_name, "")

        t0 = time.perf_counter()
        if auth_type == "bearer_token":
            from bot_ofd.yandex_ofd import YandexOfdClient
            client = YandexOfdClient(token=token)
            result = client.call(method_path, params or {})
        else:
            from bot_ofd.ofd_client import OfdApiClient
            # Determine HTTP method from provider endpoint config
            ep_info = None
            for ep_name, ep in provider.get("endpoints", {}).items():
                if ep.get("method", "").endswith(method_path) or method_path in ep.get("method", ""):
                    ep_info = ep
                    break
            http_method = "GET"
            if ep_info:
                ms = ep_info.get("method", "GET /")
                http_method = ms.split(" ")[0] if " " in ms else "POST"
            client = OfdApiClient(provider, token=token)
            result = client.call(method_path, http_method, params or {})
        t1 = time.perf_counter()

        return jsonify({
            "response": result,
            "status": 200,
            "url": f"{base_url}/{method_path.lstrip('/')}",
            "timing": {"total_ms": round((t1 - t0) * 1000, 2)},
        })
    except Exception as e:
        return jsonify({"error": str(e), "status": 500})


@bp.route("/api/methods", methods=["GET"])
def api_methods_old():
    """Redirect to default provider for backward compatibility."""
    return api_methods("yandex_ofd")


def get_client():
    token = os.environ.get("OFD_YARU_TOKEN", "")
    return YandexOfdClient(token=token)
