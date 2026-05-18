from session import get_quota, get_user, get_current_session
from config import DEFAULT_MODEL, TG_ALL_DIR

MODEL_CONTEXT = {
    # Claude — specific versions
    "opus-4.7": 1_000_000, "opus-4.6": 1_000_000,
    "sonnet-4.6": 1_000_000,
    "opus-4.5": 200_000, "opus-4.1": 200_000, "opus-4": 200_000,
    "sonnet-4.5": 200_000, "sonnet-4": 200_000,
    "haiku-4": 200_000,
    # Claude — generic fallback
    "haiku": 200_000, "opus": 200_000, "sonnet": 200_000, "claude": 200_000,
    # OpenAI GPT
    "gpt-5.5": 1_000_000, "gpt-5.4": 1_000_000,
    "gpt-5.3": 1_000_000, "gpt-5.2": 1_000_000, "gpt-5.1": 1_000_000,
    "gpt-5-nano": 128_000, "gpt-5": 400_000, "gpt-4": 128_000,
    # DeepSeek — all 1M
    "deepseek-v4-flash-free": 1_000_000,
    "deepseek-v4-flash": 1_000_000,
    "deepseek-v4-pro": 1_000_000,
    "deepseek-chat": 1_000_000, "deepseek-reasoner": 1_000_000,
    "deepseek": 1_000_000,
    # Gemini — all 1M
    "gemini-3.1-pro": 1_000_000, "gemini-3-pro": 1_000_000,
    "gemini-3": 1_000_000,
    "gemini-2.5": 1_000_000, "gemini-2.0": 1_000_000,
    "gemini": 1_000_000,
    # Kimi
    "kimi-k2.6": 256_000, "kimi-k2.5": 128_000,
    "kimi": 128_000,
    # Qwen
    "qwen3": 131_072, "qwen": 128_000,
    # MiniMax — all 1M
    "minimax-m2": 1_000_000, "minimax-m1": 1_000_000,
    "minimax": 1_000_000,
    # GLM
    "glm-5": 200_000,
    "glm-4.7": 200_000, "glm-4.6": 200_000,
    "glm-4.5": 128_000, "glm-4": 128_000,
    # Other
    "nemotron": 128_000, "mistral": 128_000,
}
DEFAULT_CONTEXT = 64_000


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


def _context_hint(model):
    if not model:
        return DEFAULT_CONTEXT
    for key, ctx in MODEL_CONTEXT.items():
        if key in model.lower():
            return ctx
    return DEFAULT_CONTEXT


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


def build_footer(uid, user=None, agent=None, parse_mode=None, fmt_style="link", live_tok=0):
    if user is None:
        user = get_user(uid)
    if not user:
        return ""

    fcount, fsize = get_quota(uid)
    limits = user.get("limits")
    model = _model_for_user(user)
    short = _short_model(model)
    ctx = _context_hint(model)

    key, sess = get_current_session(uid)
    sname = sess["name"] if sess else "-"

    if agent is None and sess and sess.get("_build_mode"):
        agent = "build"

    if agent:
        sname = f"{sname} [AM] {agent}"
    msgs = sess["messages"] if sess else 0

    tokens_used = sess.get("tokens", 0) if sess else 0
    show_tok = max(tokens_used, live_tok)
    if ctx:
        ctx_part = f"+{_fmt_tokens(live_tok)} · 📊 {_fmt_tokens(show_tok)} · 📁 [{_fmt_tokens(ctx)}]"
    else:
        ctx_part = f"+{_fmt_tokens(live_tok)} · 📊 {_fmt_tokens(show_tok)} · 📁 [-]"
    if user.get("role") == "super":
        msg_part = f"{msgs}/-"
        storage_part = f"{_fmt_size(fsize)}/-"
        file_part = f"{fcount}/-"
    else:
        if limits:
            msg_limit = limits.get("msg", 50)
            storage_mb = limits.get("storage_mb", 500)
            file_limit = limits.get("file_count", 1000)
            storage_bytes = storage_mb * 1_000_000
        else:
            msg_limit = 50
            storage_bytes = 500_000_000
            file_limit = 1000
        msg_part = f"{msgs}/{msg_limit}"
        storage_part = f"{_fmt_size(fsize)}/{_fmt_size(storage_bytes)}"
        file_part = f"{fcount}/{file_limit}"

    if parse_mode == "MarkdownV2":
        model_line = f"🤖 {_escape_md(short)}"
        ctx_line = _escape_md(f"💬 {msg_part} · 🔤 {ctx_part}")
        sname_line = f"📁 {_escape_md(sname)}"
        storage_line = _escape_md(f"💾 {storage_part} · 📄 {file_part}")
        footer = f"{model_line}\n{ctx_line}\n{sname_line}\n{storage_line}"
        if fmt_style == "spoiler":
            footer = f"||{footer}||"
        elif fmt_style == "mono":
            footer = f"`{footer}`"
    elif parse_mode == "HTML":
        model_line = f"🤖 {_escape_html(short)}"
        ctx_line = f"💬 {msg_part} · 🔤 {ctx_part}"
        sname_line = f"📁 {_escape_html(sname)}"
        storage_line = f"💾 {storage_part} · 📄 {file_part}"
        footer = f"{model_line}\n{ctx_line}\n{sname_line}\n{storage_line}"
        if fmt_style == "spoiler":
            footer = f'<span class="tg-spoiler">{footer}</span>'
        elif fmt_style == "mono":
            footer = f"<code>{footer}</code>"
    else:
        footer = (
            f"🤖 {short}\n"
            f"💬 {msg_part} · 🔤 {ctx_part}\n"
            f"📁 {sname}\n"
            f"💾 {storage_part} · 📄 {file_part}"
        )

    return footer


def fmt_session_list(uid):
    from session import list_users
    users = list_users()
    sid = str(uid)
    u = users.get(sid)
    if not u:
        return "Нет данных"
    lines = [f"📂 Сессии {u.get('name', uid)}:"]
    sessions = u.get("sessions", {})
    current = sessions.get("current")
    sess_list = sessions.get("list", {})
    if not sess_list:
        lines.append("  (нет сессий)")
    else:
        for key, s in sess_list.items():
            marker = "✅" if key == current else "  "
            msgs = s.get("messages", 0)
            model = s.get("model") or _model_for_user(u)
            short = _short_model(model)
            from datetime import datetime
            created = datetime.fromtimestamp(s.get("created", 0)).strftime("%d.%m %H:%M")
            lines.append(f"  {marker} [{key}] \"{s.get('name', '')}\" — {msgs} msg · {short}")
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
