import re
from typing import Dict, Any


# Patterns that are not allowed in user-edited code.
# Each entry is (pattern, flags). Most patterns are case-insensitive, but the
# Function constructor must be matched case-sensitively so that normal
# `function` declarations are not rejected.
FORBIDDEN_PATTERNS = [
    (r'eval\s*\(', re.IGNORECASE),
    (r'\bFunction\s*\(', 0),
    (r'document\.cookie', re.IGNORECASE),
    (r'localStorage\s*\.', re.IGNORECASE),
    (r'sessionStorage\s*\.', re.IGNORECASE),
    (r'fetch\s*\(', re.IGNORECASE),
    (r'XMLHttpRequest', re.IGNORECASE),
    (r'WebSocket\s*\(', re.IGNORECASE),
    (r'window\.parent', re.IGNORECASE),
    (r'window\.top', re.IGNORECASE),
    (r'location\.href\s*=', re.IGNORECASE),
    (r'location\.replace', re.IGNORECASE),
    (r'<script\s+src=["\']https?://', re.IGNORECASE),
]


def validate_code(code: str) -> Dict[str, Any]:
    """Basic validation to prevent obvious malicious code."""
    for pattern, flags in FORBIDDEN_PATTERNS:
        if re.search(pattern, code, flags):
            return {
                'ok': False,
                'error': f'Forbidden pattern detected: {pattern}'
            }
    return {'ok': True}


def _build_libs_html(libraries: list) -> str:
    libs = []
    if libraries:
        for lib in libraries:
            if lib == 'lightweight-charts':
                libs.append('<script src="/static/vendor/lightweight-charts@5.2.0/lightweight-charts.standalone.production.js"></script>')
            elif lib == 'tradingview':
                libs.append('<script src="/static/vendor/tradingview/tv.js"></script>')
    return '\n'.join(libs)


def _inject_libs_into_html(code: str, libs_html: str) -> str:
    """Insert vendor scripts into an existing HTML document."""
    if not libs_html:
        return code
    # Avoid duplicates
    for src in re.findall(r'src="([^"]+)"', libs_html):
        if src in code:
            return code
    head_close = re.search(r'</head>', code, re.IGNORECASE)
    if head_close:
        pos = head_close.start()
        return code[:pos] + libs_html + '\n' + code[pos:]
    html_tag = re.search(r'<html[^>]*>', code, re.IGNORECASE)
    if html_tag:
        pos = html_tag.end()
        return code[:pos] + '\n<head>\n' + libs_html + '\n</head>' + code[pos:]
    return libs_html + '\n' + code


def wrap_code(code: str, libraries: list = None) -> str:
    """Wrap user code in a safe iframe HTML using local vendor scripts.

    If the submitted code is already a full HTML document, return it directly
    (with requested libraries injected) instead of wrapping it in a script tag.
    """
    libs_html = _build_libs_html(libraries or [])
    stripped = code.strip()
    is_html = stripped.lower().startswith('<!doctype') or stripped.lower().startswith('<html')

    if is_html:
        return _inject_libs_into_html(code, libs_html)

    return f'''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'unsafe-inline'; img-src data: blob:;">
  {libs_html}
  <style>
    body {{ margin: 0; background: #131722; color: #d1d4dc; font-family: sans-serif; }}
    #error {{ color: #f85149; padding: 20px; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <div id="error"></div>
  <script>
    window.onerror = function(msg, url, line) {{
      document.getElementById('error').textContent = 'Error at line ' + line + ': ' + msg;
      return true;
    }};
    try {{
      {code}
    }} catch(e) {{
      document.getElementById('error').textContent = 'Error: ' + e.message;
    }}
  </script>
</body>
</html>'''


def execute_code(code: str, libraries: list = None) -> Dict[str, Any]:
    """Validate and wrap code, return HTML for sandbox iframe."""
    validation = validate_code(code)
    if not validation['ok']:
        return validation
    
    return {
        'ok': True,
        'html': wrap_code(code, libraries)
    }
