"""Классификация и извлечение данных из сообщений TG/Max бота."""

import re
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import Counter

# ——— Classification ——————————————————————————————————————————

_TRADING_KEYWORDS = [
    'bitget', 'long', 'short', 'usdt', 'btc', 'eth', 'сигнал',
    'midasflow', 'авто-сигнал', 'entry', 'take profit', 'stop loss',
    'long entry', 'short entry',
]

_TRADING_SYMBOL_RE = re.compile(
    r'\b([A-Z]{2,10}(?:USDT|USD|BTC|ETH)|#?[A-Z]{2,10})\b'
)

_YOUTUBE_RE = re.compile(
    r'(youtube\.com/watch\?v=|youtu\.be/|m\.youtube\.com|youtube\.com/shorts)'
)

_GITHUB_RE = re.compile(r'github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+')

_URL_RE = re.compile(r'https?://\S+')


def classify(text: str) -> str:
    """Классифицировать сообщение."""
    t = text.strip()
    if not t:
        return "empty"
    if t.startswith("/"):
        return "command"
    if _YOUTUBE_RE.search(t):
        return "youtube"
    if _GITHUB_RE.search(t):
        return "github"
    low = t.lower()
    if any(kw in low for kw in _TRADING_KEYWORDS):
        return "trading_signal"
    urls = _URL_RE.findall(t)
    if urls:
        return "url"
    if len(t) > 100:
        return "article"
    return "ai_query"


def extract_symbols(text: str) -> list[str]:
    """Извлечь тикеры из текста."""
    raw = _TRADING_SYMBOL_RE.findall(text)
    seen = set()
    result = []
    for s in raw:
        s = s.lstrip("#").upper()
        if s not in seen and len(s) >= 2:
            seen.add(s)
            result.append(s)
    return result


def extract_urls(text: str) -> list[str]:
    """Извлечь URL из текста."""
    return _URL_RE.findall(text)


# ——— Message record ———————————————————————————————————————————

def build_record(
    uid: int, text: str, forward_data: dict | None = None,
    msg_id: str = "", ts: str = "",
) -> dict:
    """Построить запись сообщения."""
    if not ts:
        ts = datetime.now().isoformat()
    if not msg_id:
        msg_id = f"msg_{uid}_{int(datetime.now().timestamp()*1000)}"

    record = {
        "id": msg_id,
        "ts": ts,
        "uid": uid,
        "text": text[:500],
        "type": classify(text),
        "symbols": extract_symbols(text),
        "urls": extract_urls(text),
        "is_forward": bool(forward_data),
    }
    if forward_data:
        record["forward"] = forward_data
    return record


# ——— NDJSON storage ————————————————————————————————————————————

def save_record(uid: int, text: str, forward_data: dict | None = None,
                base_dir: str = None, ts: str = "") -> str | None:
    """Сохранить одно сообщение в NDJSON."""
    if base_dir is None:
        base_dir = str(Path(__file__).resolve().parents[2] / "ALL_USERS")
    dir_path = Path(base_dir)
    for d in dir_path.rglob(f"usr_*"):
        state_file = d.parent.parent / "projects" / "07_tg_bot_aiforguest" / "bot" / "state.json"
        break
    tg_ids = []
    if Path(d).name.startswith("usr_"):
        pass

    # Use standard ALL_USERS path
    for user_dir in dir_path.glob("usr_*"):
        links_dir = user_dir / "tg_" + str(uid)
        if links_dir.exists() or any(
            int(p.name.replace("tg_", "")) == uid
            for p in user_dir.iterdir() if p.name.startswith("tg_")
        ):
            analytics = user_dir / "analytics"
            analytics.mkdir(parents=True, exist_ok=True)
            out = analytics / "messages.ndjson"
            record = build_record(uid, text, forward_data, ts=ts)
            with open(out, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            return str(out)
    return None


# ——— Batch parser (from bot.log) ———————————————————————————————

def parse_log(log_path: str, limit: int = 0) -> list[dict]:
    """bot.log → list[стротурированных сообщений]."""
    log_re = re.compile(
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*?'
        r'Dispatch:\s+uid=(\d+)(?:\s+fwd_.*?)?\s+text=(.*)'
    )
    results = []
    with open(log_path, encoding="utf-8") as f:
        content = f.read()
    matches = log_re.findall(content)
    if limit:
        matches = matches[-limit:]
    for ts, uid, text in matches:
        record = build_record(int(uid), text.strip(), ts=ts)
        results.append(record)
    return results


# ——— Statistics ————————————————————————————————————————————————

def compute_stats(records: list[dict]) -> dict:
    """Сводка по сообщениям."""
    if not records:
        return {}
    types = Counter(r["type"] for r in records)
    forwards = sum(1 for r in records if r.get("is_forward"))
    commands = sum(1 for r in records if r["type"] == "command")
    cmd_counts = Counter(
        r["text"].split()[0] for r in records if r["type"] == "command"
    )
    symbols = Counter(
        s for r in records for s in r.get("symbols", [])
    )

    return {
        "total": len(records),
        "types": dict(types),
        "forwards": forwards,
        "commands": commands,
        "top_commands": cmd_counts.most_common(10),
        "top_symbols": symbols.most_common(10),
        "date_range": {
            "first": records[0]["ts"],
            "last": records[-1]["ts"],
        },
    }


# ——— CLI ————————————————————————————————————————————————————————

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Message parser for TG/Max bot")
    parser.add_argument("--log", default=None, help="bot.log path")
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--last", type=int, default=0, help="Last N messages")
    args = parser.parse_args()

    if args.log:
        records = parse_log(args.log, limit=args.last)
        print(f"Parsed {len(records)} messages")
        if args.stats:
            stats = compute_stats(records)
            print(json.dumps(stats, indent=2, ensure_ascii=False))
        else:
            for r in records[-5:]:
                print(json.dumps(r, ensure_ascii=False))
    else:
        print("Usage: --log <path> [--stats] [--last N]")


if __name__ == "__main__":
    main()
