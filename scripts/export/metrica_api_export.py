#!/usr/bin/env python3
"""Metrica API Export — Reporting API + Management API.

Токен читается из корневого .env (YANDEX_OAUTH_TOKEN).
Токены и секреты никогда не печатаются.

Запуск из корня проекта:
  python scripts/export/metrica_api_export.py
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

REPORTING_URL = "https://api-metrika.yandex.net/stat/v1/data.json"
MGMT_URL = "https://api-metrika.yandex.net/management/v1"


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


ENV = load_env()
TOKEN = ENV.get("YANDEX_OAUTH_TOKEN", "") or os.getenv("METRIKA_API_TOKEN", "")
COUNTER = ENV.get("METRIKA_COUNTER_ID", "50863157") or "50863157"

DATE2 = datetime.now().strftime("%Y-%m-%d")
DATE1 = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")


def report(metrics, dimensions, date1=DATE1, date2=DATE2, limit=10000, extra=None):
    params = {
        "ids": COUNTER,
        "metrics": metrics,
        "dimensions": dimensions,
        "date1": date1,
        "date2": date2,
        "limit": limit,
    }
    if extra:
        params.update(extra)
    r = requests.get(REPORTING_URL,
                     headers={"Authorization": "OAuth " + TOKEN},
                     params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def mgmt(path):
    r = requests.get(MGMT_URL + path,
                     headers={"Authorization": "OAuth " + TOKEN}, timeout=30)
    r.raise_for_status()
    return r.json()


def export_sources_summary():
    """Источники трафика за 12 месяцев (день)."""
    return report(
        "ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:pageDepth,"
        "ym:s:avgVisitDurationSeconds",
        "ym:s:date,ym:s:lastTrafficSource", extra={"group": "day"})


def export_search_queries():
    """Поисковые запросы: движок x фраза."""
    return report(
        "ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:pageDepth",
        "ym:s:searchEngine,ym:s:searchPhrase", limit=5000)


def export_landing_pages():
    """Страницы входа."""
    return report(
        "ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:pageDepth,"
        "ym:s:avgVisitDurationSeconds",
        "ym:s:startURL", limit=5000)


def export_goals():
    """Конфигурация целей счётчика."""
    return mgmt("/counter/%s/goals" % COUNTER)


def export_ecommerce():
    """E-commerce: заказы и выручка по дням (если dataLayer шлёт)."""
    return report(
        "ym:s:ecommercePurchases,ym:s:ecommerceRevenue",
        "ym:s:date", extra={"group": "day"})


def main():
    if not TOKEN:
        print("Нет токена. Сначала: yandex_oauth.py auth-url -> exchange.")
        return 2
    # NOTE 2026-09-27: каталог data/exports/metrika повреждён на уровне ФС
    # (фантомная запись: видна в листинге, недоступна). Пишем в metrika_api/.
    out = Path(ROOT) / "data" / "exports" / "metrika_api" / DATE2
    out.mkdir(parents=True, exist_ok=True)

    jobs = [
        ("sources_summary", export_sources_summary),
        ("search_queries", export_search_queries),
        ("landing_pages", export_landing_pages),
        ("goals", export_goals),
        ("ecommerce", export_ecommerce),
    ]
    failed = 0
    for name, fn in jobs:
        try:
            data = fn()
            with open(out / (name + ".json"), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=1)
            n = len(data.get("data", data) if isinstance(data, dict) else data)
            print("ok: %s (%s строк)" % (name, n))
        except requests.HTTPError as e:
            body = e.response.text[:300] if e.response is not None else "?"
            print("ОШИБКА %s: HTTP %s — %s" % (name, e, body))
            failed += 1
    print("Готово: %s (%d ошибок)" % (out, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
