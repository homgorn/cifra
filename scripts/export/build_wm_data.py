#!/usr/bin/env python3
"""Build js/wm-data.js for the cifra18 audit report site from webmaster exports.

Reads brain/wiki/webmaster_analytics/exports/*.csv and writes
reports/cifra18-audit/js/wm-data.js as `const WM = {...};`
All numbers on the wm-* pages and charts come from this file.
"""
import csv
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXP = os.path.join(ROOT, "brain", "wiki", "webmaster_analytics", "exports")
OUT = os.path.join(ROOT, "reports", "cifra18-audit", "js", "wm-data.js")


def read_csv(name):
    path = os.path.join(EXP, name)
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def count_rows(name):
    return len(read_csv(name))


# --- 1. Page statuses (one export file per status) ---
status_files = {
    "SEARCHABLE": "searchable_pages.csv",
    "DUPLICATE": "duplicate_pages.csv",
    "PARSE_ERROR": "parse_error_pages.csv",
    "REDIRECT_NOTSEARCHABLE": "redirect_pages.csv",
    "OTHER": "other_pages.csv",
    "BAD_QUALITY": "bad_quality_pages.csv",
    "HTTP_ERROR": "http_error_pages.csv",
}
statuses = {k: count_rows(v) for k, v in status_files.items()}
total_pages = sum(statuses.values())

# --- 2. Sections ---
sections = []
for r in read_csv("site_structure.csv"):
    try:
        sections.append({
            "section": r["Section"],
            "indexed": int(r["Indexed"]),
            "downloaded": int(r["Downloaded"]),
            "searchable": int(r["Searchable"]),
            "rate": float(r["Indexation_Rate_%"]),
        })
    except (ValueError, KeyError):
        continue
sections_by_indexed = sorted(
    [s for s in sections if not s["section"].startswith("http")],
    key=lambda s: s["indexed"], reverse=True)[:8]

# --- 3. Queries (positions + shows + clicks + CTR) ---
queries = []
for r in read_csv("all_queries_positions.csv"):
    try:
        queries.append({
            "q": r["Query"],
            "avg": float(r["Avg_Position"]),
            "mn": float(r["Min_Position"]),
            "mx": float(r["Max_Position"]),
            "days": int(r["Days_With_Data"]),
            "shows": int(r["Shows_Total"]),
            "clicks": int(r["Clicks_Total"]),
            "ctr": float(r["CTR_%"]),
            "detail": r["Positions_Detail"],
        })
    except (ValueError, KeyError):
        continue

DAYS = ["2026-09-14", "2026-09-15", "2026-09-16", "2026-09-17",
        "2026-09-18", "2026-09-19", "2026-09-20"]
shows_daily = {d: 0 for d in DAYS}
clicks_daily = {d: 0 for d in DAYS}
for r in read_csv("query_shows_daily.csv"):
    for d in DAYS:
        try:
            shows_daily[d] += int(r[d] or 0)
        except (ValueError, KeyError):
            pass
for r in read_csv("query_clicks_daily.csv"):
    for d in DAYS:
        try:
            clicks_daily[d] += int(r[d] or 0)
        except (ValueError, KeyError):
            pass

bins = {"1": 0, "1-3": 0, "3-5": 0, "5-10": 0, "10-20": 0, "20+": 0}
for q in queries:
    a = q["avg"]
    if a <= 1.0:
        bins["1"] += 1
    elif a <= 3.0:
        bins["1-3"] += 1
    elif a <= 5.0:
        bins["3-5"] += 1
    elif a <= 10.0:
        bins["5-10"] += 1
    elif a <= 20.0:
        bins["10-20"] += 1
    else:
        bins["20+"] += 1
top1 = bins["1"]
top3 = bins["1"] + bins["1-3"]
top10 = top3 + bins["3-5"] + bins["5-10"]

by_q = {q["q"]: q for q in queries}
MONEY = ["визитки ижевск", "печать визиток ижевск", "типография ижевск",
         "типография цифра", "печать визиток", "ксерокопия ижевск",
         "печатный салон ижевск", "пакеты на заказ", "печать на пакетах ижевск",
         "цифра ижевск", "полиграфия ижевск", "пресс волл"]
money = [dict(by_q[k], q=k) for k in MONEY if k in by_q][:10]

trend = []
for m in money[:6]:
    series = {d: None for d in DAYS}
    for part in (m["detail"] or "").split(";"):
        part = part.strip()
        if ":" in part:
            d, v = part.split(":", 1)
            d = d.strip()
            if d in series:
                try:
                    series[d] = float(v)
                except ValueError:
                    pass
    trend.append({"q": m["q"], "series": [series[d] for d in DAYS]})

def classify_pattern(url):
    u = url or ""
    if u.startswith("https://xn--18-6kc5a3bxam.xn--p1ai/"):
        u = u[len("https://xn--18-6kc5a3bxam.xn--p1ai/") - 1:]
    import re
    if re.match(r"^/\d+\.html", u):
        return "numericHtml"
    if "detail.php" in u:
        return "detailPhp"
    if "/shop/" in u:
        return "shop"
    return "other"


def pattern_counts(rows):
    from collections import Counter
    c = Counter(classify_pattern(r.get("URL", "")) for r in rows)
    return {"numericHtml": c.get("numericHtml", 0), "detailPhp": c.get("detailPhp", 0),
            "shop": c.get("shop", 0), "other": c.get("other", 0)}


dupPatterns = pattern_counts(read_csv("duplicate_pages.csv"))
parsePatterns = pattern_counts(read_csv("parse_error_pages.csv"))

events_add = 0
events_delete = 0
for r in read_csv("indexing_events.csv"):
    if r.get("Event") == "ADD":
        events_add += 1
    elif r.get("Event") == "DELETE":
        events_delete += 1

# --- 4. Gaps ---
gaps = []
for r in read_csv("content_gaps_prioritized.csv"):
    try:
        gaps.append({
            "query": r["Query"],
            "pos": float(r["Avg_Position"]),
            "cluster": r["Cluster"],
            "kind": r["Missing_Page_Type"],
            "url": r["Suggested_URL"],
            "effort": r["Effort"],
            "impact": r["Impact"],
        })
    except (ValueError, KeyError):
        continue

# --- 5. Internal links ---
link_status = {r["Status"]: int(r["Count"]) for r in read_csv("internal_links_by_status.csv")}
link_total = sum(link_status.values())
link_broken = {k: v for k, v in link_status.items() if k in ("404", "500", "502")}


def short_url(u):
    u = (u or "").rstrip("/")
    return "/" + u.split("xn--18-6kc5a3bxam.xn--p1ai/")[-1] if "xn--" in u else u


broken_targets = []
for r in read_csv("internal_links_target_summary.csv")[:8]:
    try:
        broken_targets.append({"url": short_url(r["Target_URL"]),
                               "count": int(r["Broken_Inbound_Count"])})
    except (ValueError, KeyError):
        continue
image_hotlinks = count_rows("internal_links_image_hotlinks.csv")
typos = count_rows("internal_links_typos.csv")

# --- 6. Clusters (from 04_Semantic_Clusters.md metrics table) ---
clusters = [
    {"name": "Визитки", "queries": 35, "avg": 3.8, "top10": 95, "pages": 8, "coverage": 40},
    {"name": "Календари", "queries": 22, "avg": 4.5, "top10": 85, "pages": 10, "coverage": 67},
    {"name": "Кружки и магниты", "queries": 28, "avg": 6.2, "top10": 70, "pages": 6, "coverage": 33},
    {"name": "Листовки и флаеры", "queries": 18, "avg": 6.8, "top10": 75, "pages": 5, "coverage": 38},
    {"name": "Широкоформат", "queries": 25, "avg": 6.5, "top10": 65, "pages": 8, "coverage": 44},
    {"name": "Мобильные стенды", "queries": 20, "avg": 7.2, "top10": 60, "pages": 8, "coverage": 40},
    {"name": "Сувенирка и мерч", "queries": 30, "avg": 8.5, "top10": 50, "pages": 15, "coverage": 33},
    {"name": "Инженерная печать", "queries": 22, "avg": 7.0, "top10": 65, "pages": 12, "coverage": 65},
]

# --- 7. ICE top actions (from 10_Priority_Matrix.md; Yandex-only wording) ---
ice = [
    {"action": "Карта сайта: генерация, путь /sitemap.xml, robots.txt", "score": 9.7},
    {"action": "Canonical глобально + Clean-param", "score": 9.4},
    {"action": "Блокировка /shop/ и *.html (PARSE_ERROR)", "score": 9.3},
    {"action": "Длинные тире заменить запятыми", "score": 8.8},
    {"action": "Подкатегории визиток и широкоформата (6 шт.)", "score": 8.4},
    {"action": "JSON-LD: организация, адрес, хлебные крошки", "score": 8.4},
    {"action": "Локальные лендинги Ижевск (3 шт.)", "score": 8.1},
    {"action": "Уникальные title и meta для страниц в поиске", "score": 8.0},
    {"action": "Метрика + Вебмастер: цели, переобход", "score": 7.7},
    {"action": "IndexNow для мгновенной индексации", "score": 6.9},
]

# --- 8. Forecast ---
forecast = {
    "labels": ["Старт", "1 мес", "2 мес", "3 мес", "6 мес", "12 мес"],
    "searchable": [142, 220, 350, 500, 800, 1100],
}

WM = {
    "meta": {"totalPages": total_pages, "totalQueries": len(queries),
             "linkTotal": link_total, "generated": "2026-09-23"},
    "statuses": statuses,
    "dupPatterns": dupPatterns,
    "parsePatterns": parsePatterns,
    "events": {"add": events_add, "delete": events_delete},
    "sections": sections,
    "sectionsTop": sections_by_indexed,
    "queryBins": bins,
    "queryTops": {"top1": top1, "top3": top3, "top10": top10},
    "money": [{"q": m["q"], "avg": round(m["avg"], 2), "days": m["days"],
               "shows": m["shows"], "clicks": m["clicks"], "ctr": m["ctr"]} for m in money],
    "trendDays": [d[5:] for d in DAYS],
    "trend": trend,
    "showsDaily": [shows_daily[d] for d in DAYS],
    "clicksDaily": [clicks_daily[d] for d in DAYS],
    "gaps": gaps,
    "linkStatus": link_status,
    "linkBroken": link_broken,
    "brokenTargets": broken_targets,
    "imageHotlinks": image_hotlinks,
    "typos": typos,
    "clusters": clusters,
    "ice": ice,
    "forecast": forecast,
}

with open(OUT, "w", encoding="utf-8") as f:
    f.write("/* Generated by scripts/export/build_wm_data.py. Do not edit by hand. */\n")
    f.write("const WM = ")
    json.dump(WM, f, ensure_ascii=False)
    f.write(";\n")

print("Wrote %s" % OUT)
print("pages=%d queries=%d links=%d" % (total_pages, len(queries), link_total))
print("statuses=%s" % (statuses,))
