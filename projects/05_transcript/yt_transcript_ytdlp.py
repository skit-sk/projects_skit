#!/usr/bin/env python3
"""YouTube transcript fetcher using yt-dlp subtitles."""
import os
import sys
import subprocess
import re

def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)
    return p

def extract_video_id(url: str) -> str:
    m = re.search(r"v=([A-Za-z0-9_-]{11})", url)
    if m:
        return m.group(1)
    m = re.search(r"youtu\.be/([A-Za-z0-9_-]{11})", url)
    if m:
        return m.group(1)
    return None

def fetch_subtitles(url: str, lang_list):
    video_id = extract_video_id(url) or 'video'
    tmpdir = "/tmp/yttranscripts"
    ensure_dir(tmpdir)
    for lang in lang_list:
        out_template = os.path.join(tmpdir, f"{video_id}.{lang}.vtt")
        cmd = ["yt-dlp",
               "--skip-download",
               "--write-auto-sub",
               f"--sub-lang={lang}",
               f"--output={out_template}",
               url]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(out_template):
                return out_template
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

def main():
    if len(sys.argv) < 2:
        print("Usage: yt_transcript_ytdlp.py <youtube_url> [langs]", file=sys.stderr)
        sys.exit(2)
    url = sys.argv[1]
    langs = [l for l in (sys.argv[2].split(',') if len(sys.argv) > 2 else [])]
    if not langs:
        langs = ["en", "ru"]
    sub_path = fetch_subtitles(url, langs)
    if not sub_path:
        print("No transcript available", end="")
        sys.exit(0)
    text = vtt_to_text(sub_path)
    print(text)

if __name__ == "__main__":
    main()
