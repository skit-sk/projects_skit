from datetime import datetime
from kb import (
    save_bookmark, get_bookmark, list_bookmarks,
    search_bookmarks, list_tags, kb_stats,
    _load_config,
)
from kb_analyzer import (
    validate_url, extract_meta, queue_analysis,
    pending_count, process_analysis_queue,
)


def cmd_save(uid, args) -> str:
    if not args:
        return ("❌ /save <url> [теги]\n"
                "Пример: /save https://example.com статья, python")

    parts = args
    url = parts[0]

    err = validate_url(url)
    if err:
        return f"❌ {err}"

    tags = []
    if len(parts) > 1:
        raw_tags = " ".join(parts[1:])
        tags = [t.strip().lower() for t in raw_tags.split(",") if t.strip()]

    meta = extract_meta(url)
    title = meta.get("title") or url

    slug = save_bookmark(url, title, tags=tags, source="tg", status="pending")

    reply = (
        f"📑 **Сохранено**\n\n"
        f"🔗 [{title}]({url})\n"
        f"🏷 Теги: {', '.join(tags) if tags else '—'}\n"
        f"🆔 `{slug}`\n"
        f"📊 Статус: ожидает анализа"
    )

    queue_analysis(slug)

    return reply


def cmd_bookmarks(uid, args) -> str:
    tag = None
    limit = 20
    status_filter = None
    show_pending = False

    for a in args:
        if a.startswith("--tag="):
            tag = a.split("=", 1)[1].lower()
        elif a.startswith("--limit="):
            try:
                limit = int(a.split("=", 1)[1])
            except ValueError:
                pass
        elif a == "--pending":
            status_filter = "pending"
        elif a == "--analyzing":
            status_filter = "analyzing"
        elif a == "--complete":
            status_filter = "complete"

    bookmarks = list_bookmarks(tag=tag, limit=limit, status=status_filter)

    if not bookmarks:
        return "📭 Нет закладок."

    lines = [f"📑 **Закладки** ({len(bookmarks)}):\n"]
    for b in bookmarks:
        meta = b["meta"]
        title = meta.get("title", "?")[:50]
        tags_list = meta.get("tags", [])
        status_icon = {"pending": "⏳", "analyzing": "🔍", "complete": "✅", "error": "❌"}.get(
            meta.get("status", ""), "❓"
        )
        tag_str = ", ".join(tags_list[:3])
        if len(tags_list) > 3:
            tag_str += f"… (+{len(tags_list) - 3})"
        lines.append(
            f"{status_icon} `{b['slug']}` — {title}\n"
            f"   🏷 {tag_str or '—'}"
        )

    if len(bookmarks) >= limit:
        lines.append(f"\n... показано {limit} из {len(list_bookmarks(tag=tag))}")

    return "\n".join(lines)


def cmd_search(uid, args) -> str:
    if not args:
        return "❌ /search <запрос>\nПример: /search python asyncio"

    query = " ".join(args)
    results = search_bookmarks(query, max_results=15)

    if not results:
        return f"🔍 Ничего не найдено по «{query}»."

    lines = [f"🔍 **Результаты поиска**: «{query}» ({len(results)})\n"]
    for b in results:
        meta = b["meta"]
        title = meta.get("title", "?")[:60]
        tag_str = ", ".join(meta.get("tags", [])[:3])
        lines.append(f"📄 `{b['slug']}` — {title}")
        if tag_str:
            lines.append(f"   🏷 {tag_str}")

    return "\n".join(lines)


def cmd_tags(uid, args) -> str:
    filter_str = " ".join(args) if args else None
    tags = list_tags(filter_str)

    if not tags:
        return "🏷 Нет тегов."

    lines = [f"🏷 **Теги** ({len(tags)}):\n"]
    for tag, slugs in sorted(tags.items()):
        lines.append(f"  `{tag}` — {len(slugs)}")

    return "\n".join(lines)


def cmd_kb_stats(uid) -> str:
    stats = kb_stats()
    total = stats["total"]
    tag_count = stats["tags"]
    by_status = stats.get("by_status", {})
    by_domain = stats.get("by_domain", {})

    lines = [
        "📊 **KB Statistics**\n",
        f"📑 Всего закладок: {total}",
        f"🏷 Тегов: {tag_count}",
        f"⏳ В очереди анализа: {pending_count()}",
        "",
        "**По статусам:**",
    ]
    for s, cnt in sorted(by_status.items()):
        lines.append(f"  {s}: {cnt}")

    if by_domain:
        lines.append("")
        lines.append("**Топ доменов:**")
        for d, cnt in list(by_domain.items())[:5]:
            lines.append(f"  {d}: {cnt}")

    return "\n".join(lines)
