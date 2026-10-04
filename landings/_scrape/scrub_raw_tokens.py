#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Убрать сессионные токены клиента из сырой выкачки в landings/_scrape/raw.

Зачем. Выкачка сохраняет HTML страниц сайта заказчика как есть, а в HTML
каждой страницы Битрикс24 лежит `sessid`: идентификатор сессии, по
которому можно действовать от имени посетителя, пока сессия жива. Плюс
внутренний `aid` аналитики. Все три значения одинаковы во всех 457
файлах, то есть токен один на всю выкачку.

Это не абстрактная опасность. Gейт scripts/export/scan_secrets.py нашёл
2283 вхождения в 457 файлах, и папка была в git: 62,7 МБ чужих страниц
с сессией клиента в истории репозитория.

Что делает скрипт. Заменяет 32-символьные hex-токены на плейсхолкер
вида SESSION_TOKEN_REDACTED_n, где n это номер токена в порядке первого
появления. Номер нужен, чтобы разные токены остались разными: если
схлопнуть всё в один плейсхолдер, потеряется информация о том, что
значений было три, и правка перестанет быть проверяемой.

Чего скрипт НЕ делает. Он не чинит историю git. Значения уже в коммитах,
и оттуда их надо убирать git filter-repo с перезаписью истории, а это
необратимая операция с общей веткой, решать должен владелец репозитория.
Скрипт чистит только рабочую копию, чтобы новых попаданий не было.

Запуск из корня проекта:
  python landings/_scrape/scrub_raw_tokens.py            проверить
  python landings/_scrape/scrub_raw_tokens.py --apply    почистить
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"

# Тот же шаблон, что и первый в scripts/export/scan_secrets.py, плюс
# якоря: нужны границы, иначе под правило попадают куски 32-символьных
# имён файлов внутри URL и скрипт заменит половину путей.
TOKEN = re.compile(r"(?<![/\w])([0-9a-f]{32})(?![/\w])")

PLACEHOLDER = "SESSION_TOKEN_REDACTED_{}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true",
                    help="перезаписать файлы. Без этого только отчёт.")
    args = ap.parse_args()

    if not RAW.is_dir():
        print(f"Нет папки {RAW}")
        return 1

    # Порядок номеров задаётся первым появлением во всей выкачке, а не
    # поимённо по файлам. Иначе один и тот же токен в разных файлах
    # получил бы разные номера, и проверка «после чистки токенов нет»
    # перестала бы работать.
    order: dict[str, int] = {}
    for p in sorted(RAW.glob("*.html")):
        body = p.read_text(encoding="utf-8", errors="replace")
        for m in TOKEN.finditer(body):
            order.setdefault(m.group(1), len(order) + 1)

    if not order:
        print("Токенов не найдено, чистить нечего.")
        return 0

    print(f"уникальных токенов: {len(order)}")
    for val, n in order.items():
        # само значение не печатается: отчёт может попасть в чат или в
        # лог, и тогда цель чистки будет достигнута ровно на том самом
        # файле, где осталось проверить, что токена там нет
        print(f"  #{n}  {val[:4]}…{val[-4:]}  ({len(val)} симв.)")

    total = 0
    touched = 0
    for p in sorted(RAW.glob("*.html")):
        body = p.read_text(encoding="utf-8", errors="replace")
        new = TOKEN.sub(lambda m: PLACEHOLDER.format(order[m.group(1)]), body)
        if new != body:
            total += len(TOKEN.findall(body))
            touched += 1
            if args.apply:
                p.write_text(new, encoding="utf-8", newline="")

    verb = "заменено вхождений" if args.apply else "найдено вхождений (не тронуто)"
    print(f"{verb}: {total} в {touched} файлах из {len(list(RAW.glob('*.html')))}")

    if not args.apply:
        print("Это был отчёт. Повторить с --apply, чтобы почистить.")
        return 0

    # Повторная проверка на тех же файлах. Без неё скрипт сообщил бы
    # «сделано» по факту записи, а не по факту отсутствия токенов.
    left = 0
    for p in sorted(RAW.glob("*.html")):
        left += len(TOKEN.findall(p.read_text(encoding="utf-8",
                                              errors="replace")))
    print(f"осталось токенов после чистки: {left}")
    if left:
        print("Чистка неполная, разбираться вручную.")
        return 1

    # Парсер должен продолжать работать на очищенных файлах. Проверяем
    # это здесь, а не после: иначе очистка ломает выкачку, и это
    # обнаружится на следующем запуске _parse_only, то есть поздно.
    sys.path.insert(0, str(ROOT))
    try:
        import fetch_catalog  # noqa: F401
    except Exception as e:  # noqa: BLE001
        print(f"! fetch_catalog не импортируется: {type(e).__name__}: {e}")
        return 1
    print("fetch_catalog импортируется, парсер не сломан.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())