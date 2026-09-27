#!/usr/bin/env python3
"""Yandex Webmaster API Export (v4).

Токен читается из корневого .env (YANDEX_OAUTH_TOKEN, запасной YW_API_KEY).
Host определяется автоматически (первый с 'cifra' в ID, иначе первый).
Токены и секреты никогда не печатаются.

Запуск из корня проекта:
  python scripts/export/yw_api_export.py
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
TOKEN = ENV.get("YANDEX_OAUTH_TOKEN", "") or os.getenv("YW_API_KEY", "")


def api(path, params=None):
    r = requests.get(BASE_URL + path,
                     headers={"Authorization": "OAuth " + TOKEN},
                     params=params or {}, timeout=60)
    r.raise_for_status()
    return r.json()


SITE_MARKS = ("cifra", "xn--18-6kc5a3bxam", "цифра")


def discover_host():
    me = api("/user")
    uid = me["user_id"]
    hosts = api("/user/%s/hosts" % uid).get("hosts", [])
    if not hosts:
        raise RuntimeError("В Вебмастере нет сайтов на этом аккаунте")
    for h in hosts:
        blob = (h.get("host_id", "") + h.get("ascii_host_url", "")).lower()
        if any(m in blob for m in SITE_MARKS):
            print("host: %s (verified=%s)" % (h["host_id"], h.get("verified")))
            return uid, h["host_id"]
    verified = [h for h in hosts if h.get("verified")]
    pool = verified or hosts
    h = pool[0]
    print("Сайт cifra не найден, беру первый подтверждённый: %s" %
          (h.get("ascii_host_url") or h.get("host_id")))
    return uid, h["host_id"]


def main():
    if not TOKEN:
        print("Нет токена. Сначала: yandex_oauth.py auth-url -> exchange.")
        return 2
    uid, host = discover_host()
    print("host: %s" % host)
    base = "/user/%s/hosts/%s" % (uid, host)
    out = Path(ROOT) / "data" / "exports" / "yandex_webmaster" / DATE2
    out.mkdir(parents=True, exist_ok=True)

    # Нюанс API: indexing/events без дат отдают полную историю (с датами — пусто),
    # search-queries/* отдают тексты, но indicators всегда пустые (нужен beta-инструмент
    # pro/serp/queries/download, см. yw_serp_export.py). Внешние ссылки требуют
    # права webmaster:hostinfo, поэтому их отсутствие не считаем ошибкой.
    jobs = [
        ("summary", base + "/summary", None),
        ("sqi_history", base + "/sqi-history", None),
        ("queries_popular", base + "/search-queries/popular",
         {"order_by": "TOTAL_CLICKS", "limit": 500}),
        ("indexing_history", base + "/indexing/history", None),
        ("insearch_history", base + "/search-urls/in-search/history",
         {"date_from": DATE1, "date_to": DATE2}),
        ("events_history", base + "/search-urls/events/history", None),
        ("sitemaps", base + "/sitemaps", None),
        ("diagnostics", base + "/diagnostics", None),
        ("recrawl_quota", base + "/recrawl/quota", None),
        ("important_urls", base + "/important-urls", None),
        ("indexing_samples", base + "/indexing/samples", None),
        ("insearch_samples", base + "/search-urls/in-search/samples", None),
        ("events_samples", base + "/search-urls/events/samples", None),
        ("external_links_history", base + "/links/external/history",
         {"indicator": "LINKS_TOTAL_COUNT"}),
    ]
    # Эти эндпоинты недоступны на текущем API/правах, но проверка нужна:
    # если Яндекс их включит, выгрузка подхватится сама.
    soft = {"external_links_history"}
    failed = 0
    for name, path, params in jobs:
        try:
            data = api(path, params)
            with open(out / (name + ".json"), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=1)
            print("ok: %s" % name)
        except requests.HTTPError as e:
            code = e.response.status_code if e.response is not None else "?"
            body = e.response.text[:200] if e.response is not None else "?"
            if name in soft:
                print("нет прав: %s (HTTP %s) — %s" % (name, code, body))
            else:
                print("ОШИБКА %s: HTTP %s — %s" % (name, code, body))
                failed += 1
        except RuntimeError as e:
            print("ОШИБКА: %s" % e)
            return 1
    print("Готово: %s (%d ошибок)" % (out, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
