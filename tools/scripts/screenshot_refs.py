#!/usr/bin/env python3
"""Full analysis of all reference URLs: screenshots, text, page tree."""
import os, sys, json, re, time
from pathlib import Path
from urllib.parse import urlparse, urljoin

os.environ['LD_LIBRARY_PATH'] = os.path.expanduser('~/workspace/tools/playwright/lib')

from playwright.sync_api import sync_playwright

# Use Chrome 149 (more stable than headless-shell v1217)
CHROME = os.path.expanduser(
    '~/workspace/tools/playwright/browsers/chromium_headless_shell-1217/chrome-headless-shell-linux64/chrome-headless-shell')

ARGS = [
    '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
    '--disable-software-rasterizer', '--disable-accelerated-2d-canvas',
    '--disable-setuid-sandbox',
]

# workspace/projects/12_tradehelp/static/ref/
BASE = Path(__file__).resolve().parents[2] / 'projects/12_tradehelp/static/ref'
BASE.mkdir(parents=True, exist_ok=True)

RESOURCES = [
    {'id': 'pifagor-bookmap', 'url': 'https://metrics.pifagor.trade/bookmap.html',     'depth': 1, 'title': 'Pifagor Trade — BookMap'},
    {'id': 'gexbot',          'url': 'https://www.gexbot.com/',                          'depth': 1, 'title': 'GexBot'},
    {'id': 'mobchart',        'url': 'https://mobchart.com/',                            'depth': 1, 'title': 'MobChart'},
    {'id': 'youtube-bookmap', 'url': 'https://www.youtube.com/embed/vLspipSCg6Y',      'depth': 1, 'title': 'YouTube BookMap'},
    {'id': 'deepcharts',      'url': 'https://my.deepcharts.com/',                       'depth': 2, 'title': 'Deepcharts'},
    {'id': 'tradingiq',       'url': 'https://www.tradingiq.io',                         'depth': 2, 'title': 'TradingIQ'},
    {'id': 'kingfisher',      'url': 'https://thekingfisher.io/ru/blogs',                'depth': 2, 'title': 'Kingfisher'},
    {'id': 'watchlist-top',   'url': 'https://watchlist.top/#list/0',                    'depth': 2, 'title': 'Watchlist.Top'},
    {'id': 'quantower',       'url': 'https://help.quantower.com/quantower/',            'depth': 3, 'title': 'Quantower'},
]


def get_internal_links(page, base_url):
    links = set()
    base_host = urlparse(base_url).hostname
    for a in page.query_selector_all('a[href]'):
        href = a.get_attribute('href')
        if not href or href.startswith('#') or href.startswith('javascript:'):
            continue
        abs_url = urljoin(base_url, href)
        h = urlparse(abs_url).hostname
        if h and base_host in h and not any(x in abs_url for x in ['.pdf', '.zip', 'mailto:']):
            links.add(abs_url)
    return list(links)[:25]


def slugify(url):
    p = urlparse(url).path.strip('/').replace('/', '-') or 'main'
    p = re.sub(r'[^a-z0-9_-]', '', p.lower())[:60]
    return p or 'main'


def analyze_page(browser, url, out_dir, seq):
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    slug = f'{seq:02d}-{slugify(url)}'
    png = out_dir / f'{slug}.png'
    txt = out_dir / f'{slug}.txt'
    result = {'url': url, 'slug': slug}

    try:
        page.goto(url, wait_until='networkidle', timeout=20000)
    except Exception:
        try:
            page.goto(url, wait_until='load', timeout=20000)
        except Exception as e:
            result['error'] = str(e)
            page.close()
            return result

    result['title'] = page.title()
    time.sleep(1)

    # Dismiss cookie/consent dialogs on known domains
    for lbl in ['Accept all', 'I agree', 'Akkoord', 'Принять все', 'Accept', 'Agree']:
        try:
            btn = page.get_by_text(lbl, exact=False)
            if btn.count() > 0:
                btn.first.click(timeout=2000)
                time.sleep(0.5)
                break
        except Exception:
            pass

    # Screenshot with fallback
    try:
        page.screenshot(path=str(png), full_page=True)
        result['screenshot'] = str(png.relative_to(BASE.parent.parent))
    except Exception:
        try:
            page.screenshot(path=str(png), full_page=False)
        except Exception as e:
            result['screenshot_error'] = str(e)

    # Text
    try:
        text = page.inner_text('body')
        txt.write_text(text[:20000], encoding='utf-8')
    except Exception as e:
        result['text_error'] = str(e)

    # Sections (h1, h2, h3)
    sections = []
    try:
        for h in page.query_selector_all('h1, h2, h3'):
            tag = h.evaluate('el => el.tagName.toLowerCase()')
            txt_h = h.inner_text().strip()
            if txt_h:
                sections.append({'tag': tag, 'text': txt_h[:100]})
    except Exception:
        pass
    result['sections'] = sections

    page.close()
    return result


def main():
    all_data = []

    for res in RESOURCES:
        rid = res['id']
        print(f'\n=== {res["title"]} ({rid}) ===')
        out_dir = BASE / rid
        out_dir.mkdir(parents=True, exist_ok=True)
        pages = []

        # New browser for each resource (isolates crashes)
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(
                    headless=True, executable_path=CHROME, args=ARGS,
                )
            except Exception as e:
                print(f'  LAUNCH FAILED: {e}')
                continue

            try:
                # 1. Main page
                print(f'  [{len(pages):02d}] {res["url"]}')
                r = analyze_page(browser, res['url'], out_dir, len(pages))
                pages.append(r)

                # 2. Subpages
                if res['depth'] > 1 and 'error' not in r:
                    try:
                        pg = browser.new_page(viewport={'width': 1920, 'height': 1080})
                        pg.goto(res['url'], wait_until='networkidle', timeout=15000)
                        links = get_internal_links(pg, res['url'])
                        pg.close()
                    except Exception:
                        links = []

                    seen = {res['url']}
                    for link in links:
                        if link in seen or len(pages) >= 20:
                            continue
                        seen.add(link)
                        print(f'  [{len(pages):02d}] {link}')
                        r = analyze_page(browser, link, out_dir, len(pages))
                        pages.append(r)
                        time.sleep(0.5)
            except Exception as e:
                print(f'  ERROR: {e}')

            try:
                browser.close()
            except Exception:
                pass

        # 3. Save tree.json
        tree = {'id': rid, 'title': res['title'], 'url': res['url'], 'pages': pages}
        (out_dir / 'tree.json').write_text(json.dumps(tree, indent=2, ensure_ascii=False), encoding='utf-8')
        all_data.append(tree)

    # 4. Global index
    (BASE / 'data.json').write_text(json.dumps(all_data, indent=2, ensure_ascii=False), encoding='utf-8')

    total_png = sum(len(t['pages']) for t in all_data)
    total_err = sum(1 for t in all_data for p in t['pages'] if 'error' in p)
    print(f'\n=== DONE ===\nResources: {len(all_data)}\nPages: {total_png}\nErrors: {total_err}')


if __name__ == '__main__':
    main()
