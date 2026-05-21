#!/usr/bin/env python3
"""Демон метрик: пишет JSONL в /tmp/opencode/metrics.log каждые 3с.

Управление:
  python3 metrics_logger.py start
  python3 metrics_logger.py stop
  python3 metrics_logger.py status
"""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

BASE = Path("/tmp/opencode")
LOG = BASE / "metrics.log"
PIDFILE = BASE / "metrics_logger.pid"
STOPFILE = BASE / "metrics_logger.stop"


# ── читалки /proc ──

_cpu_prev = (0, 0.0)  # (total_jiffies, idle_jiffies)


def _read_uptime() -> float:
    with open("/proc/uptime") as f:
        return float(f.read().split()[0])


def _read_cpu() -> float:
    global _cpu_prev
    with open("/proc/stat") as f:
        line = f.readline().strip().split()
    # user nice system idle iowait irq softirq steal guest guest_nice
    total = sum(int(v) for v in line[1:])
    idle = int(line[4])
    diff_total = total - _cpu_prev[0]
    diff_idle = idle - _cpu_prev[1]
    _cpu_prev = (total, idle)
    if diff_total == 0:
        return 0.0
    return round(100.0 * (diff_total - diff_idle) / diff_total, 1)


def _read_loadavg():
    with open("/proc/loadavg") as f:
        parts = f.read().split()
    return {
        "load": [float(parts[0]), float(parts[1]), float(parts[2])],
        "proc": int(parts[3].split("/")[0]),
    }


def _read_meminfo():
    with open("/proc/meminfo") as f:
        raw = {k: int(v) for line in f for k, v in [line.replace(" kB", "").split(":", 1)] for v in [v.strip()]}
    total = raw.get("MemTotal", 0) // 1024
    free = raw.get("MemFree", 0) // 1024
    cached = (raw.get("Cached", 0) + raw.get("SReclaimable", 0)) // 1024
    available = raw.get("MemAvailable", 0) // 1024
    used = total - free - cached
    swp_total = raw.get("SwapTotal", 0) // 1024
    swp_free = raw.get("SwapFree", 0) // 1024
    swp_used = swp_total - swp_free
    return {
        "mem": {"t": total, "u": used, "f": free, "c": cached, "a": available},
        "swp": {"t": swp_total, "u": swp_used, "f": swp_free},
    }


def _read_disk():
    # статистика I/O (накопленная)
    with open("/proc/diskstats") as f:
        r_sectors = w_sectors = 0
        for line in f:
            parts = line.split()
            if len(parts) >= 14 and parts[2][-1].isdigit():
                r_sectors += int(parts[5])
                w_sectors += int(parts[9])
    # статистика файловой системы /
    si = os.statvfs("/")
    total = si.f_frsize * si.f_blocks // 1024 // 1024
    free = si.f_frsize * si.f_bfree // 1024 // 1024
    avail = si.f_frsize * si.f_bavail // 1024 // 1024
    used = total - free
    return {
        "dsk": {
            "rt": r_sectors * 512 // 1024,  # kB read total
            "wt": w_sectors * 512 // 1024,  # kB write total
            "t": total,
            "u": used,
            "f": free,
            "a": avail,
        }
    }


def _read_net():
    with open("/proc/net/dev") as f:
        f.readline()
        f.readline()
        rx = tx = 0
        for line in f:
            parts = line.strip().split()
            if parts[0].startswith("lo:") or ":" not in parts[0]:
                continue
            rx += int(parts[1])
            tx += int(parts[9])
    return {"net": {"rx": rx, "tx": tx}}


def _read_top5():
    try:
        out = subprocess.check_output(
            ["ps", "-eo", "comm=,%cpu=,%mem=,rss=,etimes=", "--no-headers"],
            timeout=3, text=True
        )
        groups = {}
        for line in out.strip().split("\n"):
            parts = line.strip().split()
            if len(parts) < 5:
                continue
            comm = parts[0][:20]
            try:
                cpu = float(parts[1])
                rss = int(parts[3])
                mem_mb = rss // 1024
                etime = int(parts[4])
            except (ValueError, IndexError):
                continue
            g = groups.setdefault(comm, {"cpu": 0.0, "mem": 0, "cnt": 0, "etime": 0})
            g["cpu"] += cpu
            g["mem"] += mem_mb
            g["cnt"] += 1
            g["etime"] = max(g["etime"], etime)
        sorted_g = sorted(groups.items(), key=lambda x: x[1]["cpu"], reverse=True)[:5]
        return [[n, round(g["cpu"], 1), g["mem"], g["cnt"], g["etime"]] for n, g in sorted_g]
    except Exception:
        return []


def collect() -> dict:
    uptime = _read_uptime()
    cpu = _read_cpu()
    la = _read_loadavg()
    mem = _read_meminfo()
    dsk = _read_disk()
    net = _read_net()
    top = _read_top5()
    out = {"ts": time.time(), "cpu": cpu, "uptime": uptime}
    out.update(la)
    out.update(mem)
    out.update(dsk)
    out.update(net)
    out["top"] = top
    return out


# ── управление ──


def start():
    BASE.mkdir(parents=True, exist_ok=True)
    pid = os.fork()
    if pid > 0:
        with open(PIDFILE, "w") as f:
            f.write(str(pid))
        print(f"metrics_logger started (PID: {pid})")
        return
    # дочерний процесс
    os.setsid()
    sys.stdin.close()
    with open(os.devnull, "w") as null:
        os.dup2(null.fileno(), 1)
        os.dup2(null.fileno(), 2)
    _loop()


def _loop():
    # первый замер cpu будет 0 — пропускаем
    with open(LOG, "a") as log:
        pass
    while not STOPFILE.exists():
        entry = collect()
        with open(LOG, "a") as f:
            f.write(json.dumps(entry, separators=(",", ":")) + "\n")
        time.sleep(3)
    PIDFILE.unlink(missing_ok=True)
    os._exit(0)


def stop():
    STOPFILE.touch()
    pid = _read_pid()
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    print("metrics_logger stopped")


def status():
    pid = _read_pid()
    if pid:
        try:
            os.kill(pid, 0)
            print(f"metrics_logger running (PID: {pid})")
            return
        except ProcessLookupError:
            pass
    print("metrics_logger not running")


def _read_pid():
    try:
        return int(PIDFILE.read_text().strip())
    except (FileNotFoundError, ValueError):
        return None


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "start":
        if PIDFILE.exists():
            p = int(PIDFILE.read_text().strip())
            if os.path.exists(f"/proc/{p}"):
                print(f"metrics_logger already running (PID: {p})")
                sys.exit(0)
            PIDFILE.unlink(missing_ok=True)
        STOPFILE.unlink(missing_ok=True)
        start()
    elif cmd == "stop":
        stop()
        time.sleep(1)
        PIDFILE.unlink(missing_ok=True)
        STOPFILE.unlink(missing_ok=True)
    elif cmd == "status":
        status()
    else:
        print(f"Usage: {sys.argv[0]} {{start|stop|status}}")
