#!/usr/bin/env python3
"""Convert TradingView gallery iframes to sequential lazy-loaded placeholders."""
from pathlib import Path
import re

BASE_DIR = Path(__file__).parent
INDEX = BASE_DIR / "index.html"

html = INDEX.read_text(encoding="utf-8")

# Replace <iframe src="widgets/.../index.html"></iframe> inside .card-preview
# with placeholder and data-widget-src on parent.

def replace_iframe(match):
    src = match.group(1)
    return f'<div class="widget-placeholder">Loading...</div></div>\n            </div>\n            <div class="card-info" data-widget-src="{src}">'

# Actually we need to operate on the card-preview div structure.
# Pattern: <div class="card-preview"><iframe src="..."></iframe></div>
html = re.sub(
    r'<div class="card-preview"><iframe src="([^"]+)"></iframe></div>',
    r'<div class="card-preview" data-widget-src="\1"><div class="widget-placeholder">Loading...</div></div>',
    html
)

# Insert CSS and JS before </body>
css_js = '''
<style>
.widget-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #787b86;
    font-size: 11px;
    background: #131722;
    text-align: center;
}
.widget-placeholder a {
    color: #2962ff;
    text-decoration: none;
}
.widget-placeholder a:hover {
    text-decoration: underline;
}
.card-preview iframe {
    width: 100%;
    height: 100%;
    border: none;
}
</style>
<script>
(function() {
    const MAX_CONCURRENT = 3;
    const DELAY_MS = 800;
    const TIMEOUT_MS = 10000;

    const containers = Array.from(document.querySelectorAll('.card-preview[data-widget-src]'));
    let index = 0;
    let active = 0;

    function loadNext() {
        while (active < MAX_CONCURRENT && index < containers.length) {
            const container = containers[index++];
            active++;
            loadWidget(container);
        }
    }

    function loadWidget(container) {
        const src = container.getAttribute('data-widget-src');
        const placeholder = container.querySelector('.widget-placeholder');
        const iframe = document.createElement('iframe');
        iframe.src = src;
        let loaded = false;

        const timer = setTimeout(() => {
            if (!loaded) {
                iframe.remove();
                if (placeholder) {
                    placeholder.innerHTML = '<a href="' + src + '" target="_blank">Open ↗</a>';
                }
                active--;
                setTimeout(loadNext, DELAY_MS);
            }
        }, TIMEOUT_MS);

        iframe.onload = function() {
            if (loaded) return;
            loaded = true;
            clearTimeout(timer);
            if (placeholder) placeholder.remove();
            active--;
            setTimeout(loadNext, DELAY_MS);
        };

        iframe.onerror = function() {
            if (loaded) return;
            loaded = true;
            clearTimeout(timer);
            iframe.remove();
            if (placeholder) {
                placeholder.innerHTML = '<a href="' + src + '" target="_blank">Open ↗</a>';
            }
            active--;
            setTimeout(loadNext, DELAY_MS);
        };

        container.appendChild(iframe);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', loadNext);
    } else {
        loadNext();
    }
})();
</script>
'''

html = html.replace('</body>', css_js + '\n</body>')

INDEX.write_text(html, encoding="utf-8")
print(f"Updated {INDEX}")
print(f"Lazy-loaded containers: {html.count('data-widget-src')}")
