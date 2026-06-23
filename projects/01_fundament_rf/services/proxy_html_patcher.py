import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup


def _prefix(project_id: str, path: str) -> str:
    """Rewrite an absolute path to go through the proxy prefix.

    Shared vendor files under /static/vendor/ are served by the main app and
    should not be proxied to a sandbox project.
    """
    if not path or not path.startswith('/'):
        return path
    if path.startswith('/static/vendor/'):
        return path
    return f'/proxy/{project_id}{path}'


def patch_html(content: bytes, project_id: str, base_url: str) -> bytes:
    """Patch absolute links in HTML to go through /proxy/<project_id>/."""
    try:
        text = content.decode('utf-8')
    except UnicodeDecodeError:
        return content

    soup = BeautifulSoup(text, 'lxml')

    # Tag -> attribute mappings
    tag_attrs = [
        ('a', 'href'),
        ('link', 'href'),
        ('img', 'src'),
        ('script', 'src'),
        ('iframe', 'src'),
        ('source', 'src'),
        ('video', 'src'),
        ('audio', 'src'),
        ('embed', 'src'),
        ('object', 'data'),
        ('form', 'action'),
        ('input', 'formaction'),
        ('button', 'formaction'),
    ]

    for tag_name, attr_name in tag_attrs:
        for tag in soup.find_all(tag_name):
            val = tag.get(attr_name)
            if val:
                tag[attr_name] = _prefix(project_id, val)

    # SVG use / image with xlink:href or href
    for tag in soup.find_all(['use', 'image']):
        for attr in ['xlink:href', 'href']:
            val = tag.get(attr)
            if val:
                tag[attr] = _prefix(project_id, val)

    # Base href
    for base in soup.find_all('base'):
        val = base.get('href')
        if val:
            if val.startswith('/'):
                base['href'] = _prefix(project_id, val)
            elif val.startswith(base_url):
                rest = val[len(base_url):]
                base['href'] = f'/proxy/{project_id}/{rest.lstrip("/")}'

    # Meta refresh
    for meta in soup.find_all('meta', attrs={'http-equiv': 'refresh'}):
        content_val = meta.get('content', '')
        m = re.search(r'url=([^;\s]+)', content_val, re.IGNORECASE)
        if m:
            url = m.group(1)
            new_url = _prefix(project_id, url)
            meta['content'] = content_val.replace(url, new_url)

    # Inline styles with url(/...)
    for tag in soup.find_all(style=True):
        tag['style'] = _patch_css_url(tag['style'], project_id)

    # Inline scripts
    for script in soup.find_all('script'):
        if script.string:
            script.string = _patch_inline_js(script.string, project_id, base_url)

    # Event handlers with inline JS
    for tag in soup.find_all(True):
        for attr in tag.attrs:
            if attr.startswith('on'):
                tag[attr] = _patch_inline_js(tag[attr], project_id, base_url)

    return str(soup).encode('utf-8')


def patch_css(content: bytes, project_id: str) -> bytes:
    """Patch url(/...) references in CSS."""
    return _patch_css_url_bytes(content, project_id)


def _patch_css_url(text: str, project_id: str) -> str:
    def repl(m):
        path = m.group(2)
        quote = m.group(1) or ''
        new_path = _prefix(project_id, path)
        return f'url({quote}{new_path}{quote})'
    return re.sub(r'url\((["\']?)(/[^\)"\']*)\1\)', repl, text)


def _patch_css_url_bytes(content: bytes, project_id: str) -> bytes:
    def repl(m):
        quote = (m.group(1) or b'').decode('utf-8')
        path = m.group(2).decode('utf-8')
        new_path = _prefix(project_id, path)
        return f'url({quote}{new_path}{quote})'.encode('utf-8')
    return re.sub(rb'url\((["\']?)(/[^\)"\']*)\1\)', repl, content)


def _patch_inline_js(js: str, project_id: str, base_url: str) -> str:
    prefix = f'/proxy/{project_id}'

    # Strings starting with '/' inside quotes or backticks:
    # fetch('/api'), fetch(`/api/summary?symbol=${symbol}`), '/static', etc.
    def _rewrite_path(m):
        path = m.group(2)
        if path.startswith('/static/vendor/'):
            return m.group(0)
        return f'{m.group(1)}{prefix}{path}{m.group(3)}'

    js = re.sub(
        r'([`"\'])(/[^`"\']*)([`"\'])',
        _rewrite_path,
        js
    )

    # WebSocket ws://localhost:PORT/ws -> ws://localhost:5000/proxy/NN/ws
    base_port = base_url.split(':')[-1].rstrip('/')
    js = re.sub(
        rf'ws://localhost:{re.escape(base_port)}/',
        f'ws://localhost:5000/proxy/{project_id}/',
        js
    )

    # window.location.href = '/...' — already covered by string patch if quoted
    # location.assign('/...') — covered
    return js


def patch_location_header(location: str, project_id: str, base_url: str) -> str:
    """Rewrite a redirect Location header."""
    if location.startswith('/'):
        return _prefix(project_id, location)
    if location.startswith(base_url):
        rest = location[len(base_url):].lstrip('/')
        return f'/proxy/{project_id}/{rest}'
    return location
