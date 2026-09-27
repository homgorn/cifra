"""Скриншоты живой версии сайта, а не локальных файлов.

Зачем: локальный рендер и опубликованный могут разойтись, если деплой
не прошёл или отдался кэш. Проверять надо то, что видит пользователь.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "reports" / "cifra18-audit" / "_qa"
BASE = "https://homgorn.github.io/cifra"
PAGES = [("index", ""), ("wm", "pages/wm-clusters.html"),
         ("plan", "pages/plan-3m.html"), ("dash", "pages/dash-audience.html")]


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright не установлен")
        return 2
    OUT.mkdir(parents=True, exist_ok=True)
    bad = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1440, "height": 1000},
                                  color_scheme="light")
        page = ctx.new_page()
        for name, rel in PAGES:
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)[:120]))
            page.goto(BASE + "/" + rel)
            page.wait_for_timeout(1100)
            f = OUT / ("live-%s.png" % name)
            page.screenshot(path=str(f))
            bg = page.evaluate("getComputedStyle(document.body).backgroundColor")
            print("%-18s body=%-22s errors=%d" % (f.name, bg, len(errors)))
            if errors:
                bad.append("%s: %s" % (name, errors[:2]))
        page.goto(BASE + "/")
        page.wait_for_timeout(800)
        page.keyboard.press("/")
        page.wait_for_timeout(400)
        page.fill(".search-input", "кластеры")
        page.wait_for_timeout(300)
        page.screenshot(path=str(OUT / "live-search.png"))
        print("live-search.png     снят")
        ctx.close()
        browser.close()
    print()
    for b in bad:
        print("FAIL: %s" % b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
