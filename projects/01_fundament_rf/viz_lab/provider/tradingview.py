import os
import subprocess
import time
import uuid
from pathlib import Path
from viz_lab.provider.base import ModelProvider, ProviderResponse, TokenUsage, FileRef


SCREENSHOT_BROWSER = str(Path(__file__).parent.parent.parent.parent
                         / 'projects' / '07_tg_bot_aiforguest' / 'bot' / 'screenshot_browser.py')
SCREENSHOT_WIDGET = str(Path(__file__).parent.parent.parent.parent
                        / 'projects' / '07_tg_bot_aiforguest' / 'bot' / 'screenshot_widget.py')


class TradingViewProvider(ModelProvider):
    def __init__(self):
        self.name = 'tv-screenshot'
        self.provider = 'tradingview'
        self.capabilities = {'chart'}
        self.max_tokens = 0
        self.cost_per_1k_input = 0
        self.cost_per_1k_output = 0
        self._output_dir = Path('/tmp/viz_lab_tv_screenshots')
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, prompt: str, context: list[FileRef] | None = None) -> ProviderResponse:
        return ProviderResponse(
            text='TradingView provider only supports chart screenshots. Use render() with chart_type="screenshot".'
        )

    def render(self, data: dict, chart_type: str) -> ProviderResponse:
        start = time.time()
        symbol = data.get('symbol', 'BTCUSDT')
        tf = data.get('timeframe', '1d')
        range_val = data.get('range', '')
        use_widget = data.get('use_widget', False)

        output_path = self._output_dir / f'tv_{uuid.uuid4().hex[:8]}_{symbol}.png'

        env = os.environ.copy()
        env['DISPLAY'] = ':99'

        if use_widget:
            script = SCREENSHOT_WIDGET
        else:
            script = SCREENSHOT_BROWSER

        try:
            result = subprocess.run(
                ['python3', script, symbol, tf, range_val],
                capture_output=True, text=True, timeout=60,
                cwd=str(Path(script).parent),
                env=env,
            )
            duration = (time.time() - start) * 1000

            path = result.stdout.strip()
            if os.path.exists(path):
                dest = output_path
                import shutil
                shutil.copy2(path, dest)
                size = os.path.getsize(dest)
                return ProviderResponse(
                    text=f'TradingView screenshot: {symbol} {tf} {range_val}',
                    files=[FileRef(path=str(dest), name=f'{symbol}_{tf}.png',
                                    mime='image/png', size_bytes=size)],
                    usage=TokenUsage(duration_ms=duration),
                )
            else:
                return ProviderResponse(
                    text=f'Screenshot error:\nstdout: {result.stdout[:500]}\nstderr: {result.stderr[:500]}',
                    usage=TokenUsage(duration_ms=duration),
                )

        except subprocess.TimeoutExpired:
            return ProviderResponse(
                text='TradingView screenshot timeout (60s)',
                usage=TokenUsage(duration_ms=60000),
            )
        except FileNotFoundError:
            return ProviderResponse(
                text=f'Screenshot script not found: {script}',
                usage=TokenUsage(duration_ms=0),
            )


def create_tradingview() -> TradingViewProvider:
    return TradingViewProvider()


providers = [create_tradingview]
