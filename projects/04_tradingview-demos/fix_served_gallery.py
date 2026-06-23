#!/usr/bin/env python3
"""Convert served TradingView gallery iframes to sequential lazy-loaded placeholders."""
from pathlib import Path
import re

INDEX = Path('/home/user_aioc/workspace/projects/01_fundament_rf/static/sandbox/04/index.html')

html = INDEX.read_text(encoding='utf-8')

# Replace <div class="card-preview"><iframe src="..."></iframe></div>
html = re.sub(
    r'<div class="card-preview"><iframe src="([^"]+)"></iframe></div>',
    r'<div class="card-preview" data-widget-src="\1"><div class="widget-placeholder">Loading...</div></div>',
    html
)

# Add placeholder CSS inside existing <style> block
css = '''
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
'''

# Insert CSS before </style> in head
html = html.replace('</style>', css + '\n    </style>', 1)

# Add sequential loader script before existing search script
loader_script = '''
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

# Insert loader script before the search script
html = html.replace('<script>\n    document.addEventListener(\'DOMContentLoaded\', function() {', loader_script + '\n<script>\n    document.addEventListener(\'DOMContentLoaded\', function() {')

INDEX.write_text(html, encoding='utf-8')
print(f"Updated {INDEX}")
print(f"Lazy-loaded containers: {html.count('data-widget-src')}")
