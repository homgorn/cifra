#!/usr/bin/env python3
"""Расширенная выгрузка поисковых запросов по URL из API Вебмастера (beta).

Зачем: обычные `search-queries/*` на этом аккаунте отдают тексты запросов, но
`indicators` всегда пустые, то есть показов, кликов, CTR и позиций нет. Beta-инструмент
`pro/serp/queries/download` отдаёт полную таблицу: дата, хост, URL, запрос, регион,
клики, показы, позиция. Это единственный способ закрыть анализ сниппетов через API.

Лимиты (базовый доступ): 100 URL-дней в сутки, не больше 100 элементов суммарно
в датах и путях, глубина истории 550 дней. Выгрузка считается офлайн 20 минут — 2 часа,
ссылка на файл живёт 24 часа, поэтому task_id сохраняется и выгрузка разбирается
отдельным вызовом.

  python scripts/export/yw_serp_export.py init      создать задачу
  python scripts/export/yw_serp_export.py status    проверить и скачать, если готово
  python scripts/export/yw_serp_export.py limits    квоты и доступные даты
"""
import csv
import gzip
import io
import json
import os
import sys
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(ROOT, ".env")
BASE_URL = "https://api.webmaster.yandex.net/v4"
DATE2 = datetime.now().strftime("%Y-%m-%d")
OUT = Path(ROOT) / "data" / "exports" / "yandex_webmaster" / DATE2 / "serp_queries"
STATE = OUT / "task_state.json"

# Дни подряд: 5 последних доступных дат. Меняйте здесь, если нужен другой срез.
DAYS_BACK = 5
# Сколько URL-дней тратить за раз (базовый доступ = 100 в сутки).
BUDGET = 100


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
SITE_MARKS = ("cifra", "xn--18-6kc5a3bxam", "цифра")


def discover():
    r = requests.get(BASE_URL + "/user", headers={"Authorization": "OAuth " + TOKEN}, timeout=60)
    r.raise_for_status()
    uid = r.json()["user_id"]
    hosts = requests.get(BASE_URL + "/user/%s/hosts" % uid,
                         headers={"Authorization": "OAuth " + TOKEN}, timeout=60).json().get("hosts", [])
    for h in hosts:
        blob = (h.get("host_id", "") + h.get("ascii_host_url", "")).lower()
        if any(m in blob for m in SITE_MARKS):
            return uid, h["host_id"]
    return uid, hosts[0]["host_id"]


def hdr(extra=None):
    h = {"Authorization": "OAuth " + TOKEN, "Accept": "application/json"}
    if extra:
        h.update(extra)
    return h


def money_paths(limit):
    """Ключевые пути по данным панели: структура сайта, отсортированная по
    числу страниц в поиске. Одна страница = один URL в выгрузке, поэтому
    первыми идут разделы, которые реально видны в выдаче."""
    parsed = json.load(open(os.path.join(ROOT, "webmaster", "parsed_data.json"), encoding="utf-8"))
    rows = []
    for r in parsed.get("structure", []):
        raw = (r.get("g-link") or "").strip()
        if not raw:
            continue
        path = raw.split("://")[-1]
        path = "/" + path.split("/", 1)[1] if "/" in path else "/"
        if not path.startswith("/"):
            continue
        try:
            searchable = int(str(r.get("g-link 3") or "0").replace(" ", ""))
        except ValueError:
            searchable = 0
        indexed = r.get("g-link 2") or "0"
        rows.append((searchable, path, indexed))
    rows.sort(reverse=True)
    out, seen = [], set()
    for searchable, path, indexed in rows:
        if path in seen:
            continue
        seen.add(path)
        out.append(path)
        if len(out) >= limit:
            break
    return out


def cmd_limits():
    uid, host = discover()
    base = "/user/%s/hosts/%s" % (uid, host)
    for name, path in (("limits", base + "/pro/limits"),
                       ("dates", base + "/pro/serp/dates")):
        r = requests.get(BASE_URL + path, headers=hdr(), timeout=60)
        print("\n[%s] HTTP %d" % (name, r.status_code))
        if r.ok:
            d = r.json()
            s = json.dumps(d, ensure_ascii=False)
            print(s[:900])
        else:
            print(r.text[:300])
    return 0


def cmd_init():
    uid, host = discover()
    base = "/user/%s/hosts/%s" % (uid, host)
    dates_r = requests.get(BASE_URL + base + "/pro/serp/dates", headers=hdr(), timeout=60)
    available = dates_r.json().get("dates", []) if dates_r.ok else []
    if not available:
        print("API не отдал доступные даты, fallback на последние дни")
        available = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, DAYS_BACK + 1)]
    dates = available[-DAYS_BACK:]
    n_paths = max(1, BUDGET // max(1, len(dates)))
    paths = money_paths(n_paths)
    print("дат: %s" % ", ".join(dates))
    print("URL: %d" % len(paths))
    for p in paths:
        print("  %s" % p)
    body = {"dates": dates, "paths": paths, "region_ids": [], "use_pro_tariff": "false"}
    r = requests.post(BASE_URL + base + "/pro/serp/queries/download/",
                      headers=hdr({"Content-Type": "application/json"}),
                      data=json.dumps(body), timeout=90)
    print("\nHTTP %d" % r.status_code)
    if not r.ok:
        print(r.text[:500])
        return 1
    d = r.json()
    OUT.mkdir(parents=True, exist_ok=True)
    state = {"task_id": d["task_id"], "created": datetime.now().isoformat(timespec="seconds"),
             "dates": dates, "paths": paths,
             "free_quota_remaining": d.get("free_quota_remaining")}
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
    print("task_id: %s" % d["task_id"])
    print("квота: использовано %s, осталось %s" %
          (d.get("total_quota_used"), d.get("free_quota_remaining")))
    print("состояние: %s" % STATE)
    print("Дальше: python scripts/export/yw_serp_export.py status (через 20 мин — 2 ч)")
    return 0


def cmd_status():
    if not STATE.exists():
        print("Задачи нет. Сначала: python scripts/export/yw_serp_export.py init")
        return 2
    state = json.load(open(STATE, encoding="utf-8"))
    uid, host = discover()
    url = "%s/user/%s/hosts/%s/pro/serp/queries/download/%s" % (
        BASE_URL, uid, host, state["task_id"])
    r = requests.get(url, headers=hdr(), timeout=60)
    r.raise_for_status()
    d = r.json()
    status = d.get("download_status")
    print("статус: %s" % status)
    if status != "SUCCESS":
        if d.get("error_message"):
            print("ошибка: %s (%s)" % (d["error_message"], d.get("error_code")))
        else:
            print("Задача ещё считается. Проверьте позже.")
        return 1
    file_url = d["url"]
    print("качаю отчёт...")
    blob = requests.get(file_url, headers={"User-Agent": "curl/8"}, timeout=300).content
    OUT.mkdir(parents=True, exist_ok=True)
    raw = OUT / ("serp_raw_%s.bin" % datetime.now().strftime("%Y%m%d_%H%M"))
    raw.write_bytes(blob)
    rows = []
    if blob[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            for nm in z.namelist():
                if nm.lower().endswith(".csv"):
                    with z.open(nm) as f:
                        rows.extend(csv.reader(io.TextIOWrapper(f, encoding="utf-8-sig")))
    elif blob[:2] == b"\x1f\x8b":
        # Яндекс отдаёт gzip, не zip
        text = gzip.decompress(blob).decode("utf-8-sig", errors="replace")
        delim = "\t" if text.count("\t") > text.count(",") else ","
        rows = list(csv.reader(io.StringIO(text), delimiter=delim))
    else:
        text = blob.decode("utf-8-sig", errors="replace")
        delim = "\t" if text.count("\t") > text.count(",") else ","
        rows = list(csv.reader(io.StringIO(text), delimiter=delim))
    if not rows:
        print("отчёт пустой, raw сохранён: %s" % raw)
        return 1
    header = rows[0]
    out_csv = OUT / "serp_queries_raw.csv"
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows[1:])
    print("строк: %d" % (len(rows) - 1))
    print("колонки: %s" % header)
    print("сохранено: %s" % out_csv)
    return 0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "status"
    fn = {"init": cmd_init, "status": cmd_status, "limits": cmd_limits}.get(mode)
    if not fn:
        print("Режимы: init, status, limits")
        sys.exit(2)
    sys.exit(fn())
