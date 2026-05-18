#!/usr/bin/env python3
import os
import sys
import json
import re
import subprocess
from datetime import date

CACHE_DIR = os.path.expanduser("~/.cache/opencode/transcripts")
os.makedirs(CACHE_DIR, exist_ok=True)

def video_id_from_url(url: str) -> str:
    m = re.search(r"v=([A-Za-z0-9_-]{11})", url)
    if m:
        return m.group(1)
    m = re.search(r"youtu\\.be/([A-Za-z0-9_-]{11})", url)
    if m:
        return m.group(1)
    return None

def fetch_playlist_entries(url):
    try:
        cmd = ["yt-dlp", "-j", "--flat-playlist", url]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        entries = []
        if proc.returncode == 0:
            for line in proc.stdout.splitlines():
                try:
                    obj = json.loads(line)
                    entries.append({"id": obj.get("id"), "title": obj.get("title")})
                except Exception:
                    continue
        return entries
    except Exception:
        return []

def download_subtitles(url, lang=["en"]):
    vid = video_id_from_url(url) or "video"
    tmp = "/tmp/yttranscripts"
    os.makedirs(tmp, exist_ok=True)
    for l in lang:
        out = os.path.join(tmp, f"{vid}.{l}.vtt")
        cmd = ["yt-dlp", "--skip-download", "--write-auto-sub", f"--sub-lang={l}", f"--output={out}", url]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(out):
                return out
        except Exception:
            continue
    return None

def vtt_to_text(path: str) -> str:
    lines = []
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("WEBVTT"):
                continue
            if "-->" in line:
                continue
            if re.match(r"^[0-9:.]+$", line):
                continue
            lines.append(line)
    return " ".join(lines)

def get_title(url: str) -> str:
    vid = video_id_from_url(url) or "video"
    try:
        res = subprocess.run(["yt-dlp", "--get-title", url], capture_output=True, text=True, check=True)
        return res.stdout.strip() or vid
    except Exception:
        return vid

def process_video(url, langs=["en"]):
    sub = download_subtitles(url, langs)
    if not sub:
        return None
    text = vtt_to_text(sub)
    title = get_title(url)
    vid = video_id_from_url(url) or title
    md = f"""---
video_id: {vid}
title: {title}
url: {url}
format: transcript-md
---

{text}
"""
    path = os.path.join(CACHE_DIR, f"{vid}.md")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(md)
    return path

def main():
    if len(sys.argv) < 2:
        print("Usage: playlist_transcript.py <playlist_url>")
        sys.exit(2)
    playlist_url = sys.argv[1]
    entries = fetch_playlist_entries(playlist_url)
    paths = []
    for e in entries:
        video_url = f"https://www.youtube.com/watch?v={e.get('id')}"
        p = process_video(video_url, ["en"])
        if p:
            paths.append(p)
            print(p)
    lines = []
    for e, p in zip(entries, paths):
        lines.append(f"- [{e.get('title')}]({os.path.basename(p)})")
    content = "\n".join(lines)
    pl_md = f"---\nplaylist_url: {playlist_url}\ndate: {date.today().isoformat()}\n---\n\n{content}"
    pl_path = os.path.join(CACHE_DIR, "playlist.md")
    with open(pl_path, 'w', encoding='utf-8') as f:
        f.write(pl_md)
    print(pl_path)

if __name__ == "__main__":
    main()
