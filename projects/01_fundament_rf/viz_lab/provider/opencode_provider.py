import json
import os
import re
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from viz_lab.provider.base import ModelProvider, ProviderResponse, TokenUsage, FileRef


OPENCODE_BIN = os.environ.get('OPENCODE_BIN', '/home/user_aioc/.opencode/bin/opencode')
OPENCODE_WORKDIR = os.environ.get('OPENCODE_WORKDIR', '/tmp/viz_lab_opencode')


class OpenCodeProvider(ModelProvider):
    def __init__(self, name: str, model_id: str, provider: str,
                 capabilities: set[str] | None = None,
                 max_tokens: int = 8192,
                 cost_per_1k_input: float = 0.0,
                 cost_per_1k_output: float = 0.0):
        self.name = name
        self.model_id = model_id
        self.provider = provider
        self.capabilities = capabilities or {'chart', 'code', 'vision'}
        self.max_tokens = max_tokens
        self.cost_per_1k_input = cost_per_1k_input
        self.cost_per_1k_output = cost_per_1k_output
        self._workdir = Path(OPENCODE_WORKDIR)
        self._workdir.mkdir(parents=True, exist_ok=True)

    def generate(self, prompt: str, context: list[FileRef] | None = None) -> ProviderResponse:
        start = time.time()
        system_prompt = self._build_system_prompt('code', context)
        full_prompt = f'{system_prompt}\n\n{prompt}'

        stdout, stderr, returncode = self._run_opencode(full_prompt)
        duration = (time.time() - start) * 1000

        if returncode != 0:
            return ProviderResponse(
                text=f'Error (exit {returncode}): {stderr[:500]}',
                usage=TokenUsage(duration_ms=duration),
            )

        text = stdout.strip()
        usage = self._parse_usage(stdout, stderr, duration)
        files = self._extract_code_blocks(text)
        script = self._find_main_script(files)

        return ProviderResponse(
            text=text,
            files=files,
            script=script,
            usage=usage,
        )

    def render(self, data: dict, chart_type: str) -> ProviderResponse:
        data_json = json.dumps(data, indent=2, ensure_ascii=False)
        prompt = (
            f'Create a {chart_type} visualization using this data:\n\n'
            f'```json\n{data_json[:5000]}\n```\n\n'
            f'Generate Python code using plotly that creates the chart. '
            f'Save the output as an HTML file. Use the filename "chart.html".'
        )
        return self.generate(prompt)

    def to_dict(self) -> dict:
        d = super().to_dict()
        d['model_id'] = self.model_id
        return d

    def _build_system_prompt(self, task: str, context: list[FileRef] | None) -> str:
        lines = [
            'You are a data visualization assistant. Generate Python code for charts.',
            'Use libraries: plotly, matplotlib, pandas, numpy, json.',
            'IMPORTANT:',
            '- Save all output files in the current directory.',
            '- Use filename "chart.html" for Plotly/HTML charts.',
            '- Use filename "chart.png" or "chart.svg" for image output.',
            '- Include complete, working code in a single ```python block.',
            '- Do NOT use interactive display (plt.show). Use savefig/write_html.',
        ]
        if context:
            lines.append('\nContext files available:')
            for f in context:
                lines.append(f'  - {f.name}')
        return '\n'.join(lines)

    def _run_opencode(self, prompt: str) -> tuple[str, str, int]:
        clean_env = {k: v for k, v in os.environ.items()
                     if k not in ('TERM', 'COLUMNS', 'LINES')}
        clean_env['OPENCODE_HOME'] = str(self._workdir)
        timeout = 60
        try:
            result = subprocess.run(
                [OPENCODE_BIN, 'run', '--dir', str(self._workdir),
                 '--model', self.model_id,
                 prompt],
                capture_output=True, text=True, timeout=timeout,
                env=clean_env,
            )
            if result.stdout:
                return result.stdout, result.stderr, result.returncode
            error_text = result.stderr.lower()
            if 'unauthorized' in error_text or 'credits' in error_text or 'error' in error_text:
                return '', f'API Error: {result.stderr[:300]}', 1
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return '', f'Timeout ({timeout}s) - model may be overloaded', -1
        except FileNotFoundError:
            return '', f'opencode not found at {OPENCODE_BIN}', -1

    def _parse_usage(self, stdout: str, stderr: str, duration_ms: float) -> TokenUsage:
        tokens = re.findall(r'(\d+)\s*tokens', stdout + stderr)
        input_t = int(tokens[0]) if tokens else 0
        output_t = int(tokens[1]) if len(tokens) > 1 else 0
        return TokenUsage(
            input_tokens=input_t,
            output_tokens=output_t,
            total_tokens=input_t + output_t,
            duration_ms=duration_ms,
        )

    def _extract_code_blocks(self, text: str) -> list[FileRef]:
        files = []
        lang_map = {
            'python': 'py', 'py': 'py',
            'javascript': 'js', 'js': 'js',
            'html': 'html', 'svg': 'svg',
            'json': 'json', 'csv': 'csv',
            'bash': 'sh', 'shell': 'sh',
            'text': 'txt', 'txt': 'txt',
        }
        pattern = re.compile(r'```(\w+)?\n(.*?)```', re.DOTALL)
        for match in pattern.finditer(text):
            lang = match.group(1) or 'txt'
            code = match.group(2).strip()
            if len(code) > 20:
                ext = lang_map.get(lang.lower(), lang)
                fname = f'code_{uuid.uuid4().hex[:8]}.{ext}'
                fpath = str(self._workdir / fname)
                with open(fpath, 'w') as f:
                    f.write(code)
                files.append(FileRef(path=fpath, name=fname, mime=f'text/{ext}'))
        return files

    def _find_main_script(self, files: list[FileRef]) -> str | None:
        for f in files:
            if f.name.endswith('.py'):
                try:
                    with open(f.path) as fh:
                        return fh.read()
                except OSError:
                    pass
        return None
