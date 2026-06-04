import json
import os
import subprocess
import glob
import time
import re
import logging
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional
from faster_whisper import WhisperModel


log = logging.getLogger('viz_lab.transcriber')

TRANSCRIPT_PIPELINE_DIR = Path(__file__).parent.parent.parent.parent / '09_model_catalog'
CATALOG_PATH = TRANSCRIPT_PIPELINE_DIR / 'models_catalog.json'

AUDIO_DIR = Path('/tmp/viz_lab_transcribe')
OUT_DIR = Path(__file__).parent.parent / 'data' / 'results'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Whisper cache as writable dir (same pattern as TG bot)
_WHISPER_CACHE = Path(__file__).parent / '.whisper_cache'
_HF_CACHE = Path(__file__).parent / '.hf_cache'
_WHISPER_CACHE.mkdir(parents=True, exist_ok=True)
_HF_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault('HF_HOME', str(_HF_CACHE))
os.environ.setdefault('HUGGINGFACE_HUB_CACHE', str(_HF_CACHE / 'hub'))

_whisper_model = None


def _get_whisper():
    global _whisper_model
    if _whisper_model is None:
        log.info('Loading faster-whisper tiny (int8)...')
        t0 = time.time()
        _whisper_model = WhisperModel(
            'tiny', device='cpu', compute_type='int8',
            download_root=str(_WHISPER_CACHE),
        )
        log.info('Whisper loaded in %.1fs', time.time() - t0)
    return _whisper_model


class Transcriber:
    CHAINS_CACHE = None

    def get_chains(self) -> list[dict]:
        if self.CHAINS_CACHE is not None:
            return self.CHAINS_CACHE
        if CATALOG_PATH.exists():
            with open(CATALOG_PATH) as f:
                data = json.load(f)
            chains = data.get('chains', [])
            self.CHAINS_CACHE = chains
            return chains
        return []

    def transcribe(self, media_url: str, session_id: str = '',
                   chain_id: str = '', model: str = '',
                   language: str = 'ru') -> dict:
        start = time.time()
        log.info('Transcribe start: url=%s chain=%s lang=%s', media_url[:60], chain_id, language)

        if not chain_id:
            chain_id = 'local-whisper'

        if os.path.isfile(media_url):
            audio_path = media_url
            log.info('Using local file: %s', audio_path)
        else:
            audio_path = self._download_audio(media_url)
            if not audio_path:
                log.error('Audio download failed: %s', media_url[:60])
                return {'error': 'audio download failed', 'output': None}

        log.info('Audio downloaded: %s (%.1f MB)',
                 os.path.basename(audio_path),
                 os.path.getsize(audio_path) / 1e6)

        if chain_id == 'local-whisper':
            result = self._transcribe_whisper(audio_path, language)
        else:
            result = self._transcribe_opencode(audio_path, chain_id, model, language, session_id)

        result['duration_total'] = time.time() - start
        log.info('Transcribe done: %s err=%s len=%d',
                 result.get('model', '?'),
                 result.get('error', 'ok'),
                 len(result.get('text', '')))
        return result

    def _download_audio(self, url: str) -> Optional[str]:
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        try:
            result = subprocess.run(
                ['yt-dlp', '-x', '--audio-format', 'mp3',
                 '--audio-quality', '0',
                 '-o', f'{AUDIO_DIR}/%(id)s.%(ext)s', url],
                capture_output=True, text=True, timeout=300,
            )
            if result.returncode != 0:
                log.warning('yt-dlp failed: %s', result.stderr[:200])
                return None
            files = glob.glob(f'{AUDIO_DIR}/*.mp3')
            if files:
                latest = max(files, key=os.path.getmtime)
                log.info('yt-dlp ok: %s', os.path.basename(latest))
                return latest
        except subprocess.TimeoutExpired:
            log.error('yt-dlp timeout (300s)')
        except Exception as e:
            log.error('yt-dlp error: %s', e)
        return None

    def _transcribe_opencode(self, audio_path: str, chain_id: str,
                              model: str, language: str,
                              session_id: str) -> dict:
        chains = self.get_chains()
        chain = None
        for c in chains:
            if c['id'] == chain_id:
                chain = c
                break
        if not chain:
            chain = chains[0] if chains else None
        if not chain:
            return {'error': 'no transcription chain available'}

        sel_model = model or (chain.get('models') or [None])[0]
        if not sel_model:
            return {'error': 'no model specified'}

        prompts = {
            'one-pass': (
                f'Transcribe this audio file verbatim in {language}. '
                f'Then summarize with key points.\n'
                f'Format: ## Transcript\\n\\n[full text]\\n\\n## Summary\\n\\n[bullet points]'
            ),
            'split': (
                f'Transcribe this audio file verbatim in {language}. '
                f'Return only the transcript text.'
            ),
        }
        prompt = prompts.get(chain.get('mode', 'one-pass'), prompts['one-pass'])

        t0 = time.time()
        try:
            clean_env = {k: v for k, v in os.environ.items()
                         if k not in ('TERM', 'COLUMNS', 'LINES')}
            result = subprocess.run(
                ['opencode', 'run', '--model', sel_model,
                 '--dir', os.path.dirname(audio_path), prompt],
                capture_output=True, text=True, timeout=600,
                env=clean_env,
            )
            dur = time.time() - t0
            if result.returncode != 0:
                err = result.stderr[:300]
                log.error('opencode failed: %s', err)
                return {'error': f'opencode error: {err}'}

            text = result.stdout.strip()
            if not text:
                return {'error': 'empty response from model'}

            transcript_path = self._save_transcript(text, session_id, sel_model)
            return {
                'text': text,
                'summary': self._extract_summary(text),
                'output': transcript_path,
                'duration': dur,
                'model': sel_model,
                'chain': chain_id,
                'language': language,
                'tokens': len(text.split()),
                'cost': 0,
            }
        except subprocess.TimeoutExpired:
            log.error('opencode timeout (600s)')
            return {'error': 'timeout (600s)'}
        except Exception as e:
            log.error('opencode exception: %s', e)
            return {'error': str(e)}

    def _transcribe_whisper(self, audio_path: str, language: str) -> dict:
        try:
            with tempfile.TemporaryDirectory() as tmp:
                wav_path = os.path.join(tmp, 'audio.wav')
                t0 = time.time()

                subprocess.run(
                    ['ffmpeg', '-y', '-i', audio_path,
                     '-ar', '16000', '-ac', '1', wav_path],
                    capture_output=True, check=True, timeout=120,
                )
                log.info('FFmpeg convert: %.1fs', time.time() - t0)

                model = _get_whisper()
                t0 = time.time()
                segments, info = model.transcribe(wav_path, language=language[:2])
                dur = time.time() - t0

                text = ' '.join(s.text for s in segments).strip()
                log.info('faster-whisper: %.1fs text=%d chars lang=%s',
                         dur, len(text), info.language)

            transcript_path = self._save_transcript(text, '', 'faster-whisper-tiny')
            return {
                'text': text,
                'summary': self._extract_summary(text),
                'output': transcript_path,
                'duration': dur,
                'model': 'faster-whisper-tiny',
                'chain': 'local-whisper',
                'language': info.language if info else language,
                'tokens': len(text.split()) if text else 0,
            }
        except ImportError:
            log.error('faster_whisper not installed')
            return {'error': 'faster_whisper not installed'}
        except subprocess.CalledProcessError as e:
            log.error('ffmpeg failed: %s', e.stderr[:200] if e.stderr else str(e))
            return {'error': f'ffmpeg failed: {str(e)[:100]}'}
        except Exception as e:
            log.error('whisper error: %s', e)
            return {'error': str(e)}

    def _save_transcript(self, text: str, session_id: str, model: str) -> Optional[str]:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        uid = session_id or 'anon'
        fname = f'{uid}_{ts}_trnscb.md'
        fpath = OUT_DIR / fname
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(text)
        log.info('Transcript saved: %s (%d chars)', fname, len(text))
        return str(fpath)

    def _extract_summary(self, text: str) -> str:
        lines = text.split('\n')
        summary_lines = []
        in_summary = False
        for line in lines:
            if re.match(r'^##?\s*Summary', line, re.IGNORECASE):
                in_summary = True
                continue
            if in_summary:
                if re.match(r'^##?\s', line) and 'Summary' not in line:
                    break
                summary_lines.append(line)
        return '\n'.join(summary_lines).strip() if summary_lines else text[:500]


_transcriber = Transcriber()

def get_transcriber() -> Transcriber:
    return _transcriber
