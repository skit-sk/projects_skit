import json, os, time
from pathlib import Path

LOG_FILE = Path("/tmp/opencode/transcript.log")


def _read_proc_stats() -> dict:
    cpu = 0.0
    mem_mb = 0
    net_rx_kb = 0
    net_tx_kb = 0
    disk_read_mb = 0
    disk_write_mb = 0
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    mem_mb = int(line.split()[1]) // 1024
                    break
    except Exception:
        pass
    try:
        with open("/proc/self/io") as f:
            for line in f:
                if line.startswith("read_bytes:"):
                    disk_read_mb = int(line.split()[1]) // (1024 * 1024)
                elif line.startswith("write_bytes:"):
                    disk_write_mb = int(line.split()[1]) // (1024 * 1024)
    except Exception:
        pass
    try:
        with open("/proc/net/dev") as f:
            for line in f:
                if "eth0" in line or "ens" in line:
                    parts = line.split()
                    rx = int(parts[1])
                    tx = int(parts[9])
                    net_rx_kb = rx // 1024
                    net_tx_kb = tx // 1024
    except Exception:
        pass
    return {
        "cpu_pct": cpu,
        "mem_mb": mem_mb,
        "net_rx_kb": net_rx_kb,
        "net_tx_kb": net_tx_kb,
        "disk_read_mb": disk_read_mb,
        "disk_write_mb": disk_write_mb,
    }


def log_step(step: str, model: str = "", tokens_in: int = 0, tokens_out: int = 0,
             cost: float = 0.0, duration_sec: float = 0.0, output_chars: int = 0,
             chain: str = "", uid: str = ""):
    entry = {"_type": "transcript_step", "ts": time.time(), "step": step,
             "model": model, "tokens_in": tokens_in, "tokens_out": tokens_out,
             "cost": cost, "duration_sec": duration_sec, "output_chars": output_chars,
             "chain": chain, "uid": uid}
    entry.update(_read_proc_stats())
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def log_start(cmd: str, chain: str, model: str, uid: str, url: str = "",
              audio_duration_sec: float = 0.0):
    entry = {"_type": "transcript_start", "ts": time.time(), "cmd": cmd,
             "chain": chain, "model": model, "uid": uid, "url": url,
             "audio_duration_sec": audio_duration_sec}
    entry.update(_read_proc_stats())
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def log_end(total_sec: float, total_cost: float, total_tokens_in: int,
            total_tokens_out: int, output_file: str, steps: list[str],
            chain: str = "", uid: str = ""):
    entry = {"_type": "transcript_end", "ts": time.time(), "total_sec": total_sec,
             "total_cost": total_cost, "total_tokens_in": total_tokens_in,
             "total_tokens_out": total_tokens_out, "output_file": output_file,
             "steps": steps, "chain": chain, "uid": uid}
    entry.update(_read_proc_stats())
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
