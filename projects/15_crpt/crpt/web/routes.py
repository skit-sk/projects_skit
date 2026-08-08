"""Flask Blueprint: API Explorer для CRPT."""

import json
import os
import time
from flask import Blueprint, render_template, request, jsonify

from crpt.mobile_api import MobileCheckClient
from crpt.true_api import TrueApiClient
from crpt.nk_api import NkApiClient
from crpt.types import ApiEnv, BASE_URLS

_BP_DIR = os.path.dirname(os.path.abspath(__file__))
web_bp = Blueprint(
    "crpt_web", __name__,
    template_folder=os.path.join(_BP_DIR, "templates"),
    static_folder=os.path.join(_BP_DIR, "static"),
    url_prefix="/crpt",
)

# ── Дерево эндпоинтов (категории → методы → параметры) ──────

ENDPOINT_TREE = {
    "📱 Mobile API (публичный, без авторизации)": {
        "icon": "📱",
        "desc": "Проверка кодов через мобильное приложение. Не требует токенов.",
        "methods": {
            "check_datamatrix": {
                "label": "Проверка DataMatrix",
                "desc": "GET /mobile/check?codeType=datamatrix",
                "params": [{"name": "code", "label": "Код DataMatrix", "type": "text"}],
                "handler": lambda p: MobileCheckClient().check_datamatrix(p["code"]),
            },
            "check_ean13": {
                "label": "Проверка EAN-13",
                "desc": "GET /mobile/check?codeType=ean13",
                "params": [{"name": "code", "label": "Штрихкод (13 цифр)", "type": "text"}],
                "handler": lambda p: MobileCheckClient().check_ean13(p["code"]),
            },
            "check_qr": {
                "label": "Проверка QR-чека",
                "desc": "GET /mobile/check?codeType=qr",
                "params": [{"name": "code", "label": "QR-строка чека", "type": "text"}],
                "handler": lambda p: MobileCheckClient().check_qr(p["code"]),
            },
            "check_receipt": {
                "label": "Проверка чека (receipt)",
                "desc": "POST /mobile/check — проверка по реквизитной строке",
                "params": [{"name": "receipt", "label": "Реквизитная строка чека (t=...&s=...&fn=...)", "type": "text"}],
                "handler": lambda p: MobileCheckClient().check_receipt(p["receipt"]),
            },
        },
    },
    "🏢 True API — публичные методы": {
        "icon": "🏢",
        "desc": "Методы ГИС МТ, доступные без авторизации.",
        "methods": {
            "participants": {
                "label": "Проверка УОТ по ИНН",
                "desc": "GET /participants?inns={inn} — статус, товарные группы, роли",
                "params": [{"name": "inn", "label": "ИНН участника", "type": "text"}],
                "handler": lambda p: TrueApiClient().get_participants(p["inn"]),
            },
            "mods_list": {
                "label": "Список МОД",
                "desc": "GET /mods/list — места осуществления деятельности",
                "params": [
                    {"name": "inns", "label": "ИНН (необязательно)", "type": "text"},
                    {"name": "product_groups", "label": "Товарная группа (код)", "type": "text"},
                ],
                "handler": lambda p: TrueApiClient().get_mods_list(
                    inns=p.get("inns"), product_groups=p.get("product_groups")
                ),
            },
            "cises_public": {
                "label": "Общедоступная инфо о КИ",
                "desc": "POST /cises/public-info — публичная информация о кодах",
                "params": [{"name": "cises", "label": "Список КИ (через запятую)", "type": "text"}],
                "handler": lambda p: TrueApiClient().cises_public_info(
                    [c.strip() for c in p["cises"].split(",") if c.strip()]
                ),
            },
        },
    },
    "📦 True API — коды, товары (токен)": {
        "icon": "📦",
        "desc": "Методы требующие аутентификационный токен.",
        "auth_required": True,
        "methods": {
            "product_info": {
                "label": "Инфо о товаре по GTIN",
                "desc": "GET /product/info?gtin={gtin}",
                "params": [{"name": "gtin", "label": "GTIN товара", "type": "text"}],
                "handler": lambda p, t: TrueApiClient(auth=t).product_info(p["gtin"]),
            },
            "products_gtin_list": {
                "label": "Список GTIN товаров",
                "desc": "GET /products/gtin/list",
                "params": [
                    {"name": "inn", "label": "ИНН (необязательно)", "type": "text"},
                    {"name": "product_group", "label": "Товарная группа", "type": "text"},
                ],
                "handler": lambda p, t: TrueApiClient(auth=t).products_gtin_list(
                    inn=p.get("inn"), product_group=p.get("product_group")
                ),
            },
            "cises_info": {
                "label": "Подробная инфо о КИ",
                "desc": "POST /cises/info",
                "params": [{"name": "cises", "label": "Список КИ (через запятую)", "type": "text"}],
                "handler": lambda p, t: TrueApiClient(auth=t).cises_info(
                    [c.strip() for c in p["cises"].split(",") if c.strip()]
                ),
            },
            "cises_history": {
                "label": "История движения КИ",
                "desc": "POST /cises/history",
                "params": [{"name": "cises", "label": "Список КИ (через запятую)", "type": "text"}],
                "handler": lambda p, t: TrueApiClient(auth=t).cises_history(
                    [c.strip() for c in p["cises"].split(",") if c.strip()]
                ),
            },
        },
    },
    "📄 True API — документы и чеки (токен)": {
        "icon": "📄",
        "desc": "Документы, чеки ККТ, квитанции.",
        "auth_required": True,
        "methods": {
            "documents_list": {
                "label": "Список документов",
                "desc": "GET /documents/list",
                "params": [
                    {"name": "limit", "label": "Лимит", "type": "number", "default": "100"},
                    {"name": "doc_type", "label": "Тип документа", "type": "text"},
                    {"name": "status", "label": "Статус", "type": "text"},
                ],
                "handler": lambda p, t: TrueApiClient(auth=t).documents_list(
                    limit=int(p.get("limit", 100)), doc_type=p.get("doc_type"), status=p.get("status")
                ),
            },
            "document_info": {
                "label": "Содержимое документа",
                "desc": "GET /doc/{id}/info",
                "params": [{"name": "doc_id", "label": "ID документа", "type": "text"}],
                "handler": lambda p, t: TrueApiClient(auth=t).document_info(p["doc_id"]),
            },
            "document_cises": {
                "label": "КИ по документу",
                "desc": "GET /doc/{id}/cises",
                "params": [{"name": "doc_id", "label": "ID документа", "type": "text"}],
                "handler": lambda p, t: TrueApiClient(auth=t).document_cises(p["doc_id"]),
            },
            "checks_list": {
                "label": "Список чеков ККТ",
                "desc": "GET /checks/list",
                "params": [{"name": "limit", "label": "Лимит", "type": "number", "default": "100"}],
                "handler": lambda p, t: TrueApiClient(auth=t).checks_list(limit=int(p.get("limit", 100))),
            },
        },
    },
    "🏪 Национальный каталог (API Key)": {
        "icon": "🏪",
        "desc": "Карточки товаров, справочники, категории. Требует API Key.",
        "nk_auth": True,
        "methods": {
            "nk_product": {
                "label": "Карточка товара",
                "desc": "GET /v3/feed-product?gtin={gtin}",
                "params": [{"name": "gtin", "label": "GTIN / код товара", "type": "text"}],
                "handler": lambda p, k: NkApiClient(api_key=k).get_product(p["gtin"]),
            },
            "nk_short_product": {
                "label": "Краткая карточка",
                "desc": "GET /v3/short-product?gtin={gtin}",
                "params": [{"name": "gtin", "label": "GTIN", "type": "text"}],
                "handler": lambda p, k: NkApiClient(api_key=k).get_short_product(p["gtin"]),
            },
            "nk_categories": {
                "label": "Дерево категорий",
                "desc": "GET /v3/dict/categories",
                "params": [],
                "handler": lambda p, k: NkApiClient(api_key=k).get_categories(),
            },
            "nk_brands": {
                "label": "Справочник брендов",
                "desc": "GET /v3/dict/brands",
                "params": [{"name": "name", "label": "Поиск по названию", "type": "text"}],
                "handler": lambda p, k: NkApiClient(api_key=k).get_brands(name=p.get("name")),
            },
            "nk_countries": {
                "label": "Справочник стран",
                "desc": "GET /v3/dict/countries",
                "params": [],
                "handler": lambda p, k: NkApiClient(api_key=k).get_countries(),
            },
            "nk_own_products": {
                "label": "Мои карточки",
                "desc": "GET /v3/feed-products — список собственных товаров",
                "params": [{"name": "limit", "label": "Лимит", "type": "number", "default": "100"}],
                "handler": lambda p, k: NkApiClient(api_key=k).get_own_products(limit=int(p.get("limit", 100))),
            },
            "nk_attributes": {
                "label": "Атрибуты категории",
                "desc": "GET /v3/dict/attributes?category_id={id}",
                "params": [{"name": "category_id", "label": "ID категории", "type": "number"}],
                "handler": lambda p, k: NkApiClient(api_key=k).get_attributes(int(p["category_id"])),
            },
        },
    },
    "📊 Выгрузки (токен)": {
        "icon": "📊",
        "desc": "Формирование выгрузок данных (диспенсер).",
        "auth_required": True,
        "methods": {
            "dispenser_create": {
                "label": "Создать задание на выгрузку",
                "desc": "POST /dispenser/tasks",
                "params": [
                    {"name": "task_type", "label": "Тип выгрузки (cises / errors / filter)", "type": "text"},
                ],
                "handler": lambda p, t: TrueApiClient(auth=t).dispenser_tasks_create(p["task_type"], {}),
            },
            "dispenser_status": {
                "label": "Статус задания",
                "desc": "GET /dispenser/tasks/{id}",
                "params": [{"name": "task_id", "label": "ID задания", "type": "text"}],
                "handler": lambda p, t: TrueApiClient(auth=t).dispenser_task_status(p["task_id"]),
            },
        },
    },
}


@web_bp.route("/")
def index():
    return render_template("explorer.html", tree=ENDPOINT_TREE)


@web_bp.route("/api/execute", methods=["POST"])
def execute():
    data = request.get_json()
    category = data.get("category", "")
    method = data.get("method", "")
    params = data.get("params", {})
    token = data.get("token", "")
    api_key = data.get("api_key", "")

    group = ENDPOINT_TREE.get(category, {})
    methods = group.get("methods", {})
    method_info = methods.get(method)

    if not method_info:
        return jsonify({"error": "Method not found"}), 404

    start = time.monotonic()
    try:
        from crpt.auth import TokenAuth

        handler = method_info["handler"]
        if group.get("auth_required") and token:
            result = handler(params, TokenAuth(token))
        elif group.get("nk_auth") and api_key:
            result = handler(params, api_key)
        else:
            result = handler(params)

        elapsed_ms = round((time.monotonic() - start) * 1000)
        return jsonify({"result": result, "elapsed_ms": elapsed_ms})
    except Exception as e:
        elapsed_ms = round((time.monotonic() - start) * 1000)
        return jsonify({"error": str(e), "elapsed_ms": elapsed_ms}), 500


@web_bp.route("/api/env")
def env_info():
    return jsonify({
        "sandbox_true_api_v3": BASE_URLS["sandbox"]["true_api_v3"],
        "sandbox_true_api_v4": BASE_URLS["sandbox"]["true_api_v4"],
        "sandbox_nk_api": BASE_URLS["sandbox"]["nk_api"],
        "production_true_api_v3": BASE_URLS["production"]["true_api_v3"],
        "production_nk_api": BASE_URLS["production"]["nk_api"],
    })
