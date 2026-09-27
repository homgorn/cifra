"""Геометрия раскладки: ищет элементы, вывалившиеся из контентной колонки.

Зачем: 2026-09-27 пользователь показал скриншот, где фильтр таблицы и сама
таблица оказались левее контента. Числовые проверки это не видят: страница
валидна, ссылки целые, тема одна. Видно только геометрию в браузере.

Запуск из корня проекта:
  python scripts/export/check_layout.py
"""
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SITE = ROOT / "reports" / "cifra18-audit"
PAGES = ["index.html", "pages/wm-clusters.html", "pages/wm-queries.html",
         "pages/technical.html", "pages/plan-3m.html", "pages/dash-money.html",
         "pages/wm-duplicates.html", "pages/marketing.html"]

PROBE = """
() => {
  const out = {boxes: {}, problems: [], charts: []};
  const vw = document.documentElement.clientWidth;
  out.viewport = vw;
  const pick = (sel) => document.querySelector(sel);
  const measure = (name, el) => {
    if (!el) return;
    const r = el.getBoundingClientRect();
    out.boxes[name] = {x: Math.round(r.x), w: Math.round(r.width)};
  };
  measure('sidebar', pick('.sidebar'));
  measure('content', pick('.content') || pick('main .container') || pick('main > div'));
  measure('table', pick('.table-wrapper'));
  measure('tools', pick('.table-tools'));

  // Все канвасы поимённо: 300x150 означает, что Chart.js не подхватил
  // размер контейнера и график остался дефолтным.
  document.querySelectorAll('canvas').forEach((cv) => {
    const r = cv.getBoundingClientRect();
    const box = cv.closest('.chart-container');
    const item = {
      id: cv.id || '(без id)',
      w: Math.round(r.width), h: Math.round(r.height),
      boxH: box ? Math.round(box.getBoundingClientRect().height) : null
    };
    out.charts.push(item);
    if (r.width < 120 || r.height < 60) {
      out.problems.push('канвас ' + item.id + ' не получил размер: ' + item.w + 'x' + item.h);
    }
  });

  out.scrollW = document.documentElement.scrollWidth;
  if (out.scrollW > vw + 1) out.problems.push('страница шире экрана на ' + (out.scrollW - vw) + 'px');
  const cont = out.boxes.content;
  const tbl = out.boxes.table;
  if (cont && tbl && tbl.x + 6 < cont.x) {
    out.problems.push('таблица левее контентной колонки: x=' + tbl.x + ' против ' + cont.x);
  }
  const tools = out.boxes.tools;
  if (cont && tools && tools.x + 6 < cont.x) {
    out.problems.push('фильтр таблицы левее контентной колонки: x=' + tools.x + ' против ' + cont.x);
  }
  return out;
}
"""


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright не установлен")
        return 2

    bad = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for scheme in ("dark", "light"):
            ctx = browser.new_context(viewport={"width": 1440, "height": 1000},
                                      color_scheme=scheme)
            page = ctx.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)[:140]))
            for rel in PAGES:
                errors.clear()
                page.goto((SITE / rel).as_uri())
                # Chart.js тянет размер на следующем кадре после загрузки
                # шрифтов; 450ms хватало не всегда, и проверка ловила
                # недоделанный график вместо готового.
                page.wait_for_timeout(1100)
                r = page.evaluate(PROBE)
                tag = "[%s] %s" % (scheme, rel)
                pr = list(r["problems"])
                if errors:
                    pr.append("ошибки JS: " + "; ".join(errors[:2]))
                if pr:
                    bad.append("%s: %s" % (tag, "; ".join(pr)))
                    print("FAIL %s" % tag)
                    for x in pr:
                        print("       %s" % x)
                else:
                    ch = ", ".join("%s %dx%d" % (c["id"], c["w"], c["h"])
                                   for c in r["charts"])
                    print("ok   %-42s %s" % (tag, ch))
            ctx.close()
        browser.close()

    print()
    if bad:
        print("LAYOUT FAILED: %d проблем на %d страницах" % (len(bad), len(PAGES)))
        return 1
    print("LAYOUT PASSED: раскладка и графики в порядке в обеих схемах")
    return 0


if __name__ == "__main__":
    sys.exit(main())
