from session import get_quota, get_user, get_current_session, get_session_full, _context_limit
from config import DEFAULT_MODEL, TG_ALL_DIR

def _context_hint(model):
    """Deprecated — use session._context_limit instead"""
    return _context_limit(model)


def _provider_from_model(model):
    if not model:
        return ""
    if "/" in model:
        parts = model.split("/")
        if len(parts) >= 2:
            return parts[0]
    return ""


def _short_model(model):
    if not model:
        return "not set"
    if "/" in model:
        parts = model.split("/")
        return f"{parts[-1]} | [{parts[0]}]"
    return f"{model} | [system]"


def _fmt_size(bytes_val):
    if bytes_val >= 1_000_000_000:
        return f"{bytes_val/1_000_000_000:.1f}GB"
    if bytes_val >= 1_000_000:
        return f"{bytes_val/1_000_000:.0f}MB"
    if bytes_val >= 1000:
        return f"{bytes_val/1000:.0f}KB"
    return f"{bytes_val}B"


def _fmt_tokens(t):
    if t >= 1_000_000:
        return f"{t/1_000_000:.1f}M"
    if t >= 1000:
        return f"{t//1000}K"
    return str(t)


def _vis_width(s):
    w = 0
    for ch in s:
        w += 2 if ord(ch) > 0x2000 else 1
    return w


def _model_for_user(u):
    return u.get("model") or DEFAULT_MODEL


def _escape_md(text):
    for ch in r"_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text


def _escape_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_footer(uid, user=None, agent=None, parse_mode=None, fmt_style="link",
                 live_tok=0, last_cost=0, gid=None, lid=None):
    """Единый футер — вызывается из handler._reply и monitor.status_block4"""
    data = get_session_full(uid)
    if not data:
        return ""

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    created_ts = data["session_created"]
    age_s = int(now.timestamp() - created_ts) if created_ts else 0
    if age_s >= 86400:
        age_str = f"{age_s // 86400}d {age_s % 86400 // 3600}h"
    elif age_s >= 3600:
        age_str = f"{age_s // 3600}h {age_s % 3600 // 60}m"
    else:
        age_str = f"{age_s // 60}m"

    model = data["model"]
    if "/" in model:
        parts = model.split("/")
        model_short = f"[{parts[-1]}] | [{parts[0]}]"
    else:
        model_short = f"[{model}]"

    ctx = data["context"]
    total_tok = max(data["tokens"], live_tok)
    pct = (total_tok / ctx * 100) if ctx else 0
    bar_len = 8
    filled = min(int(pct / 100 * bar_len), bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)

    last_in = data["last_input"]
    last_out = data["last_output"]
    cum_in = data["cum_input"]
    cum_out = data["cum_output"]
    total_cum = cum_in + cum_out
    cost_in_last = data["last_msg"].get("cost_in", 0) if data.get("last_msg") else 0
    cost_out_last = data["last_msg"].get("cost_out", 0) if data.get("last_msg") else 0
    cost_in_cum = data["usage"].get("cost_in", 0) if data.get("usage") else 0
    cost_out_cum = data["usage"].get("cost_out", 0) if data.get("usage") else 0
    cost = data["cost"]
    windows = cum_in // ctx if ctx else 0

    sname = data["session_name"]
    msgs = data["messages"]
    fsize = data["storage_used"]
    fcount = data["file_count"]

    if data["role"] == "super" or data["msg_limit"] is None:
        msg_part = f"{msgs}/-"
        storage_part = f"{_fmt_size(fsize)}/-"
        file_part = f"{fcount}/-"
    else:
        msg_part = f"{msgs}/{data['msg_limit']}"
        storage_part = f"{_fmt_size(fsize)}/{_fmt_size(data['storage_limit'])}"
        file_part = f"{fcount}/{data['file_limit']}"

    cost_str = f"${cost:.2f}" if cost else ""
    last_cost_str = f"${last_cost:.2f}" if last_cost else ""

    gid_use = gid if gid is not None else data.get("gid")
    lid_use = lid if lid is not None else data.get("lid")
    gid_lid = f" G#{gid_use} L#{lid_use}" if gid_use is not None and lid_use is not None else ""

    if agent:
        sname = f"{sname} [AM] {agent}"

    lines = [
        f"🤖 {model_short}",
        f"🔤 ↙ {_fmt_tokens(last_in)}💲{cost_in_last:.6f} · ↗ {_fmt_tokens(last_out)}💲{cost_out_last:.6f} · {_fmt_tokens(total_tok)} / {_fmt_tokens(ctx)} · 💰${cost_in_last + cost_out_last:.4f} · {bar} {int(pct)}%",
        f"↙ {_fmt_tokens(cum_in)}💲{cost_in_cum:.4f} · ↗ {_fmt_tokens(cum_out)}💲{cost_out_cum:.4f} · [{_fmt_tokens(total_cum)}]💰${cost_in_cum + cost_out_cum:.4f}{f' [{windows}w]' if windows > 0 else ''}{gid_lid}",
        f"📁 {sname}  [{age_str}]",
        f"💬 {msg_part} · 💾 {storage_part} · 📄 {file_part}",
    ]

    footer = "\n".join(lines)

    if parse_mode == "MarkdownV2":
        for ch in r"_*[]()~`>#+-=|{}.!":
            footer = footer.replace(ch, f"\\{ch}")
    elif parse_mode == "HTML":
        footer = footer.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    return footer


def fmt_session_list(uid, show_all=False):
    from session import list_users, rebuild_ranks, get_session_full, get_user
    from config import DEFAULT_MODEL
    users = list_users()
    sid = str(uid)
    u = users.get(sid)
    if not u:
        return "Нет данных"

    uname = u.get('name', str(uid))
    stats = session_stats if isinstance(session_stats := None, type(None)) else None
    # get stats from the actual state
    from datetime import datetime

    # collect all sessions for the user
    sessions = u.get("sessions", {})
    current = sessions.get("current")
    sess_list = sessions.get("list", {})
    if not sess_list:
        return f"📂 Сессии {uname}\n  (нет сессий)"

    # compute ranks
    ranks = rebuild_ranks(uid).get(uid, {})

    lines = [f"📂 Сессии {uname}"]
    sep = "═" * 50
    lines.append(sep)

    active_sessions = []
    archived_sessions = []

    for key, s in sess_list.items():
        st = s.get("status", "ACT")
        name = s.get("name", "-")
        created = s.get("created", 0)
        msgs = s.get("messages", 0)
        usage = s.get("usage", {}) or {}
        cost = s.get("cost", 0) or 0

        inp = usage.get("input", 0) or 0
        out = usage.get("output", 0) or 0
        total = inp + out
        cost_str = f"${cost:.2f}" if cost else "$0.00"

        gid = ranks.get(key, {}).get("gid", "-")
        lid = ranks.get(key, {}).get("lid", "-")
        gid_str = str(gid)
        lid_str = str(lid)

        created_str = datetime.fromtimestamp(created).strftime("%d.%m.%y %H:%M") if created else "-"
        age_s = int(datetime.now().timestamp() - created) if created else 0
        if age_s >= 86400:
            age_str = f"{age_s // 86400}d {age_s % 86400 // 3600}h"
        elif age_s >= 3600:
            age_str = f"{age_s // 3600}h {age_s % 3600 // 60}m"
        else:
            age_str = f"{age_s // 60}m"

        # status badge
        badge = {"ACT": "ACT", "ERR": "ERR", "ORN": "ORN", "ARC": "ARC", "DED": "DED"}.get(st, st)

        entry = {
            "key": key,
            "name": name,
            "gid": gid_str,
            "lid": lid_str,
            "status": badge,
            "msgs": msgs,
            "inp": inp,
            "out": out,
            "total": total,
            "cost": cost_str,
            "created": created_str,
            "age": age_str,
            "is_active": st in ("ACT", "ERR"),
            "is_current": key == current,
        }

        if st in ("ARC", "DED"):
            archived_sessions.append(entry)
        else:
            active_sessions.append(entry)

    # sort active by lid
    active_sessions.sort(key=lambda x: int(x["lid"]) if x["lid"].isdigit() else 999)

    # render active
    for e in active_sessions:
        marker = "✅" if e["is_current"] else "  "
        inp_s = _fmt_tokens(e["inp"]) if e["inp"] else "-"
        out_s = _fmt_tokens(e["out"]) if e["out"] else "-"
        total_s = _fmt_tokens(e["total"]) if e["total"] else "-"
        lines.append(
            f"{marker}{e['name']}  [{e['created']}]  [{e['age']}]"
        )
        lines.append(
            f" {e['gid']:>2} │ {e['lid']} │ {e['status']}│ {e['msgs']:>4} "
            f"│ ↙ {inp_s} ↗ {out_s} [{total_s}]│ {e['cost']}│"
        )

    # render archived
    if archived_sessions:
        lines.append("─" * 50)
        lines.append(" ═══ Архив ═══")
        for e in archived_sessions:
            inp_s = _fmt_tokens(e["inp"]) if e["inp"] else "-"
            out_s = _fmt_tokens(e["out"]) if e["out"] else "-"
            total_s = _fmt_tokens(e["total"]) if e["total"] else "-"
            lines.append(f"{e['name']}  [{e['created']}]  [{e['age']}]")
            lines.append(
                f" - │ - │ {e['status']}│ {e['msgs']:>4} "
                f"│ ↙ {inp_s} ↗ {out_s} [{total_s}]│ {e['cost']}│"
            )

    return "\n".join(lines)


def fmt_user_info(uid, as_super=False):
    from session import list_users
    users = list_users()
    sid = str(uid)
    u = users.get(sid)
    if not u:
        return f"Пользователь {uid} не найден"
    fcount, fsize = get_quota(uid)
    model = _model_for_user(u)
    short = _short_model(model)
    limits = u.get("limits")
    role = u.get("role", "normal")

    lines = [
        f"📊 Пользователь: {u.get('name', '-')} ({uid})",
        f"Роль: {role} · Модель: {short}",
    ]

    if limits:
        lines.append("")
        lines.append("📈 Статистика:")
        lines.append(f"  💬 {limits.get('msg', '-')} msgs")
        lines.append(f"  🔤 {_fmt_tokens(limits.get('token', 1_000_000))} tokens")
        lines.append(f"  💾 {limits.get('storage_mb', 500)}MB / 📄 {limits.get('file_count', 1000)} files")
        lines.append(f"  (текущее: {_fmt_size(fsize)} / {fcount} файлов)")

    lines.append("")
    lines.append(fmt_session_list(uid))
    return "\n".join(lines)


def fmt_quota(uid):
    fcount, fsize = get_quota(uid)
    user = get_user(uid)
    limits = user.get("limits") if user else None
    lines = [f"📁 TG_ALL/TG_{uid}/"]
    lines.append(f"💾 Использовано: {_fmt_size(fsize)}")
    lines.append(f"📄 Файлов: {fcount}")

    if limits:
        smb = limits.get("storage_mb", 500) * 1_000_000
        fc = limits.get("file_count", 1000)
        lines.append(f"Лимит: {_fmt_size(smb)} / {fc} файлов")
        lines.append(f"Свободно: {_fmt_size(smb - fsize)} / {fc - fcount} файлов")

    lines.append("")
    uploads = TG_ALL_DIR / f"TG_{uid}" / "uploads"
    if uploads.exists():
        files = sorted(uploads.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)[:15]
        if files:
            lines.append("📂 Файлы (последние 15):")
            for f in files:
                sz = _fmt_size(f.stat().st_size)
                from datetime import datetime
                mt = datetime.fromtimestamp(f.stat().st_mtime).strftime("%d.%m %H:%M")
                lines.append(f"  {f.name}  {sz}  {mt}")
    return "\n".join(lines)
