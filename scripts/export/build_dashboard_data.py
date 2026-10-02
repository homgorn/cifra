#!/usr/bin/env python3
"""Данные для дашбордов отчёта: js/dash-data.js.

Заменяет внешний BI (DataLens) собственными страницами с Chart.js: всё
считается скриптами из выгрузок API, ручных цифр нет.

Источники (всё из data/exports, никаких ручных правок):
- Вебмастер: SQI-история, квота переобхода, важные URL, выборки событий,
  годовые топы запросов, структура сайта из панели.
- Метрика (счётчик сайта 50863157): устройства, города, пол, возраст,
  интересы, боты, источники по месяцам, внешние переходы, e-commerce, цели.
- Метрика (счётчик карточки 59102713): просмотры карточки, действия
  (звонки, маршруты, переходы на сайт).

Запуск из корня проекта:
  python scripts/export/build_dashboard_data.py
"""
import csv
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wm_latest import latest_day  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WM_BASE = Path(ROOT) / "data" / "exports" / "yandex_webmaster"
MT_BASE = Path(ROOT) / "data" / "exports" / "metrica"
# Дата берётся из выгрузки, а не из сегодняшнего дня и не по
# умолчанию. И то и другое давало нули вместо данных, молча: при
# сегодняшней дате запуск в любой другой день уходил в
# несуществующую папку, а нули это правдоподобное значение, и
# собранный файл выглядел собранным.
#
# Метки разные: у Вебмастера summary.json, у Метрики
# ecommerce.json, которого summary.json там не заменяет, потому
# что его там нет вовсе.
DATE = latest_day(str(WM_BASE), "summary.json")
MT_DATE = latest_day(str(MT_BASE), "ecommerce.json")
if not DATE:
    sys.exit("в %s нет выгрузки Вебмастера с summary.json" % WM_BASE)
if not MT_DATE:
    sys.exit("в %s нет выгрузки Метрики с ecommerce.json" % MT_BASE)
WM = WM_BASE / DATE
MT = MT_BASE / MT_DATE

# Ноль в собранном файле должен быть заслуженным, а не следствием
# неверного пути. Если обязательного входа нет, падаем до сборки.
for _d, _n in ((WM, "summary.json"),
                (MT, "ecommerce.json"),
                (MT, "search_queries.json")):
    if not (_d / _n).is_file():
        sys.exit("в выгрузке %s нет %s, сборка остановлена, чтобы "
                 "не записать нули вместо данных"
                 % (_d.name, _n))
print("собираю из выгрузок: Вебмастер %s, Метрика %s" % (DATE, MT_DATE))
MT_CUTS = MT / "cuts"
MT_MAPS = MT / "cuts_maps"
PARSED = Path(ROOT) / "webmaster" / "parsed_data.json"
OUT = Path(ROOT) / "reports" / "cifra18-audit" / "js" / "dash-data.js"


def jload(p, default=None):
    p = Path(p)
    if not p.is_file():
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def dim(row, i=0):
    d = row.get("dimensions") or []
    if len(d) <= i:
        return ""
    return (d[i].get("name") or "").strip()


def metrics(row):
    return row.get("metrics") or []


def top(cut, n, key=0, metric=0, limit=10000):
    """Топ строк среза по метрике."""
    rows = (cut or {}).get("data", [])
    items = []
    for r in rows:
        v = metrics(r)
        if len(v) <= metric:
            continue
        val = v[metric] or 0
        if val <= 0:
            continue
        items.append((dim(r, key), val))
    items.sort(key=lambda x: -x[1])
    return [{"k": k, "v": round(v)} for k, v in items[:n]]


def monthly(cut, metric=0, key=0, source_key=None, sources=None):
    """Дневные строки сворачиваются в месяцы. source_key: имя 1-го измерения."""
    agg = defaultdict(float)
    for r in (cut or {}).get("data", []):
        d = dim(r, key)
        if not d:
            continue
        m = d[:7]
        v = metrics(r)
        if len(v) <= metric:
            continue
        name = dim(r, source_key) if source_key is not None else None
        if sources and name and name not in sources:
            continue
        agg[m] += v[metric] or 0
    return [{"m": k, "v": round(v)} for k, v in sorted(agg.items())]


def weighted(cut, num_idx, den_idx, prefix=""):
    """Взвешенное среднее по месяцам (например, отказы)."""
    num, den = defaultdict(float), defaultdict(float)
    for r in (cut or {}).get("data", []):
        d = dim(r, 0)
        if not d:
            continue
        m = d[:7]
        v = metrics(r)
        if len(v) <= den_idx:
            continue
        num[m] += (v[num_idx] or 0) * (v[den_idx] or 0)
        den[m] += v[den_idx] or 0
    return [{"m": k, "v": round(num[k] / den[k] * 100, 1) if den[k] else 0}
            for k in sorted(den)]


SMAP = {"Search engine traffic": "Поиск", "Internal traffic": "Внутренние",
        "Direct traffic": "Прямые", "Social network traffic": "Соцсети",
        "Link traffic": "Ссылки", "Messenger traffic": "Мессенджеры",
        "Ad traffic": "Реклама", "Cached page traffic": "Кэш",
        "Recommendation system traffic": "Рекомендации"}


def source_series(cut, top=5):
    """Ряды по источникам: [{name, data:[{m,v}]}]. Без разбивки по названию
    график «источники по месяцам» собрать нельзя."""
    per = defaultdict(lambda: defaultdict(float))
    for r in (cut or {}).get("data", []):
        d = dim(r, 0)
        src = dim(r, 1)
        v = metrics(r)
        if not d or not src or not v:
            continue
        per[SMAP.get(src, src)][d[:7]] += v[0] or 0
    totals = sorted(((sum(v.values()), k) for k, v in per.items()), reverse=True)
    out = []
    for _, name in totals[:top]:
        out.append({"name": name,
                    "data": [{"m": m, "v": round(v)} for m, v in sorted(per[name].items())]})
    return out


LEGACY_RE = re.compile(r"^/\d+\.html$")
SEC_NAMES = {"/catalog": "Каталог", "/shop": "Магазин (legacy /shop/)",
             "/product": "Товары (legacy /product/)", "/news": "Новости",
             "/product-category": "Категории товаров (legacy)"}
PREFIX = "https://xn--18-6kc5a3bxam.xn--p1ai"


def _section(url):
    path = url[len(PREFIX):] if url.startswith(PREFIX) else url
    segs = [s for s in path.split("/") if s]
    if not segs:
        return "/"
    first = "/" + segs[0]
    if first in SEC_NAMES:
        return first
    return "/legacy_html" if LEGACY_RE.match(first) else "/other"


def indexing_sample():
    """Индексация по разделам из выборки панели (717 URL). Нужна, чтобы
    отличать мёртвые разделы от рабочего каталога: общий процент 19,8%
    тянет /shop, а каталог сам по себе на 59,8%."""
    agg = defaultdict(lambda: {"urls": 0, "search": 0, "err": 0, "dup": 0})
    for p in parsed.get("pages", []):
        a = agg[_section(p.get("url") or "")]
        a["urls"] += 1
        st = p.get("status")
        if st == "SEARCHABLE":
            a["search"] += 1
        elif st == "DUPLICATE":
            a["dup"] += 1
        elif st in ("PARSE_ERROR", "HTTP_ERROR", "BAD_QUALITY"):
            a["err"] += 1
    out = []
    for key, a in agg.items():
        out.append({
            "k": SEC_NAMES.get(key, "Легаси .html" if key == "/legacy_html" else
                              ("Главная" if key == "/" else "Прочие страницы")),
            "u": a["urls"], "s": a["search"], "e": a["err"], "d": a["dup"],
            "p": round(a["search"] / a["urls"] * 100, 1) if a["urls"] else 0,
        })
    out.sort(key=lambda x: -x["u"])
    return out


MOJIBAKE = re.compile(r"^[\x00-\x7F\s]{20,}$")


def serp_rows():
    """Выгрузка pro/serp/queries/download: дата, URL, запрос, регион, клики,
    показы, позиция. Это единственный источник показов и CTR по запросам:
    обычный search-queries отдаёт тексты без метрик. Мусор с latin-символами
    (следы неверной кодировки на стороне Яндекса) выбрасываем."""
    import csv as _csv
    out = WM / "serp_queries" / "serp_queries_raw.csv"
    if not out.is_file():
        return [], 0
    agg = defaultdict(lambda: {"clicks": 0, "imp": 0, "pos": [], "paths": set()})
    total = 0
    with open(out, encoding="utf-8-sig", newline="") as f:
        for r in _csv.DictReader(f):
            total += 1
            q = (r.get("query") or "").strip()
            if not q or MOJIBAKE.match(q):
                continue
            a = agg[q]
            a["clicks"] += int(r.get("clicks") or 0)
            a["imp"] += int(r.get("impressions") or 0)
            try:
                a["pos"].append(float(r.get("position") or 0))
            except ValueError:
                pass
            a["paths"].add((r.get("path") or "").replace("https://xn--18-6kc5a3bxam.xn--p1ai", ""))
    rows = []
    for q, a in agg.items():
        rows.append({
            "q": q,
            "c": a["clicks"],
            "i": a["imp"],
            "p": round(sum(a["pos"]) / len(a["pos"]), 1) if a["pos"] else 0,
            "ctr": round(a["clicks"] / a["imp"] * 100, 1) if a["imp"] else 0,
            "u": ", ".join(sorted(a["paths"])[:2]),
        })
    rows.sort(key=lambda x: (-x["i"], -x["c"]))
    return rows[:40], total


DASH = {"generated": DATE}

# ---------------------------------------------------------------- Вебмастер
summary = jload(WM / "summary.json", {})
sqi = (jload(WM / "sqi_history.json", {}) or {}).get("points", [])
sqi_monthly = {}
for p in sqi:
    sqi_monthly[p["date"][:7]] = p["value"]
sqi_series = [{"m": k, "v": v} for k, v in sorted(sqi_monthly.items())]
quota = jload(WM / "recrawl_quota.json", {})
parsed = jload(PARSED, {}) or {}

sections = []
for r in parsed.get("structure", []):
    raw = (r.get("g-link") or "").strip()
    if not raw:
        continue
    path = raw.split("://")[-1]
    path = "/" + path.split("/", 1)[1] if "/" in path else "/"
    def num(x):
        try:
            return int(str(x or "0").replace(" ", ""))
        except ValueError:
            return 0
    sections.append({"p": path, "i": num(r.get("g-link 2")), "s": num(r.get("g-link 3"))})

important = []
for u in (jload(WM / "important_urls.json", {}) or {}).get("urls", []):
    st = u.get("indexing_status") or {}
    important.append({
        "url": (u.get("url") or "").split("/", 3)[-1] or "/",
        "code": st.get("http_code") or 0,
        "status": st.get("status") or "",
        "access": (u.get("last_access") or "")[:10],
        "chg": ",".join(u.get("change_indicators") or []),
    })

events = []
for s in (jload(WM / "events_samples.json", {}) or {}).get("samples", []):
    events.append({"d": (s.get("event_date") or "")[:10], "e": s.get("event") or "",
                   "u": (s.get("url") or "").split("/", 3)[-1] or "/"})
http = []
for s in (jload(WM / "indexing_samples.json", {}) or {}).get("samples", []):
    http.append({"u": (s.get("url") or "").split("/", 3)[-1] or "/",
                 "code": s.get("http_code") or 0, "s": s.get("status") or "",
                 "d": (s.get("access_date") or "")[:10]})

q12 = jload(WM / "queries_12m" / "q_popular_click_12m.json", {}) or {}
queries_12m = [q.get("query_text") for q in q12.get("queries", [])[:60] if q.get("query_text")]

serp, serp_total = serp_rows()
indexing = indexing_sample()
dead = sum(x["u"] for x in indexing if x["k"].startswith(("Магазин", "Легаси", "Товары", "Категории")))

DASH["tech"] = {
    "sqi": summary.get("sqi", 0),
    "sqiSeries": sqi_series,
    "sqiFirst": sqi_series[0] if sqi_series else None,
    "searchable": summary.get("searchable_pages_count", 0),
    "excluded": summary.get("excluded_pages_count", 0),
    "recrawlDaily": quota.get("daily_quota", 0),
    "recrawlLeft": quota.get("quota_remainder", 0),
    "sections": sections,
    "important": important,
    "events": events[:40],
    "http": http[:40],
    "queries12m": queries_12m,
    "serp": serp,
    "serpTotal": serp_total,
    "indexing": indexing,
    "dead": dead,
}

# ---------------------------------------------------------------- Метрика: сайт
mt = jload(MT_CUTS / "month_total.json", {}) or {}
eco = jload(MT / "ecommerce.json", {}) or {}
goals = (jload(MT / "goals.json", {}) or {}).get("goals", [])

rev_by_month, pur_by_month = defaultdict(float), defaultdict(float)
for r in eco.get("data", []):
    d = dim(r, 0)
    m = d[:7]
    v = metrics(r)
    if len(v) > 0:
        pur_by_month[m] += v[0] or 0
    if len(v) > 1:
        rev_by_month[m] += v[1] or 0

rev_days = sorted(((dim(r, 0), round(metrics(r)[1] or 0), int(metrics(r)[0] or 0))
                   for r in eco.get("data", []) if len(metrics(r)) > 1 and (metrics(r)[1] or 0) > 0),
                  key=lambda x: -x[1])
# Итоги по всем строкам, а не только по тем, где есть выручка: заказы без
# суммы тоже заказы, иначе счётчик занижался.
eco_rows = [metrics(r) for r in eco.get("data", []) if metrics(r)]
eco_purchases = sum(m[0] or 0 for m in eco_rows)
eco_revenue = sum(m[1] or 0 for m in eco_rows if len(m) > 1)

robots = {dim(r, 0): (metrics(r)[0] or 0) for r in (jload(MT_CUTS / "robots.json", {}) or {}).get("data", [])}
bot_v = robots.get("Robots", 0)
peo_v = robots.get("People", 0)

mt_rows = mt.get("data") or []


def _m1(idx):
    return sum(metrics(r)[idx] or 0 for r in mt_rows if len(metrics(r)) > idx)


DASH["site"] = {
    "visitsTotal": round(_m1(0)),
    "usersTotal": round(_m1(1)),
    "monthly": monthly(mt, 0),
    "monthlyUsers": monthly(mt, 1),
    "bounce": weighted(mt, 3, 0),
    "devices": top(jload(MT_CUTS / "devices.json", {}), 4),
    "browsers": top(jload(MT_CUTS / "browsers.json", {}), 8),
    "cities": top(jload(MT_CUTS / "cities.json", {}), 12),
    "countries": top(jload(MT_CUTS / "countries.json", {}), 8),
    "regions": top(jload(MT_CUTS / "regions.json", {}), 8),
    "gender": top(jload(MT_CUTS / "gender.json", {}), 3),
    "age": top(jload(MT_CUTS / "age.json", {}), 8),
    "interests": top(jload(MT_CUTS / "interests.json", {}), 10),
    "bots": {"people": round(peo_v), "robots": round(bot_v),
             "share": round(bot_v / (bot_v + peo_v) * 100, 1) if (bot_v + peo_v) else 0},
    "referers": top(jload(MT_CUTS / "external_refs.json", {}), 20),
    "sources": source_series(jload(MT_CUTS / "source_month.json", {}), 5),
    "landing": top(jload(MT / "landing_pages.json", {}), 15),
    "phrases": top(jload(MT / "search_queries.json", {}), 20),
}

DASH["money"] = {
    "revenue": round(eco_revenue),
    "purchases": int(eco_purchases),
    "revByMonth": [{"m": k, "v": round(v)} for k, v in sorted(rev_by_month.items()) if v],
    "purByMonth": [{"m": k, "v": round(v)} for k, v in sorted(pur_by_month.items()) if v],
    "topDays": [{"d": d, "v": v, "p": p} for d, v, p in rev_days[:8]],
    "goals": [{"n": g.get("name"), "t": g.get("type"), "s": g.get("status")} for g in goals],
    "goalsActive": sum(1 for g in goals if g.get("status") == "Active"),
}

# ------------------------------------------------- Метрика: карточка в Картах
maps_month = jload(MT_MAPS / "month_total.json", {}) or {}
actions = top(jload(MT_MAPS / "actions.json", {}), 12, metric=0)
maps_goals = {}
for a in actions:
    for key, label in (("Позвонить", "calls"), ("маршрут", "routes"),
                       ("Переход на сайт", "site"), ("мессенджер", "messengers")):
        if key.lower() in a["k"].lower():
            maps_goals[label] = maps_goals.get(label, 0) + a["v"]
            break
maps_rows = (jload(MT_MAPS / "month_total.json", {}) or {}).get("data") or []
DASH["maps"] = {
    "viewsTotal": round(sum(metrics(r)[0] or 0 for r in maps_rows if metrics(r))),
    "monthly": monthly(maps_month, 0),
    "entries": top(jload(MT_MAPS / "entries.json", {}), 12),
    "sources": top(jload(MT_MAPS / "sources.json", {}), 8),
    "actions": actions,
    "goals": maps_goals,
    "cities": top(jload(MT_MAPS / "cities.json", {}), 10),
    "search": top(jload(MT_MAPS / "search.json", {}), 12),
    "devices": top(jload(MT_MAPS / "devices.json", {}), 4),
}

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write("/* Generated by scripts/export/build_dashboard_data.py. Do not edit by hand. */\n")
    f.write("const DASH = ")
    json.dump(DASH, f, ensure_ascii=False)
    f.write(";\n")

size = OUT.stat().st_size
print("Wrote %s (%.1f KB)" % (OUT, size / 1024))
print("sqi=%s series=%d sites=%s important=%d" % (DASH["tech"]["sqi"], len(sqi_series),
                                                 DASH["site"]["visitsTotal"], len(important)))
print("serp: rows=%d из %d сырых строк" % (len(serp), serp_total))
print("money: revenue=%s purchases=%s goals=%s" % (DASH["money"]["revenue"],
                                                  DASH["money"]["purchases"], DASH["money"]["goalsActive"]))
print("maps: views=%s calls=%s routes=%s" % (DASH["maps"]["viewsTotal"],
                                             DASH["maps"]["goals"].get("calls"),
                                             DASH["maps"]["goals"].get("routes")))
print("bots share=%s%%" % DASH["site"]["bots"]["share"])
