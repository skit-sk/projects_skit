Project Refresh Plan

This repository contains utilities to fetch and process YouTube transcripts.

- playlist_transcript.py: Fetches transcripts from a YouTube playlist and caches Markdown transcripts under ~/.cache/opencode/transcripts.
- transcript_pipeline.py: A more advanced pipeline that handles single videos and playlists with optional language support and summary generation.
- yt_transcript_ytdlp.py: Small helper to fetch subtitles using yt-dlp.

How to use:
- Extract a playlist: python3 playlist_transcript.py <playlist_url>
- Process a video (with optional languages): python3 transcript_pipeline.py <youtube_url> [langs=en,ru]
- Simple transcript fetch (for quick checks): python3 yt_transcript_ytdlp.py <youtube_url> [langs=en,ru]

Environment notes:
- yt-dlp must be installed in PATH for the transcript scripts to download subtitles.
- Python 3.8+ is recommended.

Project bootstrap steps:
- 1) Initialize git and structure (this step): see .gitignore and README for guidance.
- 2) Create a minimal environment setup script (setup_env.sh).
- 3) Optionally add a requirements.txt for Python dependencies and a virtualenv setup routine.

If you want, I can commit this initial bootstrap and set up a minimal CI later.
