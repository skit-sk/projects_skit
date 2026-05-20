import re
from datetime import datetime
from task_state import _load, get_user_name


def _fmt(ms):
    if ms >= 60000:
        return f"{ms//60000}m{ms%60000//1000}s"
    if ms >= 1000:
        return f"{ms/1000:.1f}s"
    return f"{ms}ms"


def parse_args(uid, text, role):
    parts = text.strip().split()
    depth = 1
    targets = []
    error = None

    i = 1
    while i < len(parts):
        p = parts[i]
        if p.startswith("D"):
            m = re.match(r"^D(\d+)$", p)
            if m and int(m.group(1)) >= 1:
                depth = int(m.group(1))
            elif p == "D":
                error = "❌ Неверный формат: D. Используйте D3, D5, all"
            else:
                error = f"❌ Неверный формат: {p}. Используйте D3, D5, all"
        elif p == "all":
            depth = None  # all dates
        elif p == "--all":
            if role == "super":
                targets.append("--all")
            else:
                error = "❌ Только super."
        elif p == "global":
            if role == "super":
                targets.append("global")
            else:
                error = "❌ Только super."
        elif p.isdigit():
            if role == "super":
                targets.append(int(p))
            else:
                error = "❌ Только super."
        else:
            error = f"❌ Неизвестный аргумент: {p}"
        i += 1

    if not targets and role == "super":
        targets = [uid, "global"]
    elif not targets:
        targets = [uid]

    if error:
        targets = [uid]
        if role == "super":
            targets.append("global")

    return targets, depth, error


def _format_dates(dates, depth):
    if not dates:
        return ""
    if depth is None:
        selected = list(enumerate(dates, 1))
    elif depth == 1:
        return f"  [{dates[-1]}]"
    else:
        selected = list(enumerate(dates, 1))[-depth:]

    lines = []
    total = len(dates)
    for i, (n, d) in enumerate(selected):
        prefix = "├─" if i < len(selected) - 1 else "└─"
        lines.append(f"{prefix} [{n}]-[{d}]")
    return "\n".join(lines)


def _build_section(title, rows, depth):
    lines = [title, "─" * 50]
    for row in rows:
        code = row["code"]
        count = row["count"]
        if row.get("min_ms") is not None:
            min_s = _fmt(row["min_ms"])
            avg_s = _fmt(row["total_ms"] // row["count"]) if row["count"] else "—"
            max_s = _fmt(row["max_ms"])
            line = f"{code}  [{min_s}][{avg_s}][{max_s}]  [{count}]"
        else:
            line = f"{code}  [{count}]"
        dates_str = _format_dates(row.get("dates", []), depth)
        if dates_str:
            if depth == 1:
                line += f"  {dates_str}"
            else:
                line += f"\n{dates_str}"
        lines.append(line)
    return "\n".join(lines)


def _agg_for_uid(data, uid, is_errors=False):
    sid = str(uid)
    user_name = get_user_name(uid)
    stats = data.get("stats", {})
    errors = data.get("errors", {})

    if is_errors:
        by_user = errors.get("by_user", {}).get(sid, {})
        raw = by_user.get("by_code", {})
        rows = []
        for code, cnt in raw.items():
            rows.append({"code": code, "count": cnt, "min_ms": None, "total_ms": 0, "dates": []})
        rows.sort(key=lambda r: -r["count"])
        total_err = by_user.get("count", 0)
    else:
        rows = []
        for code, s in stats.items():
            rows.append({
                "code": code,
                "count": s["count"],
                "min_ms": s["min_ms"],
                "total_ms": s["total_ms"],
                "max_ms": s["max_ms"],
                "dates": s.get("dates", []),
            })
        rows.sort(key=lambda r: -r["count"])

    title = f"{uid} [{user_name}] [{datetime.now().strftime('%d.%m.%y %H:%M')}] [{sum(r['count'] for r in rows)}]"
    return title, rows


def _agg_global(data, is_errors=False):
    stats = data.get("stats", {})
    errors = data.get("errors", {})

    if is_errors:
        ge = errors.get("global", {})
        raw = ge.get("by_code", {})
        rows = []
        for code, cnt in raw.items():
            rows.append({"code": code, "count": cnt, "min_ms": None, "total_ms": 0, "dates": []})
        rows.sort(key=lambda r: -r["count"])
        total = ge.get("count", 0)
        users = len(errors.get("by_user", {}))
    else:
        rows = []
        for code, s in stats.items():
            rows.append({
                "code": code,
                "count": s["count"],
                "min_ms": s.get("min_ms"),
                "total_ms": s.get("total_ms", 0),
                "max_ms": s.get("max_ms"),
                "dates": s.get("dates", []),
            })
        rows.sort(key=lambda r: -r["count"])
        total = sum(r["count"] for r in rows)
        users = len(data.get("users", {}))

    title = f"Global [{users} users] [{datetime.now().strftime('%d.%m.%y %H:%M')}] [{total}]"
    return title, rows


def stats_run(data, target_uids, depth):
    parts = []

    for target in target_uids:
        if target == "global":
            title, rows = _agg_global(data, is_errors=False)
            parts.append(_build_section(title, rows, depth))
        elif target == "--all":
            for sid in data.get("users", {}):
                title, rows = _agg_for_uid(data, int(sid), is_errors=False)
                if rows:
                    parts.append(_build_section(title, rows, depth))
            title, rows = _agg_global(data, is_errors=False)
            parts.append(_build_section(title, rows, depth))
        else:
            title, rows = _agg_for_uid(data, target, is_errors=False)
            if rows:
                parts.append(_build_section(title, rows, depth))

    return "\n\n".join(parts)


def errors_run(data, target_uids, depth):
    parts = []

    for target in target_uids:
        if target == "global":
            title, rows = _agg_global(data, is_errors=True)
            parts.append(_build_section(title, rows, depth))
        elif target == "--all":
            for sid in data.get("users", {}):
                title, rows = _agg_for_uid(data, int(sid), is_errors=True)
                if rows:
                    parts.append(_build_section(title, rows, depth))
            title, rows = _agg_global(data, is_errors=True)
            parts.append(_build_section(title, rows, depth))
        else:
            title, rows = _agg_for_uid(data, target, is_errors=True)
            if rows:
                parts.append(_build_section(title, rows, depth))

    return "\n\n".join(parts)
