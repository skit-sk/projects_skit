import os, re, subprocess, time
from pathlib import Path

def video_id_from_url(url: str) -> str | None:
    m = re.search(r"v=([A-Za-z0-9_-]{11})", url)
    if m:
        return m.group(1)
    m = re.search(r"youtu\.be/([A-Za-z0-9_-]{11})", url)
    if m:
        return m.group(1)
    return None

def get_title(url: str) -> str:
    vid = video_id_from_url(url) or "video"
    try:
        res = subprocess.run(
            ["yt-dlp", "--get-title", url],
            capture_output=True, text=True, timeout=30
        )
        return res.stdout.strip() or vid
    except Exception:
        return vid

def extract_topic(title: str) -> str:
    words = title.lower().split()[:4]
    topic = "-".join(words)
    topic = re.sub(r'[^a-zа-я0-9-]', '', topic)
    return topic or "untitled"

def download_audio(url: str, out_dir: str = "/tmp", audio_format: str = "mp3", quality: int = 0) -> str | None:
    vid = video_id_from_url(url) or "audio"
    out_path = os.path.join(out_dir, f"{vid}.{audio_format}")
    if os.path.exists(out_path):
        return out_path
    try:
        subprocess.run(
            ["yt-dlp", "-x", "--audio-format", audio_format,
             "--audio-quality", str(quality),
             "-o", out_path, url],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=300
        )
        if os.path.exists(out_path):
            return out_path
    except subprocess.TimeoutExpired:
        pass
    except subprocess.CalledProcessError:
        pass
    return None

def get_duration(path: str) -> float:
    try:
        res = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=15
        )
        return float(res.stdout.strip())
    except Exception:
        return 0.0
