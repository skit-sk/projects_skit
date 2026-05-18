import os
import logging
import tempfile
import subprocess
from faster_whisper import WhisperModel

log = logging.getLogger("tg_bot")

_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".whisper_cache")
os.makedirs(_CACHE_DIR, exist_ok=True)
log.info("Whisper cache: %s", _CACHE_DIR)

# Force HF Hub to use writable dirs (default ~/.cache/huggingface is root-owned)
_HF_CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".hf_cache")
os.makedirs(_HF_CACHE, exist_ok=True)
os.environ["HF_HOME"] = _HF_CACHE
os.environ["HUGGINGFACE_HUB_CACHE"] = os.path.join(_HF_CACHE, "hub")
log.info("HF_HOME: %s", _HF_CACHE)

_model = None


def _get_model():
    global _model
    if _model is None:
        log.info("Loading Whisper tiny model...")
        try:
            _model = WhisperModel("tiny", device="cpu", compute_type="int8", download_root=_CACHE_DIR)
        except Exception as e:
            log.error(f"Whisper model load failed: {e}")
            fallback = "/tmp/whisper_cache"
            os.makedirs(fallback, exist_ok=True)
            _model = WhisperModel("tiny", device="cpu", compute_type="int8", download_root=fallback)
        log.info("Whisper model loaded")
    return _model


async def transcribe_voice(update, context) -> str:
    voice = update.message.voice
    file_id = voice.file_id
    duration = voice.duration

    log.info(f"Voice message: file_id={file_id} duration={duration}s")

    tg_file = await context.bot.get_file(file_id)

    with tempfile.TemporaryDirectory() as tmp:
        ogg_path = os.path.join(tmp, "voice.ogg")
        wav_path = os.path.join(tmp, "voice.wav")

        await tg_file.download_to_drive(ogg_path)

        subprocess.run(
            ["ffmpeg", "-y", "-i", ogg_path, "-ar", "16000", "-ac", "1", wav_path],
            capture_output=True, check=True
        )

        model = _get_model()
        segments, info = model.transcribe(wav_path, language="ru")

        text = " ".join(seg.text for seg in segments).strip()

    if not text:
        log.warning("Voice transcription returned empty text")
        return ""

    log.info(f"Transcribed ({len(text)} chars): {text[:100]}")
    return text
