#!/usr/bin/env python3
"""Полный разбор выгрузок Яндекс.Метрики, вики-аналитика и экспорты.

Читает metrika/*.csv, считает агрегаты и пишет:
  brain/wiki/metrika_analytics/exports/*.csv + metrika_summary.json

ОСТОРОЖНО, счётчик. Ручная выгрузка из панели Метрики не несёт
идентификатора счётчика: скачал ты карточку в Яндекс Картах или сайт,
видно только по цифрам. Именно так здесь и получилось: файлы в metrika/
оказались выгрузкой карточки (79 002 визита, поиск 2,7%), а назывались и
лежали так, будто это сайт. Дальше эти числа уехали в site-data.js как
«визиты сайта», и ошибка была не видна, потому что никто не сверял их с
отчётом.

Поэтому скрипт требует явного объявления счётчика в metrika/COUNTER и
отказывается работать, если там счётчик карточки. Правильный источник
для сайта — API-срез в data/exports/metrica/<дата>/cuts, где счётчик
записан в _index.json. Смотри site_cuts_from_api в build_site_data.py.

Кросс-анализ с Вебмастером: поисковые фразы Метрики и позиции Вебмастера.
Строка 'Итого и средние' из деталей исключается (идёт в summary отдельно).

Запуск из корня проекта: python scripts/export/build_metrika_data.py
"""
import csv
import hashlib
import json
import os
import re
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
META = os.path.join(ROOT, "metrika")
EXPORTS = os.path.join(ROOT, "brain", "wiki", "metrika_analytics", "exports")

ENV = {}
if os.path.isfile(os.path.join(ROOT, ".env")):
    for _ln in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
        _ln = _ln.strip()
        if _ln and not _ln.startswith("#") and "=" in _ln:
            _k, _v = _ln.split("=", 1)
            ENV[_k.strip()] = _v.strip()
SITE_COUNTER = ENV.get("METRIKA_COUNTER_ID", "50863157")
MAPS_COUNTER = ENV.get("METRIKA_MAPS_COUNTER_ID", "59102713")

# Откуда взяты файлы в metrika/. У ручной выгрузки из панели нет
# идентификатора счётчика: скачал ты карточку в Яндекс Картах или сайт,
# видно только по цифрам. Именно так здесь и получилось: файлы в metrika/
# оказались выгрузкой карточки (79 002 визита, поиск 2,7%), а назывались
# и лежали так, будто это сайт. Дальше эти числа уехали в site-data.js
# как «визиты сайта», и ошибка была не видна, потому что никто не
# сверял их с отчётом.
#
# Поэтому счётчик объявляется явно, а выгрузка карточки кладётся в
# отдельную папку. Общее имя файла плюс чужие числа это ловушка, и
# проверка на счётчик в validate_report.py её теперь ловит.
DECLARED = os.path.join(META, "COUNTER")
if not os.path.isfile(DECLARED):
    raise SystemExit(
        "нет metrika/COUNTER.\n"
        "Укажи, с какого счётчика выгрузка: сайт или карточка в Картах.\n"
        "  echo %s > metrika/COUNTER   (или %s для карточки)\n"
        "Без этого нельзя знать, чьи это числа, а перепутать счётчики уже\n"
        "приходилось: сайт %s, карточка %s."
        % (SITE_COUNTER, MAPS_COUNTER, SITE_COUNTER, MAPS_COUNTER))
source_counter = open(DECLARED, encoding="utf-8").read().strip()
IS_MAPS = source_counter == MAPS_COUNTER
OUT = os.path.join(EXPORTS, "maps_card") if IS_MAPS else EXPORTS
os.makedirs(OUT, exist_ok=True)
print("источник: счётчик %s (%s) -> %s"
      % (source_counter,
         "карточка в Яндекс Картах" if IS_MAPS else
         ("сайт" if source_counter == SITE_COUNTER else "НЕИЗВЕСТНЫЙ"),
         os.path.relpath(OUT, ROOT)))

F_SRC = "Источники, сводка-2023-01-12-2026-09-23.csv"
F_Q = "Поисковые запросы-2023-01-12-2026-09-23.csv"
F_ATT = "Посещаемость-2023-01-12-2026-09-23.csv"
F_E1 = "Страницы входа-2023-01-12-2026-09-23.csv"
F_E2 = "Страницы входа-2023-01-12-2026-09-23 (1).csv"


def read_csv(name):
    with open(os.path.join(META, name), "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fnum(v, default=0.0):
    try:
        return float((v or "").strip() or default)
    except (ValueError, AttributeError):
        return default


def inum(v, default=0):
    return int(fnum(v, default))


def tsec(v):
    m = re.match(r"(\d+):(\d\d):(\d\d)", (v or "").strip())
    if not m:
        return 0
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))


def wcsv(name, header, rows):
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print("written %s (%d rows)" % (name, len(rows)))


# ---------- 0. дедупликация файлов входа ----------
def fhash(name):
    h = hashlib.md5()
    with open(os.path.join(META, name), "rb") as f:
        h.update(f.read())
    return h.hexdigest()


same = fhash(F_E1) == fhash(F_E2)
# Файлы — один и тот же отчёт, скачанный дважды (различаются 3 строки:
# округления метрик + время). Берём один, чтобы не двоить визиты.
entry_files = [F_E1]
print("entry files: %s (второй файл — повторное скачивание, пропущен; "
      "идентичны: %s)" % (entry_files, "да" if same else "нет (3 строки расходятся)"))

# ---------- 1. источники ----------
src_rows = [r for r in read_csv(F_SRC) if r["Источник трафика"] != "Итого и средние"]
src_total = {"visits": sum(inum(r["Визиты"]) for r in src_rows),
             "visitors": sum(inum(r["Посетители"]) for r in src_rows)}
src_agg = defaultdict(lambda: {"visits": 0, "visitors": 0, "bounce_w": 0.0, "depth_w": 0.0})
for r in src_rows:
    a = src_agg[r["Источник трафика"]]
    v = inum(r["Визиты"])
    a["visits"] += v
    a["visitors"] += inum(r["Посетители"])
    a["bounce_w"] += fnum(r["Отказы"]) * v
    a["depth_w"] += fnum(r["Глубина просмотра"]) * v
src_out = sorted(
    [[k, v["visits"], v["visitors"],
      round(v["bounce_w"] / v["visits"], 4) if v["visits"] else 0,
      round(v["depth_w"] / v["visits"], 3) if v["visits"] else 0,
      round(v["visits"] / src_total["visits"] * 100, 2)]
     for k, v in src_agg.items()],
    key=lambda x: -x[1])
wcsv("traffic_by_source.csv",
     ["source", "visits", "visitors", "bounce_rate", "depth", "share_pct"], src_out)

# ---------- 2. посещаемость ----------
att = [r for r in read_csv(F_ATT) if r["Интервал дат визита"] != "Итого и средние"]
att_out = [[r["Интервал дат визита"], inum(r["Визиты"]), inum(r["Посетители"]),
            inum(r["Просмотры"]), round(fnum(r["Доля новых посетителей"]), 4),
            round(fnum(r["Отказы"]), 4), round(fnum(r["Глубина просмотра"]), 3),
            tsec(r["Время на сайте"])] for r in att]
att_out.sort()
wcsv("attendance_daily.csv",
     ["date", "visits", "visitors", "pageviews", "new_share", "bounce_rate",
      "depth", "time_sec"], att_out)

mon = defaultdict(lambda: {"visits": 0, "visitors": 0, "views": 0, "days": 0,
                            "bounce_w": 0.0, "depth_w": 0.0, "time_w": 0})
for d in att_out:
    m = mon[d[0][:7]]
    m["visits"] += d[1]
    m["visitors"] += d[2]
    m["views"] += d[3]
    m["days"] += 1
    m["bounce_w"] += d[5] * d[1]
    m["depth_w"] += d[6] * d[1]
    m["time_w"] += d[7] * d[1]
mon_out = [[k, v["visits"], v["visitors"], v["views"], v["days"],
            round(v["bounce_w"] / v["visits"], 4) if v["visits"] else 0,
            round(v["depth_w"] / v["visits"], 3) if v["visits"] else 0,
            round(v["time_w"] / v["visits"]) if v["visits"] else 0]
           for k, v in sorted(mon.items())]
wcsv("attendance_monthly.csv",
     ["month", "visits", "visitors", "pageviews", "days",
      "bounce_rate", "depth", "avg_time_sec"], mon_out)

# ---------- 3. поисковые запросы ----------
qrows = [r for r in read_csv(F_Q) if r["Поисковая фраза"] != "Итого и средние"]
q_out = [[r["Поисковая фраза"], r["Поисковая система"], inum(r["Визиты"]),
          inum(r["Посетители"]), round(fnum(r["Отказы"]), 4),
          round(fnum(r["Глубина просмотра"]), 3), tsec(r["Время на сайте"])]
         for r in qrows]
q_out.sort(key=lambda x: -x[2])
wcsv("search_queries_top.csv",
     ["query", "engine", "visits", "visitors", "bounce_rate", "depth",
      "time_sec"], q_out)

eng = defaultdict(lambda: {"visits": 0, "queries": 0})
for q in q_out:
    e = eng[q[1]]
    e["visits"] += q[2]
    e["queries"] += 1
wcsv("search_by_engine.csv", ["engine", "visits", "queries"],
     sorted([[k, v["visits"], v["queries"]] for k, v in eng.items()],
            key=lambda x: -x[1]))

BRAND = ["цифра", "cifra", "циффра", "цыфра"]
def is_brand(q):
    ql = q.lower()
    return any(b in ql for b in BRAND)
brand_v = sum(q[2] for q in q_out if is_brand(q[0]))
total_qv = sum(q[2] for q in q_out)
print("search: queries=%d visits=%d brand_share=%.1f%%" %
      (len(q_out), total_qv, brand_v / total_qv * 100 if total_qv else 0))

# ---------- 4. страницы входа ----------
erows = []
for fn in entry_files:
    erows += [r for r in read_csv(fn) if r["Страница входа"] != "Итого и средние"]
seen, entry = set(), []
for r in erows:
    if not (r["Страница входа"] or "").strip():
        continue  # строка с пустым URL (79042 визитов) — артефакт выгрузки
    key = (r["Страница входа"], r["Страница входа, ур. 1"])
    if key in seen:
        continue
    seen.add(key)
    entry.append([r["Страница входа"], r["Страница входа, ур. 1"],
                  r["Страница входа, ур. 2"], inum(r["Визиты"]),
                  inum(r["Посетители"]), round(fnum(r["Отказы"]), 4),
                  round(fnum(r["Глубина просмотра"]), 3), tsec(r["Время на сайте"])])
entry.sort(key=lambda x: -x[3])
wcsv("entry_pages_top.csv",
     ["entry_url", "level1", "level2", "visits", "visitors", "bounce_rate",
      "depth", "time_sec"], entry)

def host_of(url):
    m = re.match(r"https?://([^/]+)", (url or "").strip().lower())
    return m.group(1) if m else "(пусто)"

# хост самого глубокого уровня = фактическая страница входа
host_agg = defaultdict(lambda: {"visits": 0, "urls": 0})
for e in entry:
    h = host_of(e[0])
    host_agg[h]["visits"] += e[3]
    host_agg[h]["urls"] += 1
host_out = sorted([[h, v["visits"], v["urls"]] for h, v in host_agg.items()],
                  key=lambda x: -x[1])
wcsv("entry_by_host.csv", ["host", "visits", "urls"], host_out)
for h, v, u in host_out[:12]:
    print("host %s: visits=%d urls=%d" % (h, v, u))

SITE_HOSTS = {"xn--18-6kc5a3bxam.xn--p1ai", "цифра18.рф"}
site_entry = [e for e in entry if host_of(e[0]) in SITE_HOSTS]
site_visits = sum(e[3] for e in site_entry)
ref_visits = sum(e[3] for e in entry) - site_visits
print("entry: urls=%d site_urls=%d site_visits=%d other_visits=%d" %
      (len(entry), len(site_entry), site_visits, ref_visits))

# служебный мусор во входах: админка битрикса
admin_visits = sum(e[3] for e in site_entry if "back_url_admin" in (e[0] or ""))
print("admin entries visits=%d" % admin_visits)

# ---------- 5. кросс с Вебмастером ----------
wm_path = os.path.join(ROOT, "brain", "wiki", "webmaster_analytics",
                       "exports", "all_queries_positions.csv")
wm = {}
if os.path.isfile(wm_path):
    with open(wm_path, "r", encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            wm[r["Query"].strip().lower()] = r
met_by_q = defaultdict(lambda: {"visits": 0, "bounce_w": 0.0})
for q in q_out:
    m = met_by_q[q[0].strip().lower()]
    m["visits"] += q[2]
    m["bounce_w"] += q[4] * q[2]
cross = []
for ql, m in met_by_q.items():
    w = wm.get(ql)
    cross.append([ql, m["visits"],
                  round(m["bounce_w"] / m["visits"], 4) if m["visits"] else 0,
                  w["Avg_Position"] if w else "",
                  w["Shows_Total"] if w else "",
                  w["Clicks_Total"] if w else "",
                  "yes" if w else "no"])
cross.sort(key=lambda x: -x[1])
wcsv("cross_metrika_webmaster.csv",
     ["query", "metrika_visits", "metrika_bounce",
      "wm_avg_position", "wm_shows", "wm_clicks", "in_webmaster"], cross)
matched = sum(1 for c in cross if c[6] == "yes")
print("cross: metrika_queries=%d matched_wm=%d" % (len(cross), matched))

# ---------- 6. summary ----------
summary = {
    "counter": source_counter,
    "kind": "yandex_maps_card" if IS_MAPS else
            ("yandex_metrica_site" if source_counter == SITE_COUNTER else "unknown"),
    "period": "2023-01-12 — 2026-09-23",
    "visits_total": src_total["visits"],
    "visitors_total": src_total["visitors"],
    "sources": len(src_agg),
    "attendance_days": len(att_out),
    "search_queries": len(q_out),
    "search_visits": total_qv,
    "brand_share_pct": round(brand_v / total_qv * 100, 1) if total_qv else 0,
    "entry_urls": len(entry),
    "site_entry_urls": len(site_entry),
    "site_entry_visits": site_visits,
    "other_entry_visits": ref_visits,
    "admin_entry_visits": admin_visits,
    "cross_matched": matched,
}
with open(os.path.join(OUT, "metrika_summary.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

# Счётчик пишется отдельным файлом рядом с CSV. Имя файла не говорит, чьи
# это числа, а счётчик говорит, и читать его проще, чем гадать по имени.
with open(os.path.join(OUT, "PROVENANCE.md"), "w", encoding="utf-8") as f:
    f.write("""# Происхождение файлов в %s

Счётчик: `%s` (%s)
Источник: ручная выгрузка из панели Метрики, папка `metrika/`
Сайт: `%s`, карточка в Яндекс Картах: `%s`

Счётчик сайта: 21 110 визитов за 12 месяцев, поиск 43,0%%
Счётчик карточки: 79 002 визита, поиск 2,7%%

Если числа в этих CSV не сходятся с отчётом клиенту, сначала проверь
счётчик, потом дату. Раньше счётчик не был записан нигде, и выгрузка
карточки лежала под общим именем, из-за чего 79 002 визита карточки
ушли в сайт как «визиты сайта».

Данные сайта собираются отдельно, из API-среза
`data/exports/metrica/<дата>/cuts/`, где счётчик записан в `_index.json`
при выгрузке: `build_metrika_site_exports.py`.
""" % ("exports/maps_card/" if IS_MAPS else "exports/",
       source_counter,
       "карточка в Яндекс Картах" if IS_MAPS else
       ("сайт" if source_counter == SITE_COUNTER else "НЕИЗВЕСТНЫЙ, проверь"),
       SITE_COUNTER, MAPS_COUNTER))
print("summary:", json.dumps(summary, ensure_ascii=False))
print("DONE")
