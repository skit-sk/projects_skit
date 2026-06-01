import json
import re
import time
import asyncio
import logging
import subprocess
from html.parser import HTMLParser
from urllib.parse import urlparse
from pathlib import Path

import requests
from kb import (
    save_bookmark, get_bookmark, update_bookmark,
    update_bookmark_status, _load_config, list_bookmarks,
)

log = logging.getLogger("tg_bot")

_analysis_semaphore = asyncio.Semaphore(2)
_analysis_queue: list[str] = []


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._text = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            text = data.strip()
            if text:
                self._text.append(text)

    def get_text(self) -> str:
        return " ".join(self._text)


_SAFE_SCHEMES = {"http", "https"}


def validate_url(url: str) -> str | None:
    if not url:
        return "URL пустой"
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in _SAFE_SCHEMES:
        return f"Схема '{parsed.scheme}' не поддерживается"
    return None


def extract_meta(url: str) -> dict:
    result = {"title": "", "description": "", "text": "", "error": None}
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (compatible; KnowledgeBot/1.0)",
        })
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            result["description"] = f"[{content_type}]"
            result["title"] = url
            return result

        html = resp.text
        parser = _TextExtractor()
        parser.feed(html)
        text = parser.get_text()

        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        if title_match:
            result["title"] = re.sub(r'\s+', ' ', title_match.group(1)).strip()

        desc_match = re.search(
            r'<meta\s+[^>]*name\s*=\s*["\']description["\'][^>]*content\s*=\s*["\']([^"\']*)["\']',
            html, re.IGNORECASE
        )
        if not desc_match:
            desc_match = re.search(
                r'<meta\s+[^>]*content\s*=\s*["\']([^"\']*)["\'][^>]*name\s*=\s*["\']description["\']',
                html, re.IGNORECASE
            )
        if desc_match:
            result["description"] = re.sub(r'\s+', ' ', desc_match.group(1)).strip()

        cfg = _load_config()
        max_bytes = cfg.get("max_fetch_bytes", 50000)
        if len(text) > max_bytes:
            text = text[:max_bytes]
        result["text"] = text

    except requests.Timeout:
        result["error"] = "Timeout"
    except requests.ConnectionError:
        result["error"] = "ConnectionError"
    except requests.HTTPError as e:
        result["error"] = f"HTTP {e.response.status_code}"
    except Exception as e:
        result["error"] = str(e)
    return result


async def analyze_bookmark(slug: str):
    async with _analysis_semaphore:
        entry = get_bookmark(slug)
        if not entry:
            log.warning("analyze_bookmark: %s not found", slug)
            return

        update_bookmark_status(slug, "analyzing")
        url = entry["meta"].get("url", "")

        meta = extract_meta(url)
        if meta["error"]:
            update_bookmark(slug, {
                "status": "error",
                "fetch_error": meta["error"],
            })
            return

        title = meta["title"] or url
        text = meta["text"]

        update_bookmark(slug, {"title": title})

        if not text.strip():
            update_bookmark(slug, {
                "status": "complete",
                "language": "?",
            })
            body = (
                f"# {title}\n\n"
                f"> URL: {url}\n\n"
                f"## Summary\n"
                f"*(нет текста для анализа — возможно, PDF/видео)*\n\n"
                f"## Key Points\n"
                f"- *(текст не извлечён)*\n"
            )
            update_bookmark(slug, body_text=body)
            return

        analysis = await _ai_analyze(title, url, text)
        if analysis:
            tags = analysis.get("tags", [])
            body = (
                f"# {title}\n\n"
                f"> URL: {url}\n\n"
                f"## Summary\n"
                f"{analysis.get('summary', '*нет summary*')}\n\n"
                f"## Key Points\n"
            )
            for kp in analysis.get("key_points", []):
                body += f"- {kp}\n"

            body += f"\n## Entities\n"
            for ent in analysis.get("entities", []):
                body += f"- **{ent.get('name', '?')}** ({ent.get('type', '?')})\n"

            body += f"\n## Tags\n"
            for t in tags:
                body += f"- {t}\n"

            language = analysis.get("language", "")
            update_bookmark(slug, {
                "status": "complete",
                "language": language,
                "tags": tags,
                "analyzed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }, body_text=body)

            index = __import__("kb")._load_tags()
            for tag in tags:
                tag = tag.lower()
                if tag not in index:
                    index[tag] = []
                if slug not in index[tag]:
                    index[tag].append(slug)
            __import__("kb")._save_tags(index)
        else:
            update_bookmark(slug, {"status": "error", "fetch_error": "AI analysis failed"})


async def _ai_analyze(title: str, url: str, text: str) -> dict | None:
    cfg = _load_config()
    max_chars = cfg.get("max_ai_chars", 8000)
    model = cfg.get("analysis_model", "opencode/deepseek-v4-flash-free")

    if len(text) > max_chars:
        text = text[:max_chars]

    prompt = (
        f'Ты — анализатор контента. Прочитай текст и верни ТОЛЬКО JSON без пояснений:\n'
        f'{{\n'
        f'  "summary": "однозначное краткое саммари (1-3 предложения)",\n'
        f'  "key_points": ["тезис 1", "тезис 2", ...],\n'
        f'  "tags": ["тег1", "тег2", ...],\n'
        f'  "entities": [{{"name": "сущность", "type": "person|org|tech|concept|..."}}],\n'
        f'  "language": "ru|en"\n'
        f'}}\n\n'
        f'Заголовок: {title}\n'
        f'URL: {url}\n\n'
        f'Текст:\n{text}'
    )

    try:
        proc = await asyncio.create_subprocess_exec(
            "opencode", "run",
            "--dir", str(Path.cwd()),
            "--format", "default",
            "--model", model,
            prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        output = stdout.decode("utf-8", errors="replace").strip()
        stderr_text = stderr.decode("utf-8", errors="replace")

        if proc.returncode != 0:
            log.warning("AI analyze failed (rc=%d): %s", proc.returncode, stderr_text[:200])
            return None

        json_match = re.search(r'\{[^}]*"summary"[^}]*\}', output, re.DOTALL)
        if not json_match:
            json_match = re.search(r'\{.*"summary".*\}', output, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
            except json.JSONDecodeError:
                data = None
            if isinstance(data, dict) and data.get("summary"):
                if isinstance(data.get("tags"), list):
                    data["tags"] = [t.lower().strip() for t in data["tags"] if t.strip()]
                return data

        text_match = re.search(r'```(?:json)?\s*(.*?)```', output, re.DOTALL)
        if text_match:
            try:
                data = json.loads(text_match.group(1))
                if isinstance(data, dict) and data.get("summary"):
                    return data
            except json.JSONDecodeError:
                pass

        log.warning("Could not parse AI response as JSON for %s", url[:80])
        log.debug("AI raw output: %s", output[:500])
        return {"summary": output[:500], "key_points": [], "tags": [], "entities": [], "language": ""}

    except asyncio.TimeoutError:
        log.warning("AI analyze timeout for %s", url[:80])
        return None
    except FileNotFoundError:
        log.warning("opencode not found in PATH")
        return None
    except Exception as e:
        log.warning("AI analyze error: %s", e)
        return None


def queue_analysis(slug: str):
    _analysis_queue.append(slug)
    log.info("KB analysis queued: %s (queue: %d)", slug, len(_analysis_queue))


async def process_analysis_queue():
    while _analysis_queue:
        slug = _analysis_queue.pop(0)
        try:
            await analyze_bookmark(slug)
        except Exception as e:
            log.error("KB analysis failed for %s: %s", slug, e)
            try:
                update_bookmark_status(slug, "error")
            except Exception:
                pass
        await asyncio.sleep(1)


def pending_count() -> int:
    return len(_analysis_queue)


def scan_pending_bookmarks():
    """Сканировать книгу на предмет status: pending и добавить в очередь."""
    from kb import list_bookmarks, get_bookmark
    pending = list_bookmarks(status="pending", limit=100)
    added = 0
    for b in pending:
        slug = b["slug"]
        if slug not in _analysis_queue:
            _analysis_queue.append(slug)
            added += 1
    if added:
        log.info("KB scan: добавлено %d pending закладок в очередь анализа", added)
    return added
