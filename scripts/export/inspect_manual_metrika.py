"""Разобрать ручные выгрузки Метрики и показать, что в них на самом деле.

Задача не в том, чтобы посчитать метрики, а в том, чтобы установить
истину о самих файлах до того, как из них что-нибудь построят:

* какой период покрывает каждый файл,
* сходится ли итог с суммой строк,
* все ли файлы про один и тот же счётчик и период,
* нет ли среди них файлов, которые вовсе не CSV, а выгрузка страницы.

Последний пункт важнее прочих. Яндекс отдаёт кнопкой экспорта CSV,
но рядом лежит возможность скопировать таблицу из браузера. Такой
файл выглядит как данные, а содержит вёрстку. Если это не поймать,
числа из него попадут в отчёт.
"""

import csv
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"C:\susa ai\2026 cifra audit"
MANUAL = os.path.join(ROOT, "data", "manual", "metrika")

# Признаки файла, который на самом деле выгрузка страницы.
HTMLISH = ("link href", "chart-legend-table", "text-overflow",
           "numeric-cell", "goals-list-item", "ellipsis-expandable",
           "data-page-type")


def read_text(path):
    """Прочитать файл, угадав кодировку.

    Экспорт из Метрики приходит в UTF-8, но если его пересохранили
    в Excel, где угодно может оказаться cp1251 или utf-8 с BOM.
    Порядок проб отражает то, как такие файлы получаются на практике.
    """
    raw = open(path, "rb").read()
    if raw[:3] == b"\xef\xbb\xbf":
        return raw.decode("utf-8-sig"), "utf-8-sig"
    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        pass
    try:
        return raw.decode("cp1251"), "cp1251"
    except UnicodeDecodeError:
        return raw.decode("utf-8", "replace"), "utf-8 с заменой"


def sniff(lines):
    """Отгадать разделитель по первой строке с данными."""
    for line in lines[:4]:
        for sep in (";", "\t", ","):
            if line.count(sep) >= 2:
                return sep
    return ";"


def num(text):
    """Число из строки Метрики.

    Разделители дробной части бывают и запятой, и точкой, между ними
    бывают пробелы и неразрывные пробелы, проценты приходят с символом.
    Молча превращать ноль в ноль нельзя: вернулось None, значит число
    не разобралось и это надо видеть.
    """
    if text is None:
        return None
    s = str(text).strip().replace("\u00a0", "").replace("\u202f", "")
    s = s.replace(" ", "")
    if not s or s in ("-", "—", "н/д"):
        return None
    pct = s.endswith("%")
    s = s.rstrip("%").replace(",", ".")
    try:
        val = float(s)
    except ValueError:
        return None
    return val / 100.0 if pct else val


def parse(path):
    """Разобрать файл в словарь: признаки, колонки, строки."""
    txt, enc = read_text(path)
    lines = [l for l in txt.splitlines() if l.strip()]
    info = {"name": os.path.basename(path), "encoding": enc,
            "bytes": len(txt), "lines": len(lines), "htmlish": False,
            "kind": None, "header": None, "rows": [], "total_row": None,
            "cols": []}
    if not lines:
        info["kind"] = "пустой"
        return info

    head = lines[0]
    hit = [m for m in HTMLISH if m in head]
    if hit:
        info["htmlish"] = True
        info["kind"] = "ВЫГРУЗКА СТРАНИЦЫ, НЕ CSV"
        info["header"] = head[:120]
        return info

    sep = sniff(lines)
    rows = list(csv.reader(io.StringIO(txt), delimiter=sep))
    rows = [r for r in rows if any(c.strip() for c in r)]
    if not rows:
        info["kind"] = "пустой"
        return info
    info["header"] = rows[0]
    info["cols"] = rows[0]
    body = rows[1:]
    for r in body:
        if r and r[0].strip() in ("Итого и средние", "Итого", "Всего"):
            info["total_row"] = r
        else:
            info["rows"].append(r)
    return info


def kind_of(info):
    """Назвать файл по колонкам, а не по имени.

    Имя файла задаёт человек, колонки задаёт Яндекс. Разбираться надо
    по колонкам: одно и то же имя может прийти с другим содержимым.
    """
    if info["htmlish"]:
        return "страница"
    cols = [c.strip() for c in info["cols"]]
    joined = " | ".join(cols)
    if "Интервал дат визита" in joined:
        return "посещаемость по дням"
    if "Источник трафика" in cols and "Тип площадки" in cols:
        return "источники трафика"
    if "Поисковая фраза" in cols:
        return "поисковые фразы"
    if "Страна" in cols and "Город" in cols:
        return "география"
    if "Тип устройства" in cols:
        return "устройства"
    if "Страница входа" in cols:
        return "страницы входа"
    if "Категория интересов, ур. 1" in cols:
        return "долгосрочные интересы"
    if "Время на сайте" in cols[:1]:
        return "распределение времени на сайте"
    if "Глубина просмотра" in cols[:1]:
        return "распределение глубины просмотра"
    if "Робот" in cols[:1]:
        return "роботы"
    if "text-overflow" in cols[:1] or "numeric-cell__value" in cols[:1]:
        return "демография"
    return "не опознан"


def find_col(cols, *needles):
    for n, c in enumerate(cols):
        for needle in needles:
            if needle in c.strip():
                return n
    return None


def main():
    if not os.path.isdir(MANUAL):
        print("Папки ручных выгрузок нет: %s" % MANUAL)
        return 1

    periods = sorted(d for d in os.listdir(MANUAL)
                     if os.path.isdir(os.path.join(MANUAL, d)))
    print("Периодов: %d, последний: %s"
          % (len(periods), periods[-1] if periods else "-"))
    print()

    for per in periods:
        pdir = os.path.join(MANUAL, per)
        print("=" * 76)
        print("ПЕРИОД КАТАЛОГА: %s" % per)
        print("=" * 76)
        infos = []
        for f in sorted(os.listdir(pdir)):
            if not f.lower().endswith(".csv"):
                continue
            info = parse(os.path.join(pdir, f))
            info["kind"] = kind_of(info)
            infos.append(info)

        # Сводка по итогам, главное расхождение.
        print()
        print("%-46s %-30s %10s" % ("вид отчёта", "файл", "итог визитов"))
        print("-" * 90)
        totals = {}
        for i in infos:
            if i["htmlish"]:
                print("%-46s %-30s %10s"
                      % ("СТРАНИЦА, НЕ ДАННЫЕ", i["name"][:30], "-"))
                continue
            cols = [c.strip() for c in i["cols"]]
            vi = find_col(cols, "Визиты")
            total = None
            if i["total_row"] and vi is not None and vi < len(i["total_row"]):
                total = num(i["total_row"][vi])
            s = "%.0f" % total if total is not None else "нет итога"
            print("%-46s %-30s %10s" % (i["kind"], i["name"][:30], s))
            if total is not None:
                totals[i["kind"]] = total
        print()

        # Сколько файлов с одним и тем же итогом: они про один срез.
        uniq = {}
        for k, v in totals.items():
            uniq.setdefault(v, []).append(k)
        print("ИТОГИ, СГРУППИРОВАННЫЕ ПО ЗНАЧЕНИЮ")
        for v, ks in sorted(uniq.items(), reverse=True):
            print("  %10.0f  %s" % (v, ", ".join(ks)))
        print()

        # Диапазон дат в посещаемости, это единственный файл с датами.
        for i in infos:
            if i["kind"] != "посещаемость по дням":
                continue
            dates = []
            for r in i["rows"]:
                if re.match(r"^\d{4}-\d{2}-\d{2}", r[0].strip()):
                    dates.append(r[0].strip())
            if dates:
                dates.sort()
                print("ПОСЕЩАЕМОСТЬ: даты от %s до %s, строк с датой %d"
                      % (dates[0], dates[-1], len(dates)))
                months = {}
                for d in dates:
                    months[d[:7]] = months.get(d[:7], 0) + 1
                print("  по месяцам: %s"
                      % ", ".join("%s %d дн." % (k, v)
                                  for k, v in sorted(months.items())))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())