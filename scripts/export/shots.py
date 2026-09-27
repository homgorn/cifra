#!/usr/bin/env python3
"""Скриншоты сайта отчёта для визуальной проверки.

Зачем: 2026-09-27 отчёт открылся в светлой схеме ОС с тёмной шапкой, это видно
только глазами. Числовые проверки такое не ловят, нужен рендер.

Снимает главную, страницу с подшапкой, план и открытый поиск, в светлой и
тёмной схеме, и проверяет, что фон страницы один и тот же (тема одна).

Запуск из корня проекта:
  python scripts/export/shots.py
  python scripts/export/shots.py --out reports/cifra18-audit/_qa
"""
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SITE = ROOT / "reports" / "cifra18-audit"
PAGES = [("index", "index.html"), ("wm", "pages/wm-clusters.html"),
         ("plan", "pages/plan-3m.html"), ("dash", "pages/dash-audience.html")]


def main():
    out = ROOT / "reports" / "cifra18-audit" / "_qa"
    for i, a in enumerate(sys.argv):
        if a == "--out" and i + 1 < len(sys.argv):
            out = Path(sys.argv[i + 1])
    out.mkdir(parents=True, exist_ok=True)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright не установлен: pip install playwright && playwright install chromium")
        return 2

    bad = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for scheme in ("dark", "light"):
            ctx = browser.new_context(viewport={"width": 1440, "height": 1000},
                                      color_scheme=scheme, device_scale_factor=1)
            page = ctx.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)[:120]))
            for name, rel in PAGES:
                page.goto((SITE / rel).as_uri())
                page.wait_for_timeout(700)
                f = out / ("%s-%s.png" % (name, scheme))
                page.screenshot(path=str(f), full_page=False)
                bg = page.evaluate("getComputedStyle(document.body).backgroundColor")
                header = page.evaluate(
                    "getComputedStyle(document.querySelector('.site-header')).backgroundColor")
                print("%-28s body=%-22s header=%-26s errors=%d"
                      % (f.name, bg, header, len(errors)))
            # оверлей поиска
            page.goto((SITE / "index.html").as_uri())
            page.wait_for_timeout(500)
            page.keyboard.press("/")
            page.wait_for_timeout(400)
            page.fill(".search-input", "дубли")
            page.wait_for_timeout(300)
            page.screenshot(path=str(out / ("search-%s.png" % scheme)))
            print("%-28s снят" % ("search-%s.png" % scheme))
            if errors:
                bad.append("%s: ошибки JS %s" % (scheme, errors[:3]))
            ctx.close()
        browser.close()

    print("\nкаталог: %s" % out)
    for b in bad:
        print("FAIL: %s" % b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
