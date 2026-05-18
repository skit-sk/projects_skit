import re
import subprocess
import json
import signal
import threading
import os
import select
import time as _time
import logging
from config import DEFAULT_MODEL, TG_ALL_DIR

_log = logging.getLogger("tg_bot")

_active_processes: dict[int, subprocess.Popen] = {}
_ACTIVE_START: dict[int, float] = {}
_ACTIVE_TOKENS: dict[int, int] = {}
_TOKEN_FINAL: dict[int, int] = {}


def cancel_process(uid: int):
    proc = _active_processes.pop(uid, None)
    if proc:
        try:
            proc.kill()
            proc.wait(timeout=5)
        except Exception:
            pass


def get_process_info(uid):
    proc = _active_processes.get(uid)
    if not proc or proc.returncode is not None:
        return None
    start = _ACTIVE_START.get(uid, _time.time())
    elapsed = int(_time.time() - start)
    mm, ss = divmod(elapsed, 60)
    try:
        r = subprocess.run(
            ["ps", "-p", str(proc.pid), "-o", "%cpu=,%mem=,rss=", "--no-headers"],
            capture_output=True, text=True, timeout=3
        )
        parts = r.stdout.strip().split()
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
    tokens = _ACTIVE_TOKENS.get(uid, 0)
    return {
        "mem_mb": mem_mb,
        "cpu": cpu,
        "time": f"{mm:02d}:{ss:02d}",
        "tokens": tokens,
    }


def get_top5():
    try:
        r = subprocess.run(
            ["ps", "-eo", "comm=,%cpu=,%mem=,rss=,etimes=", "--no-headers"],
            capture_output=True, text=True, timeout=3
        )
        rows = r.stdout.strip().split("\n")
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
        entries = []
        for comm, g in sorted_g:
            mm, ss = divmod(g["max_etime"], 60)
            hh, mm = divmod(mm, 60)
            t_str = f"{hh:02d}:{mm:02d}:{ss:02d}" if hh else f"{mm:02d}:{ss:02d}"
            entries.append((comm, g['cpu'], g['mem_mb'], g['count'], t_str))
        if not entries:
            return []
        c_len = max(len(e[0]) for e in entries) + 2
        head_name = "NAME"
        header = f"  {head_name:{c_len}s} {'CPU':>7s} {'MEM':>6s} {'CNT':>4s} {'ELAPSED':>8s}"
        sep = "  " + "━" * (c_len + 7 + 6 + 4 + 8 + 6)
        rows = [
            f"  {comm:{c_len}s} {cpu:6.1f}% {mem:5d}MB {cnt:4d} {t:>8s}"
            for comm, cpu, mem, cnt, t in entries
        ]
        result = [header] + rows
        return result
    except Exception:
        return []

BLOCKED_PATTERNS = [
    r'\.env', r'\btoken\b', r'\bsecret\b', r'\bpassword\b',
    r'\.opencode', r'auth\.json',
    r'\.\./',
    r'/etc/', r'/proc/', r'/sys/', r'/root', r'/home',
    r'\bpip (install|uninstall|list)\b', r'\bapt\b', r'\bapt-get\b',
    r'\bsudo\b', r'\bchmod\b', r'\bchown\b', r'\bpasswd\b',
    r'tg_opencode_bot', r'TG_BOT_TOKEN', r'state\.json',
    r'\bkill\b', r'\bpkill\b', r'\bshutdown\b',
    r'\bcurl\s', r'\bwget\s',
    r'\b(?:switch|change|exit|leave)\s+(?:to\s+)?(?:agent|mode|build|plan)\b',
    r'(?:переключ|смен|выход|покин)\w*\s+(?:в\s+)?(?:agent|mode|build|plan)\b',
    r'--agent', r'--mode', r'plan.exit', r'plan.mode',
    r'\brm\s+-rf\b', r'\bmv\s+\.\.', r'\bcp\s+\.\.',
    r'\bdd\b', r'\bmkfs\b', r'\bfdisk\b',
    r'>\s*/dev/', r'\|\s*tee\s', r'\bexec\s',
    r'\$\{', r'`.*`',
]

COMPILED = [re.compile(p, re.IGNORECASE) for p in BLOCKED_PATTERNS]


def pre_filter(user_id, text):
    if not text:
        return False, ""
    for p in COMPILED:
        m = p.search(text)
        if m:
            return True, f"pattern: {m.group()}"
    return False, ""




def _is_rate_limit(data: dict) -> bool:
    err = data.get("error")
    if not err:
        return False
    if isinstance(err, dict):
        sc = err.get("statusCode") or err.get("code")
        if sc == 429:
            return True
        err_text = json.dumps(err).lower()
        for kw in ["rate limit", "FreeUsageLimitError", "too many requests", "retry-after"]:
            if kw in err_text:
                return True
    if isinstance(err, str) and "429" in err:
        return True
    return False


def _is_rate_limit_text(text: str) -> bool:
    t = text.lower()
    for kw in ["rate limit", "FreeUsageLimitError", "too many requests", "retry-after", "statuscode\": 429"]:
        if kw in t:
            return True
    return False


_RATELIMIT_MSG = (
    "⚠️ Лимит запросов к модели исчерпан.\n"
    "Подождите несколько минут или переключите модель:\n"
    "  /models — список моделей\n"
    "  /setmodel <провайдер/модель> — сменить модель"
)

_PERMISSION_MSG = (
    "⚠️ Требуется подтверждение на исполнение.\n"
    "Нажмите /build, затем повторите запрос."
)


def _cleanup_process(user_id):
    _TOKEN_FINAL[user_id] = _ACTIVE_TOKENS.get(user_id, 0)
    _active_processes.pop(user_id, None)
    _ACTIVE_START.pop(user_id, None)
    _ACTIVE_TOKENS.pop(user_id, None)


def _abort(proc, user_id, msg):
    try:
        proc.kill()
        proc.wait(timeout=5)
    except Exception:
        pass
    _cleanup_process(user_id)
    return None, None, [], msg


DANGEROUS_CMDS = [
    r'rm\s+-rf\s+/', r'chmod\s+777', r'chown\b',
    r'>\s*/dev/', r'mkfs', r'dd\s+if=',
    r'fdisk', r'mkswap', r'>\s+/dev/',
]
DANGEROUS_RE = re.compile("|".join(f"(?:{p})" for p in DANGEROUS_CMDS), re.IGNORECASE)


def _extract_cmd_from_line(data: dict) -> str:
    """Извлекает команду из JSON-строки вывода opencode"""
    # tool call: bash, read, edit, etc.
    inp = data.get("state", {}).get("input", {})
    if isinstance(inp, dict):
        cmd = inp.get("command", "") or inp.get("text", "") or ""
        if cmd:
            return cmd
    # fallback: part.command / part.text
    part = data.get("part", {})
    return part.get("command", "") or part.get("text", "") or ""


def post_check(user_id, json_lines):
    violations = []
    for line in json_lines:
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        cmd = _extract_cmd_from_line(data)
        if not cmd:
            continue
        for p in COMPILED:
            if p.search(cmd):
                violations.append(cmd[:80])
                break
        if DANGEROUS_RE.search(cmd):
            violations.append(cmd[:80])
    return violations


def run_opencode(user_id, message, opencode_id=None, model=None, work_dir=None, files=None, title=None, agent=None):
    if work_dir is None:
        work_dir = TG_ALL_DIR / f"TG_{user_id}"
        work_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "opencode", "run",
        "--dir", str(work_dir),
        "--format", "json",
    ]
    if agent:
        cmd.extend(["--agent", agent])
    if opencode_id:
        cmd.extend(["--session", opencode_id])
    elif title:
        cmd.extend(["--title", title])
    if model:
        cmd.extend(["--model", model])
    if files:
        for f in files:
            cmd.extend(["--file", str(f)])
    cmd.append(message)

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError:
        return None, None, [], "opencode not found in PATH"
    except Exception as e:
        return None, None, [], f"Ошибка: {e}"

    _active_processes[user_id] = proc
    _ACTIVE_START[user_id] = _time.time()

    text_parts = []
    all_lines = []
    parsed_session_id = opencode_id
    _stderr_buf = ""

    try:
        _line_buf = ""
        while proc.poll() is None:
            r, _, _ = select.select([proc.stdout, proc.stderr], [], [], 3)
            for fd in r:
                if fd == proc.stdout:
                    raw = os.read(proc.stdout.fileno(), 65536)
                    if not raw:
                        break
                    _line_buf += raw.decode("utf-8", errors="replace")
                    while "\n" in _line_buf:
                        raw_line, _line_buf = _line_buf.split("\n", 1)
                        all_lines.append(raw_line + "\n")
                        line = raw_line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            evt = data.get("type", "?")
                            if evt in ("permission", "tool_approval"):
                                _log.warning("Permission request (stdout) for uid=%s", user_id)
                                return _abort(proc, user_id, _PERMISSION_MSG)
                            if _is_rate_limit(data):
                                _log.warning("Rate limit detected for uid=%s", user_id)
                                return _abort(proc, user_id, _RATELIMIT_MSG)
                            if evt == "step_start":
                                sid = data.get("sessionID") or data.get("part", {}).get("sessionID")
                                if sid:
                                    parsed_session_id = sid
                            if evt == "text":
                                t = data.get("part", {}).get("text", "")
                                if t:
                                    text_parts.append(t)
                            tok = (data.get("tokens") or
                                   data.get("step", {}).get("tokens") or
                                   data.get("part", {}).get("tokens"))
                            if isinstance(tok, dict):
                                total = tok.get("total")
                                if total:
                                    _ACTIVE_TOKENS[user_id] = total
                            if not parsed_session_id:
                                sid = (data.get("sessionID") or
                                       data.get("part", {}).get("sessionID") or
                                       data.get("step", {}).get("sessionID"))
                                if sid:
                                    parsed_session_id = sid
                        except json.JSONDecodeError:
                            pass
                elif fd == proc.stderr:
                    raw = os.read(proc.stderr.fileno(), 65536)
                    if raw:
                        _stderr_buf += raw.decode("utf-8", errors="replace")
                        if "permission requested" in _stderr_buf.lower() and "auto-rejecting" not in _stderr_buf.lower():
                            _log.warning("Permission request (stderr) for uid=%s", user_id)
                            return _abort(proc, user_id, _PERMISSION_MSG)
        # drain remaining stderr
        try:
            while True:
                raw = os.read(proc.stderr.fileno(), 65536)
                if not raw:
                    break
                _stderr_buf += raw.decode("utf-8", errors="replace")
        except (BlockingIOError, OSError):
            pass
        # drain remaining stdout
        while True:
            try:
                raw = os.read(proc.stdout.fileno(), 65536)
                if not raw:
                    break
                _line_buf += raw.decode("utf-8", errors="replace")
            except (BlockingIOError, OSError):
                break
        if _line_buf:
            for part in _line_buf.split("\n"):
                if part:
                    all_lines.append(part + "\n")
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        _TOKEN_FINAL[user_id] = _ACTIVE_TOKENS.get(user_id, 0)
        _active_processes.pop(user_id, None)
        _ACTIVE_START.pop(user_id, None)
        _ACTIVE_TOKENS.pop(user_id, None)
        return None, None, [], "Превышено время ожидания (300с)"
    except Exception:
        proc.kill()
        proc.wait()
        raise
    finally:
        _TOKEN_FINAL[user_id] = _ACTIVE_TOKENS.get(user_id, 0)
        _active_processes.pop(user_id, None)
        _ACTIVE_START.pop(user_id, None)
        _ACTIVE_TOKENS.pop(user_id, None)

    stderr = _stderr_buf
    lines = all_lines

    response = "".join(text_parts).strip()

    if not response:
        if _is_rate_limit_text(stderr):
            _log.warning("Rate limit in stderr for uid=%s", user_id)
            return None, parsed_session_id, lines, _RATELIMIT_MSG
        had_tool_calls = any('"tool"' in ln for ln in lines)
        if had_tool_calls:
            response = "✅ Готово."
        else:
            stderr_clean = "\n".join(
                ln for ln in stderr.split("\n")
                if not any(p in ln.lower() for p in
                    ["permission requested", "auto-rejecting",
                     "not found. falling back", "falling back to default"])
            ).strip()
            response = stderr_clean or "(пустой ответ)"

    return response, parsed_session_id, lines, None
