import json
import re
import time
import subprocess
from pathlib import Path
from datetime import datetime
from config import WORKSPACE_DIR

KB_DIR = WORKSPACE_DIR / "kb"
BOOKMARKS_DIR = KB_DIR / "bookmarks"
CONFIG_FILE = KB_DIR / "config.json"
TAGS_FILE = KB_DIR / "tags" / "index.json"

_DEFAULT_CONFIG = {
    "version": 1,
    "bookmarks_dir": "bookmarks",
    "tags_file": "tags/index.json",
    "analysis_model": "opencode/deepseek-v4-flash-free",
    "max_concurrent_analysis": 2,
    "max_fetch_bytes": 50000,
    "max_ai_chars": 8000,
}


def _ensure_dirs():
    BOOKMARKS_DIR.mkdir(parents=True, exist_ok=True)
    (KB_DIR / "tags").mkdir(parents=True, exist_ok=True)


def _load_config():
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, "w") as f:
            json.dump(_DEFAULT_CONFIG, f, indent=2)
        return dict(_DEFAULT_CONFIG)
    with open(CONFIG_FILE) as f:
        cfg = json.load(f)
    for k, v in _DEFAULT_CONFIG.items():
        cfg.setdefault(k, v)
    return cfg


def _slug(text: str, max_len=60) -> str:
    safe = re.sub(r'[^\w\s-]', '', text.lower())
    safe = re.sub(r'[-\s]+', '-', safe).strip('-')
    if len(safe) > max_len:
        safe = safe[:max_len].rstrip('-')
    return safe or f"bookmark-{int(time.time())}"


def _bookmark_path(slug: str) -> Path:
    now = datetime.now()
    month_dir = BOOKMARKS_DIR / str(now.year) / f"{now.month:02d}"
    month_dir.mkdir(parents=True, exist_ok=True)
    return month_dir / f"{slug}.md"


def _bookmark_from_path(path: Path) -> dict | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    fm = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            import yaml
            try:
                fm = yaml.safe_load(parts[1]) or {}
            except Exception:
                fm = {}
            body = parts[2].strip()
    slug = path.stem
    return {"slug": slug, "meta": fm, "body": body, "path": str(path)}


def _load_tags() -> dict:
    if not TAGS_FILE.exists():
        return {}
    with open(TAGS_FILE) as f:
        return json.load(f)


def _save_tags(index: dict):
    TAGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TAGS_FILE, "w") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)


def _tags_to_list(tags_raw) -> list[str]:
    if isinstance(tags_raw, list):
        return [t.strip().lower() for t in tags_raw if t.strip()]
    if isinstance(tags_raw, str):
        return [t.strip().lower() for t in tags_raw.split(",") if t.strip()]
    return []


def _resolve_tag_index():
    index = _load_tags()
    changed = False
    for entry in _all_bookmarks():
        slug = entry["slug"]
        tags = _tags_to_list(entry["meta"].get("tags", []))
        for tag in tags:
            if tag not in index:
                index[tag] = []
            if slug not in index[tag]:
                index[tag].append(slug)
                changed = True
    if changed:
        _save_tags(index)
    return index


def _all_bookmarks() -> list[dict]:
    _ensure_dirs()
    files = sorted(BOOKMARKS_DIR.rglob("*.md"))
    result = []
    for p in files:
        entry = _bookmark_from_path(p)
        if entry:
            result.append(entry)
    return sorted(result, key=lambda x: x["meta"].get("date", ""), reverse=True)


def save_bookmark(url: str, title: str,
                  tags: list[str] | None = None,
                  source: str = "tg",
                  status: str = "pending") -> str:
    _ensure_dirs()
    cfg = _load_config()
    tags = tags or []
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%dT%H:%M:%S")
    date_short = now.strftime("%Y-%m-%d")

    slug_base = _slug(title or url)
    slug = slug_base
    idx = 0
    while _bookmark_path(slug).exists():
        idx += 1
        slug = f"{slug_base}-{idx}"

    from urllib.parse import urlparse
    domain = urlparse(url).netloc or ""

    content = (
        f"---\n"
        f'url: "{url}"\n'
        f'title: "{title}"\n'
        f"date: {date_str}\n"
        f"tags: {json.dumps(tags, ensure_ascii=False)}\n"
        f"status: {status}\n"
        f"domain: {domain}\n"
        f"source: {source}\n"
        f"language: \"\"\n"
        f"---\n"
        f"\n"
        f"# {title}\n"
        f"\n"
        f"> URL: {url}\n"
        f"\n"
        f"## Summary\n"
        f"*(анализ в процессе)*\n"
        f"\n"
        f"## Key Points\n"
        f"- *(будет добавлено)*\n"
        f"\n"
        f"## Entities\n"
        f"- *(будет добавлено)*\n"
        f"\n"
        f"## Tags\n"
    )
    for t in tags:
        content += f"- {t}\n"

    path = _bookmark_path(slug)
    path.write_text(content, encoding="utf-8")

    index = _load_tags()
    for tag in tags:
        tag = tag.lower()
        if tag not in index:
            index[tag] = []
        if slug not in index[tag]:
            index[tag].append(slug)
    _save_tags(index)

    return slug


def get_bookmark(slug: str) -> dict | None:
    for p in BOOKMARKS_DIR.rglob(f"{slug}.md"):
        return _bookmark_from_path(p)
    return None


def list_bookmarks(tag: str | None = None,
                   limit: int = 20,
                   status: str | None = None) -> list[dict]:
    all_bm = _all_bookmarks()
    if tag:
        tag = tag.lower()
        all_bm = [b for b in all_bm if tag in _tags_to_list(b["meta"].get("tags", []))]
    if status:
        all_bm = [b for b in all_bm if b["meta"].get("status") == status]
    return all_bm[:limit]


def update_bookmark(slug: str, meta_updates: dict | None = None,
                    body_text: str | None = None) -> bool:
    entry = get_bookmark(slug)
    if not entry:
        return False
    path = Path(entry["path"])
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return False

    parts = text.split("---", 2)
    if len(parts) < 3:
        return False

    import yaml
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except Exception:
        fm = {}

    if meta_updates:
        fm.update(meta_updates)

    new_body = body_text if body_text is not None else parts[2].strip()

    new_content = (
        "---\n"
        f"{yaml.dump(fm, allow_unicode=True, default_flow_style=False).strip()}\n"
        "---\n"
        f"\n{new_body}\n"
    )
    path.write_text(new_content, encoding="utf-8")
    return True


def update_bookmark_status(slug: str, status: str):
    return update_bookmark(slug, {"status": status})


def search_bookmarks(query: str, max_results: int = 20) -> list[dict]:
    _ensure_dirs()
    try:
        proc = subprocess.run(
            ["rg", "-l", "-i", query, str(BOOKMARKS_DIR)],
            capture_output=True, text=True, timeout=30
        )
        paths = [p.strip() for p in proc.stdout.split("\n") if p.strip()]
    except FileNotFoundError:
        try:
            proc = subprocess.run(
                ["grep", "-r", "-l", "-i", query, str(BOOKMARKS_DIR)],
                capture_output=True, text=True, timeout=30
            )
            paths = [p.strip() for p in proc.stdout.split("\n") if p.strip()]
        except Exception:
            paths = []
    except Exception:
        paths = []

    results = []
    for p in paths[:max_results]:
        entry = _bookmark_from_path(Path(p))
        if entry:
            results.append(entry)
    return results


def list_tags(filter_str: str | None = None) -> dict:
    index = _resolve_tag_index()
    if filter_str:
        f = filter_str.lower()
        index = {k: v for k, v in index.items() if f in k}
    return dict(sorted(index.items()))


def kb_stats() -> dict:
    all_bm = _all_bookmarks()
    index = _resolve_tag_index()
    total = len(all_bm)
    by_status = {}
    by_domain = {}
    for b in all_bm:
        s = b["meta"].get("status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1
        d = b["meta"].get("domain", "?")
        by_domain[d] = by_domain.get(d, 0) + 1
    return {
        "total": total,
        "tags": len(index),
        "by_status": by_status,
        "by_domain": dict(sorted(by_domain.items(), key=lambda x: -x[1])[:10]),
    }
