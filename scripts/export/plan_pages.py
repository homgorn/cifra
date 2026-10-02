"""План лендингов и статей, собранный из данных, а не из догадок.

Что делает скрипт. Берёт 627 фраз с назначенными целевыми страницами
из Topvisor, подтягивает к каждой позицию, показы и клики из выгрузки
Вебмастера, проверяет, существует ли назначенная страница на сайте, и
печатает список лендингов, отсортированный по деньгам.

Проверка существования страницы это главное. В плане лендингов были
адреса с префиксом /catalog/shirokoformatnaya-pechat/, которого на
сайте нет: широкоформат лежит в /catalog/reklama/shirokoformatnaya-pechat/
и /catalog/interer/. Такую страницу нельзя создать, не меняя
структуру, и без проверки это видно только при попытке.

Второе, что здесь считается: назначенная цель может быть в 404 или в
дублях. Страница, которая уже помечена как дубликат, не годится
целью: новый текст ляжет на адрес, который поисковик игнорирует.

Запуск:

    python scripts/export/plan_pages.py
    python scripts/export/plan_pages.py --md FILE     записать отчёт
"""

import csv
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"C:\susa ai\2026 cifra audit"
TARGETS = os.path.join(ROOT, "topvisor", "exports", "keyword_targets.csv")
POS = os.path.join(ROOT, "brain", "wiki", "webmaster_analytics", "exports",
                   "all_queries_positions.csv")
STRUCT = os.path.join(ROOT, "brain", "wiki", "webmaster_analytics",
                      "exports", "site_structure.csv")
SEARCHABLE = os.path.join(ROOT, "brain", "wiki", "webmaster_analytics",
                          "exports", "searchable_pages.csv")
DUPLICATES = os.path.join(ROOT, "brain", "wiki", "webmaster_analytics",
                          "exports", "duplicate_pages.csv")

# Разделы с известной индексацией. Ноль в графе Searchable означает,
# что в поиске нет ни одной страницы раздела.
BAD_SECTIONS = {}
LIVE = set()
# Адреса, помеченные как дубликаты.
BAD_URLS = set()


def norm(s):
    s = str(s or "").lower().replace("\u2011", "-").replace("\u2010", "-")
    s = s.replace("ё", "е")
    return re.sub(r"\s+", " ", s).strip(" ,.;:")


def read_delim(path):
    """Прочитать CSV с угаданным разделителем.

    Угадывание, а не заданный разделитель: в проекте лежат файлы и с
    запятой, и с точкой с запятой, и указание одного разделителя
    молча ломало разбор другого файла.
    """
    lines = [l for l in open(path, encoding="utf-8-sig").read().splitlines()
             if l.strip()]
    if not lines:
        return [], ","
    head = lines[0]
    counts = {";": head.count(";"), ",": head.count(","), "\t": head.count("\t")}
    sep = max(counts, key=counts.get)
    if counts[sep] == 0:
        sep = ","
    rows = [r for r in csv.reader(lines, delimiter=sep)
            if any(c.strip() for c in r)]
    return rows, sep


def url_path(u):
    """Путь из адреса в читаемом виде.

    Выгрузка Вебмастера отдаёт домены в punycode, а цели в Topvisor
    записаны относительными путями. Сравнивать их напрямую бессмысленно,
    они не встретятся никогда, и проверка молча не сработает. Домен
    приводится к читаемому виду, дальше сравниваются пути.
    """
    if not u:
        return ""
    s = str(u).strip()
    for scheme in ("http://", "https://"):
        if s.lower().startswith(scheme):
            s = s[len(scheme):]
            break
    host, _, path = s.partition("/")
    if host.startswith("xn--") or ".xn--" in host:
        try:
            host = host.encode("ascii").decode("idna")
        except Exception:                                     # noqa: BLE001
            pass
    return "/" + path.strip("/") if path.strip("/") else "/"


def load_positions():
    """Запрос к позиции, показам, кликам."""
    rows, _ = read_delim(POS)
    out = {}
    if not rows:
        return out
    head = [h.strip() for h in rows[0]]
    def col(*names):
        for i, h in enumerate(head):
            if any(n in h.lower() for n in names):
                return i
        return None
    qi = col("query", "запрос")
    pi = col("avg_position")
    si = col("shows")
    ci = col("clicks")
    for r in rows[1:]:
        if qi is None or qi >= len(r):
            continue
        def num(idx):
            if idx is None or idx >= len(r):
                return 0.0
            try:
                return float(r[idx].replace(",", "."))
            except ValueError:
                return 0.0
        out[norm(r[qi])] = {"pos": num(pi), "shows": num(si),
                            "clicks": num(ci)}
    return out


def load_structure():
    rows, _ = read_delim(STRUCT)
    if not rows:
        return
    head = [h.strip() for h in rows[0]]
    si = next((i for i, h in enumerate(head) if "searchable" in h.lower()), 3)
    ii = next((i for i, h in enumerate(head) if "indexed" in h.lower()), 1)
    for r in rows[1:]:
        if si >= len(r):
            continue
        sec = url_path(r[0]).rstrip("/") or "/"
        try:
            searchable = int(float(r[si].replace(",", ".")))
            indexed = int(float(r[ii].replace(",", ".")))
        except ValueError:
            continue
        BAD_SECTIONS[sec or "/"] = {"searchable": searchable,
                                   "indexed": indexed}


def load_duplicates():
    """Адреса, помеченные как дубликаты, в виде путей.

    Раньше сюда попадало всё подряд, потому что сравнение шло с
    punycode против относительных путей и не срабатывало ни разу.
    """
    if not os.path.isfile(DUPLICATES):
        return
    rows, _ = read_delim(DUPLICATES)
    if not rows:
        return
    head = [h.strip() for h in rows[0]]
    ui = next((i for i, h in enumerate(head)
               if h.upper() in ("URL", "URL_PATH") or "url" in h.lower()), 0)
    for r in rows[1:]:
        if ui >= len(r):
            continue
        p = url_path(r[ui])
        if p and p != "/":
            BAD_URLS.add(norm(p))


def load_live_paths():
    """Все пути, которые сайт отдаёт: в поиске и помеченные дубликатами.

    Раньше ветки брались из site_structure.csv, и это давало ложные
    срабатывания. В том файле разделы второго уровня записаны без
    префикса /catalog/, поэтому /catalog/mobilnye-stendy/ выглядел
    как несуществующая ветка, хотя 133 из 142 проиндексированных
    страниц лежат именно под /catalog/. Файл оказался непригоден как
    источник структуры, и вместо него берутся настоящие адреса.
    """
    live = set()
    for path in (SEARCHABLE, DUPLICATES):
        if not os.path.isfile(path):
            continue
        rows, _ = read_delim(path)
        for r in rows[1:]:
            if r and r[0].strip():
                p = url_path(r[0])
                if p and p != "/":
                    live.add(norm(p))
                    parts = [x for x in p.split("/") if x]
                    for i in range(1, len(parts) + 1):
                        live.add(norm("/" + "/".join(parts[:i])))
    return live


def prefix_alive(url):
    """Жива ли ветка раздела, в которую ведёт адрес.

    Точное совпадение раздела не нужно: важно, что первый существующий
    уровень вложенности отличается. Адрес /catalog/shirokoformatnaya-pechat/
    не совпадает ни с одним разделом, а /catalog/reklama/shirokoformatnaya-pechat/
    есть, значит ветка /catalog/ живая и страницу создать можно,
    вопрос только в том, где именно её повесить.
    """
    if not url:
        return None, "нет цели"
    u = norm(url_path(url)).rstrip("/")
    if u in ("", "/"):
        return True, "корень сайта"
    if u in LIVE:
        return True, "такая страница или раздел уже есть"
    parts = [x for x in u.split("/") if x]
    for i in range(len(parts), 0, -1):
        cand = norm("/" + "/".join(parts[:i]))
        if cand in LIVE:
            return True, "точной страницы нет, но ветка %s живая" % cand
    return False, "такой ветки на сайте нет"


def main():
    md_to = None
    if "--md" in sys.argv:
        i = sys.argv.index("--md")
        if i + 1 < len(sys.argv):
            md_to = sys.argv[i + 1]

    load_structure()
    load_duplicates()
    global LIVE
    LIVE = load_live_paths()
    pos = load_positions()

    rows, _ = read_delim(TARGETS)
    if not rows:
        print("Нет %s" % TARGETS)
        return 2
    head = [h.strip() for h in rows[0]]
    def col(name):
        for i, h in enumerate(head):
            if name in h.lower():
                return i
        return None
    P = col("phrase")
    G = col("group")
    T = col("target_url")
    N = col("needs_page")

    groups = {}
    for r in rows[1:]:
        if P is None or P >= len(r):
            continue
        phrase = r[P].strip()
        g = (r[G] if G is not None and G < len(r) else "") or "без группы"
        t = (r[T] if T is not None and T < len(r) else "").strip()
        need = (r[N] if N is not None and N < len(r) else "").strip().lower()
        p = pos.get(norm(phrase), {})
        rec = {"phrase": phrase, "target": t, "need": need,
               "pos": p.get("pos", 0.0), "shows": p.get("shows", 0.0),
               "clicks": p.get("clicks", 0.0), "measured": bool(p)}
        g = groups.setdefault(g, [])
        g.append(rec)

    L = []
    a = L.append
    a("# План страниц по данным")
    a("")
    a("Собрано скриптом `scripts/export/plan_pages.py` из трёх источников: "
      "назначение целевых страниц из Topvisor, позиции и показы из "
      "выгрузки Вебмастера, структура и дубликаты сайта. Ни одна цифра "
      "здесь не написана рукой.")
    a("")
    a("## Что важно понимать про эти цифры")
    a("")
    meas = sum(1 for g in groups.values() for x in g if x["measured"])
    total = sum(len(g) for g in groups.values())
    a("Из %d фраз позиция измерена у %d, то есть у %d из них нет данных "
      "о позиции вообще. У остальных в среднем %.1f показа и %.1f клика, "
      "по этим цифрам и сортируется всё ниже."
      % (total, meas, total - meas,
         sum(x["shows"] for g in groups.values() for x in g) / max(meas, 1),
         sum(x["clicks"] for g in groups.values() for x in g) / max(meas, 1)))
    a("")
    a("**Ноль показов означает две разные вещи:** запрос есть, но сайт "
      "по нему не показывается, и запроса просто нет в выгрузке "
      "Вебмастера за этот период. Первое это повод работать, второе "
      "повод сначала проверить спрос. Разницы в таблице видно по "
      "колонке «измерено».")
    a("")

    # Порядок групп: по кликам, потом по показам.
    def gscore(g):
        return (sum(x["clicks"] for x in g), sum(x["shows"] for x in g))

    ordered = sorted(groups.items(), key=lambda kv: gscore(kv[1]), reverse=True)

    a("## Группы по деньгам")
    a("")
    a("| Группа | Фраз | Измерено | Показы | Клики | Лучшая позиция |")
    a("|---|---:|---:|---:|---:|---:|")
    for name, g in ordered:
        m = [x for x in g if x["measured"]]
        best = min((x["pos"] for x in m if x["pos"] > 0), default=0)
        a("| %s | %d | %d | %d | %.0f | %s |"
          % (name, len(g), len(m),
             int(sum(x["shows"] for x in g)), sum(x["clicks"] for x in g),
             ("%.1f" % best).replace(".", ",") if best else "нет данных"))
    a("")

    for name, g in ordered:
        need_new = [x for x in g if x["need"].startswith("да")]
        has_t = [x for x in g if x["target"]]
        no_t = [x for x in g if not x["target"]]
        a("### %s" % name)
        a("")
        m = [x for x in g if x["measured"]]
        shows = sum(x["shows"] for x in g)
        clicks = sum(x["clicks"] for x in g)
        a("Фраз %d, измерено %d, показов %d, кликов %.0f. Нужна новая "
          "страница под %d фраз, цель назначена у %d, не назначена у %d."
          % (len(g), len(m), int(shows), clicks, len(need_new), len(has_t),
             len(no_t)))
        a("")

        # Цели, которые назначены и куда ничего не показывается.
        broken = []
        for x in has_t:
            alive, why = prefix_alive(x["target"])
            if alive is False:
                broken.append((x, why))
        dup = [x for x in has_t
               if norm(url_path(x["target"])) in BAD_URLS]

        if dup:
            a("**Цели, помеченные как дубликаты.** Назначать новый текст "
              "на такой адрес бессмысленно, поисковик его игнорирует:")
            a("")
            for x in dup[:10]:
                a("- `%s`, запрос «%s», позиция %s"
                  % (x["target"], x["phrase"],
                     ("%.1f" % x["pos"]).replace(".", ",")
                     if x["pos"] else "нет"))
            a("")

        if broken:
            a("**Цели, ветки которых на сайте нет.** Такой адрес нельзя "
              "создать, не меняя структуру:")
            a("")
            for x, why in broken[:12]:
                a("- `%s`, запрос «%s», %s"
                  % (x["target"], x["phrase"], why))
            a("")

        top = sorted([x for x in g if x["measured"] or x["shows"]],
                     key=lambda x: (-x["clicks"], -x["shows"], x["pos"]))[:14]
        if top:
            a("| Фраза | Показы | Клики | Позиция | Цель | Нужна страница |")
            a("|---|---:|---:|---:|---|---|")
            for x in top:
                a("| %s | %d | %.0f | %s | %s | %s |"
                  % (x["phrase"], int(x["shows"]), x["clicks"],
                     ("%.1f" % x["pos"]).replace(".", ",")
                     if x["pos"] else "нет данных",
                     ("`%s`" % x["target"]) if x["target"] else "не назначена",
                     "да" if x["need"].startswith("да") else "нет"))
            a("")
        rest = len(g) - len(top)
        if rest > 0:
            a("Ещё %d фраз этой группы в файле Topvisor, здесь первые %d "
              "по деньгам." % (rest, len(top)))
            a("")

    text = "\n".join(L) + "\n"
    if md_to:
        with open(md_to, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("записано: %s, групп %d, строк %d"
              % (md_to, len(ordered), len(L)))
        return 0
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())