#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Скачивает фотографии товаров для одного лендинга.

Зачем отдельный скрипт, а не второй проход по всему каталогу:
  ночной обход каталога умер на 180-й странице из 457, и второй полный проход
  сейчас недоступен. Для первого лендинга, квартальные календари, весь нужный
  раздел уже лежит в raw/. Значит достаточно взять из out/catalog.json позиции
  нужного подраздела и забрать по одной главной фотографии на позицию.

Задержка 3 секунды из robots.txt, как и в основном скрапере.

Запуск из корня проекта:
  python landings/_scrape/fetch_images.py --section kalendari --out landings/kvartalnyy-kalendar-2027/assets
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
BASE = "https://xn--18-6kc5a3bxam.xn--p1ai"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
DELAY = 3.0
TIMEOUT = 45


def safe_name(url: str, prefix: str, index: int) -> str:
    """Имя файла из URL. Префикс позиции обязателен.

    Названия фотографий на сайте кириллические и между позициями повторяются:
    vyrubka.jpg есть у нескольких календарей, и без префикса они бы
    перетирали друг друга. Разбор расширения идёт ДО чистки имени, иначе
    остаётся хвост вида «имя-.jpg» с двумя точками.
    """
    raw = urllib.parse.urlparse(url).path.rsplit("/", 1)[-1]
    stem, dot, ext = raw.partition(".")
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-.")
    ext = re.sub(r"[^A-Za-z0-9]+", "", ext) or "jpg"
    stem = stem or f"img-{index}"
    return f"{prefix}__{stem}.{ext}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Фотографии товаров для одного лендинга.")
    ap.add_argument("--section", required=True,
                    help="подраздел каталога, например kalendari (подкатегория в URL)")
    ap.add_argument("--out", required=True, help="папка назначения")
    ap.add_argument("--all", action="store_true",
                    help="брать все фотографии позиции, а не только главную")
    ap.add_argument("--timeout", type=int, default=20,
                    help="таймаут запроса, по умолчанию 20 секунд")
    args = ap.parse_args()

    catalog = OUT / "catalog.json"
    if not catalog.exists():
        print("Нет out/catalog.json. Сначала: python landings/_scrape/fetch_catalog.py --parse-only")
        return 1

    items = json.loads(catalog.read_text(encoding="utf-8"))
    picked = [i for i in items
              if i.get("subsection") == args.section and i.get("photos")]
    if not picked:
        print(f"По подразделу {args.section} позиций с фото не найдено.")
        return 1

    dest = Path(args.out)
    dest.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9"})

    total = 0
    failed: list[str] = []
    for n, item in enumerate(picked, 1):
        photos = item["photos"] if args.all else item["photos"][:1]
        slug = re.sub(r"[^a-z0-9]+", "-", item["url"].rstrip("/").rsplit("/", 1)[-1]).strip("-")
        for k, photo in enumerate(photos):
            target = dest / safe_name(photo, slug, k)
            if target.exists() and target.stat().st_size > 2000:
                print(f"  есть {target.name}", flush=True)
                total += 1
                continue
            ok = False
            for attempt in (1, 2):
                try:
                    r = session.get(photo, timeout=args.timeout)
                    if r.status_code != 200:
                        print(f"  ! код {r.status_code} на {photo}", flush=True)
                        break
                    target.write_bytes(r.content)
                    total += 1
                    ok = True
                    print(f"  [{n}/{len(picked)}] {target.name}  {len(r.content)//1024} КБ", flush=True)
                    break
                except Exception as e:
                    print(f"  ! попытка {attempt}: {type(e).__name__} на {photo}", flush=True)
                    time.sleep(5)
            if not ok:
                failed.append(f"{slug}: {photo}")
            time.sleep(DELAY)

    print(f"Готово. Файлов на диске: {total}. Папка: {dest}")
    if failed:
        print(f"Не скачано: {len(failed)}. Повторный запуск докачает, уже скачанные пропускаются.")
        for f in failed:
            print(f"  - {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
