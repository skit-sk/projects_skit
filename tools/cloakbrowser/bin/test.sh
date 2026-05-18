#!/bin/bash
# Quick sanity check for CloakBrowser
source "$(dirname "$0")/../config/env.sh"
python3 -c "
from cloakbrowser import launch, binary_info
info = binary_info()
print(f'CloakBrowser binary: {info.get(\"version\", \"?\")} ({info.get(\"platform\", \"?\")})')
browser = launch(headless=True)
page = browser.new_page()
page.set_viewport_size({'width': 1920, 'height': 1080})
page.goto('https://example.com', wait_until='networkidle', timeout=30000)
print(f'Page title: {page.title()}')
page.screenshot(path='/tmp/cloak_test.png')
import os; sz = os.path.getsize('/tmp/cloak_test.png')
print(f'Screenshot: OK ({sz} bytes)')
browser.close()
print('SANITY CHECK PASSED')
"
