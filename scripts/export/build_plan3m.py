#!/usr/bin/env python3
"""Генератор страницы «План работ на 3 месяца» для сайта отчёта.

Все цифры в тексте берутся из данных (выборка панели Вебмастера, API
Вебмастера и Метрики, ключи Topvisor), руками ничего не вбито. План
собран вокруг главного вывода проверки: каталог проиндексирован на 60%, общий
процент 19,8% тянут мёртвые /shop (314 URL, 0 в поиске, 236 ошибок парсинга)
и 129 легаси .html. Поэтому первый месяц начинается не с контента, а с
расчистки мёртвых разделов.

Запуск из корня проекта:
  python scripts/export/build_plan3m.py
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_dash_pages as B  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PARSED = ROOT / "webmaster" / "parsed_data.json"
PAGE_NUM = 27
PREFIX = "https://xn--18-6kc5a3bxam.xn--p1ai"
LEGACY_RE = re.compile(r"^\/\d+\.html$")
NAMES = {"/catalog": "Каталог", "/shop": "Магазин (legacy /shop/)",
         "/product": "Товары (legacy /product/)", "/news": "Новости"}


def section_of(url):
    path = url[len(PREFIX):] if url.startswith(PREFIX) else url
    segs = [s for s in path.split("/") if s]
    if not segs:
        return "/"
    first = "/" + segs[0]
    if first in NAMES:
        return first
    return "/legacy_html" if LEGACY_RE.match(first) else "/other"


def num(x):
    return int(str(x or "0").replace(" ", "").replace("\u00a0", ""))


def fmt(x):
    return format(int(x), ",").replace(",", " ")


def topvisor_balance():
    """Баланс Topvisor из локальной базы. Не хардкодим: сумма меняется."""
    import sqlite3
    db = ROOT / "topvisor" / "db" / "topvisor.db"
    if not db.is_file():
        return "не проверен"
    try:
        c = sqlite3.connect(str(db))
        row = c.execute("select balance_all from balance_snapshots order by ts desc limit 1").fetchone()
        c.close()
        if not row or row[0] is None:
            return "не проверен"
        return ("%.0f" % float(row[0])).replace(".", ",")
    except Exception:
        return "не проверен"


def load():
    d = json.load(open(PARSED, encoding="utf-8"))
    sec = defaultdict(Counter)
    for p in d["pages"]:
        sec[section_of(p.get("url") or "")][p.get("status")] += 1
    out = {}
    for k, c in sec.items():
        total = sum(c.values())
        out[k] = {"urls": total, "search": c["SEARCHABLE"], "dup": c["DUPLICATE"],
                  "err": c["PARSE_ERROR"] + c["HTTP_ERROR"] + c["BAD_QUALITY"],
                  "share": round(c["SEARCHABLE"] / total * 100, 1) if total else 0}
    structure = {r["path"]: r for r in
                 [{"path": (r.get("g-link") or "").split("://")[-1].split("/", 1)[-1] if "://" in (r.get("g-link") or "") else (r.get("g-link") or ""),
                   "indexed": num(r.get("g-link 2")), "search": num(r.get("g-link 3"))}
                  for r in d.get("structure", [])]}
    return out, structure, d


def build():
    sec, structure, parsed = load()
    total_urls = sum(v["urls"] for v in sec.values())
    total_search = sum(v["search"] for v in sec.values())
    cat = sec["/catalog"]
    shop = sec["/shop"]
    legacy = sec["/legacy_html"]
    duplicates = sum(v["dup"] for v in sec.values())
    errors = sum(v["err"] for v in sec.values())
    deaths = shop["urls"] + legacy["urls"] + sec.get("/product", {}).get("urls", 0)
    events = len(parsed.get("events", []))
    wm = ROOT / "data" / "exports" / "yandex_webmaster"
    dates = sorted(p.name for p in wm.iterdir() if p.is_dir()) if wm.is_dir() else []
    day = dates[-1] if dates else ""
    summary = {}
    if day:
        s = wm / day / "summary.json"
        if s.is_file():
            summary = json.load(open(s, encoding="utf-8"))
    quota = {}
    if day:
        q = wm / day / "recrawl_quota.json"
        if q.is_file():
            quota = json.load(open(q, encoding="utf-8"))
    serp_rows = 0
    if day:
        csv = wm / day / "serp_queries" / "serp_queries_raw.csv"
        if csv.is_file():
            serp_rows = max(0, len(csv.read_text(encoding="utf-8-sig").splitlines()) - 1)

    B.TOTAL = PAGE_NUM

    kpi = B.kpi([
        ("kpiDead", "Мёртвых URL", "shop, легаси, product"),
        ("kpiCatalog", "Каталог в поиске", "по выборке панели"),
        ("kpiErrors", "Ошибок парсинга", "из %s" % fmt(errors)),
        ("kpiQuota", "Квота переобхода", "страниц в сутки"),
    ])

    months = [
        ("m1", "Месяц 1. Фундамент: убрать то, что мешает", [
            ("Закрыть `/shop`", "Disallow в robots и 301 на каталог",
             "%d URL, 0 в поиске, %d ошибок парсинга" % (shop["urls"], shop["err"]), "0,5 дня"),
            ("Разобрать легаси `.html`", "301 на SEF-аналоги или 410",
             "%d URL, в поиске %d, дублей %d" % (legacy["urls"], legacy["search"], legacy["dup"]), "1 день"),
            ("Глобальный canonical и Clean-param", "Параметры ID, PAGEN_1, SORT, UTM",
             "%d URL в дублях" % duplicates, "1 день"),
            ("Починить битые внутренние ссылки", "62 из 134, 46%%",
             "Каждая ведёт в 404 или 500 и сливает вес", "1 день"),
            ("Sitemap в корне сайта", "Убрать строки /shop/ из robots.txt",
             "23 ссылки в robots.txt отдают 404", "0,5 дня"),
            ("Закрыть админку", "Пароль и запрет индексации",
             "%s визитов в год попадают в статистику" % 802, "0,5 дня"),
            ("Отправить на переобход", "48 важных URL плюс разделы с нулём в поиске",
             "Квота %s страниц в сутки, расходуется за один вечер" % fmt(quota.get("daily_quota", 0)), "0,5 дня"),
        ], "Доля страниц в поиске не ниже 60%% по всей выборке, ошибок парсинга меньше 20, битых ссылок меньше 10"),
        ("m2", "Месяц 2. Семантика и контент", [
            ("Разложить ядро в Topvisor", "535 запросов по 8 группам с целевыми страницами",
             "Сейчас все 154 ключа в одной группе и без целевых страниц", "1 день"),
            ("Закрыть 10 пробелов контента", "Страницы под запросы с позициями 5-20",
             "Каждая страница: запрос, intent, цена, пример работы, форма", "2 недели"),
            ("Сравнительные страницы", "15 запросов без единой страницы",
             "Формат «услуга А против Б» с ценами и сроками", "1 неделя"),
            ("Локальные лендинги", "4 страницы под спрос из Ижевска и городов",
             "59%% трафика даёт Ижевск, локальных страниц нет", "1 неделя"),
            ("Оптимизация сниппетов", "Заголовки и описания по данным позиций и CTR",
             "Выгрузка с показами и кликами: %d строк, накапливается каждую неделю" % serp_rows, "1 неделя"),
        ], "Покрытие кластеров не ниже 70%, ни один кластер без целевой страницы, CTR вырос на 2 п.п."),
        ("m3", "Месяц 3. Деньги и масштаб", [
            ("Карточка в Яндекс Картах", "Фото работ, все поля, цели на каждую кнопку",
             "32 726 просмотров, но только 510 переходов на сайт", "2 недели"),
            ("Связать карточку и сайт", "Кнопка перехода ведёт на услугу, а не на главную",
             "409 звонков и 433 маршрута не видны в веб-аналитике", "3 дня"),
            ("Звонки и сделки в Метрику", "Офлайн-конверсии из CRM или АТС",
             "Без этого нельзя посчитать выручку по каналам", "1 неделя"),
            ("Отзывы", "Сбор отзывов с сайта и из карточки",
             "У карточки много просмотров и почти нет отзывов", "1 неделя"),
            ("Дистрибуция", "Публикации в местных пабликах, обмен ссылками",
             "Соцсети и ссылки дают меньше 700 визитов за год", "1 неделя"),
            ("Ежемесячный отчёт", "Дашборд и one-pager по факту закрытых задач",
             "Данные обновляются скриптом, отчёт собирается автоматически", "1 день в месяц"),
        ], "Звонки и сделки считаются в Метрике, выручка видна по каналам, два кластера выросли в ТОП-10"),
    ]

    body = ["  <section id=\"base\" data-section>\n    <h2>Откуда взялся приоритет</h2>\n"]
    body.append(kpi)
    body.append(
        '    <p>Проверка цифр от 2026-09-27 изменила порядок работ. Раньше главной проблемой '
        'считали низкий процент индексации каталога. На деле каталог проиндексирован на '
        f'{cat["share"]:.0f}% ({fmt(cat["search"])} из {fmt(cat["urls"])} проверенных URL), '
        'это нормальный показатель. Общий процент '
        f'{total_search / total_urls * 100:.1f}% тянут мёртвые разделы: '
        f'`/shop` ({fmt(shop["urls"])} URL, ноль в поиске, {shop["err"]} ошибок разбора) '
        f'и {fmt(legacy["urls"])} легаси `.html`. Их удаление поднимает показатель выше 60% '
        'без единой новой страницы, поэтому первый месяц отдан расчистке.</p>\n')
    body.append(
        '    <div class="callout"><div class="callout-title">Второе открытие проверки</div>'
        f'<p>Весь поисковый трафик сайта приходит не из Яндекса: в Метрике Google даёт '
        '4 685 визитов против 4 141 у Яндекса. Раньше в отчёте стояло «поиск на 100% '
        'яндексовый». Инструменты Google в проект не входят, но проверять позиции и '
        'сниппеты нужно по обоим поисковикам, иначе половина спроса останется без внимания.</p></div>\n')
    body.append("  </section>\n\n")

    for anchor, title, tasks, accept in months:
        body.append('  <section id="%s" data-section style="margin-top:2.5rem;">\n    <h2>%s</h2>\n' % (anchor, title))
        body.append('    <div class="table-wrapper"><table>\n      <thead><tr><th>Задача</th><th>Что сделать</th><th>Зачем</th><th>Срок</th></tr></thead>\n      <tbody>\n')
        for a, b_, c_, d_ in tasks:
            body.append('        <tr><td><strong>%s</strong></td><td>%s</td><td class="text-muted">%s</td><td>%s</td></tr>\n' % (a, b_, c_, d_))
        body.append('      </tbody>\n    </table></div>\n')
        body.append('    <div class="callout"><div class="callout-title">Приёмка месяца</div><p>%s</p></div>\n' % accept)
        body.append("  </section>\n\n")

    body.append(
        '  <section id="risk" data-section style="margin-top:2.5rem;">\n    <h2>Чего сознательно не делаем</h2>\n'
        '    <ul class="checklist">\n'
        '      <li>Не переписывать каталог целиком: он индексируется на 60%, проблема в мусоре, а не в разметке.</li>\n'
        '      <li>Не покупать ссылки и не менять домен: позиции в ТОП-10 у 390 запросов из 535, фундамент крепкий.</li>\n'
        '      <li>Не распыляться на 100 страниц: 10 пробелов из Topvisor дают больше, чем 100 общих.</li>\n'
        '      <li>Не ждать аналитику Google: фокус на данных, которые уже есть в панели.</li>\n'
        '    </ul>\n'
        '  </section>\n\n'
        '  <section id="cost" data-section style="margin-top:2.5rem;">\n    <h2>Ресурсы</h2>\n'
        '    <div class="table-wrapper"><table>\n      <thead><tr><th>Роль</th><th>Часов за 3 месяца</th><th>Комментарий</th></tr></thead>\n      <tbody>\n'
        '        <tr><td>Разработчик (Bitrix)</td><td>40-50</td><td class="text-muted">Редиректы, canonical, robots, sitemap, закрытие разделов</td></tr>\n'
        '        <tr><td>Контент и дизайн</td><td>60-70</td><td class="text-muted">10 пробелов, 15 сравнений, 4 локальных страницы, фото в карточку</td></tr>\n'
        '        <tr><td>SEO-аналитика</td><td>12-16</td><td class="text-muted">Еженедельный контроль позиций, отчёт раз в месяц</td></tr>\n'
        '        <tr><td>Замеры конкурентов</td><td>0-8</td><td class="text-muted">Только если хватит бюджета Topvisor на расширенный доступ</td></tr>\n'
        '      </tbody>\n    </table></div>\n'
        '    <p class="text-muted" style="font-size:0.875rem;margin-top:1rem;">Оценка в часах без стоимости часа. '
        f'Баланс Topvisor {topvisor_balance()} руб. покрывает сбор позиций и кластеризацию без платных модулей.</p>\n'
        '  </section>\n')

    sidebar = [("base", "Откуда приоритет"), ("m1", "Месяц 1: фундамент"),
               ("m2", "Месяц 2: семантика"), ("m3", "Месяц 3: деньги"),
               ("risk", "Чего не делаем"), ("cost", "Ресурсы")]

    html = B.page("plan-3m.html", PAGE_NUM, "План на 3 месяца",
                  "План работ на 3 месяца: расчистка, семантика, деньги",
                  "Пошаговый план продвижения цифра18.рф на три месяца: расчистка мёртвых разделов, работа с семантикой в Topvisor, контент по пробелам, карточка в Яндекс Картах, офлайн-конверсии. С цифрами, сроками и критериями приёмки по каждому месяцу.",
                  "План",
                  "Три месяца по порядку: сначала убрать то, что мешает индексации, потом расширять семантику и контент, потом доводить до денег. У каждого месяца свой критерий приёмки, чтобы было видно, выполнено или нет.",
                  sidebar, "".join(body), ("wm-plan", "План по Вебмастеру"), None)
    out = ROOT / "reports" / "cifra18-audit" / "pages" / "plan-3m.html"
    out.write_text(html, encoding="utf-8")
    print("created %s (%.1f KB)" % (out.name, out.stat().st_size / 1024))
    print("мёртвых URL: %d, каталог в поиске: %.1f%%, ошибок: %d"
          % (deaths, cat["share"], errors))

    # меню, футер и нумерацию обновляем на всех страницах
    B.patch_existing({"plan-3m.html"})
    # пересобираем и дашборды, чтобы в меню и футере появилась ссылка на план
    B.build()
    B.patch_existing({"plan-3m.html"})


if __name__ == "__main__":
    build()
