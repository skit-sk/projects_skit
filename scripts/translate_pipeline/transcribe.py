#!/usr/bin/env python3
import os
import sys
import re
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
import whisper


FFMPEG_EXE = None
try:
    import imageio_ffmpeg
    FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    pass

XDG_CACHE_HOME = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))


def parse_timestamp(ts: str) -> float:
    parts = ts.split(':')
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    return 0.0


def format_timestamp(seconds: float) -> str:
    hh = int(seconds // 3600)
    mm = int((seconds % 3600) // 60)
    ss = int(seconds % 60)
    return f"{hh:02d}:{mm:02d}:{ss:02d}"


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


def get_video_title(url: str) -> str:
    try:
        res = subprocess.run(
            ["yt-dlp", "--get-title", url],
            capture_output=True, text=True, check=True
        )
        title = res.stdout.strip()
        return title if title else extract_video_id(url) or "video"
    except Exception:
        return extract_video_id(url) or "video"


def download_audio_segment(url: str, output_path: str, start: str = None, end: str = None) -> bool:
    ensure_dir(os.path.dirname(output_path))

    cmd = ["yt-dlp", "-x", "--audio-format", "opus", "-o", output_path]
    if FFMPEG_EXE:
        cmd.extend(["--ffmpeg-location", FFMPEG_EXE])

    if start or end:
        start_ts = start if start else "00:00:00"
        end_ts = end if end else "23:59:59"
        cmd.append(f"--download-sections=*{start_ts}-{end_ts}")

    cmd.append(url)

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return os.path.exists(output_path)
    except subprocess.CalledProcessError as e:
        print(f"Download error: {e.stderr[:500]}", file=sys.stderr)
        return False


def get_audio_duration(audio_path: str) -> float:
    cmd = [FFMPEG_EXE or "ffmpeg", "-i", audio_path, "-f", "null", "-"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, stderr=subprocess.STDOUT)
        output = result.stdout + result.stderr
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+)", output)
        if m:
            return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
    except Exception:
        pass
    return 0.0


def transcribe_chunked(audio_path: str, model_name: str = "tiny", chunk_duration: int = 180) -> list:
    model = whisper.load_model(model_name)

    total_duration = get_audio_duration(audio_path)
    if total_duration == 0:
        result = model.transcribe(audio_path, word_timestamps=True)
        return result.get("segments", [])

    all_segments = []
    offset = 0

    for start_sec in range(0, int(total_duration), chunk_duration):
        end_sec = min(start_sec + chunk_duration, total_duration)
        chunk_path = f"/tmp/whisper_chunk_{os.getpid()}_{start_sec}.opus"

        cmd = [
            FFMPEG_EXE or "ffmpeg", "-y",
            "-ss", str(start_sec),
            "-t", str(chunk_duration),
            "-i", audio_path,
            "-c", "copy",
            chunk_path
        ]
        subprocess.run(cmd, capture_output=True, check=True)

        result = model.transcribe(chunk_path, word_timestamps=True)
        for seg in result.get("segments", []):
            seg["start"] += start_sec
            seg["end"] += start_sec
            all_segments.append(seg)

        os.remove(chunk_path)

    return all_segments


def build_markdown_with_timestamps(url: str, title: str, video_id: str, segments: list, start: str = None, end: str = None) -> str:
    date_str = datetime.now().strftime("%Y-%m-%d")

    lines = [
        "---",
        f"video_id: {video_id}",
        f"title: {repr(title)}",
        f"url: {url}",
        f"date: {date_str}",
        f"language: en",
        f"format: transcript-timestamps",
    ]

    if start:
        lines.append(f"start: {start}")
    if end:
        lines.append(f"end: {end}")

    lines.append("---\n")

    if start or end:
        ts_range = []
        if start:
            ts_range.append(f"from [{start}]")
        if end:
            ts_range.append(f"to [{end}]")
        lines.append(f"# Transcript ({' '.join(ts_range)})\n")
    else:
        lines.append("# Transcript\n")

    for seg in segments:
        ts = format_timestamp(seg["start"])
        yt_link = f"[{ts}]({url}&t={int(seg['start'])}s)"
        lines.append(f"- **{yt_link}** {seg['text']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="YouTube → Whisper transcription with timestamps")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--output", "-o", help="Output directory (default: auto date-based)")
    parser.add_argument("--model", "-m", default="tiny", choices=["tiny", "base", "small", "medium", "large"], help="Whisper model (default: tiny)")
    parser.add_argument("--start", help="Start timestamp HH:MM:SS")
    parser.add_argument("--end", help="End timestamp HH:MM:SS")
    parser.add_argument("--code", help="Custom code for output files")
    parser.add_argument("--chunk-duration", type=int, default=120, help="Chunk duration in seconds (default: 120)")

    args = parser.parse_args()

    url = args.url
    video_id = extract_video_id(url) or "video"
    code = args.code or video_id
    title = get_video_title(url)

    if args.output:
        out_dir = args.output
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")
        out_dir = os.path.join("scripts", "transcripts", date_str)
    ensure_dir(out_dir)

    audio_path = os.path.join("/tmp", f"{code}.opus")

    if not download_audio_segment(url, audio_path, args.start, args.end):
        print(f"Failed to download audio for {url}", file=sys.stderr)
        sys.exit(1)

    print(f"Transcribing with Whisper model '{args.model}'...", file=sys.stderr)
    segments = transcribe_chunked(audio_path, args.model, args.chunk_duration)

    en_md = build_markdown_with_timestamps(url, title, video_id, segments, args.start, args.end)

    en_path = os.path.join(out_dir, f"{code}.en.md")
    with open(en_path, "w", encoding="utf-8") as f:
        f.write(en_md)

    print(f"EN transcript: {en_path}")
    return en_path


if __name__ == "__main__":
    main()