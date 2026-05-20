import asyncio

_task_locks: dict[str, asyncio.Lock] = {}

TASK_GROUPS = {
    "opencode": "Выполнение opencode",
    "audit": "Аудит IP",
    "screenshot": "Скриншот/коллаж",
    "voice": "Распознавание голоса",
    "youtube": "Транскрипция YouTube",
}

TASK_INSTANT = {
    "start", "info", "menu", "models", "sysinfo",
    "sessions", "switch", "drop", "purge",
    "quota", "files", "rm", "clean", "format",
    "users", "setmodel", "request", "deny",
    "approve", "approve-model", "setlimit",
    "adduser", "removeuser", "userinfo", "view",
    "rename", "dropsession",
    "build", "plan", "cd", "unauthorized",
    "sandbox", "broadcast", "shutdown",
    "sc_positions", "tg_positions",
    "task_stats", "task_errors",
}


def _task_key(uid: int, task_type: str) -> str:
    return f"{uid}:{task_type}"


def _type_by_cmd(cmd: str) -> str | None:
    parts = cmd.strip().split()
    base = parts[0].lower().lstrip("/") if parts else "text"
    if base in TASK_INSTANT:
        return "instant"
    if base in ("sc", "wg", "wgc", "sc_positions", "tg_positions"):
        return "screenshot"
    if base in ("audit_ip", "audit_deep"):
        return "audit"
    if base in ("voice",):
        return "voice"
    if base in ("youtube",):
        return "youtube"
    return "opencode"


async def acquire(uid: int, cmd: str) -> tuple[bool, str]:
    task_type = _type_by_cmd(cmd)
    if task_type == "instant":
        return True, ""

    key = _task_key(uid, task_type)
    lock = _task_locks.setdefault(key, asyncio.Lock())

    if lock.locked():
        msg = TASK_GROUPS.get(task_type, task_type)
        return False, f"⏳ {msg} уже выполняется. Дождитесь ответа."

    await lock.acquire()
    return True, ""


def release(uid: int, cmd: str):
    task_type = _type_by_cmd(cmd)
    if task_type == "instant":
        return
    key = _task_key(uid, task_type)
    lock = _task_locks.get(key)
    if lock and lock.locked():
        lock.release()
