#!/usr/bin/env python3
"""Playwright: поиск исполнительных производств на fssp.gov.ru по ИНН.

Вывод: JSON строка с результатом или ошибкой.
Использование: playwright.sh audit_fssp.py <INN>
"""
import json
import sys
import os

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/home/user_aioc/workspace/tools/browser-temp/browsers"

from playwright.sync_api import sync_playwright

INN = sys.argv[1] if len(sys.argv) > 1 else ""


def main():
    if not INN:
        return {"status": "❌", "note": "INN not provided"}

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_default_timeout(20000)

            page.goto("https://fssp.gov.ru/", wait_until="networkidle")
            page.wait_for_timeout(2000)

            # Click "Банк данных исполнительных производств"
            try:
                page.click("text=Банк данных исполнительных производств", timeout=15000)
            except Exception:
                # Try alternative selector
                page.goto("https://fssp.gov.ru/iss/ip", wait_until="networkidle")
                page.wait_for_timeout(3000)

            page.wait_for_timeout(3000)

            # Find and fill the search input
            try:
                page.fill("input[name='number']", INN, timeout=10000)
            except Exception:
                try:
                    page.fill("input[placeholder*='номер']", INN, timeout=5000)
                except Exception:
                    return {"status": "❌", "note": "поле ввода ИНН не найдено"}

            # Click search button
            try:
                page.click("button[type='submit']", timeout=10000)
            except Exception:
                page.press("input[name='number']", "Enter")

            page.wait_for_timeout(5000)

            # Check results
            html = page.content()
            browser.close()

            if "ничего не найдено" in html.lower() or "0 записей" in html.lower():
                return {"status": "✅", "productions": [], "note": "исполнительных производств не найдено"}

            # Try to parse results table
            import re
            rows = re.findall(
                r'<tr[^>]*>.*?</tr>',
                re.search(r'<table[^>]*class=["\']result["\'][^>]*>.*?</table>', html, re.DOTALL).group(0)
                if re.search(r'<table[^>]*class=["\']result["\'][^>]*>.*?</table>', html, re.DOTALL)
                else '', re.DOTALL
            ) if re.search(r'<table[^>]*class=["\']result["\'][^>]*>.*?</table>', html, re.DOTALL) else []

            if rows:
                return {"status": "✅", "productions": [r.strip() for r in rows[:10]]}
            return {"status": "⚠️", "note": "страница загружена, но таблица не найдена", "html_len": len(html)}

    except Exception as e:
        return {"status": "❌", "note": str(e)[:200]}


if __name__ == "__main__":
    result = main()
    print(json.dumps(result, ensure_ascii=False))
