import os
import time
from collections import defaultdict


def _read_proc(path):
    try:
        with open(path) as f:
            return f.read()
    except Exception:
        return ""


def _fmt_bytes(b):
    b = int(b)
    if b >= 1_000_000_000:
        return f"{b/1_000_000_000:.1f}G"
    if b >= 1_000_000:
        return f"{b/1_000_000:.0f}M"
    if b >= 1000:
        return f"{b/1000:.0f}K"
    return str(b)


def _fmt_time(s):
    s = int(s)
    d, s = divmod(s, 86400)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    if d:
        return f"{d}d {h:02d}h{m:02d}"
    return f"{h:02d}h{m:02d}"


def get_system_status():
    lines = []

    # uptime + load
    uptime_raw = _read_proc("/proc/uptime").strip()
    if uptime_raw:
        parts = uptime_raw.split()
        uptime_secs = float(parts[0])
        loads = parts[1].split(",") if len(parts) > 1 else ["0", "0", "0"]
        line = f"uptime: {_fmt_time(uptime_secs)}  load: {' '.join(loads)}"
    else:
        line = "uptime: N/A"
    lines.append(line)

    # MEM
    meminfo = _read_proc("/proc/meminfo")
    mem_total = mem_avail = swap_total = swap_free = 0
    cached = 0
    for ln in meminfo.split("\n"):
        if ln.startswith("MemTotal:"):
            mem_total = int(ln.split()[1])
        elif ln.startswith("MemAvailable:"):
            mem_avail = int(ln.split()[1])
        elif ln.startswith("Cached:"):
            cached = int(ln.split()[1])
        elif ln.startswith("SwapTotal:"):
            swap_total = int(ln.split()[1])
        elif ln.startswith("SwapFree:"):
            swap_free = int(ln.split()[1])
    mem_used = mem_total - mem_avail
    swap_used = swap_total - swap_free
    lines.append(
        f"MEM: {_fmt_bytes(mem_total*1024)} total · "
        f"{_fmt_bytes(mem_used*1024)} used · "
        f"{_fmt_bytes(mem_avail*1024)} free · "
        f"{_fmt_bytes(cached*1024)} cache"
    )
    lines.append(
        f"SWAP: {_fmt_bytes(swap_total*1024)} · "
        f"{_fmt_bytes(swap_used*1024)} used · "
        f"{_fmt_bytes(swap_free*1024)} free"
    )

    # PROCESSES
    try:
        pcount = len(os.listdir("/proc")) - 2
    except Exception:
        pcount = 0
    lines.append(f"PROCESSES: {pcount} total")

    # NET: sum RX/TX from all interfaces
    net_dev = _read_proc("/proc/net/dev")
    rx_total = tx_total = 0
    for ln in net_dev.split("\n")[2:]:
        if ":" in ln:
            parts = ln.strip().split()
            rx_total += int(parts[1])
            tx_total += int(parts[9])
    lines.append(f"NET: RX {_fmt_bytes(rx_total)} · TX {_fmt_bytes(tx_total)}")

    # DISK: sum read/write sectors from all disks
    diskstat = _read_proc("/proc/diskstats")
    read_sectors = write_sectors = 0
    for ln in diskstat.split("\n"):
        parts = ln.strip().split()
        if len(parts) >= 14:
            name = parts[2]
            if name and not name[0].isdigit() and not name.startswith("loop"):
                read_sectors += int(parts[5])
                write_sectors += int(parts[9])
    lines.append(f"DISK: READ {_fmt_bytes(read_sectors*512)} · WRITE {_fmt_bytes(write_sectors*512)}")

    # TOP processes grouped
    try:
        import subprocess
        result = subprocess.run(
            ["ps", "-eo", "comm=,%cpu=,%mem=", "--no-headers"],
            capture_output=True, text=True, timeout=5
        )
        groups = defaultdict(lambda: {"cnt": 0, "cpu": 0.0, "mem": 0.0})
        for row in result.stdout.strip().split("\n"):
            p = row.strip().split()
            if len(p) < 3:
                continue
            comm = p[0]
            try:
                cpu = float(p[1])
                mem = float(p[2])
            except ValueError:
                continue
            if comm.startswith("opencode"):
                key = "opencode"
            elif comm.startswith("python") or "python" in comm:
                key = "python3"
            elif "browser" in comm:
                key = "agent-browser"
            elif comm in ("sh", "-sh", "su"):
                key = "sh/su"
            elif comm in ("bash", "zsh", "-bash", "-zsh"):
                key = "bash"
            elif comm in ("tail", "sort", "ps", "awk", "grep", "sed", "cut", "head"):
                key = "tail/sort/ps/awk"
            else:
                key = comm[:20]
            groups[key]["cnt"] += 1
            groups[key]["cpu"] += cpu
            groups[key]["mem"] += mem

        sorted_g = sorted(groups.items(), key=lambda x: -x[1]["cpu"])
        c_len = max(len(k) for k in [g[0] for g in sorted_g] + ["COMMAND"])
        c_len = max(c_len, 10)
        lines.append("")
        lines.append(f"  {'COMMAND':{c_len}s}  CNT  %CPU  %MEM")
        for comm, g in sorted_g:
            lines.append(f"  {comm:{c_len}s}  {g['cnt']:3d}  {g['cpu']:5.1f} "
                         f"{g['mem']:5.1f}")
    except Exception:
        pass

    return "\n".join(lines)


def get_uptime():
    """Системный uptime в формате dd hh:mm:ss"""
    try:
        with open('/proc/uptime', 'r') as f:
            secs = int(float(f.read().split()[0]))
        return _fmt_time(secs)
    except Exception:
        return "—"
