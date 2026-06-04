"""
graphics_v2 — Экспериментальная версия /graphics/v2 (Bento + Compact).

Полностью изолированный Blueprint. Использует тот же API /graphics/chart/<id>
из основного graphics.py, не дублирует логику расчётов.

Безопасно: если этот модуль сломается, основной /graphics/all продолжает работать.
"""
from flask import Blueprint, render_template
from storage import get_storage

bp = Blueprint("graphics_v2", __name__, template_folder="../templates")


@bp.route("/graphics/v2")
def all_charts_v2():
    storage = get_storage()
    objects = storage.list()
    archived_ids = set()
    for obj in objects:
        lp = obj.data.get("live_position")
        if not lp or not lp.get("hold_side"):
            archived_ids.add(obj.id)
    return render_template(
        "graphics_v2/all.html",
        objects=objects,
        archived_ids=archived_ids,
    )
