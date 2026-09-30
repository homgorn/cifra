#!/usr/bin/env python3
"""Дополнительные срезы Метрики: устройства, география, пол, возраст, лояльность,
заголовки страниц, параметры URL, внешние переходы, роботы, сезонность.

Список взят из research/data-needs-deep-research.md (разделы 1.1-1.3).
Скрипт не угадывает: каждый срез отправляется в API, и всё, что вернулось,
складывается в data/exports/metrica/<дата>/cuts/. Несуществующие измерения
Яндекс отклоняет с 400, они просто не попадут в отчёт.

Запуск из корня проекта:
  python scripts/export/metrica_cuts_export.py
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

DATE2 = datetime.now().strftime("%Y-%m-%d")
DATE_FULL = "2023-01-12"          # жизнь счётчика
DATE_YEAR = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
DATE_2Y = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")

V = "ym:s:visits"
U = "ym:s:users"
PV = "ym:s:pageviews"
BR = "ym:s:bounceRate"
DEPTH = "ym:s:pageDepth"
DUR = "ym:s:avgVisitDurationSeconds"


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
TOKEN = ENV.get("YANDEX_OAUTH_TOKEN", "")
COUNTER = ENV.get("METRIKA_COUNTER_ID", "50863157")
MAPS_COUNTER = ENV.get("METRIKA_MAPS_COUNTER_ID", "59102713")

# (имя, размерности, метрики, период, group)
# Имена измерений проверены пробами 2026-09-27: в этой версии API нет
# ym:s:dateMonth, ym:s:visitType, ym:s:pageTitle, ym:s:os, ym:s:screenSize,
# ym:s:queryParams, ym:s:URLPathFull и ym:s:visitors (есть ym:s:users).
# Месяцы берутся через group=month по ym:s:date, а не отдельным измерением.
CUTS = [
    ("devices", ["ym:s:deviceCategory"], [V, U, BR, DEPTH], DATE_FULL, None),
    ("browsers", ["ym:s:browser"], [V, U], DATE_YEAR, None),
    ("countries", ["ym:s:regionCountry"], [V, U], DATE_YEAR, None),
    ("regions", ["ym:s:region"], [V, U], DATE_YEAR, None),
    ("cities", ["ym:s:regionCity"], [V, U], DATE_YEAR, None),
    ("gender", ["ym:s:gender"], [V, U], DATE_YEAR, None),
    ("age", ["ym:s:age"], [V, U], DATE_YEAR, None),
    ("interests", ["ym:s:interest"], [V, U], DATE_YEAR, None),
    ("robots", ["ym:s:isRobot"], [V, U, PV], DATE_FULL, None),
    ("external_refs", ["ym:s:referer"], [V, U], DATE_YEAR, None),
    ("source_month", ["ym:s:date", "ym:s:lastTrafficSource"], [V, U, BR, DUR], DATE_FULL, "month"),
    ("device_source", ["ym:s:deviceCategory", "ym:s:lastTrafficSource"], [V], DATE_YEAR, None),
    ("phrase_month", ["ym:s:date", "ym:s:searchPhrase"], [V], DATE_2Y, "month"),
    ("month_total", ["ym:s:date"], [V, U, PV, BR, DEPTH, DUR], DATE_FULL, "month"),
]

# Карточка в Яндекс Картах: свой набор, без e-commerce и без целей сайта.
MAPS_CUTS = [
    ("month_total", ["ym:s:date"], [V, U, PV, BR, DEPTH, DUR], DATE_FULL, "month"),
    ("entries", ["ym:s:startURL"], [V, U], DATE_YEAR, None),
    ("sources", ["ym:s:lastTrafficSource"], [V, U], DATE_YEAR, None),
    # Действия в карточке: переход на сайт, клик на позвонить, маршрут,
    # переход в мессенджеры. Это те самые звонки и маршруты, которых не было
    # в отчёте: в API они лежат в счётчике карточки, а не сайта.
    ("actions", ["ym:s:goal"], [V, U], DATE_YEAR, None),
    ("cities", ["ym:s:regionCity"], [V, U], DATE_YEAR, None),
    ("search", ["ym:s:searchPhrase"], [V], DATE_YEAR, None),
    ("devices", ["ym:s:deviceCategory"], [V, U], DATE_FULL, None),
    ("source_month", ["ym:s:date", "ym:s:lastTrafficSource"], [V, U], DATE_FULL, "month"),
]


def report(dimensions, metrics, date1, group=None, limit=10000, counter=None):
    params = {
        "ids": counter or COUNTER,
        "dimensions": ",".join(dimensions) if dimensions else None,
        "metrics": ",".join(metrics),
        "date1": date1,
        "date2": DATE2,
        "limit": limit,
    }
    if group:
        params["group"] = group
    params = {k: v for k, v in params.items() if v is not None}
    r = requests.get(REPORTING_URL, headers={"Authorization": "OAuth " + TOKEN},
                     params=params, timeout=120)
    r.raise_for_status()
    return r.json()


def preflight(counter):
    """Проверяет доступ к данным счётчика до того, как что-то создаётся.

    Зачем. Раньше скрипт создавал папку среза, писал в неё _index.json
    с пустым списком успешных и возвращал ноль, то есть рапортовал об
    успехе при полностью провалившейся выгрузке. Дальше facts.py берёт
    самую свежую папку по дате, то есть подхватывала именно её, и все
    цифры Метрики в отчёте становились нулевыми без единого сообщения.

    Карточка счётчика при этом открывается кому угодно, а данные
    принадлежат владельцу, поэтому проверять надо именно данные, и
    одним запросом за один день.
    """
    params = {"counters": counter, "fields": "visits",
              "date_from": DATE2, "date_to": DATE2}
    try:
        r = requests.get(REPORTING_URL, headers={"Authorization": "OAuth " + TOKEN},
                         params=params, timeout=30)
    except Exception as e:
        print("Проверка доступа к счётчику %s не прошла: %s" % (counter, e))
        return False
    if r.status_code == 200:
        return True
    print()
    print("ОТКАЗ: к данным счётчика %s нет доступа (HTTP %s)." % (counter, r.status_code))
    print("Ничего не записано, предыдущие выгрузки не тронуты.")
    print()
    if r.status_code == 403:
        print("Токен выдан не под тем аккаунтом, которому принадлежит счётчик,")
        print("либо доступ к счётчику этому приложению ещё не выдан.")
        print("Проверить: python scripts\\export\\yandex_oauth.py test")
    print()
    return False


def main():
    if not TOKEN:
        print("Нет токена. Сначала: yandex_setup.bat")
        return 2
    for cid, label in ((COUNTER, "сайта"), (MAPS_COUNTER, "карточки в Картах")):
        if not preflight(cid):
            print("Счётчик %s (%s) недоступен, выгрузка остановлена." % (cid, label))
            return 3
    root = Path(ROOT) / "data" / "exports" / "metrica" / DATE2
    base = root / "cuts"
    base.mkdir(parents=True, exist_ok=True)
    maps_dir = root / "cuts_maps"
    maps_dir.mkdir(parents=True, exist_ok=True)
    print("счётчик сайта %s, окно %s ... %s" % (COUNTER, DATE_FULL, DATE2))
    ok, fail = [], []
    for name, dims, metrics, date1, group in CUTS:
        limit = 60000 if name == "phrase_month" else 10000
        try:
            data = report(dims, metrics, date1, group, limit=limit)
        except requests.HTTPError as e:
            body = e.response.text[:140] if e.response is not None else "?"
            print("  %-15s FAIL HTTP %s %s" % (name, e.response.status_code, body))
            fail.append(name)
            continue
        rows = data.get("data", [])
        with open(base / (name + ".json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        print("  %-15s ok rows=%d" % (name, len(rows)))
        ok.append(name)
    with open(base / "_index.json", "w", encoding="utf-8") as f:
        json.dump({"counter": COUNTER, "ok": ok, "failed": fail,
                   "date_full_from": DATE_FULL, "date_to": DATE2}, f, ensure_ascii=False, indent=1)

    # Второй счётчик: карточка в Яндекс Картах. Это отдельный канал, а не сайт,
    # поэтому его срезы лежат рядом и никогда не смешиваются с данными сайта.
    print("\nсчётчик карточки в Картах %s" % MAPS_COUNTER)
    maps_ok, maps_fail = [], []
    for name, dims, metrics, date1, group in MAPS_CUTS:
        try:
            data = report(dims, metrics, date1, group, counter=MAPS_COUNTER)
        except requests.HTTPError as e:
            print("  %-15s FAIL HTTP %s" % (name, e.response.status_code))
            maps_fail.append(name)
            continue
        rows = data.get("data", [])
        with open(maps_dir / (name + ".json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        print("  %-15s ok rows=%d" % (name, len(rows)))
        maps_ok.append(name)
    with open(maps_dir / "_index.json", "w", encoding="utf-8") as f:
        json.dump({"counter": MAPS_COUNTER, "kind": "yandex_maps_card",
                   "ok": maps_ok, "failed": maps_fail,
                   "date_full_from": DATE_FULL, "date_to": DATE2}, f, ensure_ascii=False, indent=1)

    print("\nСайт: %d срезов, %d отклонено. Карточка: %d срезов, %d отклонено."
          % (len(ok), len(fail), len(maps_ok), len(maps_fail)))
    if fail:
        print("Отклонены (сайт): %s" % ", ".join(fail))
    if maps_fail:
        print("Отклонены (карточка): %s" % ", ".join(maps_fail))
    # Ноль при отказанных срезах раньше означал «успех», и следующий
    # скрипт в цепочке строил отчёт по заведомо неполным данным. Теперь
    # отказ виден и в коде возврата, и в сообщении.
    if not ok and not maps_ok:
        print("\nНи один срез не получен. Код возврата 4.")
        return 4
    if fail or maps_fail:
        print("\nЧасть срезов отклонена, код возврата 5.")
        return 5
    return 0


if __name__ == "__main__":
    sys.exit(main())
