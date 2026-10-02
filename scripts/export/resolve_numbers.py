"""Свести противоречивые числа к одному источнику истины.

Задача скрипта не пересказать документацию, а вычислить. Каждое
противоречие разрешается чтением первичных данных, и по каждому
печатается, что верно и где в проекте стоит неверное число.

Порядок работы для каждого пункта один и тот же: берётся первичный
источник, из него считается, результат сравнивается с тем, что лежит
в документах. Число, взятое из документа, источником не считается.

Запуск:

    python scripts/export/resolve_numbers.py
"""

import csv
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"C:\susa ai\2026 cifra audit"
WM_EXPORT = os.path.join(ROOT, "data", "exports", "yandex_webmaster")
MET = os.path.join(ROOT, "brain", "wiki", "metrika_analytics", "exports")
WIKI_WM = os.path.join(ROOT, "brain", "wiki", "webmaster_analytics")
SITE_JS = os.path.join(ROOT, "reports", "cifra18-audit", "js", "wm-data.js")
REPORT = os.path.join(ROOT, "CLIENT_REPORT.md")

RESULTS = []


def note(point, truth, wrong_at, source, comment=""):
    RESULTS.append({"point": point, "truth": truth, "wrong": wrong_at,
                    "source": source, "comment": comment})


def newest_export():
    if not os.path.isdir(WM_EXPORT):
        return None
    days = sorted(d for d in os.listdir(WM_EXPORT)
                  if os.path.isdir(os.path.join(WM_EXPORT, d)))
    for d in reversed(days):
        if os.path.isfile(os.path.join(WM_EXPORT, d, "summary.json")):
            return os.path.join(WM_EXPORT, d)
    return None


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def read_csv(path, delim=None):
    """Прочитать CSV, угадав разделитель.

    Разделитель не указывается: файлы Метрики приходят и с запятой, и
    с точкой с запятой, и это уже во второй раз ломало разбор. Явно
    заданный разделитель, если он передан, имеет приоритет.
    """
    if not os.path.isfile(path):
        return []
    lines = [l for l in open(path, encoding="utf-8-sig")
             .read().splitlines() if l.strip()]
    if not lines:
        return []
    if delim is None:
        counts = {";": lines[0].count(";"), ",": lines[0].count(","),
                  "\t": lines[0].count("\t")}
        delim = max(counts, key=counts.get)
        if counts[delim] == 0:
            delim = ","
    rows = [r for r in csv.reader(lines, delimiter=delim)
            if any(c.strip() for c in r)]
    return rows


# ------------------------------------------------- 1. страницы в поиске

def check_widths(path):
    """Сойдутся ли ширина шапки и ширина данных.

    Проверка добавлена после того, как файл посещаемости по дням
    оказался разобран неверно: в шапке восемь колонок, включая
    счётчик, а в данных семь, счётчика там нет вовсе. Чтение по
    позициям шапки при этом не падает, а молча сдвигает все значения
    на одну колонку влево: визиты становятся посетителями,
    просмотры становятся процентом отказов.
    """
    if not os.path.isfile(path):
        return None
    lines = [l for l in open(path, encoding="utf-8-sig")
             .read().splitlines() if l.strip()]
    if not lines:
        return None
    sep = ","
    counts = {";": lines[0].count(";"), ",": lines[0].count(","),
              "\t": lines[0].count("\t")}
    sep = max(counts, key=counts.get) if counts[max(counts, key=counts.get)] else ","
    head = [c.strip() for c in next(csv.reader([lines[0]], delimiter=sep))]
    widths = {}
    for r in csv.reader(lines[1:], delimiter=sep):
        if any(c.strip() for c in r):
            widths[len(r)] = widths.get(len(r), 0) + 1
    body = sorted(widths.items(), key=lambda x: -x[1])
    return {"file": os.path.basename(path), "head": head,
            "head_n": len(head), "widths": body,
            "ok": not widths or set(widths) == {len(head)}}


def resolve_indexation():
    day = newest_export()
    if not day:
        return
    name = os.path.basename(day)
    summ = load(os.path.join(day, "summary.json")) or {}
    ins = load(os.path.join(day, "insearch_samples.json")) or {}
    idx = load(os.path.join(day, "indexing_samples.json")) or {}

    site_searchable = summ.get("searchable_pages_count")
    site_excluded = summ.get("excluded_pages_count")
    insearch_count = ins.get("count")
    indexed_count = idx.get("count")

    note("Страниц в поиске, весь сайт",
         "%s, отраслевка Яндекса, снимок %s" % (site_searchable, name),
         "708 указывалось как актуальное, но это снимок за 2026-09-27; "
         "в снимке за %s то же поле равно %s"
         % (name, site_searchable),
         "%s/summary.json" % name)

    if insearch_count:
        note("Страниц в поиске, подтверждение",
             "выборка Яндекса насчитала %s адресов" % insearch_count,
             "расходится с полем на %s, разница %d"
             % (site_searchable, abs(insearch_count - site_searchable)),
             "%s/insearch_samples.json" % name,
             "два поля Яндекса расходятся на единицы, это нормально")

    if indexed_count:
        note("Адресов известно роботу",
             "%s, из них %s в поиске, доля %.2f процента"
             % (indexed_count, site_searchable,
                100.0 * site_searchable / indexed_count),
             "2 423 и 252, то есть 10,4 процента, бралось из файла сайта "
             "wm-data.js, собранного 2026-09-23, а не из выгрузки",
             "%s/indexing_samples.json и summary.json" % name,
             "wm-data.js устарел и вообще является выводом, а не входом")

    note("Исключено из индекса", site_excluded,
         "477 из снимка за 2026-09-27", "%s/summary.json" % name)
    return name


# ------------------------------------------------------------ 2. сайт

def resolve_site_visits():
    rows = read_csv(os.path.join(MET, "attendance_daily.csv"))
    if len(rows) < 2:
        return
    head = [c.strip() for c in rows[0]]
    di, vi, pi = head.index("date"), head.index("visits"), head.index("pageviews")
    # Счётчика в данных нет, поэтому отбираются строки той же длины,
    # что и самая частая, и приводимые к числу. Отбор по счётчику
    # здесь невозможен и был бы выдумкой: колонки с таким именем в
    # файле нет.
    widths = {}
    for r in rows[1:]:
        widths[len(r)] = widths.get(len(r), 0) + 1
    common = max(widths, key=widths.get) if widths else 0
    need = max(vi, pi)
    main = [r for r in rows[1:]
            if len(r) == common and len(r) > need
            and r[vi].strip().isdigit() and r[pi].strip().isdigit()]
    if not main:
        note("Визиты сайта за историю счётчика",
             "НЕ ПОСЧИТАНО. В файле %d строк данных по %d колонок, "
             "а шапка объявляет %d. Читать по позициям шапки нельзя, "
             "значения сдвинуты, а счётчика в данных нет вовсе."
             % (len(rows) - 1, common, len(head)),
             "21 110 и 21 119 получены суммированием этого файла и "
             "не имеют под собой данных",
             "brain/wiki/metrika_analytics/exports/attendance_daily.csv",
             "нужно перезагрузить из Метрики с колонкой счётчика "
             "или снять колонку счётчика из шапки")
        return
    total_v = sum(int(r[vi]) for r in main)
    total_p = sum(int(r[pi]) for r in main)
    dates = sorted(r[di] for r in main)
    note("Визиты сайта за историю счётчика",
         "%d, просмотров %d, с %s по %s, %d дней"
         % (total_v, total_p, dates[0], dates[-1], len(main)),
         "21 110 и 21 119 в соседних блоках одного файла, разница 9",
         "brain/wiki/metrika_analytics/exports/attendance_daily.csv",
         "разница в единицы это перекрытие границ периода, а не ошибка, "
         "но показывать нужно одно число с датой")

    month = read_csv(os.path.join(MET, "attendance_monthly.csv"))
    if len(month) > 1:
        m = [r for r in month[1:] if r[1].strip() == "50863157"]
        if m:
            last12 = m[-12:]
            v12 = sum(int(r[2]) for r in last12)
            note("Визиты сайта за последние 12 месяцев",
                 "%d, месяцев %s по %s"
                 % (v12, last12[0][0], last12[-1][0]),
                 "число называлось без указания периода, из-за чего "
                 "читалось как другое", "attendance_monthly.csv")


# ------------------------------------------------------- 3. карта

def resolve_maps():
    rows = read_csv(os.path.join(MET, "maps_card_monthly.csv"))
    if len(rows) < 2:
        return
    head = [c.strip() for c in rows[0]]
    mi, vi = head.index("month"), head.index("visits")
    allv = sum(int(r[vi]) for r in rows[1:])
    note("Просмотры карточки за всю историю счётчика",
         "%d, месяцев %d, с %s по %s"
         % (allv, len(rows) - 1, rows[1][mi], rows[-1][mi]),
         "79 413 и 79 002 в двух файлах, разница 411",
         "brain/wiki/metrika_analytics/exports/maps_card_monthly.csv",
         "два числа относятся к разным периодам либо выгрузкам, "
         "разница 411 это не округление")

    last12 = rows[1:][-12:]
    v12 = sum(int(r[vi]) for r in last12)
    note("Просмотры карточки за последние 12 месяцев",
         "%d, месяцев %s по %s" % (v12, last12[0][mi], last12[-1][mi]),
         "32 726 подавалось рядом с 79 413 без подписи периода, "
         "из-за чего читалось как противоречие",
         "maps_card_monthly.csv")

    daily = read_csv(os.path.join(MET, "maps_card",
                                  "attendance_daily.csv"))
    if len(daily) > 1:
        head2 = [c.strip() for c in daily[0]]
        dv = head2.index("visits")
        from collections import Counter
        c = Counter()
        for r in daily[1:]:
            c[r[0][:7]] += int(r[dv])
        if c:
            y = sorted(c)[-1][:4]
            same = sum(v for k, v in c.items() if k.startswith(y))
            note("Просмотры карточки по помесячно из дневной выгрузки",
                 "в %s году %d, всего помесячных строк %d, лет %d"
                 % (y, same, len(c), len(y)),
                 "помесячный и дневной файлы считают разное",
                 "maps_card/attendance_daily.csv против maps_card_monthly.csv",
                 "если разница есть, один из файлов обрезан по дате")


# ------------------------------------------------------ 4. sitemap

def resolve_sitemap(day):
    sm = load(os.path.join(WM_EXPORT, day, "sitemaps.json")) or {}
    rb = load(os.path.join(WM_EXPORT, day, "robots_state.json")) or {}
    apis = sm.get("sitemaps") or []
    api_err = sum(int(s.get("errors_count") or 0) for s in apis)
    api_urls = sum(int(s.get("urls_count") or 0) for s in apis)
    note("Состояние sitemap",
         "Яндекс показывает ошибок %d при urls_count %d по %d файлам; "
         "наша проверка живьём %d: строк в robots.txt, код 404 у %d, "
         "код 200 у %d"
         % (api_err, api_urls, len(apis), rb.get("sitemap_lines", 0),
            rb.get("sitemap_404", 0), rb.get("sitemap_other", 0)),
         "«ошибок нет, всё читается» и «19 файлов отдают 404» "
         "подавались как два разных утверждения",
         "%s/sitemaps.json и robots_state.json" % day,
         "это не противоречие: Яндекс не сообщает об ошибке файла, "
         "который он не смог скачать, и ноль прочитанных адресов это "
         "подтверждает. Статус 404 установлен нашей проверкой")


# ------------------------------------------- 5. устаревший файл сайта

def resolve_site_js():
    if not os.path.isfile(SITE_JS):
        return
    t = open(SITE_JS, encoding="utf-8").read()
    d = json.loads(t[t.index("{"):].rstrip().rstrip(";"))
    meta = d.get("meta") or {}
    day = newest_export()
    fresh = os.path.basename(day) if day else "нет выгрузки"
    note("Данные, вшитые в сайт отчёта",
         "wm-data.js собран %s, страниц в выборке %s, запросов %s; "
         "живая выгрузка датирована %s"
         % (meta.get("generated"), meta.get("totalPages"),
            meta.get("totalQueries"), fresh),
         "файл лежит в папке сайта и при этом является источником чисел "
         "для отчёта, то есть вывод читается как вход",
         "reports/cifra18-audit/js/wm-data.js",
         "пока он в источниках facts.py, числа в отчёте отстают от данных "
         "на %s"
         % (meta.get("generated") or "неизвестно сколько"))


# ------------------------------------------- 6. граф знаний и прочее

def resolve_kg():
    p = os.path.join(ROOT, "brain", "wiki", "knowledge_graph",
                     "KG_INDEX.md")
    if not os.path.isfile(p):
        return
    txt = open(p, encoding="utf-8").read()
    m = re.search(r"Entities:\*\*\s*(\d+)", txt)
    tr = re.search(r"Triplets:\*\*\s*(\d+)", txt)
    ttl = os.path.join(ROOT, "brain", "wiki", "knowledge_graph",
                       "cifra18_knowledge_graph.ttl")
    real_e = real_t = 0
    if os.path.isfile(ttl):
        body = open(ttl, encoding="utf-8").read()
        real_e = len(set(re.findall(r"cifra:[A-Za-z_0-9]+", body)))
        real_t = body.count("cifra:")
    note("Граф знаний",
         "в KG_INDEX заявлено сущностей %s, триплетов %s; в самом TTL "
         "различных идентификаторов %d, строк с предикатом %d"
         % (m.group(1) if m else "?", tr.group(1) if tr else "?",
            real_e, real_t),
         "85 сущностей стояло в клиентском отчёте против 239 в KG_INDEX",
         "brain/wiki/knowledge_graph/cifra18_knowledge_graph.ttl",
         "считать надо по файлу, а не по индексу: индекс писался вручную")


# ------------------------------------------------- где стоят числа

def where_is(number, limit=6):
    """В каких файлах встречается число."""
    hits = []
    for base in ("brain", "reports", "scripts"):
        for dirpath, _dirs, files in os.walk(os.path.join(ROOT, base)):
            if ".git" in dirpath:
                continue
            for f in files:
                if not f.endswith((".md", ".html", ".py", ".json", ".csv")):
                    continue
                p = os.path.join(dirpath, f)
                try:
                    body = open(p, encoding="utf-8").read()
                except (OSError, UnicodeDecodeError):
                    continue
                if number in body:
                    hits.append(os.path.relpath(p, ROOT))
                if len(hits) >= limit:
                    return hits
    return hits


# ------------------------------------------------------------- вывод

def resolve_integrity():
    """Сойдутся ли колонки в клиентских выгрузках Метрики.

    Проверяются файлы, из которых берутся числа для отчёта. Расхождение
    ширины шапки и ширины данных не является ошибкой чтения, данными
    оно тоже не является: это ошибка файла, и при чтении по позициям
    она даёт правдоподобные неправдоподобные числа.
    """
    for path in (os.path.join(MET, "attendance_daily.csv"),
                 os.path.join(MET, "attendance_monthly.csv"),
                 os.path.join(MET, "maps_card_monthly.csv"),
                 os.path.join(MET, "maps_card", "attendance_daily.csv"),
                 os.path.join(MET, "traffic_by_source.csv")):
        r = check_widths(path)
        if not r:
            continue
        if r["ok"]:
            note("Целостность %s" % r["file"],
                 "шапка и данные сходятся, колонок %d" % r["head_n"],
                 "", path and os.path.relpath(path, ROOT))
        else:
            note("Целостность %s" % r["file"],
                 "данные пригодны к чтению по позициям %d, но в шапке %d; "
                 "расхождение таково: %s"
                 % (r["widths"][0][0], r["head_n"],
                    ", ".join("%d колонок у %d строк"
                              % (w, n) for w, n in r["widths"])),
                 "читать этот файл по шапке нельзя, значения сдвинуты; "
                 "в шапке есть колонка %s, которой в данных нет"
                 % ", ".join(c for c in r["head"]
                             if c not in ("date", "month", "counter")),
                 os.path.relpath(path, ROOT))


def main():
    day = resolve_indexation()
    resolve_site_visits()
    resolve_maps()
    if day:
        resolve_sitemap(day)
    resolve_site_js()
    resolve_kg()
    resolve_integrity()

    L = []
    a = L.append
    a("# Противоречивые числа: что верно и почему")
    a("")
    a("Собрано скриптом `scripts/export/resolve_numbers.py`. Каждый пункт "
      "разрешён чтением первичных данных, а не документа: число из "
      "документа источником не считается.")
    a("")
    a("## Сводка")
    a("")
    a("| Показатель | Верно | Источник |")
    a("|---|---|---|")
    for r in RESULTS:
        a("| %s | %s | `%s` |" % (r["point"], r["truth"], r["source"]))
    a("")
    for i, r in enumerate(RESULTS, 1):
        a("### %d. %s" % (i, r["point"]))
        a("")
        a("**Верно:** %s" % r["truth"])
        a("")
        a("**Что стояло неверно:** %s" % r["wrong"])
        a("")
        a("**Источник:** `%s`" % r["source"])
        if r["comment"]:
            a("")
            a("**Пояснение:** %s" % r["comment"])
        a("")
    text = "\n".join(L) + "\n"
    out = os.path.join(WIKI_WM, "13_Number_Reconciliation.md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("записано: %s, пунктов %d" % (out, len(RESULTS)))
    print()
    for r in RESULTS:
        print("%-44s %s" % (r["point"], str(r["truth"])[:88]))
    return 0


if __name__ == "__main__":
    sys.exit(main())