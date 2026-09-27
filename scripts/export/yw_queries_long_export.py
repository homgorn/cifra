#!/usr/bin/env python3
"""Годовая статистика запросов и страниц из API Вебмастера (v4).

Зачем: `queries_popular` в основном экспорте отдаёт неделю, а разбору
сниппетов нужен год (показы, клики, CTR, позиции).

API Вебмастера капризная: часть эндпоинтов отдаёт пустые `indicators` при
любых датах, часть принимает период. Скрипт не гадает, а перебирает варианты
и пишет в лог, что сработало. Всё, что вернуло строки, сохраняется в
data/exports/yandex_webmaster/<дата>/queries_12m/.

Запуск из корня проекта:
  python scripts/export/yw_queries_long_export.py
"""
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(ROOT, ".env")
BASE_URL = "https://api.webmaster.yandex.net/v4"

DATE2 = datetime.now().strftime("%Y-%m-%d")
DATE1 = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
PERIOD = {"date_from": DATE1, "date_to": DATE2}

SITE_MARKS = ("cifra", "xn--18-6kc5a3bxam", "цифра")


def load_env():
    env = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env


TOKEN = load_env().get("YANDEX_OAUTH_TOKEN", "") or os.getenv("YW_API_KEY", "")


def api(path, params=None):
    r = requests.get(BASE_URL + path,
                     headers={"Authorization": "OAuth " + TOKEN},
                     params=params or {}, timeout=60)
    return r


def jget(path, params=None):
    r = api(path, params)
    r.raise_for_status()
    return r.json()


def rows_of(payload):
    """Достаёт строки из разных форм ответа API."""
    if not isinstance(payload, dict):
        return []
    for key in ("queries", "urls", "points", "history", "rows", "data"):
        v = payload.get(key)
        if isinstance(v, list):
            return v
    return []


def has_numbers(rows):
    for row in rows:
        if isinstance(row, dict):
            for k, v in row.items():
                if k.startswith("indicators") or k in ("positions", "clicks", "shows", "ctr", "query_text", "url"):
                    return True
    return bool(rows)


def discover():
    me = jget("/user")
    uid = me["user_id"]
    hosts = jget("/user/%s/hosts" % uid).get("hosts", [])
    for h in hosts:
        blob = (h.get("host_id", "") + h.get("ascii_host_url", "")).lower()
        if any(m in blob for m in SITE_MARKS):
            return uid, h["host_id"]
    return uid, hosts[0]["host_id"]


def save(out, name, payload):
    with open(out / (name + ".json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)


def main():
    if not TOKEN:
        print("Нет токена. Сначала: yandex_setup.bat")
        return 2
    uid, host = discover()
    base = "/user/%s/hosts/%s" % (uid, host)
    out = Path(ROOT) / "data" / "exports" / "yandex_webmaster" / DATE2 / "queries_12m"
    out.mkdir(parents=True, exist_ok=True)
    print("host: %s, period: %s ... %s" % (host, DATE1, DATE2))
    report = []

    def probe(name, path, params):
        """Пробует вызов, печатает результат, сохраняет если есть строки."""
        try:
            data = jget(path, params)
        except requests.HTTPError as e:
            body = e.response.text[:160] if e.response is not None else "?"
            print("  %-34s HTTP %s %s" % (name, e.response.status_code, body))
            report.append((name, "http_%s" % e.response.status_code, 0))
            return None
        rows = rows_of(data)
        n = len(rows)
        state = "ok" if has_numbers(rows) else "empty"
        print("  %-34s %s rows=%d" % (name, state, n))
        report.append((name, state, n))
        if n:
            save(out, name, data)
        return data

    print("\n[1] Популярные запросы, разные окна и сортировки")
    probe("q_popular_click_week", base + "/search-queries/popular",
          {"order_by": "TOTAL_CLICKS", "limit": 500})
    probe("q_popular_click_12m", base + "/search-queries/popular",
          dict(PERIOD, order_by="TOTAL_CLICKS", limit=500))
    probe("q_popular_shows_12m", base + "/search-queries/popular",
          dict(PERIOD, order_by="TOTAL_SHOWS", limit=500))
    probe("q_top_12m", base + "/search-queries/top", dict(PERIOD, limit=500))

    print("\n[2] Популярные страницы")
    probe("u_popular_click_12m", base + "/search-urls/popular",
          dict(PERIOD, order_by="TOTAL_CLICKS", limit=500))
    probe("u_popular_shows_12m", base + "/search-urls/popular",
          dict(PERIOD, order_by="TOTAL_SHOWS", limit=500))
    probe("u_insearch_12m", base + "/search-urls/in-search", dict(PERIOD, limit=500))

    print("\n[3] История по конкретным запросам и URL")
    pop = out / "q_popular_click_12m.json"
    if pop.exists():
        qs = rows_of(json.load(open(pop, encoding="utf-8")))
        print("  беру 5 запросов из годового топа")
        for q in qs[:5]:
            qid = q.get("query_id") or q.get("id")
            if qid:
                probe("q_hist_%s" % qid, base + "/search-queries/%s/history" % qid, None)
                probe("q_pos_%s" % qid, base + "/search-queries/%s/positions" % qid, PERIOD)
    else:
        print("  годового топа нет, историю запросов не проверить")

    upop = out / "u_popular_click_12m.json"
    if upop.exists():
        us = rows_of(json.load(open(upop, encoding="utf-8")))
        print("  беру 5 URL из годового топа")
        for u in us[:5]:
            uid_ = u.get("url_id") or u.get("id")
            if uid_:
                probe("u_hist_%s" % uid_, base + "/search-urls/%s/history" % uid_, None)

    print("\n[4] Прочее")
    probe("q_negative", base + "/search-queries/possible-negative", PERIOD)
    probe("important_urls", base + "/important-urls/history", PERIOD)

    with open(out / "_probe_report.json", "w", encoding="utf-8") as f:
        json.dump({"host": host, "date_from": DATE1, "date_to": DATE2,
                   "probes": report}, f, ensure_ascii=False, indent=1)

    ok = [r for r in report if r[1] == "ok"]
    print("\nГотово: %d/%d вариантов вернули данные. Каталог: %s" %
          (len(ok), len(report), out))
    if len(ok) < 2:
        print("Вывод: годовая статистика запросов через API недоступна,")
        print("нужна ручная выгрузка из панели Вебмастера.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
