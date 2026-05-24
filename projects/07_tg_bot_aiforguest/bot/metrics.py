import json
import time
from pathlib import Path

METRICS_LOG = Path("/tmp/opencode/metrics.log")

SPARKS = "▁▂▃▄▅▆▇█"
WIDTH = 10


def mark_task_start(uid: int, task_id: str, cmd: str, cmd_code: str):
    _append({
        "ts": time.time(),
        "_type": "task_start",
        "task_id": task_id, "uid": uid,
        "cmd": cmd[:200], "cmd_code": cmd_code,
    })


def mark_task_end(uid: int, task_id: str, elapsed_ms: int, delta_tok: int, cost: float):
    _append({
        "ts": time.time(),
        "_type": "task_end",
        "task_id": task_id, "uid": uid,
        "elapsed_ms": elapsed_ms,
        "delta_tok": delta_tok,
        "cost": round(cost, 6),
    })


def _append(entry: dict):
    try:
        METRICS_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(METRICS_LOG, "a") as f:
            f.write(json.dumps(entry, separators=(",", ":")) + "\n")
    except Exception:
        pass


def read_task_samples(task_id: str) -> list[dict] | None:
    if not METRICS_LOG.exists():
        return None
    try:
        with open(METRICS_LOG) as f:
            lines = f.readlines()
    except Exception:
        return None
    in_range = False
    samples = []
    for line in lines:
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = entry.get("_type")
        if t == "task_start" and entry.get("task_id") == task_id:
            in_range = True
            samples.clear()
            continue
        if t == "task_end" and entry.get("task_id") == task_id:
            in_range = False
            continue
        if in_range and "_type" not in entry:
            if all(k in entry for k in ("cpu", "mem", "dsk", "net")):
                samples.append(entry)
    return samples if samples else None


def _spark(vals: list[float]) -> str:
    if len(vals) < 2:
        return ""
    step = max(len(vals) // WIDTH, 1)
    sampled = vals[::step][:WIDTH]
    mn, mx = min(sampled), max(sampled)
    rng = mx - mn or 1
    return "".join(SPARKS[min(int((v - mn) / rng * 7), 7)] for v in sampled)


def _stats(vals: list[float]):
    return min(vals), sum(vals) / len(vals), max(vals)


def _speeds(vals: list[float], times: list[float]):
    out = [0.0]
    for i in range(1, len(vals)):
        dt = times[i] - times[i - 1]
        out.append(abs(vals[i] - vals[i - 1]) / dt if dt else 0)
    return out


def _fmt_compact(val: float, unit: str = "") -> str:
    if unit in ("GB", "TB"):
        if val >= 1024:
            return f"{val/1024:.1f}"
        return f"{val:.1f}"
    if val >= 1000:
        return f"{val:.0f}"
    if val >= 10:
        return f"{val:.1f}"
    return f"{val:.2f}"


def _fmt_net(mb_s: float) -> str:
    if mb_s >= 1048576:
        return f"{mb_s/1048576:.1f}"
    if mb_s >= 1024:
        return f"{mb_s/1024:.1f}"
    if mb_s >= 1000:
        return f"{mb_s:.0f}"
    if mb_s >= 10:
        return f"{mb_s:.1f}"
    return f"{mb_s:.2f}"


def _fmt_mem(gb: float) -> str:
    return _fmt_compact(gb, "GB")


def _fmt_disk(mb_s: float) -> str:
    if mb_s >= 1000:
        return f"{mb_s:.0f}"
    if mb_s >= 10:
        return f"{mb_s:.1f}"
    return f"{mb_s:.2f}"


def _line(icon: str, spark: str, mn, avg, mx, suffix: str) -> str:
    s = spark or SPARKS[0] * WIDTH
    return f"{icon} {s}  {mn} | {avg} | {mx} {suffix}".rstrip()


def build_metrics_block(samples: list[dict]) -> list[str]:
    if len(samples) < 2:
        return []

    ts = [s["ts"] for s in samples]
    cpu = [s["cpu"] for s in samples]
    mem = [s["mem"]["u"] / 1024 for s in samples]

    disk_r_vals = [s["dsk"]["rt"] for s in samples]
    disk_w_vals = [s["dsk"]["wt"] for s in samples]
    net_rx_vals = [s["net"]["rx"] for s in samples]
    net_tx_vals = [s["net"]["tx"] for s in samples]

    disk_r_spd = _speeds(disk_r_vals, ts)
    disk_w_spd = _speeds(disk_w_vals, ts)
    net_rx_spd = _speeds(net_rx_vals, ts)
    net_tx_spd = _speeds(net_tx_vals, ts)

    lines = []

    mn, avg, mx = _stats(cpu)
    lines.append(_line("⚡", _spark(cpu), _fmt_compact(mn), _fmt_compact(avg), _fmt_compact(mx), "%"))

    mn, avg, mx = _stats(mem)
    lines.append(_line("🧠", _spark(mem), _fmt_mem(mn), _fmt_mem(avg), _fmt_mem(mx), "GB"))

    if max(disk_r_spd) >= max(disk_w_spd):
        vals = disk_r_spd
        dsk_sfx = "MB/s R"
    else:
        vals = disk_w_spd
        dsk_sfx = "MB/s W"
    mn, avg, mx = _stats(vals)
    lines.append(_line("💾", _spark(vals), _fmt_disk(mn), _fmt_disk(avg), _fmt_disk(mx), dsk_sfx))

    if max(net_rx_spd) >= max(net_tx_spd):
        vals = net_rx_spd
        net_sfx = " RX"
    else:
        vals = net_tx_spd
        net_sfx = " TX"
    mn, avg, mx = _stats(vals)
    lines.append(_line("🌐", _spark(vals), _fmt_net(mn), _fmt_net(avg), _fmt_net(mx), "GB/s" + net_sfx))

    return lines
