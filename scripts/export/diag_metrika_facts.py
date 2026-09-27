#!/usr/bin/env python3
"""Ключевые факты из экспортов Метрики для вики."""
import csv
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "brain", "wiki", "metrika_analytics", "exports")


def load(n):
    with open(os.path.join(OUT, n), "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


print("== SOURCES ==")
for r in load("traffic_by_source.csv"):
    print("  %(source)s: visits=%(visits)s share=%(share_pct)s%% bounce=%(bounce_rate)s depth=%(depth)s" % r)

print("== MONTHLY: first 3 / last 6 ==")
mon = load("attendance_monthly.csv")
for r in mon[:3] + mon[-6:]:
    print("  %(month)s: visits=%(visits)s days=%(days)s bounce=%(bounce_rate)s" % r)
peak = max(mon, key=lambda r: int(r["visits"]))
print("  PEAK:", peak["month"], peak["visits"])

print("== SEARCH TOP-20 ==")
for r in load("search_queries_top.csv")[:20]:
    print("  %(visits)s | %(bounce_rate)s | %(depth)s | %(query)s" % r)

print("== ENGINES ==")
for r in load("search_by_engine.csv"):
    print("  ", r)

print("== SITE ENTRY TOP-20 (host цифра18.рф) ==")
n = 0
for r in load("entry_pages_top.csv"):
    if "xn--18-6kc5a3bxam" in r["entry_url"] or "цифра18.рф" in r["entry_url"]:
        n += 1
        if n <= 20:
            print("  %(visits)s | %(bounce_rate)s | %(entry_url)s" % r)

print("== MAPS ENTRIES (yandex maps org urls, top 10) ==")
n = 0
for r in load("entry_pages_top.csv"):
    if "/maps" in r["entry_url"] and "org" in r["entry_url"]:
        n += 1
        if n <= 10:
            print("  %(visits)s | %(entry_url)s" % r)

print("== CROSS: top metrika queries NOT in webmaster (top 15 by visits) ==")
n = 0
for r in load("cross_metrika_webmaster.csv"):
    if r["in_webmaster"] == "no":
        n += 1
        if n <= 15:
            print("  %(metrika_visits)s | %(query)s" % r)

print("== CROSS: top matched (top 15) ==")
n = 0
for r in load("cross_metrika_webmaster.csv"):
    if r["in_webmaster"] == "yes":
        n += 1
        if n <= 15:
            print("  %(metrika_visits)s | pos %(wm_avg_position)s | shows %(wm_shows)s | %(query)s" % r)
