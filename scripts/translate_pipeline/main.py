#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime


def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)
    return p


def main():
    parser = argparse.ArgumentParser(description="YouTube → EN transcript + RU study guide pipeline")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--provider", "-p", default="openrouter", help="AI provider (default: openrouter)")
    parser.add_argument("--model", "-m", help="AI model (default: provider default)")
    parser.add_argument("--whisper-model", "-w", default="small", choices=["tiny", "base", "small", "medium", "large"], help="Whisper model (default: small)")
    parser.add_argument("--start", help="Start timestamp HH:MM:SS")
    parser.add_argument("--end", help="End timestamp HH:MM:SS")
    parser.add_argument("--code", help="Custom code for output files")
    parser.add_argument("--output", "-o", help="Output directory")
    parser.add_argument("--config", "-c", help="providers.json path")
    parser.add_argument("--skip-transcribe", action="store_true", help="Skip transcription (use existing .en.md)")
    parser.add_argument("--skip-translate", action="store_true", help="Skip translation")

    args = parser.parse_args()

    script_dir = Path(__file__).parent.resolve()
    transcribe_py = script_dir / "transcribe.py"
    translate_py = script_dir / "translate.py"

    video_id = _extract_video_id(args.url) or args.code or "video"
    code = args.code or video_id

    date_str = datetime.now().strftime("%Y-%m-%d")
    if args.output:
        out_dir = args.output
    else:
        out_dir = script_dir.parent / "transcripts" / date_str
    ensure_dir(out_dir)

    if not args.skip_transcribe:
        import subprocess

        cmd = [sys.executable, str(transcribe_py), args.url]
        if args.output:
            cmd.extend(["--output", args.output])
        if args.code:
            cmd.extend(["--code", args.code])
        cmd.extend(["--model", args.whisper_model])
        if args.start:
            cmd.extend(["--start", args.start])
        if args.end:
            cmd.extend(["--end", args.end])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Transcription failed: {result.stderr}", file=sys.stderr)
            sys.exit(1)

        en_path = result.stdout.strip()
        print(f"Transcription done: {en_path}")
    else:
        en_path = str(Path(out_dir) / f"{code}.en.md")
        if not os.path.exists(en_path):
            print(f"File not found: {en_path}", file=sys.stderr)
            sys.exit(1)

    if not args.skip_translate:
        import subprocess

        cmd = [sys.executable, str(translate_py), en_path]
        if args.provider:
            cmd.extend(["--provider", args.provider])
        if args.model:
            cmd.extend(["--model", args.model])
        if args.config:
            cmd.extend(["--config", args.config])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Translation failed: {result.stderr}", file=sys.stderr)
            sys.exit(1)

        ru_path = result.stdout.strip()
        print(f"Translation done: {ru_path}")

    print(f"\nOutput directory: {out_dir}")
    print(f"Files:")
    for f in os.listdir(out_dir):
        print(f"  - {f}")


def _extract_video_id(url: str) -> str:
    import re
    m = re.search(r"v=([A-Za-z0-9_-]{11})", url)
    if m:
        return m.group(1)
    m = re.search(r"youtu\.be/([A-Za-z0-9_-]{11})", url)
    if m:
        return m.group(1)
    return None


if __name__ == "__main__":
    main()