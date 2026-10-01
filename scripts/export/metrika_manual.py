"""Привести ручные выгрузки Метрики к тому же виду, что и выгрузки API.

Зачем это нужно. Отчёты Метрики по API отдают 403, и единственный
источник данных о посещаемости сейчас это то, что человек выгружает
из интерфейса браузером. Дальше с этим должен работать тот же конвейер,
что и с остальным: факты, отчёт, сайт. Значит ручное и автоматическое
должно лежать рядом и иметь одну форму, иначе придётся держать две
реализации одного и того же.

Три входные формы, все три встречаются на практике:

1. Родной экспорт Яндекса, CSV, заголовки человеческие.
2. Копирование таблицы из браузера в текстовый файл. Данные целые,
   колонки разделены табуляцией или точкой с запятой. Такой файл
   приходит как `.txt`, чтобы не путать с родным экспортом.
3. Выгрузка расширения браузера, где колонки названы классами CSS.
   Данные целые, имена бесполезны, раскладывать по позициям.

Отдельно обрабатывается файл, в котором данных нет вовсе: расширение
иногда отдаёт вёрстку страницы вместо таблицы. Такой файл обязан
остановить сборку. Если разобрать его как пустой, в отчёте появятся
нули, а нули читаются как «трафика не было».

Правила, которые здесь зашиты:

* вид отчёта определяется колонками, а не именем файла: `goals.csv`
  назван верно и данных не содержит, `ages.csv` назван неверно и
  содержит;
* мера берётся по номеру колонки, а не по подстроке в заголовке:
  «Время на сайте» в отчёте по времени встречается дважды, первый
  столбец это срез, второй это среднее;
* период берётся из файла, где есть даты, и наследуется остальными;
* итоги сверяются между файлами, и расхождение останавливает сборку,
  а не печатается как предупреждение;
* колонка, которую не удалось опознать, помечается как неопознанная,
  а не угадывается.

Запуск:

    python scripts/export/metrika_manual.py            разобрать и собрать
    python scripts/export/metrika_manual.py --check    только проверить
"""

import csv
import datetime as dt
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"C:\susa ai\2026 cifra audit"
SRC = os.path.join(ROOT, "data", "manual", "metrika")
OUT = os.path.join(ROOT, "data", "exports", "metrika_manual")

# Допуск при сверке итогов. Метрика округляет по разным причинам и
# даже на одном срезе счётчики расходятся на единицы: география не
# привязывает часть визитов, а интересы считаются по выборке. Единицы
# это норма, десятки и тем более разы нет.
TOLERANCE = 5


# ---------------------------------------------------------------- формат

HTML_MARKERS = ("link href", "chart-legend-table", "goals-list-item",
                "ellipsis-expandable", "data-page-type", "widget__",
                "<td", "<th")


def read_any(path):
    """Прочитать файл, угадав кодировку.

    Родной экспорт приходит в UTF-8. Если файл пересохраняли в Excel,
    где угодно может оказаться cp1251 или BOM. Порядок проб отражает
    то, как файлы получаются на практике, а не перебор на всякий случай.
    """
    raw = open(path, "rb").read()
    if raw[:3] == b"\xef\xbb\xbf":
        return raw.decode("utf-8-sig"), "utf-8-sig"
    for enc in ("utf-8", "cp1251"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace"), "utf-8 с заменой"


def split_table(text):
    """Разделить таблицу на строки и колонки.

    Разделитель определяется по строке заголовка: табуляция важнее
    точки с запятой, потому что точка с запятой встречается внутри
    самих данных, например в списке поисковых фраз.
    """
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return [], [], ""
    head = lines[0]
    counts = {"\t": head.count("\t"),
              ";": head.count(";"),
              ",": head.count(",")}
    sep = max(counts, key=counts.get)
    if counts[sep] == 0:
        sep = ";"
    rows = []
    for r in csv.reader(lines, delimiter=sep):
        r = [c.strip() for c in r]
        if any(c for c in r):
            rows.append(r)
    return rows[0], rows[1:], sep


def is_html_dump(header, body):
    """Файл не таблица, а вёрстка страницы.

    Проверяется и заголовок, и тело: у вёрстки в теле бывают ссылки на
    интерфейс Метрики, у настоящей таблицы не бывает.
    """
    head_txt = " ".join(header) if isinstance(header, (list, tuple)) \
        else str(header)
    joined = head_txt + " " + " ".join(" ".join(r) for r in body[:4])
    if any(m in joined for m in HTML_MARKERS):
        return True
    return any(m in head_txt for m in HTML_MARKERS)


# ------------------------------------------------------------- значения

NBSP = "\u00a0"
NNBSP = "\u202f"


def to_number(text):
    """Число из строки Метрики.

    Дробная часть приходит и точкой, и запятой, между разрядами бывают
    обычные и неразрывные пробелы, проценты с символом процента,
    время приходит как ``00:08:45``. Нераспознанное возвращает None,
    а не ноль: ноль это число, которого не было.
    """
    if text is None:
        return None
    s = str(text).strip().replace(NBSP, "").replace(NNBSP, "")
    s = s.replace(" ", "").replace("\u2009", "")
    if not s or s in ("-", "\u2014", "н/д", "Не определено"):
        return None
    if re.match(r"^\d{2}:\d{2}:\d{2}$", s):
        h, m, sec = (int(x) for x in s.split(":"))
        return h * 3600 + m * 60 + sec
    pct = s.endswith("%")
    s = s.rstrip("%").replace(",", ".")
    try:
        val = float(s)
    except ValueError:
        return None
    return val / 100.0 if pct else val


def human_time(seconds):
    if seconds is None:
        return ""
    return "%02d:%02d:%02d" % (seconds // 3600, (seconds % 3600) // 60,
                                seconds % 60)


# ------------------------------------------------------------- реестр

# dim: сколько ведущих колонок являются измерениями, то есть
#      разрезами отчёта. Всё, что после них, это меры.
# measures: имя меры и номер колонки в строке файла, считая с нуля.
# subset: True, если итог вида заведомо меньше итога периода.
# full: True, если вид обязан дать полный итог периода.
KINDS = {
    "visits_daily": {
        "label": "посещаемость по дням",
        "detect": lambda c: any("интервал дат визита" in x for x in c),
        "dim": 1, "date_col": 0, "full": True,
        "measures": {"visits": 1, "visitors": 2, "views": 3,
                     "new_visitors_share": 4, "bounce_rate": 5,
                     "depth": 6, "time_on_site": 7},
    },
    "sources": {
        "full": True,
        "label": "источники трафика",
        "detect": lambda c: "источник трафика" in c and
                            any("тип площадки" in x for x in c),
        "dim": 3,
        "dims": ["Источник трафика", "Источник трафика (детально)",
                 "Тип площадки"],
        "measures": {"visits": 3, "visitors": 4, "bounce_rate": 5,
                     "depth": 6, "time_on_site": 7},
    },
    "search_phrases": {
        "full": False,
        "label": "поисковые фразы",
        "detect": lambda c: any("поисковая фраза" in x for x in c),
        "dim": 2, "dims": ["Поисковая фраза", "Поисковая система"],
        "measures": {"visits": 2, "visitors": 3, "bounce_rate": 4,
                     "depth": 5, "time_on_site": 6},
    },
    "geo": {
        "subset": True,
        "label": "география",
        "detect": lambda c: any(x.strip() == "страна" for x in c),
        "dim": 3, "dims": ["Страна", "Область", "Город"],
        "measures": {"visits": 3, "visitors": 4, "bounce_rate": 5,
                     "depth": 6, "time_on_site": 7},
        "subset": True,
    },
    "devices": {
        "full": True,
        "label": "устройства",
        "detect": lambda c: any("тип устройства" in x for x in c),
        "dim": 3, "dims": ["Тип устройства", "Производитель устройства",
                           "Модель устройства"],
        "measures": {"visits": 3, "visitors": 4, "bounce_rate": 5,
                     "depth": 6, "time_on_site": 7},
    },
    "entry_pages": {
        "full": True,
        "label": "страницы входа",
        "detect": lambda c: sum(1 for x in c if "страница входа" in x) >= 2,
        "dim": 5,
        "dims": ["Страница входа, ур. 1", "Страница входа, ур. 2",
                 "Страница входа, ур. 3", "Страница входа, ур. 4",
                 "Страница входа"],
        "measures": {"visits": 5, "visitors": 6, "bounce_rate": 7,
                     "depth": 8, "time_on_site": 9},
    },
    "goals": {
        "label": "цели",
        "detect": lambda c: any("цель" in x for x in c) or
                            any("goal" in x for x in c),
        "dim": 1, "dims": ["Цель"],
        "measures": {"visits": 1, "visitors": 2},
    },
    "time_on_site": {
        "full": True,
        "label": "распределение времени на сайте",
        # Первая колонка это срез, а не мера. Искать по подстроке нельзя:
        # «Время на сайте» в этом же файле есть ещё и как среднее.
        "detect": lambda c: bool(c) and "время на сайте" == c[0].strip(),
        "dim": 1, "dims": ["Время на сайте"],
        "measures": {"visits": 1, "visitors": 2, "bounce_rate": 3,
                     "depth": 4, "time_on_site": 5},
    },
    "depth": {
        "full": True,
        "label": "распределение глубины просмотра",
        "detect": lambda c: bool(c) and "глубина просмотра" == c[0].strip(),
        "dim": 1, "dims": ["Глубина просмотра"],
        "measures": {"visits": 1, "visitors": 2, "bounce_rate": 3,
                     "depth": 4, "time_on_site": 5},
    },
    "interests": {
        "subset": True,
        "label": "долгосрочные интересы",
        "detect": lambda c: any("категория интересов" in x for x in c),
        "dim": 3,
        "dims": ["Категория интересов, ур. 1", "Категория интересов, ур. 2",
                 "Категория интересов, ур. 3"],
        "measures": {"visits": 3, "visitors": 4, "affinity": 5,
                     "bounce_rate": 6, "depth": 7, "time_on_site": 8},
        "subset": True,
    },
    "robots": {
        "subset": True,
        "label": "роботы",
        "detect": lambda c: bool(c) and c[0].strip() == "робот",
        "dim": 1, "dims": ["Робот"],
        "measures": {"visits": 1},
        "subset": True,
    },
    # Колонки названы классами CSS, расширение браузера отдаёт так.
    # Данные целые, раскладываются по позициям.
    "ages": {
        "subset": True,
        "label": "возраст",
        "detect": lambda c: bool(c) and "text-overflow" in c[0],
        "dim": 1, "dims": ["Возраст"],
        "measures": {"visits": 1, "visits_share": 2,
                     "visitors": 3, "visitors_share": 4},
        "unmapped": [5, 6, 7, 8, 9],
        "subset": True,
    },
}


def detect_kind(cols):
    """Определить вид отчёта по колонкам.

    Колонки приводятся к строчным буквам здесь, а не в каждой проверке.
    Проверки написаны строчными литералами, а файлы приходят с
    заглавных, и без приведения ни одна не срабатывает.
    """
    cols = [str(c).strip().lower() for c in cols]
    for key, spec in KINDS.items():
        try:
            if spec["detect"](cols):
                return key
        except Exception:                                    # noqa: BLE001
            continue
    return None


# ------------------------------------------------------------- разбор

TOTAL_LABELS = ("итого и средние", "итого", "всего")


def parse_file(path):
    """Разобрать один файл в структуру, пригодную для отчёта."""
    text, enc = read_any(path)
    header, body, sep = split_table(text)
    res = {"file": os.path.basename(path), "encoding": enc, "sep": sep,
           "header": header, "rows": [], "total_row": None,
           "problem": None, "kind": None, "kind_label": "",
           "measures": {}, "dims": [], "unmapped_cols": []}
    if not header:
        res["problem"] = "файл пуст"
        return res
    if is_html_dump(header, body):
        res["problem"] = ("не таблица, а вёрстка страницы: в заголовке "
                          "имена классов CSS вместо названий колонок")
        return res

    key = detect_kind(header)
    if key is None:
        res["problem"] = ("вид отчёта не опознан, заголовки: %s"
                          % " | ".join(header[:6]))
        return res
    spec = KINDS[key]
    res["kind"] = key
    res["kind_label"] = spec["label"]

    dim_names = spec.get("dims") or []
    dim_n = spec["dim"]

    for row in body:
        if row and row[0].strip().lower() in TOTAL_LABELS:
            res["total_row"] = row
            continue
        rec = {}
        for i in range(dim_n):
            rec[dim_names[i] if i < len(dim_names)
                else "измерение %d" % (i + 1)] = \
                row[i] if i < len(row) else ""
        for name, idx in spec["measures"].items():
            rec[name] = to_number(row[idx]) if idx < len(row) else None
        res["rows"].append(rec)

    if res["total_row"]:
        for name, idx in spec["measures"].items():
            res["measures"][name] = (to_number(res["total_row"][idx])
                                     if idx < len(res["total_row"]) else None)
    res["unmapped_cols"] = spec.get("unmapped") or []
    return res


def period_of(parsed):
    """Период из файла, где есть даты, иначе из имени файла.

    Имя файла может врать, имена приходили от человека, а даты в
    колонке ставит Яндекс. Поэтому даты из колонки главнее, а имя
    используется только там, где дат нет вовсе.
    """
    daily = KINDS["visits_daily"]
    if parsed["kind"] == daily.get("kind", "visits_daily") or \
            daily["detect"](parsed["header"]):
        dates = []
        for r in parsed["rows"]:
            key = list(r.keys())[0]
            m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", str(r.get(key, "")).strip())
            if m:
                dates.append(m.group(0))
        if dates:
            dates.sort()
            return {"from": dates[0], "to": dates[-1], "days": len(dates),
                    "source": "колонка дат"}
    m = re.search(r"(\d{4}-\d{2}-\d{2}).{0,3}(\d{4}-\d{2}-\d{2})",
                  parsed["file"])
    if m:
        f, t = m.group(1), m.group(2)
        days = (dt.date.fromisoformat(t) - dt.date.fromisoformat(f)).days + 1
        return {"from": f, "to": t, "days": days, "source": "имя файла"}
    return None


# ------------------------------------------------------- сверка и сборка

def reconcile(parsed_files, period):
    """Свести итоги и найти расхождения.

    Главное правило: вид, помеченный полным, обязан дать итог периода.
    Если два полных вида разошлись, один из файлов про другой срез или
    другой счётчик, и выбирать «самый частый» молча нельзя: это
    выдумывание. Сборка останавливается и перечисляет расхождение.
    """
    full, subsets, unknown = {}, {}, []
    for p in parsed_files:
        spec = KINDS[p["kind"]]
        visits = p["measures"].get("visits")
        if visits is None:
            unknown.append(p["kind_label"])
            p["no_total_row"] = True
            continue
        if spec.get("full"):
            full[p["kind"]] = visits
        else:
            subsets[p["kind"]] = visits

    base = None
    if full:
        # Базой считается самое частое значение, а не любое: метрика
        # округляет по разным причинам и разные разрезы одного счётчика
        # расходятся на единицы. Кратная разница ошибкой не считается.
        vals = sorted(full.values())
        base = max(set(vals), key=vals.count)
        off = {k: v for k, v in full.items()
               if abs(v - base) > TOLERANCE}
        if off:
            return {"ok": False, "base": base, "full": full,
                    "subsets": subsets,
                    "problem": "полные виды разошлись с базой %d: %s"
                               % (base, ", ".join(
                                   "%s %d" % (KINDS[k]["label"], v)
                                   for k, v in sorted(off.items())))}
    # Подмножество выше базы означает чужой срез или другой счётчик.
    # Разница в единицы допустима, кратная разница означает ошибку.
    over = {k: v for k, v in subsets.items()
            if base is not None and v > base + TOLERANCE}
    if over:
        return {"ok": False, "base": base, "full": full,
                "subsets": subsets, "unknown": unknown,
                "problem": "подмножество больше базы периода: %s"
                           % ", ".join("%s %d против базы %d"
                                       % (KINDS[k]["label"], v, base)
                                       for k, v in over.items())}
    return {"ok": True, "base": base, "full": full, "subsets": subsets,
            "unknown": unknown}


def period_key(period):
    """Ключ группировки по периоду."""
    if not period:
        return "неизвестен"
    return "%s..%s" % (period["from"], period["to"])


def duplicate_measure(parsed, min_rows=5, min_share=0.10):
    """Найти строки, у которых совпали визиты и посетители.

    Отчёт по разрезу не может дать двадцать разных запросов с одним и
    тем же числом визитов и посетителей. Если такое есть, отчёт про
    другой счётчик либо данные подставные.

    Условие не в самом повторе, а в его доле итога. Пять строк по
    одному посещению это норма, их ноль процентов от отчёта. Восемнадцать
    строк по 1369 посещений это семьдесят пять процентов отчёта, и
    так быть не может. Проверка по доле, иначе она ругается на всякий
    отчёт, где есть хвост из единичных строк.
    """
    rows = parsed.get("rows") or []
    buckets = {}
    for r in rows:
        v, vis = r.get("visits"), r.get("visitors")
        if v is None or vis is None:
            continue
        buckets.setdefault((v, vis), []).append(
            str(next((r[k] for k in r if k in ("Поисковая фраза", "Источник "
                    "трафика", "Страна", "Тип устройства", "Цель",
                    "Возраст", "Глубина просмотра", "Время на сайте",
                    "Робот") or ""), ""))[:60])

    total = parsed.get("measures", {}).get("visits")
    if not total:
        return None
    worst = None
    for (v, vis), labels in buckets.items():
        if len(labels) < min_rows:
            continue
        share = len(labels) * v / float(total)
        if share < min_share:
            continue
        if worst is None or share > worst["share"]:
            worst = {"rows": len(labels), "visits": v, "visitors": vis,
                     "share": share, "examples": labels}
    return worst


def collect():
    """Собрать все файлы из ручного каталога."""
    found = []
    if not os.path.isdir(SRC):
        return [], []
    for period_dir in sorted(os.listdir(SRC)):
        pdir = os.path.join(SRC, period_dir)
        if not os.path.isdir(pdir) or period_dir.startswith("_"):
            continue
        for f in sorted(os.listdir(pdir)):
            if not f.lower().endswith((".csv", ".txt")):
                continue
            p = parse_file(os.path.join(pdir, f))
            p["period_dir"] = period_dir
            found.append(p)
    return found, sorted(set(p["period_dir"] for p in found))


def main():
    check_only = "--check" in sys.argv
    files, period_dirs = collect()
    if not files:
        print("Ручных выгрузок нет в %s" % SRC)
        print("Положить выгруженные файлы в подпапку с названием периода,")
        print("например data\\manual\\metrika\\2026-09\\, и запустить снова.")
        return 2

    print("Папок с выгрузками: %d, файлов: %d" % (len(period_dirs),
                                                  len(files)))
    print("Папки: %s" % ", ".join(period_dirs))
    print()

    good, broken = [], []
    print("%-34s %-24s %-10s %10s" % ("вид", "файл", "итог", "строк"))
    print("-" * 84)
    no_total = []
    for p in files:
        if p["problem"]:
            broken.append(p)
            print("%-34s %-24s %-10s %10s"
                  % ("НЕ РАЗОБРАНО", p["file"][:24], "-", "-"))
            continue
        good.append(p)
        visits = p["measures"].get("visits")
        if visits is None:
            no_total.append(p["kind_label"])
            shown = "не итог"
        else:
            shown = "%.0f" % visits
        print("%-34s %-24s %-10s %10d"
              % (p["kind_label"], p["file"][:24], shown, len(p["rows"])))

    print()
    if no_total:
        print("Без строки итогов: %s" % ", ".join(no_total))
        print("  У таких файлов итог не сверяется. Сумма строк проверяется")
        print("  отдельно, в гейтах.")
        print()
    if broken:
        print("НЕ РАЗОБРАНО, требует вмешательства: %d" % len(broken))
        for b in broken:
            print("  %s" % b["file"])
            print("    причина: %s" % b["problem"])
        print()

    # Период у каждого файла свой. Группировать по периоду надо,
    # иначе срез за три года сверяется со срезом за квартал и
    # получается выдуманная ошибка. Файлы без дат и без периода в
    # имени в сверку не попадают вовсе: сравнивать не с чем.
    for p in good:
        p["period"] = period_of(p)

    groups = {}
    for p in good:
        groups.setdefault(period_key(p["period"]), []).append(p)

    print("ПЕРИОДЫ, НАЙДЕННЫЕ В ФАЙЛАХ")
    for key in sorted(groups):
        members = groups[key]
        p0 = members[0]["period"]
        head = ("с %s по %s, дней %d, источник: %s"
                % (p0["from"], p0["to"], p0["days"], p0["source"])
                if p0 else "не определён, в файлах нет ни дат, ни имён")
        print("  %s" % head)
        for p in members:
            print("      %s" % p["kind_label"])
    print()

    all_ok = True
    summary = {}
    for key in sorted(groups):
        rec = reconcile(groups[key], groups[key][0]["period"])
        summary[key] = rec
        print("СВЕРКА ИТОГОВ, ПЕРИОД: %s" % (
            key if key != "неизвестен" else "неизвестен, сверка не выполняется"))
        if rec["base"] is not None:
            print("  база периода: %.0f визитов" % rec["base"])
        for k, v in rec["full"].items():
            mark = ("" if abs(v - rec["base"]) <= TOLERANCE
                    else "  ОТКЛОНЕНИЕ")
            print("  полный   %-32s %10.0f%s" % (KINDS[k]["label"], v, mark))
        for k, v in rec["subsets"].items():
            print("  подмножество %-27s %10.0f (ожидается меньше базы)"
                  % (KINDS[k]["label"], v))
        if rec["unknown"]:
            print("  без итога: %s" % ", ".join(rec["unknown"]))
        print()
        if not rec["ok"]:
            all_ok = False
            print("  ОШИБКА: %s" % rec["problem"])
            print()

    # Плоская таблица: много разных строк с одинаковыми числами.
    # На настоящих данных так не бывает, и период этого не объясняет.
    flat = []
    for p in good:
        dups = duplicate_measure(p)
        if dups:
            flat.append((p, dups))
    if flat:
        print("ОДИНАКОВЫЕ ЧИСЛА В РАЗНЫХ СТРОКАХ")
        for p, dups in flat:
            print("  %s, файл %s" % (p["kind_label"], p["file"]))
            print("    строк с одинаковыми визитами и посетителями: %d"
                  % dups["rows"])
            print("    значение: визиты %s, посетители %s"
                  % (dups["visits"], dups["visitors"]))
            print("    это %.0f процентов итога отчёта" % (dups["share"] * 100))
            for label in dups["examples"][:4]:
                print("      %s" % label)
        print()
        print("  Период этого не объясняет: длинный срез делает итог")
        print("  больше, но не делает одинаковыми числа у несвязанных")
        print("  строк. Обычно это другой счётчик или демонстрационные")
        print("  данные. Такой файл в отчёт не идёт.")
        print()
        all_ok = False

    period = None
    for p in good:
        if p["period"]:
            period = p["period"]
            break
    rec = next((r for k, r in sorted(summary.items())
                if r.get("base") is not None), {"ok": all_ok, "base": None,
                                                "full": {}, "subsets": {},
                                                "unknown": []})
    print()

    exit_code = 0
    if not all_ok:
        print("СБОРКА ОСТАНОВЛЕНА")
        print()
        print("Что делать по расхождению итогов: открыть оба отчёта в")
        print("интерфейсе Метрики и сверить верхнюю строку «Итого и")
        print("средние», а также какой счётчик и период выбраны. Если")
        print("один отчёт про другой период, это норма: он встанет в")
        print("свою группу и перестанет считаться ошибкой.")
        print()
        print("Что делать по одинаковым числам: проверить в шапке")
        print("отчёта, какой счётчик выбран. Совпадение визитов и")
        print("посетителей у несвязанных строк означает другой счётчик.")
        print()
        exit_code = 1
    if broken:
        exit_code = 1

    if check_only or exit_code:
        return exit_code

    day = dt.date.today().isoformat()
    outdir = os.path.join(OUT, day)
    os.makedirs(outdir, exist_ok=True)
    written = []
    for p in good:
        payload = {
            "kind": p["kind"],
            "label": p["kind_label"],
            "origin": "ручная выгрузка из интерфейса Метрики",
            "source_file": p["file"],
            "source_encoding": p["encoding"],
            "delimiter": p["sep"],
            "period": p["period"],
            "totals": p["measures"],
            "rows": p["rows"],
            "unmapped_columns": p["unmapped_cols"],
        }
        suffix = ""
        if p["period"]:
            suffix = "_%s_%s" % (p["period"]["from"], p["period"]["to"])
        path = os.path.join(outdir, p["kind"] + suffix + ".json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=1)
        written.append(p["kind"])

    index = {
        "origin": "ручная выгрузка из интерфейса Метрики",
        "parsed_at": dt.datetime.now().isoformat(timespec="seconds"),
        "period": period,
        "period_dirs": period_dirs,
        "period_base_visits": rec["base"],
        "reconciliation": {
            "full": rec["full"], "subsets": rec["subsets"],
            "tolerance": TOLERANCE,
        },
        "files_written": sorted(written),
        "files_rejected": [{"file": b["file"], "reason": b["problem"]}
                           for b in broken],
    }
    with open(os.path.join(outdir, "_index.json"), "w",
              encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False, indent=1)

    print("Записано в %s" % outdir)
    for k in sorted(written):
        print("  %s.json" % k)
    return 0


if __name__ == "__main__":
    sys.exit(main())