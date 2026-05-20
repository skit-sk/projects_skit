import asyncio
import subprocess
import time as _time
from collections import defaultdict
from templates import _fmt_tokens, _fmt_size, _short_model
from session import _context_limit
from system_info import get_uptime

_log = None


def _log_init():
    global _log
    if _log is None:
        import logging
        _log = logging.getLogger("tg_bot")


_processes: dict[int, subprocess.Popen] = {}
_starts: dict[int, float] = {}
_tokens: dict[int, int] = {}
_offsets: dict[int, int] = {}
_finals: dict[int, int] = {}
_deltas: dict[int, int] = {}
_actives: dict[int, dict] = {}
_input_tokens: dict[int, int] = {}
_output_tokens: dict[int, int] = {}
_cost: dict[int, float] = {}
_input_offsets: dict[int, int] = {}
_output_offsets: dict[int, int] = {}
_cost_offsets: dict[int, float] = {}
_input_finals: dict[int, int] = {}
_output_finals: dict[int, int] = {}
_cost_finals: dict[int, float] = {}


# ── State API ──

def register(uid: int, proc: subprocess.Popen):
    _processes[uid] = proc
    _starts[uid] = _time.time()


def set_offset(uid: int, offset: int, inp=0, out=0, cost=0.0):
    _offsets[uid] = offset
    _input_offsets[uid] = inp
    _output_offsets[uid] = out
    _cost_offsets[uid] = cost


def update_tokens(uid: int, value: int, inp=0, out=0, cost=0.0):
    if value > _tokens.get(uid, 0):
        _tokens[uid] = value
    if inp > _input_tokens.get(uid, 0):
        _input_tokens[uid] = inp
    if out > _output_tokens.get(uid, 0):
        _output_tokens[uid] = out
    if cost > _cost.get(uid, 0):
        _cost[uid] = cost


def finalize(uid: int):
    tok = _tokens.get(uid, 0)
    off = _offsets.get(uid, 0)
    _finals[uid] = tok
    _deltas[uid] = max(0, tok - off)
    _input_finals[uid] = max(0, _input_tokens.get(uid, 0) - _input_offsets.get(uid, 0))
    _output_finals[uid] = max(0, _output_tokens.get(uid, 0) - _output_offsets.get(uid, 0))
    _cost_finals[uid] = max(0.0, _cost.get(uid, 0.0) - _cost_offsets.get(uid, 0.0))


def get_final(uid: int) -> int:
    return _finals.get(uid, 0)


def get_delta(uid: int) -> int:
    return _deltas.get(uid, 0)


def get_session_usage(uid: int, sess: dict | None) -> dict:
    if not sess:
        return {"total": 0, "input": 0, "output": 0, "cost": 0.0}
    usage = sess.get("usage", {}) or {}
    cost = sess.get("cost", 0) or 0
    return {
        "total": sess.get("tokens", 0) or 0,
        "input": usage.get("input", 0) or 0,
        "output": usage.get("output", 0) or 0,
        "cost": cost,
    }


def cleanup(uid: int):
    _processes.pop(uid, None)
    _starts.pop(uid, None)
    _tokens.pop(uid, None)
    _offsets.pop(uid, None)
    # keep _finals for get_final()
    _deltas.pop(uid, None)
    _actives.pop(uid, None)
    _input_tokens.pop(uid, None)
    _output_tokens.pop(uid, None)
    _cost.pop(uid, None)
    _input_offsets.pop(uid, None)
    _output_offsets.pop(uid, None)
    _cost_offsets.pop(uid, None)
    _input_finals.pop(uid, None)
    _output_finals.pop(uid, None)
    _cost_finals.pop(uid, None)


def is_active(uid: int) -> bool:
    proc = _processes.get(uid)
    return proc is not None and proc.returncode is None


def get_process(uid: int) -> subprocess.Popen | None:
    return _processes.get(uid)


# ── Info ──

async def info(uid: int) -> dict | None:
    proc = _processes.get(uid)
    if not proc or proc.returncode is not None:
        return None
    start = _starts.get(uid, _time.time())
    elapsed = int(_time.time() - start)
    mm, ss = divmod(elapsed, 60)
    try:
        rproc = await asyncio.create_subprocess_exec(
            "ps", "-p", str(proc.pid), "-o", "%cpu=,%mem=,rss=", "--no-headers",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await asyncio.wait_for(rproc.communicate(), timeout=5)
        parts = stdout.decode().strip().split()
        if len(parts) >= 3:
            cpu = float(parts[0])
            rss_kb = int(parts[2])
            mem_mb = rss_kb // 1024
        else:
            cpu = 0.0
            mem_mb = 0
    except Exception:
        cpu = 0.0
        mem_mb = 0

    tok = _tokens.get(uid, 0)
    off = _offsets.get(uid, 0)
    delta = max(0, tok - off)
    return {
        "mem_mb": mem_mb,
        "cpu": cpu,
        "time": f"{mm:02d}:{ss:02d}",
        "tokens": tok,
        "delta": delta,
    }


async def top5() -> list:
    try:
        rproc = await asyncio.create_subprocess_exec(
            "ps", "-eo", "comm=,%cpu=,%mem=,rss=,etimes=", "--no-headers",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await asyncio.wait_for(rproc.communicate(), timeout=5)
        rows = stdout.decode().strip().split("\n")
    except Exception:
        return []

    groups = {}
    for row in rows:
        parts = row.strip().split()
        if len(parts) < 5:
            continue
        comm = parts[0][:20]
        try:
            cpu = float(parts[1])
            rss_kb = int(parts[3])
            mem_mb = rss_kb // 1024
            etime = int(parts[4])
        except (ValueError, IndexError):
            continue
        if comm not in groups:
            groups[comm] = {"cpu": 0.0, "mem_mb": 0, "count": 0, "max_etime": 0}
        g = groups[comm]
        g["cpu"] += cpu
        g["mem_mb"] += mem_mb
        g["count"] += 1
        if etime > g["max_etime"]:
            g["max_etime"] = etime

    sorted_g = sorted(groups.items(), key=lambda x: x[1]["cpu"], reverse=True)[:5]
    if not sorted_g:
        return []

    entries = []
    for comm, g in sorted_g:
        mm, ss = divmod(g["max_etime"], 60)
        hh, mm = divmod(mm, 60)
        t_str = f"{hh:02d}:{mm:02d}:{ss:02d}" if hh else f"{mm:02d}:{ss:02d}"
        entries.append((comm, g["cpu"], g["mem_mb"], g["count"], t_str))

    c_len = max(len(e[0]) for e in entries) + 2
    head_name = "NAME"
    header = f"  {head_name:{c_len}s} {'CPU':>7s} {'MEM':>6s} {'CNT':>4s} {'ELAPSED':>8s}"
    rows = [
        f"  {comm:{c_len}s} {cpu:6.1f}% {mem:5d}MB {cnt:4d} {t:>8s}"
        for comm, cpu, mem, cnt, t in entries
    ]
    return [header] + rows


# ── Imports from templates ──
# _fmt_tokens, _fmt_size, _short_model, _context_hint

_user_status_mode: dict[int, str] = {}  # "auto" | "compact" | "normal" | "full"


def set_status_mode(uid: int, mode: str):
    if mode in ("auto", "compact", "normal", "full"):
        _user_status_mode[uid] = mode


def get_status_mode(uid: int) -> str:
    return _user_status_mode.get(uid, "auto")


# cache for task state (refresh every 10s)
_TASK_CACHE_DATA = None
_TASK_CACHE_TS = 0
_TASK_CACHE_SUMMARY = {"ok": 0, "running": 0, "skip": 0, "fail": 0}


def get_task_data(force=False):
    """Загрузить task_state.json с кешем на 10с"""
    global _TASK_CACHE_DATA, _TASK_CACHE_TS, _TASK_CACHE_SUMMARY
    import time as _t
    now = _t.time()
    if not force and _TASK_CACHE_DATA is not None and now - _TASK_CACHE_TS < 10:
        return _TASK_CACHE_DATA, _TASK_CACHE_SUMMARY

    try:
        from task_state import _load, cleanup_stale
        data = _load()
        data = cleanup_stale(data)
    except Exception:
        data = {"tasks": {}}

    _TASK_CACHE_DATA = data
    _TASK_CACHE_TS = now

    summary = {"ok": 0, "running": 0, "skip": 0, "fail": 0}
    for tid, task in data.get("tasks", {}).items():
        s = task.get("status", "")
        if s == "completed":
            summary["ok"] += 1
        elif s in ("running", "queued"):
            summary["running"] += 1
        elif s == "failed":
            summary["fail"] += 1
        else:
            summary["skip"] += 1

    _TASK_CACHE_SUMMARY = summary
    return data, summary


# ── DISK / NET read + speed ──

_DISK_PREV = {"read": 0, "write": 0, "ts": 0, "max_read": 0, "max_write": 0}
_NET_PREV = {"rx": 0, "tx": 0, "ts": 0, "max_rx": 0, "max_tx": 0}

def _read_proc(path):
    try:
        with open(path) as f:
            return f.read()
    except Exception:
        return ""

def _fmt_speed(v):
    v = int(v)
    if v >= 1_000_000_000:
        return f"{v/1_000_000_000:.1f}G"
    if v >= 1_000_000:
        return f"{v/1_000_000:.0f}M"
    if v >= 1000:
        return f"{v/1000:.0f}K"
    return str(v)

async def _get_disk_io():
    global _DISK_PREV
    raw = await asyncio.to_thread(_read_proc, "/proc/diskstats")
    read_sectors = write_sectors = 0
    for ln in raw.split("\n"):
        parts = ln.strip().split()
        if len(parts) >= 14:
            name = parts[2]
            if name and not name[0].isdigit() and not name.startswith("loop"):
                read_sectors += int(parts[5])
                write_sectors += int(parts[9])
    now = _time.time()
    dt = now - _DISK_PREV["ts"] if _DISK_PREV["ts"] else 1
    r_speed = (read_sectors - _DISK_PREV["read"]) * 512 / dt if _DISK_PREV["ts"] else 0
    w_speed = (write_sectors - _DISK_PREV["write"]) * 512 / dt if _DISK_PREV["ts"] else 0
    r_speed = max(0, r_speed)
    w_speed = max(0, w_speed)
    _DISK_PREV["max_read"] = max(_DISK_PREV["max_read"], r_speed)
    _DISK_PREV["max_write"] = max(_DISK_PREV["max_write"], w_speed)
    _DISK_PREV["read"] = read_sectors
    _DISK_PREV["write"] = write_sectors
    _DISK_PREV["ts"] = now
    return {
        "read": read_sectors * 512,
        "write": write_sectors * 512,
        "r_speed": _DISK_PREV["max_read"],
        "w_speed": _DISK_PREV["max_write"],
    }

async def _get_net_io():
    global _NET_PREV
    raw = await asyncio.to_thread(_read_proc, "/proc/net/dev")
    rx_total = tx_total = 0
    for ln in raw.split("\n")[2:]:
        if ":" in ln:
            parts = ln.strip().split()
            rx_total += int(parts[1])
            tx_total += int(parts[9])
    now = _time.time()
    dt = now - _NET_PREV["ts"] if _NET_PREV["ts"] else 1
    rx_speed = (rx_total - _NET_PREV["rx"]) / dt if _NET_PREV["ts"] else 0
    tx_speed = (tx_total - _NET_PREV["tx"]) / dt if _NET_PREV["ts"] else 0
    rx_speed = max(0, rx_speed)
    tx_speed = max(0, tx_speed)
    _NET_PREV["max_rx"] = max(_NET_PREV["max_rx"], rx_speed)
    _NET_PREV["max_tx"] = max(_NET_PREV["max_tx"], tx_speed)
    _NET_PREV["rx"] = rx_total
    _NET_PREV["tx"] = tx_total
    _NET_PREV["ts"] = now
    return {
        "rx": rx_total,
        "tx": tx_total,
        "rx_speed": _NET_PREV["max_rx"],
        "tx_speed": _NET_PREV["max_tx"],
    }

async def status_block1(uid: int, elapsed: int) -> list:
    inf = await info(uid)
    from session import get_session_full
    sd = get_session_full(uid)

    disk = await _get_disk_io()
    net = await _get_net_io()

    lines = []

    # Строка 1: ⏳ · ⚡ · 🧠 · 💾 · 🌐
    if inf:
        line1 = (
            f"⏳ {inf['time']} · ⚡ {inf['cpu']:.1f}% · 🧠 {inf['mem_mb']}MB"
            f" · 💾 R:{_fmt_speed(disk['read'])} W:{_fmt_speed(disk['write'])}"
            f" · 🌐 RX:{_fmt_speed(net['rx'])} TX:{_fmt_speed(net['tx'])}"
        )
    else:
        line1 = f"⏳ {elapsed//60:02d}:{elapsed%60:02d} · ⏎ Saving..."
    lines.append(line1)

    # Строка 2: 💿 Rmax Wmax · 📡 RXmax TXmax
    line2 = (
        f"💿 Rmax:{_fmt_speed(disk['r_speed'])}/s Wmax:{_fmt_speed(disk['w_speed'])}/s"
        f" · 📡 RXmax:{_fmt_speed(net['rx_speed'])}/s TXmax:{_fmt_speed(net['tx_speed'])}/s"
    )
    lines.append(line2)

    # Строка 3: ↙💲 · ↗💲 · 🔤💲 · 📊💲
    sess_tok = sd["tokens"] if sd else 0
    if inf:
        live_tok = inf["delta"]
        live_cum = inf["tokens"]
        from templates import _fmt_tokens as _ft
        cost_avg = 0.000000685
        tok_cost = round(live_tok * cost_avg, 4)
        sess_cost = round(sess_tok * cost_avg, 4)
        line3 = (
            f"↙ 0💲0.00 · ↗ {_ft(live_tok)}💲{tok_cost:.2f}"
            f" · 🔤 +{_ft(live_tok)}💲{tok_cost:.2f}"
            f" · 📊 {_ft(sess_tok)}💲{sess_cost:.2f}"
        )
    else:
        line3 = f"📊 {_fmt_size(sess_tok)} · ⏎ Saving..."
    lines.append(line3)

    return lines


async def status_block3() -> list:
    """Top 5 proc"""
    t5 = await top5()
    if not t5:
        return []
    return ["📊 Top 5 proc:"] + t5


def _resolve_mode(uid: int, elapsed: int) -> str:
    mode = get_status_mode(uid)
    if mode == "auto":
        if elapsed < 10:
            return "compact"
        elif elapsed < 50:
            return "normal"
        else:
            return "full"
    return mode


def _task_id_short(task_id: str) -> str:
    parts = task_id.split("-")
    if len(parts) >= 4:
        return f"{parts[1]}-{parts[2]}-{parts[3]}"
    return task_id


def _task_label(task_id: str, task_data: dict | None) -> str:
    if task_data:
        cmd = task_data.get("cmd", "")
        return cmd[:50] if cmd else ""
    return ""


def _session_age(uid: int) -> str:
    try:
        from session import get_session_full
        sd = get_session_full(uid)
        created = sd.get("session_created") if sd else None
        if not created:
            return "—"
        secs = int(_time.time() - created)
        d, secs = divmod(secs, 86400)
        h, m = divmod(secs, 3600)
        return f"{d}d {h:02d}h" if d else f"{h:02d}h{m:02d}m"
    except Exception:
        return "—"


async def status_block2(uid: int, task_id: str | None, elapsed: int,
                         avg_ms: int | None = None) -> list:
    if not task_id:
        return []

    mode = _resolve_mode(uid, elapsed)
    task_data, ts = get_task_data()

    tid_short = _task_id_short(task_id)
    task_info = task_data.get("tasks", {}).get(task_id, {})
    cmd_label = _task_label(task_id, task_info)

    pct = min(elapsed / 300 * 100, 99) if elapsed < 300 else 99
    bar_len = 10
    filled = int(pct / 100 * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)

    avg_str = f"avg {avg_ms//1000}s" if avg_ms else "avg —"

    lines = []
    lines.append(f"[{cmd_label}]" if cmd_label else "[—]")
    lines.append(f"  {tid_short}")
    lines.append(f"  [{ts['ok']}/{ts['ok']+ts['running']+ts['fail']+ts['skip']}] ✅{ts['ok']} 🔄{ts['running']} ❌{ts['fail']}")

    if mode == "compact":
        lines.append(f"  ⏱ {avg_str} · {elapsed}s")
        lines.append(f"  {bar} {int(pct)}%  {_compact_stat(ts)}")
    else:
        lines.append(f"  ⏱ {avg_str} · {elapsed}s")

        if mode == "normal":
            lines.append(f"  {bar} {int(pct)}%  {_compact_stat(ts)}")
            lines.append(f"  ⏱ {_session_age(uid)}")

        elif mode == "full":
            from datetime import datetime
            now = datetime.now().strftime("%d.%m.%y")
            lines.append(f"  {bar} {int(pct)}%")
            from datetime import datetime
            now = datetime.now().strftime("%d.%m.%y")
            lines.append(f"  📋 {cmd_label[:50]}  [🗓 {now}]")
            lines.append(f"  ✅ {ts['ok']}  🔄 {ts['running']}  ⏭ {ts['skip']}  ❌ {ts['fail']}  ⏱ {_session_age(uid)}")
            lines.append("")

            from task_state import get_user_name
            all_tasks = task_data.get("tasks", {})
            sorted_tasks = sorted(
                all_tasks.items(),
                key=lambda x: x[1].get("created_ms", 0), reverse=True
            )
            shown = 0
            for tid2, t2 in sorted_tasks:
                if shown >= 6:
                    break
                st = t2.get("status", "")
                emoji = {"completed": "✅", "running": "🔄",
                         "queued": "🔄", "failed": "❌"}.get(st, "⏭")
                uname = get_user_name(t2.get("uid", 0))
                label2 = t2.get("cmd", "")[:50]
                gnum = tid2.split("-")[3] if len(tid2.split("-")) >= 4 else "?"
                ctime = datetime.fromtimestamp(
                    t2.get("created_ms", 0) / 1000
                ).strftime("%d.%m.%y")
                start_ms = t2.get("start_ms")
                elapsed_ms = t2.get("elapsed_ms")
                dur = "--:--"
                start_str = "--:--"
                end_str = "--:--"
                if start_ms:
                    start_str = datetime.fromtimestamp(
                        start_ms / 1000
                    ).strftime("%H:%M:%S")
                if elapsed_ms and start_ms:
                    end_sec = (start_ms + elapsed_ms) / 1000
                    end_str = datetime.fromtimestamp(end_sec).strftime("%H:%M:%S")
                    m, s = divmod(elapsed_ms // 1000, 60)
                    dur = f"{m:02d}:{s:02d}"
                elif st == "running":
                    end_str = "..."
                lines.append(f"  {emoji} [{gnum}] [{uname}] {label2}  [🗓 {ctime}]")
                lines.append(f"  └─ {start_str} → {end_str}  [🕛 {dur}]")
                shown += 1
        else:
            lines.append(f"  ✅ {ts['ok']}  🔄 {ts['running']}  ⏭ {ts['skip']}  ❌ {ts['fail']}  ⏱ {uptime}")

    return lines


def _compact_stat(ts: dict) -> str:
    return f"✅{ts['ok']} 🔄{ts['running']} ❌{ts['fail']}"


def status_block4(uid: int, agent=None, live_tok=0) -> str:
    """Footer — делегирует build_footer"""
    from templates import build_footer
    last_cost = max(0.0, _cost.get(uid, 0.0) - _cost_offsets.get(uid, 0.0))
    return build_footer(uid, agent=agent, live_tok=live_tok, last_cost=last_cost)

    msgs = sess["messages"] if sess else 0
    if user.get("role") == "super":
        msg_part = f"{msgs}/-"
        storage_part = f"{_fmt_size(fsize)}/-"
        file_part = f"{fcount}/-"
    else:
        limits = user.get("limits")
        msg_limit = limits.get("msg", 50) if limits else 50
        storage_mb = limits.get("storage_mb", 500) if limits else 500
        file_limit = limits.get("file_count", 1000) if limits else 1000
        msg_part = f"{msgs}/{msg_limit}"
        storage_part = f"{_fmt_size(fsize)}/{_fmt_size(storage_mb * 1_000_000)}"
        file_part = f"{fcount}/{file_limit}"

    return (
        f"🤖 {short}\n"
        f"{ctx_line}\n"
        f"💬 {msg_part} · 📁 {sname}\n"
        f"💾 {storage_part} · 📄 {file_part}"
    )
