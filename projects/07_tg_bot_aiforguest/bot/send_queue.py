import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
QUEUE_FILE = BASE / "TG_ALL" / "send_queue.json"


def _load():
    if not QUEUE_FILE.exists():
        return []
    with open(QUEUE_FILE) as f:
        return json.load(f)


def _save(data):
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(QUEUE_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False)


def queue_add(uid, file_paths, caption=""):
    data = _load()
    data.append({"uid": uid, "files": file_paths, "caption": caption})
    _save(data)


def queue_pop(uid):
    data = _load()
    for i, item in enumerate(data):
        if item["uid"] == uid:
            removed = data.pop(i)
            _save(data)
            return removed
    return None
