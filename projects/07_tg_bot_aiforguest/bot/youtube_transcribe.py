import os
import subprocess
import tempfile
import logging
from voice import _get_model

log = logging.getLogger("tg_bot")


def transcribe_youtube(url: str) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        audio = os.path.join(tmp, "audio.opus")
        wav = os.path.join(tmp, "audio.wav")

        log.info("Downloading audio from: %s", url)
        subprocess.run(
            ["yt-dlp", "-x", "--audio-format", "opus", "-o", audio, url],
            capture_output=True, check=True, timeout=300
        )

        log.info("Converting to WAV...")
        subprocess.run(
            ["ffmpeg", "-y", "-i", audio, "-ar", "16000", "-ac", "1", wav],
            capture_output=True, check=True
        )

        log.info("Transcribing...")
        model = _get_model()
        segments, _ = model.transcribe(wav, language="ru")
        text = " ".join(seg.text for seg in segments).strip()
        log.info("Transcription done (%d chars)", len(text))

    return text or "(пусто)"
