#!/usr/bin/env python3
"""CloakBrowser: поиск банкротств на fedresurs.ru по ИНН.

Вывод: JSON строка с результатом или ошибкой.
Использование: cloakbrowser.sh audit_bankruptcy.py <INN>
"""
import json
import sys
import os

os.environ.setdefault("CLOAKBROWSER_CACHE_DIR", "/home/user_aioc/workspace/tools/browser-temp/cache/cloakbrowser")

from cloakbrowser import launch

INN = sys.argv[1] if len(sys.argv) > 1 else ""


def main():
    if not INN:
        return {"status": "❌", "note": "INN not provided"}

    try:
        browser = launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(25000)

        # Search via fedresurs with Qrator bypass
        page.goto(f"https://bankrot.fedresurs.ru/Search?q={INN}", wait_until="networkidle")
        page.wait_for_timeout(3000)

        # Wait for Qrator to pass and content to load
        try:
            page.wait_for_selector("table", timeout=20000)
        except Exception:
            pass

        page.wait_for_timeout(2000)
        html = page.content()
        browser.close()

        if not html or len(html) < 500:
            return {"status": "⚠️", "note": "fedresurs не ответил (Qrator?)", "html_len": len(html)}

        import re
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()

        if "ничего не найдено" in text.lower():
            return {"status": "✅", "bankruptcies": [], "note": "банкротств не найдено"}

        # Find bankruptcy case numbers
        cases = re.findall(r'[АА-Я]{2,3}-\d+/\d+/\d+-\d+', text)
        if cases:
            return {"status": "✅", "bankruptcies": cases[:10]}

        # Check if any case mentions exist
        if "банкрот" in text.lower():
            snippets = []
            idx = 0
            for _ in range(5):
                idx = text.lower().find("банкрот", idx)
                if idx < 0:
                    break
                snippets.append(text[max(0, idx - 30):idx + 80].strip())
                idx += 1
            return {"status": "⚠️", "bankruptcies": snippets, "note": "найдены упоминания банкротства"}

        return {"status": "⚠️", "note": "страница загружена, данные не распознаны", "text_len": len(text)}

    except Exception as e:
        return {"status": "❌", "note": str(e)[:200]}


if __name__ == "__main__":
    result = main()
    print(json.dumps(result, ensure_ascii=False))
