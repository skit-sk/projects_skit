#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()

import os
import sys
import subprocess
import re
from datetime import date
import json

CACHE_DIR = os.path.expanduser("~/.cache/opencode/transcripts")
ensure_dir = lambda p: os.makedirs(p, exist_ok=True)

def video_id_from_url(url: str) -> str:
    m = re.search(r"v=([A-Za-z0-9_-]{11})", url)
    if m:
        return m.group(1)
    m = re.search(r"youtu\.be/([A-Za-z0-9_-]{11})", url)
    if m:
        return m.group(1)
    return None

def download_subtitles(url: str, langs=["en"]):
    vid = video_id_from_url(url) or "video"
    tmp = "/tmp/yttranscripts"
    os.makedirs(tmp, exist_ok=True)
    for lang in langs:
        out = os.path.join(tmp, f"{vid}.{lang}.vtt")
        cmd = ["yt-dlp", "--skip-download", "--write-auto-sub", f"--sub-lang={lang}", f"--output={out}", url]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(out):
                return out
        except Exception:
            continue
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

def process_single_video(url, langs):
    sub_path = download_subtitles(url, langs or ["en"])
    vid = video_id_from_url(url) or get_title(url)
    title = get_title(url)
    transcript_text = ""
    if sub_path and os.path.exists(sub_path):
        transcript_text = vtt_to_text(sub_path)
    md_path = None
    if transcript_text:
        md = build_markdown(url, transcript_text, title, vid)
        out_path = os.path.join(CACHE_DIR, f"{vid}.md")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(md)
        summary = summarize_text(transcript_text)
        if summary:
            with open(out_path, 'a', encoding='utf-8') as f:
                f.write("\n\n## Summary\n\n" + summary)
        md_path = out_path
    return {"vid": vid, "title": title, "md_path": md_path, "sub_path": sub_path}

def process_playlist(url, langs):
    entries = fetch_playlist_entries(url)
    md_paths = []
    titles_for_playlist = []
    for e in entries:
        vid_url = f"https://www.youtube.com/watch?v={e.get('id')}"
        info = process_single_video(vid_url, langs or ["en"])
        if info.get('md_path'):
            md_paths.append(info['md_path'])
            titles_for_playlist.append((e.get('title') or info.get('title') or info['vid'], info['md_path']))
    lines = []
    for t, p in titles_for_playlist:
        lines.append(f"- [{t}]({os.path.basename(p)})")
    content = "\n".join(lines)
    meta = {"playlist_url": url, "title": "Playlist", "date": date.today().isoformat()}
    playlist_md = markdown_front_matter(meta, content)
    pl_path = os.path.join(CACHE_DIR, "playlist.md")
    with open(pl_path, 'w', encoding='utf-8') as f:
        f.write(playlist_md)
    return pl_path, md_paths

def fetch_playlist_entries(url):
    # Fetch flat playlist entries (video IDs and titles) using yt-dlp
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

def process_single_video(url, langs):
    sub_path = download_subtitles(url, langs or ["en"])
    vid = video_id_from_url(url) or get_title(url)
    title = get_title(url)
    transcript_text = ""
    if sub_path and os.path.exists(sub_path):
        transcript_text = vtt_to_text(sub_path)
    md_path = None
    if transcript_text:
        md = build_markdown(url, transcript_text, title, vid)
        out_path = os.path.join(CACHE_DIR, f"{vid}.md")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(md)
        summary = summarize_text(transcript_text)
        if summary:
            with open(out_path, 'a', encoding='utf-8') as f:
                f.write("\n\n## Summary\n\n" + summary)
        md_path = out_path
    return {"vid": vid, "title": title, "md_path": md_path, "sub_path": sub_path}

def process_playlist(url, langs):
    entries = fetch_playlist_entries(url)
    md_paths = []
    titles_for_playlist = []
    for e in entries:
        vid_url = f"https://www.youtube.com/watch?v={e.get('id')}"
        info = process_single_video(vid_url, langs or ["en"])
        if info.get('md_path'):
            md_paths.append(info['md_path'])
            titles_for_playlist.append((e.get('title') or info.get('title') or info['vid'], info['md_path']))
    # Build playlist markdown
    lines = []
    for t, p in titles_for_playlist:
        lines.append(f"- [{t}]({os.path.basename(p)})")
    content = "\n".join(lines)
    meta = {"playlist_url": url, "title": "Playlist", "date": date.today().isoformat()}
    playlist_md = markdown_front_matter(meta, content)
    pl_path = os.path.join(CACHE_DIR, "playlist.md")
    with open(pl_path, 'w', encoding='utf-8') as f:
        f.write(playlist_md)
    return pl_path, md_paths

def fetch_playlist_entries(url):
    # Fetch flat playlist entries (video IDs and titles) using yt-dlp
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

def process_single_video(url, langs):
    sub_path = download_subtitles(url, langs or ["en"])
    vid = video_id_from_url(url) or get_title(url)
    title = get_title(url)
    transcript_text = ""
    if sub_path and os.path.exists(sub_path):
        transcript_text = vtt_to_text(sub_path)
    md_path = None
    if transcript_text:
        md = build_markdown(url, transcript_text, title, vid)
        out_path = os.path.join(CACHE_DIR, f"{vid}.md")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(md)
        summary = summarize_text(transcript_text)
        if summary:
            with open(out_path, 'a', encoding='utf-8') as f:
                f.write("\n\n## Summary\n\n" + summary)
        md_path = out_path
    return {"vid": vid, "title": title, "md_path": md_path, "sub_path": sub_path}

def process_playlist(url, langs):
    entries = fetch_playlist_entries(url)
    md_paths = []
    titles_for_playlist = []
    for e in entries:
        vid_url = f"https://www.youtube.com/watch?v={e.get('id')}"
        info = process_single_video(vid_url, langs or ["en"])
        if info.get('md_path'):
            md_paths.append(info['md_path'])
            titles_for_playlist.append((e.get('title') or info.get('title') or info['vid'], info['md_path']))
    # Build playlist markdown
    lines = []
    for t, p in titles_for_playlist:
        lines.append(f"- [{t}]({os.path.basename(p)})")
    content = "\n".join(lines)
    meta = {"playlist_url": url, "title": "Playlist", "date": date.today().isoformat()}
    playlist_md = markdown_front_matter(meta, content)
    pl_path = os.path.join(CACHE_DIR, "playlist.md")
    with open(pl_path, 'w', encoding='utf-8') as f:
        f.write(playlist_md)
    return pl_path, md_paths

def vtt_to_text(path: str) -> str:
    text_lines = []
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
            text_lines.append(line)
    return " ".join(text_lines)

def get_title(url: str) -> str:
    vid = video_id_from_url(url) or "video"
    try:
        res = subprocess.run(["yt-dlp", "--get-title", url], capture_output=True, text=True, check=True)
        return res.stdout.strip() or vid
    except Exception:
        return vid

def summarize_text(text: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        try:
            import openai
            openai.api_key = api_key
            prompt = (
                "Summarize the following transcript into 5-7 bullet points:\n\n" + text
            )
            resp = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            pass
    lines = text.split(". ")
    if len(lines) <= 4:
        return text
    return ". ".join(lines[:3]) + "."

def markdown_front_matter(meta: dict, content_md: str) -> str:
    fm = """---\n"""
    for k, v in meta.items():
        fm += f"{k}: {v}\n"
    fm += "---\n\n"
    return fm + content_md

def build_markdown(url: str, transcript_md: str, title: str, vid: str) -> str:
    meta = {
        "video_id": vid,
        "title": json.dumps(title) if isinstance(title, str) else title,
        "url": url,
        "date": date.today().isoformat(),
        "language": "en",
        "format": "transcript-md"
    }
    return markdown_front_matter(meta, transcript_md)

def main():
    if len(sys.argv) < 2:
        print("Usage: transcript_pipeline.py <youtube_url> [langs=en,ru]", file=sys.stderr)
        sys.exit(2)
    url = sys.argv[1]
    langs = [l for l in (sys.argv[2].split(',') if len(sys.argv) > 2 else [])]
    if not langs:
        langs = ["en"]

    sub_path = download_subtitles(url, langs)
    if not sub_path:
        # Fallback: try to extract audio and use Whisper API if API key is available
        print("No transcript available (trying audio + Whisper fallback if possible)")
        audio_path = None
        try:
            # Attempt to download audio
            vid = video_id_from_url(url) or "video"
            audio_path = f"/tmp/{vid}.mp3"
            cmd = ["yt-dlp", "-x", "--audio-format", "mp3", "-o", audio_path, url]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            audio_path = None
        if audio_path and os.path.exists(audio_path) and os.environ.get("OPENAI_API_KEY"):
            try:
                import requests
                api_key = os.environ.get("OPENAI_API_KEY")
                headers = {"Authorization": f"Bearer {api_key}"}
                files = {"file": open(audio_path, 'rb')}
                data = {"model": "whisper-1", "" : "text"}
                resp = requests.post("https://api.openai.com/v1/audio/transcriptions", headers=headers, files=files, data={"model":"whisper-1","response_format":"text"})
                if resp.status_code == 200:
                    transcript_text = resp.text.strip()
                    video_title = get_title(url)
                    vid = video_id_from_url(url) or video_title
                    md = build_markdown(url, transcript_text, video_title, vid)
                    with open(out_path, 'w', encoding='utf-8') as f:
                        f.write(md)
                    summary = summarize_text(transcript_text)
                    if summary:
                        with open(out_path, 'a', encoding='utf-8') as f:
                            f.write("\n\n## Summary\n\n" + summary)
                    print(out_path)
                    return
            except Exception:
                pass
        print("No transcript available (no fallback worked)")
        sys.exit(0)
    transcript_text = vtt_to_text(sub_path)
    video_title = get_title(url)
    vid = video_id_from_url(url) or video_title
    md = build_markdown(url, transcript_text, video_title, vid)

    CACHE_DIR = os.path.expanduser("~/.cache/opencode/transcripts")
    os.makedirs(CACHE_DIR, exist_ok=True)
    out_path = os.path.join(CACHE_DIR, f"{vid}.md")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(md)

    summary = summarize_text(transcript_text)
    if summary:
        with open(out_path, 'a', encoding='utf-8') as f:
            f.write("\n\n## Summary\n\n" + summary)

    print(out_path)

if __name__ == "__main__":
    main()
