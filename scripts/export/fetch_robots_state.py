#!/usr/bin/env python3
"""Живая проверка robots.txt и карт сайта.

Зачем. В отчёте стояло «23 ссылки в robots.txt отдают 404», и это число
вело первую задачу фазы 0. Проверка живьём показала 19 строк Sitemap, и
отдают 404 все 19, то есть проблема реальна, а число было неверным.

Число из отчёта брать нельзя: robots.txt меняется на стороне клиента, и
через месяц оно снова разойдётся. Поэтому оно проверяется и кладётся в
выгрузку с датой, а тексты берут его оттуда.

Пишет:
  data/exports/yandex_webmaster/<дата>/robots_state.json

Запуск из корня проекта:
  python scripts/export/fetch_robots_state.py
"""
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PREFIX = "https://xn--18-6kc5a3bxam.xn--p1ai"
UA = {"User-Agent": "Mozilla/5.0 (compatible; audit/1.0)"}
TIMEOUT = 20


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.status, r.read().decode("utf-8", "replace")


def status_of(url):
    try:
        return fetch(url)[0]
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        return type(e).__name__


def main():
    day = os.path.join(ROOT, "data", "exports", "yandex_webmaster", date.today().isoformat())
    try:
        # Каталог может быть не создан, если сегодняшнего среза ещё нет.
        os.makedirs(day, exist_ok=True)
        robots_code, body = fetch(PREFIX + "/robots.txt")
    except Exception as e:
        print("robots.txt недоступен: %s" % e)
        return 1

    lines = [l.strip() for l in body.split("\n") if l.strip()]
    sitemaps = [l.split(":", 1)[1].strip() for l in lines
                if l.lower().startswith("sitemap:")]
    disallow = [l.split(":", 1)[1].strip() for l in lines
                if l.lower().startswith("disallow")]
    user_agents = [l.split(":", 1)[1].strip() for l in lines
                   if l.lower().startswith("user-agent")]

    checked = []
    for u in sitemaps:
        checked.append({"url": u, "code": status_of(u)})
    dead = [c for c in checked if c["code"] == 404]

    out = {
        "checked_at": date.today().isoformat(),
        "robots_code": robots_code,
        "robots_bytes": len(body),
        "sitemap_lines": len(sitemaps),
        "sitemap_404": len(dead),
        "sitemap_other": len(checked) - len(dead),
        "sitemaps": checked,
        "disallow_count": len([d for d in disallow if d]),
        "disallow_rules": [d for d in disallow if d],
        "user_agents": user_agents,
        "allow_all": any(l.lower().startswith("allow: /") for l in lines),
    }
    path = os.path.join(day, "robots_state.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("robots.txt: HTTP %s, %d б, строк Sitemap %d, Disallow %d"
          % (robots_code, len(body), len(sitemaps), out["disallow_count"]))
    print("карт проверено: %d, отдают 404: %d" % (len(checked), len(dead)))
    for c in checked:
        if c["code"] != 404:
            print("  не 404: %s -> %s" % (c["code"], c["url"]))
    print("written %s" % os.path.relpath(path, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
