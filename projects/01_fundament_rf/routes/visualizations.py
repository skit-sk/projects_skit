from flask import Blueprint, render_template, jsonify, request
from storage import get_storage
from infographics.visualizations import (
    sessions_heatmap,
    liquidation_risk,
    fibonacci_tool,
    multi_equity,
    session_volatility,
)


bp = Blueprint(
    "visualizations",
    __name__,
    url_prefix="/visualizations",
    template_folder="../templates/visualizations",
    static_folder="../static",
    static_url_path="/static",
)


@bp.route("/")
def index():
    s = get_storage()
    objs = []
    for o in s.list():
        sym = o.data.get("emoji_entry", {}).get("symbol", "?")
        objs.append({"id": o.id, "symbol": sym, "name": o.name})
    return render_template("visualizations/index.html", objects=objs)


@bp.route("/api/objects")
def api_objects():
    s = get_storage()
    objs = []
    for o in s.list():
        sym = o.data.get("emoji_entry", {}).get("symbol", "?")
        objs.append({"id": o.id, "symbol": sym, "name": o.name})
    return jsonify(objs)


@bp.route("/api/sessions_heatmap/<obj_id>")
def api_sessions_heatmap(obj_id):
    days = int(request.args.get("days", 90))
    metric = request.args.get("metric", "body_pct")
    view = request.args.get("view", "calendar")
    tz_offset = int(request.args.get("tz", 3))
    return jsonify(sessions_heatmap.compute(obj_id, days=days, metric=metric,
                                            view=view, timezone_offset=tz_offset))


@bp.route("/api/liquidation_risk/<obj_id>")
def api_liquidation_risk(obj_id):
    return jsonify(liquidation_risk.compute(obj_id))


@bp.route("/api/fibonacci_tool/<obj_id>")
def api_fibonacci_tool(obj_id):
    date_from = request.args.get("from")
    date_to = request.args.get("to")
    mode = request.args.get("mode", "retracement")
    return jsonify(fibonacci_tool.compute(obj_id, date_from, date_to, mode))


@bp.route("/api/multi_equity")
def api_multi_equity():
    symbols = request.args.get("symbols", "ETH,ETC,ADA")
    sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
    normalize = request.args.get("normalize", "true").lower() == "true"
    return jsonify(multi_equity.compute(sym_list, normalize=normalize))


@bp.route("/api/session_volatility/<obj_id>")
def api_session_volatility(obj_id):
    lookback = int(request.args.get("lookback_days", 90))
    metric = request.args.get("metric", "body_pct")
    return jsonify(session_volatility.compute(obj_id, lookback, metric))


@bp.route("/api/options/<module>")
def api_options(module):
    defaults = {
        "v1_sessions_heatmap": {
            "days": {"type": "int", "default": 30, "options": [7, 30, 90, 180]},
            "metric": {"type": "select", "default": "body_pct",
                       "options": ["body_pct", "total_range", "volatility", "volume"]},
            "color_scheme": {"type": "select", "default": "viridis",
                             "options": ["viridis", "plasma", "RdYlGn", "custom"]},
            "show_session_borders": {"type": "bool", "default": True},
            "show_session_labels": {"type": "bool", "default": True},
        },
        "v2_liquidation_risk": {
            "show_10x": {"type": "bool", "default": True},
            "show_5x":  {"type": "bool", "default": True},
            "show_2x":  {"type": "bool", "default": True},
            "timeline_range": {"type": "select", "default": "30d",
                               "options": ["7d", "30d", "90d", "all"]},
            "color_scheme": {"type": "select", "default": "default",
                             "options": ["default", "colorblind", "mono"]},
        },
        "v3_fibonacci_tool": {
            "mode": {"type": "select", "default": "retracement",
                     "options": ["retracement", "extension"]},
            "show_level_labels": {"type": "bool", "default": True},
            "show_price_markers": {"type": "bool", "default": True},
            "level_0":   {"type": "bool", "default": True},
            "level_236": {"type": "bool", "default": True},
            "level_382": {"type": "bool", "default": True},
            "level_5":   {"type": "bool", "default": True},
            "level_618": {"type": "bool", "default": True},
            "level_786": {"type": "bool", "default": True},
            "level_1":   {"type": "bool", "default": True},
            "level_1618":{"type": "bool", "default": True},
        },
        "v4_multi_equity": {
            "normalize": {"type": "bool", "default": True},
            "show_absolute": {"type": "bool", "default": False},
            "y_scale": {"type": "select", "default": "linear",
                        "options": ["linear", "log"]},
            "color_per_symbol": {"type": "select", "default": "auto",
                                 "options": ["auto", "custom"]},
            "show_drawdown_zones": {"type": "bool", "default": False},
        },
        "v5_session_volatility": {
            "lookback_days": {"type": "int", "default": 90,
                              "options": [7, 30, 90, 180, 365]},
            "metric": {"type": "select", "default": "body_pct",
                       "options": ["body_pct", "total_range", "volatility", "volume"]},
            "plot_type": {"type": "select", "default": "violin",
                          "options": ["violin", "box", "both"]},
            "show_outliers": {"type": "bool", "default": True},
            "show_mean_line": {"type": "bool", "default": True},
        },
    }
    return jsonify(defaults.get(module, {}))
