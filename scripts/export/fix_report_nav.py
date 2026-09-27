#!/usr/bin/env python3
"""Propagate the Вебмастер nav dropdown + standard footer across the report site.

- Inserts the Вебмастер dropdown before the Еще dropdown (skips files that
  already have it).
- Replaces the whole footer with the standard 4-column version.
- Renumbers kickers/footers: 'из 12' -> 'из 22', 'из 23' -> 'из 22'.
- Total pages: 22 (1-12 legacy incl. methodology=9, 13-22 wm-*).
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SITE = os.path.join(ROOT, "reports", "cifra18-audit")

WM_LINKS = [
    ("wm-overview.html", "Сводка Вебмастера", "717 URL"),
    ("wm-indexing.html", "Индексация по разделам", "6%"),
    ("wm-duplicates.html", "Дубли", "128"),
    ("wm-errors.html", "Ошибки и качество", "286"),
    ("wm-redirects.html", "Редиректы", "89"),
    ("wm-queries.html", "Запросы и позиции", "535"),
    ("wm-clusters.html", "Кластеры", "8 групп"),
    ("wm-gaps.html", "Пробелы контента", "топ-10"),
    ("wm-links.html", "Внутренние ссылки", "62 битых"),
    ("wm-plan.html", "План по Вебмастеру", "ICE"),
]

PAGE_META = {
    "index.html": ("1", "Резюме"),
    "technical.html": ("2", "Техника"),
    "content.html": ("3", "Контент"),
    "competitors.html": ("4", "Конкуренты"),
    "local.html": ("5", "Регионы"),
    "geo.html": ("6", "GEO"),
    "knowledge.html": ("7", "База знаний"),
    "roadmap.html": ("8", "План"),
    "prices.html": ("10", "Цены"),
    "season.html": ("11", "Сезон"),
    "marketing.html": ("12", "Маркетинг"),
}


def wm_dropdown(prefix):
    links = "\n".join(
        '          <a href="%s%s">%s <span class="drop-hint">%s</span></a>' % (prefix, f, t, h)
        for f, t, h in WM_LINKS)
    return (
        '      <div class="nav-dropdown">\n'
        '        <button class="nav-link nav-drop-btn" aria-haspopup="true">Вебмастер <span class="drop-arrow">▾</span></button>\n'
        '        <div class="nav-drop-menu">\n'
        + links + '\n'
        '        </div>\n'
        '      </div>\n')


def footer(home, links, num, title, top):
    (idx, tech, cont, road, comp, loc, geo, know,
     wmov, wmq, wmg, wmp, meth) = links
    return (
        '<footer class="site-footer">\n'
        '  <div class="container container-wide">\n'
        '    <div class="footer-grid">\n'
        '      <div class="footer-brand"><a class="logo" href="%s"><span class="logo-mark">Ц18</span><span>Цифра. Аудит</span></a><p>Отчет по продвижению цифра18.рф. Техника, контент, конкуренты, регионы, GEO, Вебмастер. Сентябрь 2026.</p></div>\n'
        '      <div class="footer-nav"><h4>Отчет</h4><ul><li><a href="%s">Резюме</a></li><li><a href="%s">Техника</a></li><li><a href="%s">Контент</a></li><li><a href="%s">План</a></li></ul></div>\n'
        '      <div class="footer-nav"><h4>Анализ</h4><ul><li><a href="%s">Конкуренты</a></li><li><a href="%s">Регионы</a></li><li><a href="%s">GEO</a></li><li><a href="%s">База знаний</a></li></ul></div>\n'
        '      <div class="footer-nav"><h4>Вебмастер</h4><ul><li><a href="%s">Сводка</a></li><li><a href="%s">Запросы</a></li><li><a href="%s">Пробелы</a></li><li><a href="%s">План</a></li></ul></div>\n'
        '      <div class="footer-nav"><h4>Файлы</h4><ul><li><a href="%s">Методика</a></li><li><a href="%s">Сроки</a></li><li><a href="%s">Наверх</a></li></ul></div>\n'
        '    </div>\n'
        '    <div class="footer-bottom"><span>Цифра18 • Ижевск • сентябрь 2026</span><span>Страница %s из 22 • %s</span></div>\n'
        '  </div>\n'
        '</footer>' % (
            home, idx, tech, cont, road, comp, loc, geo, know,
            wmov, wmq, wmg, wmp, meth, road, top, num, title))


def process(path, prefix, num, title, top):
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    orig = html

    nav_head = html.split("</nav>")[0]
    if "wm-overview.html" not in nav_head:
        m = re.search(r'(      <div class="nav-dropdown">\n'
                      r'        <button class="nav-link nav-drop-btn(?: active)?" aria-haspopup="true">Еще)',
                      html)
        if m:
            html = html[:m.start(1)] + wm_dropdown(prefix) + m.group(1) + html[m.end(1):]
        else:
            print("WARN no nav anchor: %s" % path)

    if prefix == "pages/":
        links = ("index.html", "pages/technical.html", "pages/content.html",
                 "pages/roadmap.html", "pages/competitors.html", "pages/local.html",
                 "pages/geo.html", "pages/knowledge.html", "pages/wm-overview.html",
                 "pages/wm-queries.html", "pages/wm-gaps.html", "pages/wm-plan.html",
                 "pages/methodology.html")
        home = "index.html"
    else:
        links = ("../index.html", "technical.html", "content.html",
                 "roadmap.html", "competitors.html", "local.html",
                 "geo.html", "knowledge.html", "wm-overview.html",
                 "wm-queries.html", "wm-gaps.html", "wm-plan.html",
                 "methodology.html")
        home = "../index.html"
    new_footer = footer(home, links, num, title, top)
    html2 = re.sub(r"<footer class=\"site-footer\">.*?</footer>", new_footer, html,
                   count=1, flags=re.DOTALL)
    if html2 == html:
        print("WARN no footer replaced: %s" % path)
    html = html2

    html = html.replace(" из 12 •", " из 22 •").replace(" из 12<", " из 22<")

    if html != orig:
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print("updated %s" % path)
    else:
        print("unchanged %s" % path)


# 1. index.html (prefix pages/)
process(os.path.join(SITE, "index.html"), "pages/", "1", "Резюме", "index.html")

# 2. legacy inner pages
for fname, (num, title) in PAGE_META.items():
    if fname == "index.html":
        continue
    process(os.path.join(SITE, "pages", fname), "", num, title, fname)

# 3. fix total: wm pages + methodology say 'из 23', real total is 22
for fname in os.listdir(os.path.join(SITE, "pages")):
    if (fname.startswith("wm-") or fname == "methodology.html") and fname.endswith(".html"):
        p = os.path.join(SITE, "pages", fname)
        with open(p, "r", encoding="utf-8") as f:
            html = f.read()
        if " из 23" in html:
            html = html.replace(" из 23", " из 22")
            with open(p, "w", encoding="utf-8") as f:
                f.write(html)
            print("renumbered %s" % fname)

print("done")
