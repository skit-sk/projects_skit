from viz_lab.provider.opencode_provider import OpenCodeProvider
from viz_lab.provider.base import ModelProvider, ProviderResponse, TokenUsage


class TTSProvider(ModelProvider):
    def __init__(self):
        self.name = 'gemini-tts'
        self.provider = 'apiyi'
        self.capabilities = {'tts', 'audio'}
        self.max_tokens = 0
        self.cost_per_1k_input = 0.0
        self.cost_per_1k_output = 0.0
        self.model_id = 'apiyi/gemini-2.5-flash-tts'

    def generate(self, prompt: str, context=None) -> ProviderResponse:
        import subprocess, time, os
        start = time.time()
        clean_env = {k: v for k, v in os.environ.items()
                     if k not in ('TERM', 'COLUMNS', 'LINES')}
        try:
            result = subprocess.run(
                ['opencode', 'run', '--model', self.model_id, prompt],
                capture_output=True, text=True, timeout=30,
                env=clean_env,
            )
            dur = (time.time() - start) * 1000
            text = result.stdout.strip()
            return ProviderResponse(
                text=text or 'TTS processing complete',
                usage=TokenUsage(duration_ms=dur),
            )
        except Exception as e:
            return ProviderResponse(text=f'TTS error: {e}')

    def render(self, data: dict, chart_type: str) -> ProviderResponse:
        return self.generate(data.get('text', ''))


class AudioProvider(OpenCodeProvider):
    def __init__(self):
        super().__init__(
            name='gpt-audio',
            model_id='openrouter/openai/gpt-4o-audio-preview',
            provider='openrouter',
            capabilities={'asr', 'audio', 'code'},
            max_tokens=16384,
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.012,
        )


def create_tts() -> TTSProvider:
    return TTSProvider()


def create_audio() -> AudioProvider:
    return AudioProvider()


providers = [create_tts, create_audio]
