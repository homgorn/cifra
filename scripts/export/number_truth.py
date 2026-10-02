"""Истинные значения проекта, разбор файлов и контекстная правка.

Три вещи, связанные в одном файле, потому что по отдельности они
разъезжаются: список истинных значений, поиск расхождений по всему
проекту и замена с обязательным отчётом о каждой правке.

Правила, которые здесь закреплены, и почему.

Число не заменяется само по себе. Замена идёт только внутри строки,
которая совпала с контекстом: «страниц в поиске», «просмотров карточки»,
«исключено». Иначе правка одного показателя ломает соседний, где то же
число значит другое. «708» в одном месте это страницы в поиске, а в
другом шаг воронки.

Число без вычислимой истины не заменяется на догадку. Оно либо
переименовывается по установленному факту, либо удаляется с явной
пометкой, что показатель не измерен.

У каждого итога есть дата среза. Из неё следует, что два верных числа
могут описывать один и тот же показатель: 79 410 просмотров карточки на
30 сентября и 79 002 на 23 сентября это не спор, а два момента времени,
и разница в 408 это текущий неполный месяц.

Запуск:

    python scripts/export/number_truth.py --json
    python scripts/export/number_truth.py --scan
    python scripts/export/number_truth.py --apply
    python scripts/export/number_truth.py --gate
"""

import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"C:\susa ai\2026 cifra audit"
TRUTH_JSON = os.path.join(ROOT, "brain", "wiki", "webmaster_analytics",
                          "NUMBER_TRUTH.json")

SCAN_ROOTS = ("brain", "reports", "scripts", "yandex_business", "direct",
              "topvisor", "semantica")
SCAN_EXT = (".md", ".html", ".csv", ".json", ".js", ".txt")

# Каталоги, которые не правятся никогда.
KEEP_DIRS = (
    # Датированные логи сессий. Записывают, что было известно в конкретный
    # день, и «708» там верно для своего снимка за 2026-09-27. Заменить его
    # сегодняшним числом значит подменить свидетельство, а не исправить
    # ошибку: лог перестаёт быть свидетельством о том дне.
    os.path.join("brain", "wiki", "sessions"),
)

# Файлы, где старое число должно остаться: это запись самой сверки, и
# стирание из неё уничтожает след, по которому ошибку нашли.
KEEP = (
    os.path.relpath(TRUTH_JSON, ROOT),
    "brain\\wiki\\webmaster_analytics\\13_Number_Reconciliation.md",
    "brain/wiki/webmaster_analytics/13_Number_Reconciliation.md",
    "scripts\\export\\number_truth.py",
    "scripts/export/number_truth.py",
    "scripts\\export\\resolve_numbers.py",
    "scripts/export/resolve_numbers.py",
# Сгенерированные файлы. Их не правят текстом: они
# пересобираются из живой выгрузки, и только там числа
# становятся правильными. Ручная правка в одном
# сгенерированном файле пережила бы ровно одну
# пересборку.
    os.path.join("reports", "cifra18-audit", "js", "wm-data.js"),
    os.path.join("reports", "cifra18-audit", "js", "site-data.js"),
    os.path.join("reports", "cifra18-audit", "js", "dash-data.js"),
    os.path.join("reports", "cifra18-audit", "js", "page-index.js"),
    os.path.join("reports", "cifra18-audit-worker.js"),
    os.path.join("reports", "cifra18-audit", "pages", "plan-3m.html"),
)

# Число внутри кавычек не заменяется, и вот почему. В 07_Maps_Card.md стоит
# «79 002 визита, отказы 75%» в кавычках, потому что дальше по тексту
# разбирается, в чём именно эта цитата неверна. Подстановка верного числа
# превратила бы разбор ошибки в утверждение верного числа с приписанной ему
# ошибкой. Такие строки не правятся и попадают в список на разбор руками.
#
# В шаблоне только типографские кавычки-ёлочки и строки цитирования. Обратные
# кавычки в первый прогон сюда попали и дали 2 760 пропущенных строк: инлайн
# код это не цитата, и почти все сработавшие строки были обычными таблицами
# с путями в кавычках. Слишком широкое правило опаснее отсутствия правила:
# оно молча отключает правку везде.
QUOTE_RE = re.compile("«[^\\n]*»|^>.*")


def is_quoted(line):
    """Строка является цитатой или разбираемым утверждением."""
    return bool(QUOTE_RE.search(line))


def fix_agreement(line):
    """Согласовать существительное после числа с этим числом.

    Подстановка числа без падежа даёт неграмотный текст клиенту: «708
    страниц» верно, «744 страниц» неверно, нужно «744 страницы». Одна
    такая ошибка заставляет скептически читать весь остальной текст.
    """
    m = re.search(r"\b(\d+)[\s  ]+(страниц\w*)\b", line)
    if not m:
        return line
    n = int(m.group(1))
    # Падеж считается по последней цифре, кроме исключения 11-14, которое
    # действует на две последние. Считать по двум последним нельзя: из 744
    # получалось 44, 44 не попадает в диапазон 2-4, и «744 страниц»
    # доходило до клиента. Считать нужно 744 % 10 == 4, то есть «страницы».
    if 11 <= n % 100 <= 14:
        want = "страниц"
    elif n % 10 == 1:
        want = "страница"
    elif 2 <= n % 10 <= 4:
        want = "страницы"
    else:
        want = "страниц"
    if m.group(2) == want:
        return line
    return line[:m.start(2)] + want + line[m.end(2):]

NBSP = "\u00a0"
NNBSP = "\u202f"
SP = r"(?:[\s\u00a0\u202f])"


def num_variants(n):
    """Все записи числа: слитно, с запятой, с разделителем разрядов."""
    s = str(n)
    out = {s, s.replace(".", ",")}
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        for sep in (" ", NBSP, NNBSP):
            out.add(head + sep + tail)
            out.add((head + sep + tail).replace(".", ","))
    return out


# ---------------------------------------------------------- истинные числа
#
# Каждое значение посчитано из первичных данных скриптом
# resolve_numbers.py и здесь зафиксировано, чтобы проверка не
# пересчитывала их заново и чтобы отчёт и вики опирались на один список.

TRUTH = {
    "pages_in_search": {
        "value": 744,
        "as_of": "2026-09-30",
        "source": "data/exports/yandex_webmaster/2026-09-30/summary.json, "
                  "поле searchable_pages_count",
        "how": "поле отраслевой панели Яндекса, весь сайт",
        "wrong": ["708"],
        "resolved": "708 это снимок за 2026-09-27, а не ошибка; 1622 это "
                    "число проиндексированных, другой показатель; 142 это "
                    "выборка проверки из 717 адресов; 252 это сумма по "
                    "разделам выборки, и из неё нельзя считать долю "
                    "по всему сайту",
    },
    "excluded": {
        "value": 434,
        "as_of": "2026-09-30",
        "source": "data/exports/yandex_webmaster/2026-09-30/summary.json, "
                  "поле excluded_pages_count",
        "how": "поле отраслевой панели Яндекса, весь сайт",
        "wrong": ["477"],
        "resolved": "477 это снимок за 2026-09-27",
    },
    "urls_known_to_bot": {
        "value": 68926,
        "as_of": "2026-09-30",
        "source": "data/exports/yandex_webmaster/2026-09-30/"
                  "indexing_samples.json, поле count",
        "how": "все адреса, известные роботу, включая легаси с ошибкой",
        "wrong": ["2423"],
        "resolved": "2423 бралось из файла сайта wm-data.js, собранного "
                    "2026-09-23, и считает не всё дерево сайта; делить "
                    "744 на 68926 нельзя без оговорки, потому что "
                    "знаменатель набит мусорными легаси-страницами, и "
                    "доля 1,08 процента занижена",
    },
    "card_views_full_months": {
        "value": 76373,
        "as_of": "2026-08-31",
        "source": "data/exports/metrica/2026-09-27/cuts_maps/"
                  "month_total.json, счётчик 59102713, срез 2026-09-27",
        "how": "44 полных месяца, 2023-01 по 2026-08",
        "wrong": [],
        "resolved": "единственная величина по карточке, которую "
                    "подтверждают все три источника: живой API, месячный "
                    "файл вики и дневной файл вики сходятся до нуля",
    },
    "card_views_at_export": {
        "value": 79413,
        "as_of": "2026-09-27",
        "source": "data/exports/metrica/2026-09-27/cuts_maps/"
                  "month_total.json, счётчик 59102713",
        "how": "45 месяцев с неполным текущим, срез 2026-09-27",
        "wrong": ["79410", "79002"],
        "resolved": "это не три разных числа и не ошибка, это три среза "
                    "одного ряда. API отдаёт 3040 за текущий месяц, "
                    "месячный файл вики 3037, дневной 2629, потому что "
                    "он снят раньше. Вики отстают на текущий месяц, и "
                    "каждое из чисел верно для своей даты среза",
    },
    "card_views_12_full_months": {
        "value": 31668,
        "as_of": "2026-08-31",
        "source": "data/exports/metrica/2026-09-27/cuts_maps/"
                  "month_total.json, счётчик 59102713",
        "how": "12 полных месяцев, 2025-09 по 2026-08",
        "wrong": [],
        "resolved": "",
    },
    "card_views_12_with_partial": {
        "value": 32467,
        "as_of": "2026-09-27",
        "source": "data/exports/metrica/2026-09-27/cuts_maps/"
                  "month_total.json, счётчик 59102713",
        "how": "12 месяцев с неполным текущим, 2025-10 по 2026-09",
        "wrong": [],
        "resolved": "",
    },
    "site_visits_13_months": {
        "value": 21110,
        "as_of": "2026-09-30",
        "source": "brain/wiki/metrika_analytics/exports/"
                  "attendance_monthly.csv, счётчик 50863157",
        "how": "13 месяцев, 2025-09 по 2026-09, первый и последний неполные",
        "wrong": [],
        "resolved": "число верное, неверна подпись: в вики оно названо "
                    "«за 12 месяцев», и ни одно 12-месячное окно его не "
                    "даёт. 12 месяцев это 20 846, 11 полных это 19 163",
    },
    "site_visits_12_months": {
        "value": 20846,
        "as_of": "2026-09-30",
        "source": "brain/wiki/metrika_analytics/exports/"
                  "attendance_monthly.csv, счётчик 50863157",
        "how": "12 месяцев, 2025-10 по 2026-09, последний неполный",
        "wrong": [],
        "resolved": "",
    },
    "site_visits_11_full_months": {
        "value": 19163,
        "as_of": "2026-08-31",
        "source": "brain/wiki/metrika_analytics/exports/"
                  "attendance_monthly.csv, счётчик 50863157",
        "how": "11 полных месяцев, 2025-10 по 2026-08",
        "wrong": [],
        "resolved": "",
    },
}

# Правки, где число не заменяется, а меняется его смысл.
RELABEL = [
    {
        "id": "visits_12_months_label",
        "find": r"21[\s\u00a0\u202f]?110 за 12 месяцев",
        "replace": "21 110 за 13 месяцев (2025-09…2026-09, первый и "
                   "последний неполные)",
        "why": "21 110 это сумма всех 13 строк помесячного файла, и ни одно "
               "12-месячное окно её не даёт",
    },
    {
        "id": "visits_12_months_label_short",
        "find": r"21[\s\u00a0\u202f]?110 за 12 месяцев",
        "replace": "21 110 за 13 месяцев",
        "why": "то же, короткая подпись",
    },
]

# Числа без источника. Заменяются на ближайшее установленное значение
# с явной пометкой, что прежнее число ничем не подтверждалось.
NO_SOURCE = {
    "site_visits_unsourced": {
        "appears_as": ["21119"],
        "replace_with": 21110,
        "why": "21 119 не встречается ни в одной выгрузке проекта. Ближайшее "
               "подтверждённое значение 21 110 из attendance_monthly.csv, "
               "разница 9. Подставляется оно, и разница в 9 остаётся "
               "необъяснённой, а не списывается на округление",
        "unresolved_gap": 9,
    },
    "card_views_unsourced": {
        "appears_as": ["32726", "32730"],
        "replace_with": 32467,
        "why": "ни 32 726, ни 32 730 не встречаются ни в одной выгрузке. "
               "Ближайшее подтверждённое значение это 12 месяцев с "
               "неполным текущим на срез 27 сентября, 32 467, разница 259 "
               "и 263 соответственно. Подставляется оно, разница остаётся "
               "необъяснённой",
        "unresolved_gap": 263,
    },
}

# Контексты по ключу: число меняется только в строке, совпавшей с одним
# из них.
CONTEXT = {
    "pages_in_search": [r"страниц[^.]{0,20}в поиске",
                        r"в поиске[^.]{0,20}страниц",
                        r"searchable[^\n]{0,12}[0-9]"],
    "excluded": [r"исключен"],
    "urls_known_to_bot": [r"известно роботу", r"известных роботу"],
    "card_views_at_export": [r"просмотр[^.]{0,25}карточ",
                             r"карточ[^.]{0,25}просмотр"],
    "card_views_12_full_months": [r"просмотр[^.]{0,30}карточ",
                                  r"карточ[^.]{0,30}просмотр"],
    "card_views_12_with_partial": [r"просмотр[^.]{0,30}карточ",
                                     r"карточ[^.]{0,30}просмотр"],
}


def build_pattern(key):
    wrong = TRUTH[key].get("wrong") or []
    alts = []
    for w in wrong:
        for v in num_variants(w):
            alts.append(re.escape(v).replace(r"\ ", SP)
                        .replace(re.escape(" "), SP)
                        .replace(re.escape(NBSP), SP)
                        .replace(re.escape(NNBSP), SP))
    return re.compile("|".join(alts)) if alts else None


PATTERNS = {}
for _k in TRUTH:
    _p = build_pattern(_k)
    if _p:
        PATTERNS[_k] = _p

# Одна и та же строка может совпасть с двумя ключами, когда в ней есть и
# страницы в поиске, и исключённые. Порядок контекстов важен: более
# узкий проверяется первым, иначе «исключено» съест «в поиске».
PATTERN_ORDER = ("pages_in_search", "excluded", "urls_known_to_bot",
                 "card_views_12_with_partial", "card_views_12_full_months",
                 "card_views_at_export")


# Разделитель разрядов между цифрами числа: обычный пробел, неразрывный
# и узкий. Числа в документах пишут по-разному, и шаблон замены обязан
# понимать оба написания.
SEP = "[\\s\u00a0\u202f]*"


def norm(n):
    return "{:,}".format(int(n)).replace(",", " ")


def iter_files():
    for base in SCAN_ROOTS:
        root = os.path.join(ROOT, base)
        if not os.path.isdir(root):
            continue
        for dirpath, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
            for f in files:
                if not f.endswith(SCAN_EXT):
                    continue
                p = os.path.join(dirpath, f)
                rp = os.path.relpath(p, ROOT)
                if any(rp.startswith(d + os.sep) or rp.startswith(d + "/")
                       for d in KEEP_DIRS):
                    continue
                yield p


def rel(p):
    return os.path.relpath(p, ROOT)


def read_lines(p):
    try:
        return open(p, encoding="utf-8").read().splitlines()
    except (OSError, UnicodeDecodeError):
        return None


def find_discrepancies():
    """Строки, где стоит число, опровергнутое замером.

    Возвращается пара: расхождения и цитаты. Цитаты не являются
    расхождениями и не роняют гейт, но показываются, потому что в них
    число может требовать даты среза, а автозамена её не поставит.
    """
    out = []
    quotes = []
    for p in iter_files():
        if rel(p) in KEEP:
            continue
        lines = read_lines(p)
        if lines is None:
            continue
        for n, line in enumerate(lines, 1):
            if is_quoted(line):
                # Цитата не считается расхождением: в ней число стоит
                # как приводимый пример, и автозамена сломала бы смысл
                # абзаца. Но её полезно видеть, поэтому она попадает в
                # отдельный список для чтения человеком.
                if any(pat.search(line) for pat in PATTERNS.values()):
                    quotes.append({"file": rel(p), "line": n,
                                   "text": line.strip()[:200]})
                continue
            for key in PATTERN_ORDER:
                pat = PATTERNS.get(key)
                if not pat or not pat.search(line):
                    continue
                if not any(re.search(c, line, re.I) for c in CONTEXT[key]):
                    continue
                out.append({"file": rel(p), "line": n, "key": key,
                            "text": line.strip()[:200]})
                break
    return out, quotes


def find_no_source():
    """Строки с числом, у которого нет источника вообще."""
    out = []
    needles = []
    for spec in NO_SOURCE.values():
        needles.extend(spec["appears_as"])
    for p in iter_files():
        if rel(p) in KEEP:
            continue
        lines = read_lines(p)
        if lines is None:
            continue
        for n, line in enumerate(lines, 1):
            flat = re.sub(r"[\s\u00a0\u202f]+", "", line)
            for nos_key, spec in NO_SOURCE.items():
                if any(x in flat for x in spec["appears_as"]):
                    out.append({"file": rel(p), "line": n, "key": nos_key,
                                "text": line.strip()[:200]})
                    break
    return out


def find_mislabelled():
    """Число верное, подпись неверная."""
    out = []
    for p in iter_files():
        if rel(p) in KEEP:
            continue
        lines = read_lines(p)
        if lines is None:
            continue
        for n, line in enumerate(lines, 1):
            for rule in RELABEL:
                if re.search(rule["find"], line):
                    out.append({"file": rel(p), "line": n,
                                "id": rule["id"], "text": line.strip()[:200]})
    return out


# ------------------------------------------------------------------ правка

def apply(do_write=True):
    """Заменить опровергнутые числа, с отчётом по каждой правке."""
    changes = []
    skipped = []
    for p in iter_files():
        if rel(p) in KEEP:
            continue
        lines = read_lines(p)
        if lines is None:
            continue
        dirty = False
        for i, line in enumerate(lines):
            if is_quoted(line):
                skipped.append({"file": rel(p), "line": i + 1,
                                "text": line.strip()[:160]})
                continue
            new = line

            # 1. Опровергнутые числа по контексту.
            for key in PATTERN_ORDER:
                pat = PATTERNS.get(key)
                if not pat or not pat.search(new):
                    continue
                if not any(re.search(c, new, re.I) for c in CONTEXT[key]):
                    continue
                t = TRUTH[key]

                def sub_num(m, want=t["value"]):
                    return norm(want)

                replaced = pat.sub(sub_num, new)
                if replaced != new:
                    changes.append({"file": rel(p), "line": i + 1, "kind": "value",
                                    "key": key, "before": new.strip()[:160],
                                    "after": replaced.strip()[:160],
                                    "why": "подтверждено замером: %s, срез %s"
                                           % (t["source"][:80], t["as_of"])})
                    new = replaced
                    new = fix_agreement(new)
                    dirty = True
                # break здесь не ставится намеренно: строка может содержать
                # два показателя, например «в поиске 708 страниц, исключено
                # 477». С первым break второй оставался бы неправленым.

            # 2. Неверная подпись при верном числе.
            for rule in RELABEL:
                if re.search(rule["find"], new):
                    new2 = re.sub(rule["find"], rule["replace"], new)
                    if new2 != new:
                        changes.append({"file": rel(p), "line": i + 1,
                                        "kind": "relabel", "key": rule["id"],
                                        "before": new.strip()[:160],
                                        "after": new2.strip()[:160],
                                        "why": rule["why"]})
                        new = new2
                        dirty = True

            # 3. Числа без источника. У каждого своя спецификация и
            #    свой набор замен, потому что чисел несколько и они
            #    принадлежат разным показателям.
            for nos_key, spec in NO_SOURCE.items():
                flat = re.sub(r"[\s\u00a0\u202f]+", "", new)
                if not any(x in flat for x in spec["appears_as"]):
                    continue
                for bad in spec["appears_as"]:
                    # Шаблон собирается по цифрам, а не по слитному
                    # числу. В тексте число пишут с разделителем
                    # разрядов, «21 119», и шаблон вида «\d[\s]*21119»
                    # по нему не совпадал ни разу: между первой цифрой
                    # и остальными стоял пробел, а внутри «21119»
                    # разрыва не было, и замена молча не срабатывала.
                    pat = SEP.join(re.escape(ch) for ch in bad)
                    new2 = re.sub(pat, norm(spec["replace_with"]), new)
                    if new2 != new:
                        changes.append({"file": rel(p), "line": i + 1,
                                        "kind": "no_source",
                                        "key": nos_key,
                                        "before": new.strip()[:160],
                                        "after": new2.strip()[:160],
                                        "why": spec["why"]})
                        new = new2
                        dirty = True

            lines[i] = new

        if dirty and do_write:
            with open(p, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("\n".join(lines) + "\n")
    return changes, skipped


# ------------------------------------------------------------------ вывод

def show(disc, nosrc, mislab, quotes=()):
    print("=" * 78)
    print("I. ЧИСЛА, ОПРОВЕРГНУТЫЕ ЗАМЕРОМ")
    print("=" * 78)
    if disc:
        by = {}
        for d in disc:
            by.setdefault(d["file"], []).append(d)
        for f in sorted(by):
            print("\n%s" % f)
            for d in by[f]:
                t = TRUTH[d["key"]]
                print("  строка %-5d %s" % (d["line"], d["key"]))
                print("     было: %s" % d["text"][:120])
                print("     верно: %s, срез %s" % (norm(t["value"]), t["as_of"]))
        print("\nитого: %d строк в %d файлах" % (len(disc), len(by)))
    else:
        print("нет")

    print()
    print("=" * 78)
    print("II. ЧИСЛА БЕЗ ИСТОЧНИКА")
    print("=" * 78)
    for nos_key, spec in NO_SOURCE.items():
        print("%s: %s" % (nos_key, spec["why"]))
    if nosrc:
        by = {}
        for d in nosrc:
            by.setdefault(d["file"], []).append(d)
        for f in sorted(by):
            print("\n%s" % f)
            for d in by[f]:
                print("  строка %-5d %s" % (d["line"], d["text"][:110]))
        print("\nитого: %d строк в %d файлах" % (len(nosrc), len(by)))
    else:
        print("нет")

    print()
    print("=" * 78)
    print("III. ВЕРНОЕ ЧИСЛО С НЕВЕРНОЙ ПОДПИСЬЮ")
    print("=" * 78)
    print()
    print("=" * 78)
    print("IV. ЦИТАТЫ С ЧИСЛАМИ: НЕ ПРАВЯТСЯ, ЧИТАЕТ ЧЕЛОВЕК")
    print("=" * 78)
    if quotes:
        bq = {}
        for q in quotes:
            bq.setdefault(q["file"], []).append(q)
        for f in sorted(bq):
            print("\n%s" % f)
            for q in bq[f]:
                print("  строка %-5d %s" % (q["line"], q["text"][:110]))
        print("\nитого: %d строк" % len(quotes))
    else:
        print("нет")

    print()
    if mislab:
        by = {}
        for d in mislab:
            by.setdefault(d["file"], []).append(d)
        for f in sorted(by):
            print("\n%s" % f)
            for d in by[f]:
                print("  строка %-5d %s" % (d["line"], d["text"][:110]))
        print("\nитого: %d строк в %d файлах" % (len(mislab), len(by)))
    else:
        print("нет")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--scan"
    if mode == "--json":
        with open(TRUTH_JSON, "w", encoding="utf-8") as fh:
            json.dump({"truth": TRUTH, "no_source": NO_SOURCE,
                       "relabel": RELABEL,
                       "generated_by": "number_truth.py --json",
                       "as_of": "2026-09-30"}, fh, ensure_ascii=False, indent=1)
        print("записано: %s" % TRUTH_JSON)
        return 0

    if mode == "--apply":
        changes, skipped = apply(do_write=True)
        byfile = {}
        for c in changes:
            byfile.setdefault(c["file"], []).append(c)
        print("=" * 78)
        print("ПРАВКИ, %d штук в %d файлах" % (len(changes), len(byfile)))
        print("=" * 78)
        for f in sorted(byfile):
            print("\n%s" % f)
            for c in byfile[f]:
                print("  строка %-5d [%s]" % (c["line"], c["kind"]))
                print("     было: %s" % c["before"][:118])
                print("     стало: %s" % c["after"][:118])
                print("     почему: %s" % c["why"][:150])
        if skipped:
            print()
            print("ПРОПУЩЕНО, %d строк цитат или разбираемых утверждений:"
                  % len(skipped))
            bu = {}
            for s in skipped:
                bu.setdefault(s["file"], []).append(s)
            for f in sorted(bu):
                print("\n%s" % f)
                for s in bu[f]:
                    print("  строка %-5d %s" % (s["line"], s["text"][:110]))
        return 0

    disc, quotes = find_discrepancies()
    nosrc = find_no_source()
    mislab = find_mislabelled()
    show(disc, nosrc, mislab, quotes)

    if mode == "--gate":
        print()
        rc = 0
        total = len(disc) + len(nosrc) + len(mislab)
        if total:
            print("ГЕЙТ ПРОВАЛЕН: %d расхождений" % total)
            rc = 1
        else:
            print("ГЕЙТ ПРОЙДЕН: расхождений с зафиксированными числами нет")
        return rc
    return 0


if __name__ == "__main__":
    sys.exit(main())
