#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Покрытие каталога лендингами: какие подразделы не попали ни на одну страницу.

Зачем. Подразделы распределяются по лендингам в спецификации вручную, и
ничто не проверяет, что список не устарел. Пока этого скрипта не было,
девять подразделов из восьмидесяти девяти молча не попадали ни на одну
страницу: «Корпоративные подарки», таблички для оплаты по QR, лекала,
тейбл-тент, мелкие сувениры. Выглядело это как «каталога нет», а не как
«его забыли расписать».

Покрытие считается по фактически использованным позициям, а не по
объявленным подразделам в спецификации. Разница существенная: подраздел
может быть прописан в группе, но не получить ни одной позиции, если
лимит группы меньше числа подразделов. Отбор по кругу это чинит, а
проверка ниже показывает, где ещё не починено.

Запуск из корня проекта:
  python landings/_scrape/coverage_report.py
  python landings/_scrape/coverage_report.py --json
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
LANDINGS = ROOT.parent
CATALOG = ROOT / "out" / "catalog.json"

# Страницы-мусор из выкачки: заголовок «Каталог», ноль фотографий.
JUNK_URL = ("detail.php", "index.php", "list.php")


def is_junk(item: dict) -> bool:
    return item["name"] == "Каталог" or any(m in item["url"] for m in JUNK_URL)


def is_section_page(item: dict) -> bool:
    """Страница самого раздела, а не позиция каталога.

    У каждого раздела есть посадочная страница с названием раздела и
    нольом фотографий: «Полиграфия», «Интерьер», «Мобильные стенды».
    Подраздела у неё нет, поэтому в отчёте она попадала в «(нет)» и
    выглядела как непокрытая позиция. На лендинг такие страницы не
    берутся: это разделы сайта, а не товары.
    """
    if item["subsection"]:
        return False
    # Сравнивать название со слагом раздела бессмысленно: название
    # русское («Интерьер»), а раздел в латинице (`interer`). Признак
    # другой и точный: у страницы раздела нет подраздела и её адрес
    # заканчивается слагом раздела, то есть это корень каталога.
    return item["url"].rstrip("/").endswith("/" + item["section"])


def key_of(item: dict) -> str:
    """Ключ подраздела для отчёта: раздел плюс подраздел.

    Одного подраздела мало. Ключ «(нет)» собирал позиции сразу из семи
    разделов, и в отчёте выглядело так, будто в «Интерьере» семь
    непокрытых позиций, хотя там такая позиция одна и это сама страница
    раздела. Показывать надо адресно: `интерьер: (нет)`.
    """
    sub = item["subsection"] or "(нет)"
    return f"{item['section']} / {sub}"


def collect() -> tuple[list[dict], dict[str, list[dict]]]:
    items = json.loads(CATALOG.read_text(encoding="utf-8"))
    real = [i for i in items if not is_junk(i)]
    by_src: dict[str, list[dict]] = {}
    for i in real:
        if i.get("photos"):
            by_src.setdefault(i["photos"][0], []).append(i)

    used_by: dict[str, list[dict]] = {}
    for folder in sorted(LANDINGS.iterdir()):
        cfg = folder / "config.json"
        if not cfg.is_file():
            continue
        data = json.loads(cfg.read_text(encoding="utf-8"))
        for group in data.get("catalog", {}).get("groups", []):
            for card in group.get("items", []):
                for item in by_src.get(card.get("src"), []):
                    used_by.setdefault(key_of(item), []).append(
                        {"landing": folder.name, "name": item["name"]})
    return real, used_by


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="вывод в JSON")
    args = ap.parse_args()

    if not CATALOG.exists():
        print("Нет out/catalog.json. Сначала fetch_catalog.py --parse-only")
        return 1

    real, used_by = collect()
    real = [i for i in real if not is_section_page(i)]
    counts = collections.Counter(key_of(i) for i in real)
    covered = {k for k in counts if used_by.get(k)}
    missing = sorted((k for k in counts if k not in covered),
                     key=lambda k: -counts[k])

    if args.json:
        print(json.dumps({
            "subsectionsTotal": len(counts),
            "subsectionsCovered": len(covered),
            "missing": {k: counts[k] for k in missing},
            "usedBy": used_by,
        }, ensure_ascii=False, indent=1))
        return 1 if missing else 0

    print(f"подразделов в каталоге: {len(counts)}")
    print(f"покрыто лендингами:     {len(covered)}")
    print(f"не покрыто:             {len(missing)}")
    print()
    if missing:
        print("НЕ ПОКРЫТЫ ЛЕНДИНГАМИ:")
        for sub in missing:
            print(f"  {sub:<56} {counts[sub]:>4}")
        print()
        print("Что делать: распределить эти подразделы в category_specs.json.")
        print("Отдельный лендинг имеет смысл, только если в подразделах")
        print("набирается 12-15 позиций. Четыре позиции собирают пустую")
        print("страницу, и правильнее добавить их в существующий лендинг")
        print("по смыслу, чем заводить новый.")
    else:
        print("Все подразделы каталога попали хотя бы на один лендинг.")
        print("Это не значит, что все позиции показаны: лендинг держит")
        print("15-20 позиций, остальное остаётся на сайте заказчика.")

    print()
    print("Позиций в блоках лендингов:")
    for sub in sorted(used_by, key=lambda k: -len(used_by[k]))[:15]:
        names = sorted({u["landing"] for u in used_by[sub]})
        print(f"  {sub:<44} берётся {len(used_by[sub]):>3}  "
              f"({', '.join(names[:3])})")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())