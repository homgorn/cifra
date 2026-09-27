#!/usr/bin/env python3
"""Экспорты Метрики по счётчику сайта, из API-срезов.

Зачем отдельный скрипт. Ручная выгрузка из панели не несёт
идентификатора счётчика, и однажды в папке metrika/ оказалась выгрузка
карточки в Яндекс Картах под общим именем. Дальше 79 002 визита карточки
ушли в сайт как «визиты сайта», и никто этого не заметил, потому что
сравнивать было не с чем: число стояло в файле с именем traffic_by_source.

Здесь источник другой. API-срез лежит в
data/exports/metrica/<дата>/cuts, и счётчик записан в нём самой
выгрузкой, в _index.json. Скрипт проверяет, что счётчик совпадает со
счётчиком сайта из .env, и падает, если нет. Перепутать нельзя.

Пишет в brain/wiki/metrika_analytics/exports/:
  traffic_by_source.csv   источники трафика за окно
  attendance_daily.csv    визиты по дням
  attendance_monthly.csv  визиты по месяцам
  search_queries_top.csv  поисковые запросы
  regions.csv             регионы
  devices.csv             устройства
  metrika_summary.json    сводка с полями counter и window

Запуск из корня проекта:
  python scripts/export/build_metrika_site_exports.py
"""
import csv
import datetime
import json
import os
import re
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MT_ROOT = os.path.join(ROOT, "data", "exports", "metrica")
OUT = os.path.join(ROOT, "brain", "wiki", "metrika_analytics", "exports")
os.makedirs(OUT, exist_ok=True)

ENV = {}
if os.path.isfile(os.path.join(ROOT, ".env")):
    for ln in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
        ln = ln.strip()
        if ln and not ln.startswith("#") and "=" in ln:
            k, v = ln.split("=", 1)
            ENV[k.strip()] = v.strip()
SITE_COUNTER = ENV.get("METRIKA_COUNTER_ID", "50863157")
MAPS_COUNTER = ENV.get("METRIKA_MAPS_COUNTER_ID", "59102713")

# Метрики в срезах идут в фиксированном порядке, заданном запросом.
VISITS, USERS = 0, 1


def latest_day():
    days = sorted(d for d in os.listdir(MT_ROOT)
                  if os.path.isdir(os.path.join(MT_ROOT, d)))
    if not days:
        raise SystemExit("нет ни одного среза Метрики в data/exports/metrica")
    return days[-1]


DAY = latest_day()
API = os.path.join(MT_ROOT, DAY)
CUTS = os.path.join(API, "cuts")
IDX = os.path.join(CUTS, "_index.json")

if not os.path.isfile(IDX):
    raise SystemExit("нет %s. Запусти metrica_cuts_export.py" % IDX)
INDEX = json.load(open(IDX, encoding="utf-8"))
COUNTER = str(INDEX.get("counter") or "")
if COUNTER != SITE_COUNTER:
    raise SystemExit(
        "срез за %s собран по счётчику %s, а сайт это %s.\n"
        "Экспорты сайта не собираются из чужого счётчика."
        % (DAY, COUNTER or "неизвестен", SITE_COUNTER))

DATE_TO = INDEX.get("date_to") or ""


def minus_year(d):
    try:
        x = datetime.date.fromisoformat(d)
    except ValueError:
        return "0000-00-00"
    try:
        return x.replace(year=x.year - 1).isoformat()
    except ValueError:
        return x.replace(year=x.year - 1, day=28).isoformat()


DATE_FROM = minus_year(DATE_TO)


def jload(name):
    p = os.path.join(CUTS, name)
    if not os.path.isfile(p):
        return {}
    return json.load(open(p, encoding="utf-8"))


def rows(name):
    return jload(name).get("data") or []


def dims_of(r):
    """Метрика отдаёт роль измерения в icon_type, идентификатор в id, а
    дату просто строкой без обоих. Ключи: псевдонимы ролей и id."""
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


def in_window(d):
    return bool(d) and DATE_FROM <= d <= DATE_TO


def wcsv(name, header, data):
    p = os.path.join(OUT, name)
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(data)
    print("written %s (%d rows)" % (name, len(data)))


# ---------- источники трафика ----------
SRC_LABEL = {
    "organic": "Поиск", "direct": "Прямые заходы",
    "referral": "Ссылки", "social": "Соцсети",
    "messenger": "Мессенджеры", "advert": "Реклама",
    "cpc": "Реклама", "email": "Письма", "crm": "CRM",
}
src = defaultdict(lambda: {"visits": 0, "visitors": 0, "bounce_w": 0.0, "depth_w": 0.0})
for r in rows("source_month.json"):
    d = dims_of(r)
    if not in_window(d.get("date", {}).get("name")):
        continue
    key = d.get("traffic-source", {}).get("id", "?")
    m = r.get("metrics") or [0, 0, 0, 0]
    a = src[key]
    a["visits"] += int(m[VISITS] or 0)
    a["visitors"] += int(m[USERS] or 0)
    a["bounce_w"] += float(m[2] or 0) * float(m[VISITS] or 0)
    a["depth_w"] += float(m[3] or 0) * float(m[VISITS] or 0)
tot_src = sum(v["visits"] for v in src.values()) or 1
wcsv("traffic_by_source.csv",
     ["source", "counter", "visits", "visitors", "bounce_rate", "depth", "share_pct"],
     [[SRC_LABEL.get(k, k), SITE_COUNTER, v["visits"], v["visitors"],
       round(v["bounce_w"] / v["visits"], 4) if v["visits"] else 0,
       round(v["depth_w"] / v["visits"], 3) if v["visits"] else 0,
       round(v["visits"] / tot_src * 100, 2)]
      for k, v in sorted(src.items(), key=lambda x: -x[1]["visits"])])

# ---------- посещаемость по дням и месяцам ----------
daily = defaultdict(lambda: {"visits": 0, "visitors": 0, "views": 0,
                             "bounce_w": 0.0, "depth_w": 0.0, "time_w": 0.0})
for r in rows("month_total.json"):
    d = dims_of(r).get("date", {}).get("name")
    if not in_window(d):
        continue
    m = r.get("metrics") or [0] * 6
    a = daily[d]
    a["visits"] += int(m[VISITS] or 0)
    a["visitors"] += int(m[USERS] or 0)
    a["views"] += int(m[2] or 0)
    a["bounce_w"] += float(m[3] or 0) * float(m[VISITS] or 0)
    a["depth_w"] += float(m[4] or 0) * float(m[VISITS] or 0)
    a["time_w"] += float(m[5] or 0) * float(m[VISITS] or 0)
d_out = [[d, a["visits"], a["visitors"], a["views"],
          round(a["bounce_w"] / a["visits"], 4) if a["visits"] else 0,
          round(a["depth_w"] / a["visits"], 3) if a["visits"] else 0,
          round(a["time_w"] / a["visits"]) if a["visits"] else 0]
         for d, a in sorted(daily.items())]
wcsv("attendance_daily.csv",
     ["date", "counter", "visits", "visitors", "pageviews",
      "bounce_rate", "depth", "avg_time_sec"], d_out)

mon = defaultdict(lambda: {"visits": 0, "visitors": 0, "views": 0, "days": 0,
                           "bounce_w": 0.0, "depth_w": 0.0, "time_w": 0.0})
for row in d_out:
    m = mon[row[0][:7]]
    m["visits"] += row[1]
    m["visitors"] += row[2]
    m["views"] += row[3]
    m["days"] += 1
    m["bounce_w"] += row[4] * row[1]
    m["depth_w"] += row[5] * row[1]
    m["time_w"] += row[6] * row[1]
wcsv("attendance_monthly.csv",
     ["month", "counter", "visits", "visitors", "pageviews", "days",
      "bounce_rate", "depth", "avg_time_sec"],
     [[k, SITE_COUNTER, v["visits"], v["visitors"], v["views"], v["days"],
       round(v["bounce_w"] / v["visits"], 4) if v["visits"] else 0,
       round(v["depth_w"] / v["visits"], 3) if v["visits"] else 0,
       round(v["time_w"] / v["visits"]) if v["visits"] else 0]
      for k, v in sorted(mon.items())])

# ---------- поисковые запросы ----------
# Измерение фразы приходит без icon_type и без id, а у части строк имя
# вообще null: это те запросы, где панель не отдала текст. Такие строки
# пропускаем, иначе в сумме будет 134 визита из ниоткуда.
q = defaultdict(lambda: {"visits": 0, "users": 0})
skipped = 0
for r in rows("phrase_month.json"):
    d = r.get("dimensions") or []
    date = next((x.get("name") for x in d
                 if re.match(r"^\d{4}-\d{2}-\d{2}$", x.get("name") or "")), "")
    if not in_window(date):
        continue
    phrase = next((x.get("name") for x in d
                   if x.get("name") and not re.match(r"^\d{4}-\d{2}-\d{2}$", x["name"])), "")
    if not phrase:
        skipped += 1
        continue
    m = list(r.get("metrics") or [])
    a = q[phrase]
    a["visits"] += int(m[VISITS] if len(m) > VISITS else 0)
    a["users"] += int(m[USERS] if len(m) > USERS else 0)
q_out = sorted([[k, SITE_COUNTER, v["visits"], v["users"]]
                for k, v in q.items()], key=lambda x: -x[2])
wcsv("search_queries_top.csv", ["query", "counter", "visits", "visitors"], q_out)
if skipped:
    print("  пропущено строк без текста запроса: %d" % skipped)

# ---------- регионы и устройства ----------
# Эти срезы приходят уже суммарными за окно запроса, без измерения даты.
# Фильтр по дате тут не применяется: он отсёк бы всё и дал тихий ноль.
def aggregate(name, label, out_label=None):
    agg = defaultdict(int)
    for r in rows(name):
        dims = r.get("dimensions") or []
        key = next((x.get("name") for x in dims if x.get("name")), None)
        if not key:
            continue
        agg[key] += int((r.get("metrics") or [0])[VISITS] or 0)
    wcsv("%s.csv" % label, [out_label or label, "counter", "visits"],
         [[k, SITE_COUNTER, v] for k, v in sorted(agg.items(), key=lambda x: -x[1])])


aggregate("regions.json", "regions", "region")
aggregate("cities.json", "cities", "city")
aggregate("devices.json", "devices", "device")

# ---------- сводка ----------
visits = sum(v["visits"] for v in src.values())
search = src.get("organic", {}).get("visits", 0)
summary = {
    "counter": COUNTER,
    "kind": "yandex_metrica_site",
    "source": "API Reporting, срез %s" % DAY,
    "window": "%s..%s" % (DATE_FROM, DATE_TO),
    "visits_total": visits,
    "visitors_total": sum(v["visitors"] for v in src.values()),
    "search_visits": search,
    "search_share_pct": round(search / visits * 100, 1) if visits else 0,
    "sources": len(src),
    "attendance_days": len(d_out),
    "search_queries": len(q_out),
    "bounce_rate": round(sum(r[4] * r[1] for r in d_out) / visits, 4) if visits else 0,
    "page_depth": round(sum(r[5] * r[1] for r in d_out) / visits, 3) if visits else 0,
    "pageviews": sum(r[3] for r in d_out),
}
with open(os.path.join(OUT, "metrika_summary.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

with open(os.path.join(OUT, "PROVENANCE.md"), "w", encoding="utf-8") as f:
    f.write("""# Происхождение файлов в exports/

Счётчик: `%s` (сайт)
Источник: API Reporting Метрики, срез `%s`, окно `%s..%s`
Собран скриптом: `scripts/export/build_metrika_site_exports.py`

Данные карточки в Яндекс Картах лежат отдельно, в `exports/maps_card/`,
потому что у них другой счётчик (`%s`) и другие числа: 79 002 визита
против 21 110 у сайта. Смешивать их нельзя, и раньше они были смешаны.

Проверка счётчика стоит в трёх местах: здесь при сборке, в
`build_site_data.py` при чтении и в `validate_report.py` при деплое.
""" % (COUNTER, DAY, DATE_FROM, DATE_TO, MAPS_COUNTER))

print("summary:", json.dumps(summary, ensure_ascii=False))
print("DONE")
