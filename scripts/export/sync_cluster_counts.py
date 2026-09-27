#!/usr/bin/env python3
"""Синхронизирует числа кластеров и импорта в клиентских документах.

Зачем: 2026-09-27 классификатор расширен с 8 групп до 22, а страница
плана на 3 месяца и клиентский отчёт продолжали писать «535 запросов
по 8 группам». На сайте числа берутся из данных, в документах были
зашиты руками, и они разошлись.

Скрипт читает факты из данных и правит документы, а не наоборот.
Проверка `--check` ничего не пишет и возвращает код 1, если расхождение
есть: так расхождение видно в гейте, а не в чтении.

Запуск из корня проекта:
  python scripts/export/sync_cluster_counts.py --check
  python scripts/export/sync_cluster_counts.py
"""
import argparse
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WM_DATA = os.path.join(ROOT, "reports", "cifra18-audit", "js", "wm-data.js")
IMPORT_CSV = os.path.join(ROOT, "topvisor", "exports", "import_queries.csv")
PLAN = os.path.join(ROOT, "reports", "cifra18-audit", "pages", "plan-3m.html")
REPORT = os.path.join(ROOT, "CLIENT_REPORT.md")

# Что именно и на что заменяем. Порядок важен: сначала длинные формулировки.
# Хвост не добавляем: в исходном тексте он уже есть, иначе получается
# «с целевыми страницами с целевыми страницами».
FIXES = [
    (r"535\s+запросов\s+по\s+8\s+(?:группам|кластерам)",
     "{imp} запросов по {cln}"),
    # Следы прошлого прохода: скрипт уже подставил «22 группы», но с
    # задвоенным хвостом и без склонения. Чиним, чтобы повторный запуск
    # был безопасен на любом состоянии файла.
    (r"(\d+)\s+запросов\s+по\s+\d+\s+группам\s+с\s+целевыми\s+страницами\s+"
     r"с\s+целевыми\s+страницами",
     "{imp} запросов по {cln} с целевыми страницами"),
    (r"\b22\s+групп\s+L1", "{cln} L1"),
    (r"8\s+кластеров\s+L1", "{cln} L1"),
    (r"8\s+коммерческих\s+кластеров", "{cln}"),
    (r"8\s+групп\s+коммерческих", "{cln} коммерческих"),
    (r"\b8\s+(?:групп|кластеров|кластера)\b", "{cln}"),
]


def plural(n, one, few, many):
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def facts():
    d = {}
    t = open(WM_DATA, encoding="utf-8").read()
    wm = json.loads(t[t.index("{"):].rstrip().rstrip(";"))
    d["cl"] = len(wm.get("clusters") or [])
    d["core"] = (wm.get("queryStats") or {}).get("total", 0)
    n = 0
    if os.path.isfile(IMPORT_CSV):
        import csv
        with open(IMPORT_CSV, encoding="utf-8-sig", newline="") as f:
            n = sum(1 for _ in csv.DictReader(f))
    d["imp"] = n
    d["cln"] = "%d %s" % (d["cl"], plural(d["cl"], "группа", "группы", "групп"))
    return d


def patch_text(text, f):
    out = text
    hits = 0
    for pat, rep in FIXES:
        out, k = re.subn(pat, rep.format(**f), out)
        hits += k
    return out, hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="только проверить, ничего не писать")
    args = ap.parse_args()

    f = facts()
    if not f["cl"]:
        print("не удалось прочитать число кластеров из wm-data.js")
        return 2
    print("факты из данных: %s, в ядре %d, к импорту %d"
          % (f["cln"], f["core"], f["imp"]))

    bad = []
    total = 0
    for path in (PLAN, REPORT):
        if not os.path.isfile(path):
            continue
        before = open(path, encoding="utf-8").read()
        after, hits = patch_text(before, f)
        total += hits
        if after == before:
            print("ok    %s совпадает с данными" % os.path.relpath(path, ROOT))
            continue
        if args.check:
            bad.append(os.path.relpath(path, ROOT))
            print("FAIL  %s содержит устаревшее число кластеров"
                  % os.path.relpath(path, ROOT))
            for m in re.finditer(r"[^.]*?\b8\s+(?:групп|кластер\w*)[^.]*\.", after):
                print("       %s" % re.sub(r"\s+", " ", m.group(0)).strip()[:130])
        else:
            open(path, "w", encoding="utf-8").write(after)
            print("прав  %s: заменено вхождений %d"
                  % (os.path.relpath(path, ROOT), hits))

    if args.check and bad:
        print("SYNC FAILED: расхождение в %d файлах" % len(bad))
        return 1
    if args.check:
        print("SYNC OK: числа в документах совпадают с данными")
    else:
        print("готово, заменено вхождений: %d" % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
