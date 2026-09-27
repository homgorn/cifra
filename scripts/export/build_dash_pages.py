#!/usr/bin/env python3
"""Генератор страниц дашбордов отчёта и обновление навигации по всему сайту.

Зачем: руками держать 26 страниц одинаковыми нельзя, расхождения сразу ломают
проверки. Скрипт создаёт 4 страницы дашбордов (вместо внешнего BI) и
одновременно добавляет пункт «Дашборды» в меню, добавляет колонку в футер и
пересчитывает нумерацию «из 22» -> «из 26» на всех страницах.

Данные для графиков приходят из js/dash-data.js (build_dashboard_data.py),
в HTML только разметка и id canvas.

Запуск из корня проекта:
  python scripts/export/build_dash_pages.py
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SITE = os.path.join(ROOT, "reports", "cifra18-audit")
PAGES = os.path.join(SITE, "pages")
TOTAL = 26

DASH_LINKS = [
    ("dash-visibility.html", "Видимость", "SQI 220"),
    ("dash-audience.html", "Аудитория", "21 110 визитов"),
    ("dash-money.html", "Деньги", "e-commerce"),
    ("dash-maps.html", "Карта в Яндекс Картах", "409 звонков"),
]


def dash_dropdown(prefix, active=""):
    links = "\n".join(
        '          <a href="%s%s"%s>%s <span class="drop-hint">%s</span></a>'
        % (prefix, f, ' class="active"' if active == f else "", t, h)
        for f, t, h in DASH_LINKS)
    return (
        '      <div class="nav-dropdown">\n'
        '        <button class="nav-link nav-drop-btn%s" aria-haspopup="true">Дашборды <span class="drop-arrow">▾</span></button>\n'
        '        <div class="nav-drop-menu">\n'
        '%s\n'
        '        </div>\n'
        '      </div>\n' % (' active' if active else '', links))


def page(fname, num, title, h1, desc, kicker, intro, sidebar, body, prev, nxt):
    prefix = "../" if fname else ""
    home = "../index.html" if fname else "index.html"
    head_links = "".join(
        '      <a class="nav-link" href="%s%s"><span class="nav-indicator"></span>%s</a>' % (prefix, f, t)
        for f, t in [("technical.html", "Техника"), ("content.html", "Контент"),
                     ("competitors.html", "Конкуренты"), ("local.html", "Регионы"),
                     ("geo.html", "GEO"), ("knowledge.html", "База знаний"),
                     ("roadmap.html", "План")])
    wm_links = "\n".join(
        '          <a href="%swm-%s.html">%s <span class="drop-hint">%s</span></a>' % (prefix, k, t, h)
        for k, t, h in [("overview", "Сводка Вебмастера", "717 URL"),
                        ("indexing", "Индексация по разделам", "6%"),
                        ("queries", "Запросы и позиции", "535"),
                        ("gaps", "Пробелы контента", "топ-10"),
                        ("plan", "План по Вебмастера", "ICE")])
    wm_menu = (
        '      <div class="nav-dropdown">\n'
        '        <button class="nav-link nav-drop-btn" aria-haspopup="true">Вебмастер <span class="drop-arrow">▾</span></button>\n'
        '        <div class="nav-drop-menu">\n%s\n        </div>\n      </div>\n' % wm_links)
    side = "\n".join(
        '    <a class="sidebar-link%s" href="#%s"><span class="link-number">%d</span>%s</a>'
        % (' active' if i == 0 else "", a, i + 1, t) for i, (a, t) in enumerate(sidebar))
    footer = footer_html(home, prefix, num, title)
    prev_html = ''
    if prev:
        prev_html = ('<div class="pager"><a href="%s%s.html"><span class="pager-label">Назад</span>'
                     '<span class="pager-title">%s</span></a>' % (prefix, prev[0], prev[1]))
        if nxt:
            prev_html += ('<a href="%s%s.html" style="text-align:right;"><span class="pager-label">Дальше</span>'
                          '<span class="pager-title">%s</span></a>' % (prefix, nxt[0], nxt[1]))
        prev_html += '</div>'
    p = []
    a = p.append
    a('<!DOCTYPE html>\n<html lang="ru">\n<head>\n<meta charset="UTF-8">')
    a('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    a('<title>%s. Цифра18</title>' % title)
    a('<meta name="description" content="%s">' % desc)
    a('<link rel="preconnect" href="https://fonts.googleapis.com">')
    a('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>')
    a('<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">')
    a('<link rel="stylesheet" href="%scss/main.css">' % prefix)
    a('<link rel="stylesheet" href="%scss/report.css">' % prefix)
    a('</head>\n<body>')
    a('<header class="site-header">\n  <div class="header-inner">')
    a('<a class="logo" href="%s"><span class="logo-mark">Ц18</span><span>Цифра. Аудит</span></a>' % home)
    a('<nav class="main-nav" id="mainNav">')
    a('      <a class="nav-link" href="%s"><span class="nav-indicator"></span>Резюме</a>' % home)
    a(head_links)
    a(wm_menu)
    a(dash_dropdown(prefix, fname))
    a('      <div class="nav-dropdown">')
    a('        <button class="nav-link nav-drop-btn" aria-haspopup="true">Еще <span class="drop-arrow">▾</span></button>')
    a('        <div class="nav-drop-menu">')
    for slug, t in [("prices", "Цены и сравнения"), ("season", "Сезонный календарь"),
                    ("marketing", "Маркетинг план"), ("methodology", "Методика")]:
        a('          <a href="%s%s.html">%s</a>' % (prefix, slug, t))
    a('        </div>\n      </div>\n    </nav>')
    a('    <button class="mobile-menu-btn" id="menuBtn" aria-label="Меню">Меню</button>')
    a('  </div>\n</header>')
    a('<main class="page">\n<div class="container container-wide">\n<div class="report-layout">')
    a('<aside class="sidebar">\n  <div class="sidebar-title">На этой странице</div>')
    a('  <nav class="sidebar-nav">\n%s\n  </nav>\n</aside>' % side)
    a('<div>')
    a('  <div class="page-title-block animate-slide-up">')
    a('    <div class="page-kicker">Страница %d из %d • %s</div>' % (num, TOTAL, kicker))
    a('    <h1>%s</h1>' % h1)
    a('    <p>%s</p>' % intro)
    a('  </div>\n')
    a(body)
    a('</div>\n</div>\n</div>\n</main>\n')
    if prev_html:
        a(prev_html)
    a(footer)
    a('<script src="%sjs/vendor/chart.umd.min.js"></script>' % prefix)
    a('<script>if(typeof Chart==="undefined"){document.write("<script src=\'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js\'><\\/script>")}</script>')
    for js in ("wm-data", "site-data", "dash-data", "main"):
        a('<script src="%sjs/%s.js"></script>' % (prefix, js))
    a('</body>\n</html>\n')
    return "\n".join(p) + "\n"


FOOTER_COLS = [
    ("Отчет", [("index", "Резюме"), ("technical", "Техника"), ("content", "Контент"),
               ("roadmap", "План")]),
    ("Анализ", [("competitors", "Конкуренты"), ("local", "Регионы"), ("geo", "GEO"),
                ("knowledge", "База знаний")]),
    ("Вебмастер", [("wm-overview", "Сводка"), ("wm-queries", "Запросы"),
                   ("wm-gaps", "Пробелы"), ("wm-plan", "План")]),
    ("Дашборды", [("dash-visibility", "Видимость"), ("dash-audience", "Аудитория"),
                  ("dash-money", "Деньги"), ("dash-maps", "Карта в Картах")]),
    ("Файлы", [("methodology", "Методика"), ("season", "Сроки"), ("roadmap", "Наверх")]),
]


def footer_html(home, prefix, num, title):
    cols = []
    for head, links in FOOTER_COLS:
        items = []
        for slug, t in links:
            href = home if slug == "index" else "%s%s.html" % (prefix, slug)
            items.append('<li><a href="%s">%s</a></li>' % (href, t))
        cols.append('      <div class="footer-nav"><h4>%s</h4><ul>%s</ul></div>' % (head, "".join(items)))
    return (
        '<footer class="site-footer">\n'
        '  <div class="container container-wide">\n'
        '    <div class="footer-grid">\n'
        '      <div class="footer-brand"><a class="logo" href="%s"><span class="logo-mark">Ц18</span>'
        '<span>Цифра. Аудит</span></a><p>Отчет по продвижению цифра18.рф. Техника, контент, '
        'конкуренты, регионы, GEO, Вебмастер, дашборды. Сентябрь 2026.</p></div>\n'
        '%s\n'
        '    </div>\n'
        '    <div class="footer-bottom"><span>Цифра18 • Ижевск • сентябрь 2026</span>'
        '<span>Страница %d из %d • %s</span></div>\n'
        '  </div>\n'
        '</footer>' % (home, "\n".join(cols), int(num), TOTAL, title))


def card(title, sub, canvas, height="300px"):
    return (
        '  <div class="card">\n'
        '    <div class="card-header"><div><div class="card-title">%s</div><div class="card-subtitle">%s</div></div></div>\n'
        '    <div class="card-body"><div class="chart-container" style="height:%s"><canvas id="%s"></canvas></div></div>\n'
        '  </div>\n' % (title, sub, height, canvas))


def table(headers, tbody_id, cols):
    th = "".join("<th>%s</th>" % h for h in headers)
    return (
        '  <div class="table-wrapper"><table>\n'
        '    <thead><tr>%s</tr></thead>\n'
        '    <tbody id="%s"><tr><td colspan="%d" class="text-muted">Загрузка данных...</td></tr></tbody>\n'
        '  </table></div>\n' % (th, tbody_id, cols))


def kpi(items):
    out = ['  <div class="grid grid-4 metric-grid">\n']
    for i, (val_id, label, delta) in enumerate(items):
        out.append(
            '    <div class="card metric-card animate-slide-up%s">\n'
            '      <div class="metric-value"><span id="%s">-</span></div>\n'
            '      <div class="metric-label">%s</div>\n'
            '      <div class="metric-delta neutral">%s</div>\n'
            '    </div>\n' % (' delay-%d' % (i % 4) if i % 4 else '', val_id, label, delta))
    out.append('  </div>\n')
    return "".join(out)


def build():
    pages = {}

    # 23. Видимость
    body = ("  <section id=\"sqi\" data-section>\n    <h2>Индекс качества сайта</h2>\n"
            + kpi([("kpiSqi", "SQI сейчас", "старт был 10"),
                   ("kpiSqiGrowth", "Прирост SQI", "с 2018 года"),
                   ("kpiSearchable", "Страниц в поиске", "API Вебмастера"),
                   ("kpiRecrawl", "Квота переобхода", "страниц в сутки")])
            + card("История SQI по месяцам", "API Вебмастера, первый замер 2018 года", "dashSqiLine", "320px")
            + "  </section>\n\n"
            "  <section id=\"sections\" data-section style=\"margin-top:2.5rem;\">\n    <h2>Индексация по разделам</h2>\n"
            + card("Проиндексировано и в поиске по разделам", "Выгрузка панели Вебмастера, 20 разделов", "dashSectionBar", "360px")
            + table(["Раздел", "Проиндексировано", "В поиске", "Доля"], "dashSectionBody", 4)
            + "  </section>\n\n"
            "  <section id=\"money-urls\" data-section style=\"margin-top:2.5rem;\">\n    <h2>Денежные страницы под наблюдением</h2>\n"
            + card("Коды ответа на важных URL", "48 адресов, отслеживаемых в Вебмастере", "dashHttpBar", "300px")
            + table(["URL", "Код", "Статус", "Последний обход", "Изменения"], "dashImportantBody", 5)
            + "  </section>\n\n"
            "  <section id=\"events\" data-section style=\"margin-top:2.5rem;\">\n    <h2>События индексации</h2>\n"
            + table(["Дата", "Событие", "URL"], "dashEventBody", 3)
            + "    <div class=\"callout\"><div class=\"callout-title\">Что делать сразу</div><p>Квота переобхода в сутки позволяет руками отправлять страницы на индексацию. Сначала 48 важных URL, затем разделы с нулевой долей в поиске: shop, product, docs, pdf, account.</p></div>\n"
            + "  </section>\n")
    pages["dash-visibility.html"] = page(
        "dash-visibility.html", 23, "Видимость",
        "Видимость: SQI, индексация, важные страницы",
        "Дашборд видимости сайта цифра18.рф: история SQI по месяцам, индексация по разделам, 48 важных URL, события индексации, квота переобхода.",
        "Дашборды",
        "Панель в одном экране: как индекс качества сайта менялся с 2018 года, какие разделы реально попадают в поиск, что происходит с отслеживаемыми денежными страницами и сколько страниц можно отправить на переобход за сутки.",
        [("sqi", "Индекс качества"), ("sections", "Индексация по разделам"),
         ("money-urls", "Важные страницы"), ("events", "События индексации")],
        body, ("wm-plan", "План по Вебмастера"), ("dash-audience", "Аудитория"))

    # 24. Аудитория
    body = ("  <section id=\"base\" data-section>\n    <h2>Объём и качество трафика сайта</h2>\n"
            + kpi([("kpiVisits", "Визитов за 3,7 года", "счётчик сайта"),
                   ("kpiUsers", "Посетителей", "уникальных"),
                   ("kpiBounce", "Отказы, сайта", "по сайту, не по Картам"),
                   ("kpiBots", "Доля роботов", "из API Метрики")])
            + "    <div class=\"callout\"><div class=\"callout-title\">Уточнение по счётчикам</div><p>В Метрике два разных счётчика: сайт цифра18.рф и карточка в Яндекс Картах. Ранний разбор был построен на карточке, поэтому цифры сайта и карточки смешивались. Здесь только сайт; карточка вынесена на отдельную страницу.</p></div>\n"
            + "  </section>\n\n"
            "  <section id=\"monthly\" data-section style=\"margin-top:2.5rem;\">\n    <h2>Динамика по месяцам</h2>\n"
            + card("Визиты и посетители сайта по месяцам", "счётчик сайта, вся жизнь счётчика", "dashSiteLine", "320px")
            + card("Отказы по месяцам, процент", "взвешенно по визитам", "dashBounceLine", "260px")
            + "  </section>\n\n"
            "  <section id=\"devices\" data-section style=\"margin-top:2.5rem;\">\n    <h2>Устройства и браузеры</h2>\n"
            + '  <div class="grid grid-2">\n'
            + card("Тип устройства", "все визиты сайта", "dashDevicesDonut")
            + card("Браузеры, топ-8", "по визитам", "dashBrowsersBar")
            + "  </div>\n"
            + "  </section>\n\n"
            "  <section id=\"geo\" data-section style=\"margin-top:2.5rem;\">\n    <h2>География</h2>\n"
            + card("Города, топ-12", "по визитам", "dashCitiesBar", "360px")
            + '  <div class="grid grid-2" style="margin-top:1.5rem;">\n'
            + card("Пол", "доля визитов", "dashGenderDonut")
            + card("Возраст", "группы Метрики", "dashAgeBar")
            + "  </div>\n"
            + card("Интересы аудитории, топ-10", "группы Метрики по интересам", "dashInterestBar", "300px")
            + "  </section>\n\n"
            "  <section id=\"sources\" data-section style=\"margin-top:2.5rem;\">\n    <h2>Источники и переходы</h2>\n"
            + card("Визиты по источникам по месяцам", "поиск, внутренние, прямые и другие", "dashSourceLine", "340px")
            + card("Внешние переходы, топ-20", "откуда приходят на сайт", "dashRefsBar", "420px")
            + "  </section>\n")
    pages["dash-audience.html"] = page(
        "dash-audience.html", 24, "Аудитория",
        "Аудитория сайта: устройства, города, источники",
        "Дашборд аудитории цифра18.рф: визиты и отказы по месяцам, устройства, браузеры, города, пол и возраст, интересы, источники трафика, внешние переходы.",
        "Дашборды",
        "Кто приходит на сайт, с чего и откуда. Все цифры счётчика сайта: динамика с 2023 года, устройства, браузеры, города, пол, возраст, интересы, источники и внешние переходы.",
        [("base", "Объём и качество"), ("monthly", "Динамика по месяцам"),
         ("devices", "Устройства"), ("geo", "География и портрет"), ("sources", "Источники")],
        body, ("dash-visibility", "Видимость"), ("dash-money", "Деньги"))

    # 25. Деньги
    body = ("  <section id=\"ecom\" data-section>\n    <h2>E-commerce и цели</h2>\n"
            + kpi([("kpiRevenue", "Выручка за год", "из dataLayer"),
                   ("kpiPurchases", "Покупок за год", "из dataLayer"),
                   ("kpiGoals", "Активных целей", "звонок, форма, заказ"),
                   ("kpiAvg", "Средний чек", "выручка на заказ")])
            + card("Выручка и заказы по месяцам", "только месяцы с заказами", "dashRevLine", "300px")
            + "  </section>\n\n"
            "  <section id=\"days\" data-section style=\"margin-top:2.5rem;\">\n    <h2>Дни с выручкой</h2>\n"
            + card("Топ дней по выручке", "рубли, e-commerce Метрики", "dashRevDayBar", "300px")
            + table(["Цель", "Тип", "Статус"], "dashGoalBody", 3)
            + "  </section>\n\n"
            "  <section id=\"entry\" data-section style=\"margin-top:2.5rem;\">\n    <h2>Страницы входа и поисковые запросы</h2>\n"
            + card("Страницы входа, топ-15", "по визитам", "dashLandingBar", "380px")
            + card("Поисковые запросы сайта, топ-20", "по визитам из Метрики", "dashPhraseBar", "380px")
            + "  </section>\n")
    pages["dash-money.html"] = page(
        "dash-money.html", 25, "Деньги",
        "Деньги: заказы, выручка, цели",
        "Дашборд денег цифра18.рф: выручка и заказы e-commerce по месяцам и дням, 12 активных целей, страницы входа и поисковые запросы сайта.",
        "Дашборды",
        "Что сайт приносит прямо сейчас: заказы и выручка по слою данных сайта, какие цели настроены и работают, через какие страницы и запросы люди попадают на сайт.",
        [("ecom", "E-commerce и цели"), ("days", "Дни с выручкой"),
         ("entry", "Страницы входа")],
        body, ("dash-audience", "Аудитория"), ("dash-maps", "Карта в Яндекс Картах"))

    # 26. Карта в Яндекс Картах
    body = ("  <section id=\"maps\" data-section>\n    <h2>Карточка в Яндекс Картах</h2>\n"
            + kpi([("kpiMapViews", "Просмотров карточки", "счётчик карточки"),
                   ("kpiMapCalls", "Кликов позвонить", "из карточки"),
                   ("kpiMapRoutes", "Построено маршрутов", "из карточки"),
                   ("kpiMapSite", "Переходов на сайт", "из карточки")])
            + card("Просмотры карточки по месяцам", "счётчик карточки в Яндекс Картах", "dashMapsLine", "320px")
            + "  </section>\n\n"
            "  <section id=\"actions\" data-section style=\"margin-top:2.5rem;\">\n    <h2>Действия в карточке</h2>\n"
            + card("Звонки, маршруты, переходы", "события целей карточки", "dashMapsActionBar", "300px")
            + card("Откуда смотрят карточку, топ-12", "страницы входа счётчика карточки", "dashMapsEntryBar", "380px")
            + "  </section>\n\n"
            "  <section id=\"maps-search\" data-section style=\"margin-top:2.5rem;\">\n    <h2>Поиск и источники карточки</h2>\n"
            + card("Поисковые запросы карточки, топ-12", "как ищут типографию в Картах", "dashMapsSearchBar", "340px")
            + card("Источники переходов в карточку", "по просмотрам", "dashMapsSourceDonut", "300px")
            + "    <div class=\"callout\"><div class=\"callout-title\">Почему это важно</div><p>Карточка в Картах даёт больше просмотров, чем сайт, и из неё идут звонки. Раньше эти данные попадали в отчёт как «визиты сайта», из-за чего картина трафика была неверной: 70% отказов в отчёте belonged карточке, а не сайту.</p></div>\n"
            + "  </section>\n")
    pages["dash-maps.html"] = page(
        "dash-maps.html", 26, "Карта в Картах",
        "Карточка в Яндекс Картах: просмотры, звонки, маршруты",
        "Дашборд карточки типографии в Яндекс Картах: просмотры по месяцам, клики позвонить, построенные маршруты, переходы на сайт, источники и поисковые запросы карточки.",
        "Дашборды",
        "Карточка в Яндекс Картах работает как отдельный канал: показывает больше просмотров, чем сайт, и даёт звонки. Здесь её собственные цифры, ранее смешанные с трафиком сайта.",
        [("maps", "Просмотры карточки"), ("actions", "Действия в карточке"),
         ("maps-search", "Поиск и источники")],
        body, ("dash-money", "Деньги"), None)

    for fname, html in pages.items():
        with open(os.path.join(PAGES, fname), "w", encoding="utf-8") as f:
            f.write(html)
        print("created %s" % fname)
    return pages


def patch_existing(skip):
    """Добавляет меню дашбордов, новую колонку футера и нумерацию 26 на всех страницах."""
    files = [os.path.join(SITE, "index.html")]
    files += [os.path.join(PAGES, n) for n in sorted(os.listdir(PAGES)) if n.endswith(".html")]
    changed = 0
    for path in files:
        name = os.path.basename(path)
        if name in skip:
            continue
        with open(path, encoding="utf-8") as f:
            html = f.read()
        orig = html
        prefix = "" if name == "index.html" else ""
        nav_head = html.split("</nav>")[0]
        if "dash-visibility.html" not in nav_head:
            m = re.search(r'(      <div class="nav-dropdown">\n'
                          r'        <button class="nav-link nav-drop-btn(?: active)?" aria-haspopup="true">Еще)',
                          html)
            if m:
                html = html[:m.start(1)] + dash_dropdown("") + m.group(1) + html[m.end(1):]
            else:
                print("  WARN no nav anchor: %s" % name)
        mf = re.search(r'<div class="footer-bottom">.*?Страница (\d+) из 22 • ([^<]+)</span>', html, re.DOTALL)
        if mf:
            num, title = mf.group(1), mf.group(2)
            home = "index.html" if name == "index.html" else "../index.html"
            pre = "" if name == "index.html" else ""
            html = re.sub(r"<footer class=\"site-footer\">.*?</footer>",
                          lambda mm: footer_html(home, pre, num, title), html,
                          count=1, flags=re.DOTALL)
        html = html.replace(" из 22", " из %d" % TOTAL)
        if html != orig:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            changed += 1
            print("patched %s" % name)
    print("patched total: %d" % changed)


if __name__ == "__main__":
    made = build()
    patch_existing(set(made))
    print("done")
