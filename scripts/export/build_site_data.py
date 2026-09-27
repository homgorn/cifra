#!/usr/bin/env python3
"""Сборка js/site-data.js для главной страницы отчёта.

Тянет живые цифры из data/exports (API 2026-09-27), вики-экспортов и
webmaster/parsed_data.json. Все KPI и графики главной — только отсюда.

Запуск из корня проекта: python scripts/export/build_site_data.py
"""
import csv
import json
import os
import re
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WM_API = os.path.join(ROOT, "data", "exports", "yandex_webmaster", "2026-09-27")
MT_ROOT = os.path.join(ROOT, "data", "exports", "metrica")
MT_API = os.path.join(MT_ROOT, "2026-09-27")
WM_WIKI = os.path.join(ROOT, "brain", "wiki", "webmaster_analytics", "exports")
MT_WIKI = os.path.join(ROOT, "brain", "wiki", "metrika_analytics", "exports")
OUT = os.path.join(ROOT, "reports", "cifra18-audit", "js", "site-data.js")

# Счётчики Метрики. У сайта и у карточки в Яндекс Картах они разные, и
# путаница между ними уже случалась дважды: сначала в тексте отчёта,
# потом в данных. Здесь счётчик проверяется по файлу индекса среза,
# где он записан при выгрузке.
ENV = {}
if os.path.isfile(os.path.join(ROOT, ".env")):
    for _ln in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
        _ln = _ln.strip()
        if _ln and not _ln.startswith("#") and "=" in _ln:
            _k, _v = _ln.split("=", 1)
            ENV[_k.strip()] = _v.strip()
SITE_COUNTER = ENV.get("METRIKA_COUNTER_ID", "50863157")
MAPS_COUNTER = ENV.get("METRIKA_MAPS_COUNTER_ID", "59102713")


def jload(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def cload(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def site_cuts_from_api():
    """Визиты и доля поиска по счётчику сайта, из API-срезов.

    Срез лежит в data/exports/metrica/<дата>/cuts, рядом лежат срезы
    карточки в подпапке maps. Индекс пишет, какой счётчик использован,
    поэтому перепутать их here нельзя: если в индексе не счётчик сайта,
    сборка падает, а не подставляет чужие числа.

    Окно задаётся явно и попадает в результат. Отчёт клиенту считает
    12 месяцев, а полная история счётчика с 2023 года даёт 98 295 визитов
    и 4% поиска. Оба числа верны, и молча подставить одно вместо другого
    это ровно та ошибка, которую мы уже чинили дважды.
    """
    cuts = os.path.join(MT_API, "cuts")
    idx_path = os.path.join(cuts, "_index.json")
    if not os.path.isfile(idx_path):
        return {"visits": 0, "search_share_pct": 0, "counter": "",
                "verified": False, "window": ""}
    idx = jload(idx_path)
    counter = str(idx.get("counter") or "")
    if counter != SITE_COUNTER:
        raise SystemExit(
            "срез Метрики собран по счётчику %s, а сайт это %s. "
            "Перезапусти metrica_cuts_export.py, не подставляй чужие числа."
            % (counter or "неизвестен", SITE_COUNTER))
    date_to = idx.get("date_to") or ""
    date_from = _minus_year(date_to)

    def in_window(d):
        return bool(d) and date_from <= d <= date_to

    def row_dims(r):
        """Приводит dimensions к словарю с ключами date и traffic-source.

        Метрика отдаёт роль измерения в поле icon_type, а идентификатор в
        id, но не у всех срезов: в source_month измерение даты приходит
        без icon_type и без id, просто строкой. Если искать только по
        ключу date, окно отсекает всё и счётчик молча даёт ноль.
        """
        out, date = {}, None
        for d in (r.get("dimensions") or []):
            name = d.get("name") or ""
            role = d.get("icon_type") or ""
            if d.get("id"):
                out[d["id"]] = d
            if role:
                out[role] = d
            elif re.match(r"^\d{4}-\d{2}-\d{2}$", name):
                date = d
        if date is not None:
            out["date"] = date
        return out

    def total(path):
        j = jload(os.path.join(cuts, path))
        s = 0
        for r in j.get("data") or []:
            if not in_window(row_dims(r).get("date", {}).get("name")):
                continue
            s += int((r.get("metrics") or [0])[0] or 0)
        return s

    visits = total("month_total.json")
    src = jload(os.path.join(cuts, "source_month.json"))
    by_id = {}
    for r in src.get("data") or []:
        dims = row_dims(r)
        date = dims.get("date", {}).get("name", "")
        if not (date_from <= date <= date_to):
            continue
        key = dims.get("traffic-source", {}).get("id", "?")
        by_id[key] = by_id.get(key, 0) + int((r.get("metrics") or [0])[0] or 0)
    search = by_id.get("organic", 0)
    share = round(search / visits * 100, 2) if visits else 0
    return {"visits": visits, "search_share_pct": share, "search_visits": search,
            "direct_visits": by_id.get("direct", 0), "counter": counter,
            "verified": True, "window": "%s..%s" % (date_from, date_to),
            "by_source": by_id}


def _minus_year(date_str):
    import datetime
    try:
        d = datetime.date.fromisoformat(date_str)
    except ValueError:
        return "0000-00-00"
    try:
        return d.replace(year=d.year - 1).isoformat()
    except ValueError:          # 29 февраля
        return d.replace(year=d.year - 1, day=28).isoformat()


site_cuts = site_cuts_from_api()


summary = jload(os.path.join(WM_API, "summary.json"))
insearch = jload(os.path.join(WM_API, "insearch_history.json")).get("history", [])
popular = jload(os.path.join(WM_API, "queries_popular.json"))
eco = jload(os.path.join(MT_API, "ecommerce.json")).get("data", [])
goals = jload(os.path.join(MT_API, "goals.json")).get("goals", [])
parsed = jload(os.path.join(ROOT, "webmaster", "parsed_data.json"))

# В поиске по месяцам (последнее значение месяца)
bym = {}
for p in insearch:
    bym[p["date"][:7]] = p["value"]
insearch_monthly = [{"m": k, "v": v} for k, v in sorted(bym.items())]

# Выручка
purch = rev = 0
topdays = []
for r in eco:
    m = r.get("metrics", [0, 0])
    p, v = (m[0] if len(m) > 0 else 0), (m[1] if len(m) > 1 else 0)
    purch += p
    rev += v
    if v:
        topdays.append({"d": r["dimensions"][0]["name"], "v": round(v), "p": p})
topdays.sort(key=lambda x: -x["v"])

# Источники за год (API, англ. метки -> короткие русские)
SMAP = {"Search engine traffic": "Поиск", "Internal traffic": "Внутренние",
        "Direct traffic": "Прямые", "Social network traffic": "Соцсети",
        "Link traffic": "Ссылки", "Messenger traffic": "Мессенджеры",
        "Cached page traffic": "Кэш", "Recommendation system traffic": "Рекомендации"}
src = defaultdict(int)
for r in jload(os.path.join(MT_API, "sources_summary.json")).get("data", []):
    dims = r.get("dimensions", [])
    m = r.get("metrics", [])
    if len(dims) > 1 and m:
        src[SMAP.get(dims[1].get("name", "?"), dims[1].get("name", "?"))] += m[0]
sources = sorted(({"s": k, "v": int(v)} for k, v in src.items()),
                 key=lambda x: -x["v"])

SITE = {
    "generated": "2026-09-27",
    "searchable": summary.get("searchable_pages_count", 0),
    "excluded": summary.get("excluded_pages_count", 0),
    "sqi": summary.get("sqi", 0),
    "statuses": parsed.get("stats", {}).get("status_counts", {}),
    "insearchMonthly": insearch_monthly,
    "insearchFirst": insearch_monthly[0] if insearch_monthly else None,
    "insearchLast": insearch_monthly[-1] if insearch_monthly else None,
    "popularCount": popular.get("count", 0),
    # Разделитель диапазона дат: короткое тире, не em-dash. Правило
    # проекта «без em-dash» проверялось только main.js, а этот файл
    # собирается отдельно, и знак проехал в уже собранный коефайл.
    "popularWeek": "%s–%s" % (popular.get("date_from", "")[5:],
                               popular.get("date_to", "")[5:]),
    "popularTop10": [q["query_text"] for q in popular.get("queries", [])[:10]],
    "purchases": purch,
    "revenue": round(rev),
    "revenueTop5": topdays[:5],
    "goalsActive": sum(1 for g in goals if g.get("status") == "Active"),
    # Визиты и доля поиска берутся не из metrika_summary.json. Тот файл
    # собирается из ручных выгрузок в metrika/, где нет идентификатора
    # счётчика, и фактически оказался выгрузкой карточки в Яндекс Картах:
    # 79 002 визита и 4,22% поиска против 21 119 и 43% у сайта. Здесь
    # читается API-срез сайта, в котором счётчик записан явно.
    "metrikaVisits": site_cuts.get("visits", 0),
    "metrikaSearchShare": site_cuts.get("search_share_pct", 0),
    "metrikaCounter": site_cuts.get("counter", ""),
    "sourcesYear": sources,
}

with open(OUT, "w", encoding="utf-8") as f:
    f.write("/* Generated by scripts/export/build_site_data.py. Do not edit by hand. */\n")
    f.write("const SITE = ")
    json.dump(SITE, f, ensure_ascii=False)
    f.write(";\n")

print("Wrote %s" % OUT)
print("searchable=%s sqi=%s revenue=%s purchases=%s popular=%s" % (
    SITE["searchable"], SITE["sqi"], SITE["revenue"],
    SITE["purchases"], SITE["popularCount"]))
