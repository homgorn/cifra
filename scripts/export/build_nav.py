#!/usr/bin/env python3
"""Единая навигация сайта отчёта: реестр страниц, шапка, подшапка, футер, карта
отчёта на главной.

Зачем один скрипт: 27 страниц держать вручную нельзя, расхождения ломают и
проверки, и читателя. Здесь реестр страниц — единственный источник правды, из
него собираются:
- верхнее меню: плоское, без выпадающих списков, 6 разделов;
- подшапка: страницы текущего раздела, все видны сразу, без наведения;
- футер: все 27 страниц, разложены по колонкам с номерами;
- карта отчёта на главной: навигатор по всем страницам.

Скрипт идемпотентен: можно запускать много раз.

Запуск из корня проекта:
  python scripts/export/build_nav.py
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SITE = os.path.join(ROOT, "reports", "cifra18-audit")
PAGES_DIR = os.path.join(SITE, "pages")

# (номер, файл, название раздела, короткое описание для карты отчёта)
# Разделы верхнего меню: Резюме, Вебмастер, Дашборды, Анализ, План, Методика.
REGISTRY = [
    (1, "index.html", "Резюме", "Что чинить первым, главные цифры и живые данные из кабинетов"),
    (2, "pages/technical.html", "Анализ", "Техническое состояние: индексация, дубли, ошибки, скорость"),
    (3, "pages/content.html", "Анализ", "Контент по страницам: заголовки, описания, объём, пробелы"),
    (4, "pages/competitors.html", "Анализ", "17 конкурентов из Ижевска: ниши, цены, стратегии, дыры"),
    (5, "pages/local.html", "Анализ", "Регионы: где ищут типографию и как распределить спрос"),
    (6, "pages/geo.html", "Анализ", "Видимость в AI-поиске и ответы, которые читает машина"),
    (7, "pages/knowledge.html", "Анализ", "База знаний: термины, сущности, связи, готовые блоки"),
    (8, "pages/roadmap.html", "План", "План на 90 дней по неделям, быстрые победы, доступы"),
    (9, "pages/prices.html", "Анализ", "Цены рынка и сравнения: 50 точек по услугам"),
    (10, "pages/season.html", "Анализ", "Сезонный календарь спроса: когда готовить контент"),
    (11, "pages/marketing.html", "План", "Маркетинг-план и KPI продвижения"),
    (12, "pages/methodology.html", "Методика", "Откуда взяты все цифры и как они считались"),
    (13, "pages/wm-overview.html", "Вебмастер", "Сводка: 708 страниц в поиске, SQI 220, 22 графика"),
    (14, "pages/wm-indexing.html", "Вебмастер", "Индексация по разделам: где в поиске, где нет"),
    (15, "pages/wm-duplicates.html", "Вебмастер", "128 дублей: шаблоны, параметры, легаси"),
    (16, "pages/wm-errors.html", "Вебмастер", "Ошибки разбора и качество: 251 страница с PARSE_ERROR"),
    (17, "pages/wm-redirects.html", "Вебмастер", "Редиректы: куда уходят 89 страниц"),
    (18, "pages/wm-queries.html", "Вебмастер", "492 запроса: позиции, ТОП-1, ТОП-3, ТОП-10"),
    (19, "pages/wm-clusters.html", "Вебмастер", "13 групп запросов и покрытие страницами"),
    (20, "pages/wm-gaps.html", "Вебмастер", "Топ-10 пробелов контента с приоритетом"),
    (21, "pages/wm-links.html", "Вебмастер", "Внутренние ссылки: 62 битых из 134"),
    (22, "pages/wm-plan.html", "План", "Спринты по Вебмастеру и критерии приёмки"),
    (23, "pages/dash-visibility.html", "Дашборды", "SQI по годам, индексация по разделам, важные URL"),
    (24, "pages/dash-audience.html", "Дашборды", "Визиты, устройства, города, пол, возраст, источники"),
    (25, "pages/dash-money.html", "Дашборды", "Заказы, выручка, цели, страницы входа"),
    (26, "pages/dash-maps.html", "Дашборды", "Карточка в Яндекс Картах: просмотры, звонки, маршруты"),
    (27, "pages/plan-3m.html", "План", "План работ на 3 месяца: расчистка, семантика, деньги"),
]

# Верхнее меню: раздел -> страница, на которую он ведёт
SECTIONS = [
    ("Резюме", "index.html", "Отчёт"),
    ("Вебмастер", "pages/wm-overview.html", "Вебмастер"),
    ("Дашборды", "pages/dash-visibility.html", "Дашборды"),
    ("Анализ", "pages/competitors.html", "Анализ"),
    ("План", "pages/plan-3m.html", "План"),
    ("Методика", "pages/methodology.html", "Методика"),
]
# Разделы, чьи страницы показываются в подшапке. У «Резюме» и «Методика» их нет.
SUBBAR_SECTIONS = {"Вебмастер", "Дашборды", "Анализ", "План"}

FOOTER_COLS = [
    ("Отчёт", ["index.html", "pages/roadmap.html", "pages/plan-3m.html",
               "pages/marketing.html"]),
    ("Анализ", ["pages/technical.html", "pages/content.html", "pages/competitors.html",
                "pages/local.html", "pages/geo.html", "pages/knowledge.html",
                "pages/prices.html", "pages/season.html"]),
    ("Вебмастер", ["pages/wm-overview.html", "pages/wm-indexing.html",
                   "pages/wm-duplicates.html", "pages/wm-errors.html",
                   "pages/wm-redirects.html", "pages/wm-queries.html",
                   "pages/wm-clusters.html", "pages/wm-gaps.html",
                   "pages/wm-links.html", "pages/wm-plan.html"]),
    ("Дашборды", ["pages/dash-visibility.html", "pages/dash-audience.html",
                  "pages/dash-money.html", "pages/dash-maps.html"]),
    ("Методика", ["pages/methodology.html"]),
]

TOTAL = len(REGISTRY)
BY_SLUG = {slug: (num, section, desc) for num, slug, section, desc in REGISTRY}
TITLE_BY_SLUG = {}
for _num, _slug, _section, _desc in REGISTRY:
    TITLE_BY_SLUG[_slug] = _desc.split(":")[0].split(" с ")[0][:28]


def h1_by_slug(slug):
    """Название раздела для меню берём из h1 страницы, если он есть."""
    return None


def rel(from_slug, to_slug):
    """Правильный относительный путь: из pages/ в pages/ без лишнего ../pages/."""
    from_dir = os.path.dirname(from_slug)
    p = os.path.relpath(to_slug.replace("/", os.sep), from_dir if from_dir else ".")
    return p.replace(os.sep, "/")


def section_of(slug):
    return BY_SLUG[slug][1]


def nav_html(cur):
    """Верхнее меню: плоское, без выпадающих списков."""
    out = []
    for label, target, group in SECTIONS:
        active = ' active' if section_of(cur) == group else ""
        cur_is_target = " active" if cur == target else ""
        out.append('      <a class="nav-link%s%s" href="%s"%s>%s</a>'
                   % (cur_is_target, active, rel(cur, target),
                      ' aria-current="page"' if cur == target else "", label))
    out.append('      <a class="nav-link nav-link-all" href="%s#toc">Все страницы</a>'
               % rel(cur, "index.html"))
    return "\n".join(out)


def subbar_html(cur):
    """Подшапка: все страницы текущего раздела, сразу видны, без наведения."""
    group = section_of(cur)
    if group not in SUBBAR_SECTIONS:
        return ""
    items = [(n, s) for n, s, g, _d in REGISTRY if g == group and s != "index.html"]
    if len(items) < 2:
        return ""
    links = []
    for n, s in items:
        here = ' aria-current="page"' if s == cur else ""
        links.append('<a class="subnav-link%s" href="%s"%s>%s</a>'
                     % (" active" if s == cur else "", rel(cur, s), here, short(s)))
    return ('  <div class="subnav" id="subnav">\n'
            '    <div class="subnav-inner">\n'
            '      <span class="subnav-title">%s</span>\n'
            '      %s\n'
            '    </div>\n'
            '  </div>\n' % (group, "\n      ".join(links)))


SHORT = {
    "index.html": "Главная",
    "pages/wm-overview.html": "Сводка", "pages/wm-indexing.html": "Индексация",
    "pages/wm-duplicates.html": "Дубли", "pages/wm-errors.html": "Ошибки",
    "pages/wm-redirects.html": "Редиректы", "pages/wm-queries.html": "Запросы",
    "pages/wm-clusters.html": "Кластеры", "pages/wm-gaps.html": "Пробелы",
    "pages/wm-links.html": "Ссылки", "pages/wm-plan.html": "План ВМ",
    "pages/dash-visibility.html": "Видимость", "pages/dash-audience.html": "Аудитория",
    "pages/dash-money.html": "Деньги", "pages/dash-maps.html": "Карта в Картах",
    "pages/technical.html": "Техника", "pages/content.html": "Контент",
    "pages/competitors.html": "Конкуренты", "pages/local.html": "Регионы",
    "pages/geo.html": "GEO", "pages/knowledge.html": "Знания",
    "pages/prices.html": "Цены", "pages/season.html": "Сезон",
    "pages/roadmap.html": "90 дней", "pages/plan-3m.html": "3 месяца",
    "pages/marketing.html": "Маркетинг", "pages/methodology.html": "Методика",
}


def short(slug):
    return SHORT.get(slug, slug.split("/")[-1].replace(".html", ""))


def footer_html(cur):
    num, section, _ = BY_SLUG[cur]
    cols = []
    for head, slugs in FOOTER_COLS:
        items = []
        for s in slugs:
            n, _g, _d = BY_SLUG[s]
            here = ' aria-current="page"' if s == cur else ""
            items.append('<li><a href="%s"%s><span class="fnum">%d</span>%s</a></li>'
                         % (rel(cur, s), here, n, short(s)))
        cols.append('      <div class="footer-nav"><h4>%s</h4><ul>%s</ul></div>'
                    % (head, "".join(items)))
    return ('<footer class="site-footer">\n'
            '  <div class="container container-wide">\n'
            '    <div class="footer-grid">\n'
            '      <div class="footer-brand"><a class="logo" href="%s"><span class="logo-mark">Ц18</span>'
            '<span>Цифра. Аудит</span></a><p>Проверка и план продвижения цифра18.рф. '
            'Техника, контент, конкуренты, регионы, GEO, Вебмастер, дашборды. Сентябрь 2026.</p>'
            '<a class="footer-toc" href="%s#toc">Карта отчёта, все %d страниц</a></div>\n'
            '%s\n'
            '    </div>\n'
            '    <div class="footer-bottom"><span>Цифра18, Ижевск, сентябрь 2026</span>'
            '<span>Страница %d из %d, раздел %s</span></div>\n'
            '  </div>\n'
            '</footer>' % (rel(cur, "index.html"), rel(cur, "index.html"), TOTAL,
                           "\n".join(cols), num, TOTAL, section))


def toc_html():
    """Карта отчёта на главной: все страницы группами, с номерами и описаниями."""
    groups = []
    for head, _target, group in SECTIONS:
        items = [(n, s, d) for n, s, g, d in REGISTRY if g == group]
        if group == "Резюме":
            items = [(1, "index.html", "Главная: сводка, живые цифры и навигация по отчёту")]
        cards = []
        for n, s, d in items:
            if s == "index.html":
                continue
            cards.append('        <a class="toc-card" href="%s">\n'
                         '          <span class="toc-num">%d</span>\n'
                         '          <span class="toc-body">\n'
                         '            <span class="toc-title">%s</span>\n'
                         '            <span class="toc-desc">%s</span>\n'
                         '          </span>\n'
                         '        </a>' % (s, n, short(s), d))
        if cards:
            groups.append('      <div class="toc-group">\n'
                          '        <h3 class="toc-group-title">%s</h3>\n'
                          '        <div class="toc-grid">\n%s\n        </div>\n'
                          '      </div>' % (head, "\n".join(cards)))
    return ('  <section id="toc" data-section style="margin-top:3rem;">\n'
            '    <div class="page-title-block">\n'
            '      <h2>Карта отчёта</h2>\n'
            '      <p>Все %d страниц, сгруппированные по разделам. Каждая карточка ведёт на страницу, '
            'номер совпадает с нумерацией в подвале.</p>\n'
            '    </div>\n%s\n'
            '  </section>\n' % (TOTAL, "\n".join(groups)))


def patch(slug):
    path = os.path.join(SITE, slug.replace("/", os.sep))
    with open(path, encoding="utf-8") as f:
        html = f.read()
    orig = html
    is_index = slug == "index.html"

    # 1. верхнее меню
    new_nav = nav_html(slug)
    html = re.sub(r'(<nav class="main-nav" id="mainNav">).*?(\n    </nav>)',
                  lambda m: m.group(1) + "\n" + new_nav + m.group(2), html,
                  count=1, flags=re.DOTALL)

    # 2. подшапка сразу после header. Сначала убираем прежнюю, иначе
    # повторный запуск скрипта наслаивает копии.
    html = re.sub(r'\n?  <div class="subnav" id="subnav">.*?</div>\n  </div>\n', "\n", html,
                  flags=re.DOTALL)
    sub = subbar_html(slug)
    if sub:
        html = re.sub(r"(</header>)", lambda m: m.group(1) + "\n" + sub.rstrip("\n"), html, count=1)

    # 3. футер
    html = re.sub(r'<footer class="site-footer">.*?</footer>',
                  lambda m: footer_html(slug), html, count=1, flags=re.DOTALL)

    # 4. карта отчёта на главной
    if is_index and 'id="toc"' not in html:
        toc = toc_html()
        if "</main>" in html:
            html = html.replace("</main>", toc + "</main>", 1)
        else:
            print("  ВНИМАНИЕ: на главной нет </main>, карта отчёта не вставлена")

    # 5. подключить стили и скрипт навигации
    if 'css/nav.css' not in html:
        pre = "" if is_index else "../"
        html = html.replace('<link rel="stylesheet" href="%scss/report.css">' % pre,
                            '<link rel="stylesheet" href="%scss/report.css">\n'
                            '<link rel="stylesheet" href="%scss/nav.css">' % (pre, pre), 1)
    if 'js/search.js' not in html:
        pre = "" if is_index else "../"
        html = html.replace('<script src="%sjs/nav.js"></script>' % pre,
                            '<script src="%sjs/nav.js"></script>\n'
                            '<script src="%sjs/search.js"></script>' % (pre, pre), 1)

    if html != orig:
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        return True
    return False


def strip_old_chrome():
    """Убрать старые выпадающие списки и кнопку мобильного меню из разметки."""
    changed = 0
    for _n, slug, _s, _d in REGISTRY:
        path = os.path.join(SITE, slug.replace("/", os.sep))
        with open(path, encoding="utf-8") as f:
            html = f.read()
        if "nav-dropdown" in html or 'id="menuBtn"' in html:
            html = html.replace('    <button class="mobile-menu-btn" id="menuBtn" aria-label="Меню">Меню</button>\n', "")
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            changed += 1
    return changed


def page_index_js():
    """Индекс страниц для поиска по всему отчёту."""
    items = []
    for n, slug, section, desc in REGISTRY:
        items.append({"n": n, "p": slug, "s": section, "t": short(slug), "d": desc})
    body = "const PAGES = %s;\n" % __import__("json").dumps(items, ensure_ascii=False)
    out = os.path.join(SITE, "js", "page-index.js")
    with open(out, "w", encoding="utf-8") as f:
        f.write("/* Generated by scripts/export/build_nav.py. Do not edit by hand. */\n")
        f.write(body)
    return out


def main():
    stripped = strip_old_chrome()
    n = 0
    for _num, slug, _s, _d in REGISTRY:
        if patch(slug):
            n += 1
    idx = page_index_js()
    for _num, slug, _s, _d in REGISTRY:
        patch_assets(slug)
    print("страниц: %d, обновлено: %d, очищено от старого меню: %d"
          % (TOTAL, n, stripped))
    print("индекс поиска: %s" % os.path.relpath(idx, ROOT))
    return 0


def patch_assets(slug):
    """Отдельный проход: подключение page-index.js идёт после nav.js,
    поэтому проверяем после всех правок разметки."""
    path = os.path.join(SITE, slug.replace("/", os.sep))
    with open(path, encoding="utf-8") as f:
        html = f.read()
    if "js/page-index.js" in html:
        return
    pre = "" if slug == "index.html" else "../"
    html = html.replace('<script src="%sjs/nav.js"></script>' % pre,
                        '<script src="%sjs/page-index.js"></script>\n'
                        '<script src="%sjs/nav.js"></script>' % (pre, pre), 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    sys.exit(main())
