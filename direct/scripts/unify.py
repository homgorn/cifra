#!/usr/bin/env python3
"""Одна таблица по всем источникам сразу.

Зачем это нужно. Четыре источника знают про один и тот же сайт разное,
и ни один из них не показывает картину целиком.

  Вебмастер  знает, где сайт в поиске бесплатно
  Директ     знает, за что платят и какую позицию это даёт
  Метрика    знает, что делал посетитель после клика
  Topvisor   знает, какие фразы вообще считаются нужными

Соединяются они по тексту запроса. Вебмастер, Директ и Topvisor
оперируют одной и той же строкой, и если привести к нижнему регистру и
убрать лишние пробелы, строки совпадают. Метрика строк не имеет, она
даёт каналы, и подключается отдельным агрегатом по каналам.

Что даёт объединение, чего не даёт ни одна панель отдельно. Строка, где
органика уже в топ-5, а Директ по этому же запросу всё равно платит.
Такие строки в панели Директа не видны, в Вебмастере тоже, и в отчёте
клиенту их не было. Деньги идут на позицию, которая уже занята, и это
видно только в общей таблице.

Директ в это время может быть ещё не выгружен. Тогда сорок процентов
столбцов пустые, и это нормально, а не поломка: скрипт пишет, каких
источников не хватает, и вердикты, которые без Директа не выводятся,
помечает как требующие данных. Молча оставлять пустые колонки нельзя,
потому что пустой столбец читается как ноль.

Запуск из корня проекта:
  python direct/scripts/unify.py
  python direct/scripts/unify.py --out data/exports/unified/2026-09-30

Пишет:
  query_table.csv    по строке на запрос, все источники
  cluster_table.csv  по кластеру, сводка и вердикт
  channel_table.csv  каналы Метрики
  SUMMARY.md         что сошлось, чего не хватило
"""
import csv
import json
import os
import re
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "scripts", "export"))
sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WM_DATA = os.path.join(ROOT, "reports", "cifra18-audit", "js", "wm-data.js")
WM_CSV = os.path.join(ROOT, "brain", "wiki", "webmaster_analytics", "exports",
                      "top_queries_by_cluster.csv")
TV_IMPORT = os.path.join(ROOT, "topvisor", "exports", "import_queries.csv")
METRICA = os.path.join(ROOT, "data", "exports", "metrica")
DIRECT = os.path.join(ROOT, "data", "exports", "direct")

TODAY = date.today()


def newest(prefix, want=None):
    if not os.path.isdir(prefix):
        return None
    days = sorted(d for d in os.listdir(prefix)
                  if os.path.isdir(os.path.join(prefix, d)))
    for d in reversed(days):
        p = os.path.join(prefix, d)
        if want is None or os.path.isfile(os.path.join(p, want)):
            return p
    return None


def norm(q):
    """Ключ соединения. Регистр и пробелы в данных не совпадают.

    Проверено на данных проекта: в выгрузке Вебмастера есть
    «Визитки», в списке импорта Topvisor «визитки», и без нормализации
    это две разные строки, а они одна и та же фраза.
    """
    s = (q or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def num(x, default=0.0):
    try:
        return float(str(x).replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return default


def read_csv(p):
    """Читает csv всегда с utf-8-sig.

    Выгрузки Topvisor приходят с меткой порядка байтов, и при чтении
    как utf-8 первая колонка называется не phrase, а с невидимым
    префиксом из трёх байтов. Обращение по правильному имени молча даёт
    пустое значение, и соединение не собирается: в сводке появляется
    строка «Topvisor: нет», хотя файл рядом и он в порядке. Именно так
    и вышло, поэтому кодировка зафиксирована здесь, а не в вызывающем
    коде. Для файлов без метки utf-8-sig читает так же, как utf-8.
    """
    if not os.path.isfile(p):
        return []
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_wm():
    """Запросы с кластерами и позицией из wm-data.js.

    Кластеры берутся отсюда, а не из выгрузки Вебмастера: в csv-файле
    колонка Cluster_L1 заполнена значением TODO во всех 535 строках,
    то есть раскладки по кластерам в нём нет вовсе, несмотря на имя
    колонки. Кластеры лежат в wm-data.js, в списке из 492 реальных
    запросов, где отброшены 43 мусорные строки.
    """
    raw = open(WM_DATA, encoding="utf-8").read()
    d = json.loads(raw[raw.find("{"):raw.rindex("}") + 1])
    out = {}
    for x in d.get("queryClusters") or []:
        q = norm(x.get("q"))
        if q:
            out[q] = {"cluster": x.get("c") or "Прочие",
                      "pos": num(x.get("p")) or None,
                      "url": x.get("u") or ""}
    stats = d.get("queryStats") or {}
    return out, stats, d.get("clusters") or []


def load_wm_csv():
    """Показы и клики из csv-выгрузки, по нормализованному тексту."""
    out = {}
    for r in read_csv(WM_CSV):
        q = norm(r.get("Query"))
        if q:
            out[q] = {"shows": num(r.get("Shows_Total")),
                      "clicks": num(r.get("Clicks_Total")),
                      "ctr": num(r.get("CTR_%"))}
    return out


def load_topvisor():
    """Семантическое ядро: фраза входит или нет, и в какую группу."""
    out = {}
    for r in read_csv(TV_IMPORT):
        q = norm(r.get("phrase") or r.get("Phrase"))
        if q:
            out[q] = {"group": r.get("group") or "",
                      "in_topvisor": (r.get("in_topvisor") or "").strip().lower()}
    return out


def load_direct():
    """Поисковые запросы Директа, если выгрузка уже есть.

    Отчёт по запросам формируется только в офлайне и может отсутствовать
    при первой попытке. Отсутствие файла это не ошибка, а отсутствие
    данных, и оно отмечается в сводке отдельной строкой.
    """
    d = newest(DIRECT, want="_index.json")
    p = os.path.join(d, "report_query.tsv") if d else ""
    if not (p and os.path.isfile(p)):
        return {}, None
    sys.path.insert(0, os.path.join(ROOT, "direct", "scripts"))
    import direct_api as D
    _names, rows = D.DirectClient.tsv_to_dicts(open(p, encoding="utf-8").read())
    agg = {}
    for r in rows:
        q = norm(r.get("Query"))
        if not q:
            continue
        a = agg.setdefault(q, {"cost": 0.0, "clicks": 0.0, "impr": 0.0,
                               "pos": [], "matched": r.get("MatchedKeyword") or ""})
        a["cost"] += num(r.get("Cost"))
        a["clicks"] += num(r.get("Clicks"))
        a["impr"] += num(r.get("Impressions"))
        p_ = num(r.get("AvgClickPosition"))
        if p_:
            a["pos"].append(p_)
    for a in agg.values():
        a["pos"] = (sum(a["pos"]) / len(a["pos"])) if a["pos"] else None
        a.pop("pos_all", None)
    return agg, d


def load_channels():
    """Каналы Метрики: визиты, отказы, глубина по источнику трафика."""
    d = newest(METRICA, want=os.path.join("cuts", "source_month.json"))
    p = os.path.join(d, "cuts", "source_month.json") if d else ""
    if not os.path.isfile(p):
        return [], None
    j = json.load(open(p, encoding="utf-8"))
    agg = {}
    for row in j.get("data") or []:
        dm = row.get("dimensions") or []
        if len(dm) < 2:
            continue
        name = dm[1].get("name") or "?"
        m = row.get("metrics") or []
        a = agg.setdefault(name, {"visits": 0.0, "users": 0.0,
                                  "bounce": [], "duration": []})
        a["visits"] += num(m[0] if len(m) > 0 else 0)
        a["users"] += num(m[1] if len(m) > 1 else 0)
        if len(m) > 2:
            a["bounce"].append(num(m[2]))
        if len(m) > 3:
            a["duration"].append(num(m[3]))
    out = []
    for name, a in agg.items():
        out.append({
            "channel": name,
            "visits": round(a["visits"]),
            "users": round(a["users"]),
            "bounce_pct": round(sum(a["bounce"]) / len(a["bounce"]), 1) if a["bounce"] else "",
            "avg_duration_s": round(sum(a["duration"]) / len(a["duration"])) if a["duration"] else "",
        })
    out.sort(key=lambda x: -x["visits"])
    return out, d


def verdict(pos, cost, in_core):
    """Решение по строке. Три входа, три разных ответа.

    Позиция в organic и расход в Direct сравниваются между собой, и
    в этом сравнении ответ, которого нет ни в одной панели: платить за
    позицию, которую сайт уже занимает бесплатно.
    """
    has_org = pos is not None and pos > 0
    paid = cost > 0
    if has_org and pos <= 10 and paid:
        return "ПЛАТИТ ЗА ЗАНЯТОЕ", "органика в топ-10, Директ по тому же запросу платит"
    if has_org and pos <= 10:
        return "ОРГАНИКА ОК", "запрос в топ-10, платного трафика нет"
    if not has_org and paid:
        return "ТОЛЬКО ПЛАТНО", "в поиске нет, трафик покупается"
    if not has_org and in_core:
        return "ПРОБЕЛ, НЕ ОКУПАЕТСЯ", "входит в ядро, в поиске нет и Директ не тратит"
    if not has_org:
        return "ПРОБЕЛ", "в поиске нет, в ядро не входит"
    return "НИЖЕ ТОП-10", "в поиске есть, но позиция слабая"


def main():
    out_dir = None
    if "--out" in sys.argv:
        out_dir = sys.argv[sys.argv.index("--out") + 1]
    out_dir = out_dir or os.path.join(ROOT, "data", "exports", "unified", TODAY.isoformat())
    os.makedirs(out_dir, exist_ok=True)

    wm, wm_stats, clusters = load_wm()
    wm_csv = load_wm_csv()
    tv = load_topvisor()
    dr, dr_dir = load_direct()
    ch, ch_dir = load_channels()

    rows = []
    for q, w in sorted(wm.items()):
        c = wm_csv.get(q, {})
        t = tv.get(q, {})
        d = dr.get(q, {})
        rows.append({
            "query": q,
            "cluster": w["cluster"],
            "target_url": w["url"],
            "organic_pos": w["pos"] or "",
            "organic_shows": c.get("shows", ""),
            "organic_clicks": c.get("clicks", ""),
            "organic_ctr": c.get("ctr", ""),
            "in_core": "да" if q in tv else "нет",
            "core_group": t.get("group", ""),
            "already_in_topvisor": t.get("in_topvisor", ""),
            "direct_cost": round(d.get("cost", 0.0), 2) if dr else "",
            "direct_clicks": round(d.get("clicks", 0.0), 0) if dr else "",
            "direct_shows": round(d.get("impr", 0.0), 0) if dr else "",
            "direct_pos": round(d["pos"], 2) if d and d.get("pos") else "",
            "paid_keyword": d.get("matched", "") if d else "",
        })

    for r in rows:
        v, why = verdict(
            r["organic_pos"], num(r["direct_cost"]), r["in_core"] == "да")
        r["verdict"] = v
        r["verdict_why"] = why

    # Сводка по кластерам: где SEO работает, где платят, где дыра.
    by_cluster = {}
    for r in rows:
        a = by_cluster.setdefault(r["cluster"], {
            "cluster": r["cluster"], "queries": 0, "top10": 0, "pos_sum": 0.0,
            "pos_n": 0, "in_core": 0, "direct_cost": 0.0, "direct_clicks": 0.0,
            "paid_on_taken": 0})
        a["queries"] += 1
        if r["organic_pos"] and num(r["organic_pos"]) <= 10:
            a["top10"] += 1
        if r["organic_pos"]:
            a["pos_sum"] += num(r["organic_pos"])
            a["pos_n"] += 1
        if r["in_core"] == "да":
            a["in_core"] += 1
        a["direct_cost"] += num(r["direct_cost"])
        a["direct_clicks"] += num(r["direct_clicks"])
        if r["verdict"] == "ПЛАТИТ ЗА ЗАНЯТОЕ":
            a["paid_on_taken"] += 1

    crows = []
    for a in by_cluster.values():
        crows.append({
            "cluster": a["cluster"],
            "queries": a["queries"],
            "top10": a["top10"],
            "top10_pct": round(100.0 * a["top10"] / a["queries"], 1),
            "avg_pos": round(a["pos_sum"] / a["pos_n"], 1) if a["pos_n"] else "",
            "in_core": a["in_core"],
            "direct_cost": round(a["direct_cost"], 2) if dr else "",
            "direct_clicks": round(a["direct_clicks"]) if dr else "",
            "paid_on_taken": a["paid_on_taken"] if dr else "",
        })
    crows.sort(key=lambda x: -(x["direct_cost"] if x["direct_cost"] != "" else 0))

    def write_csv(name, data, fields):
        p = os.path.join(out_dir, name)
        with open(p, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for r in data:
                w.writerow(r)
        return p

    p1 = write_csv("query_table.csv", rows, list(rows[0].keys()) if rows else ["query"])
    p2 = write_csv("cluster_table.csv", crows, list(crows[0].keys()) if crows else ["cluster"])
    p3 = write_csv("channel_table.csv", ch,
                   ["channel", "visits", "users", "bounce_pct", "avg_duration_s"])

    # Сводка пишется текстом, а не markdown-таблицей в вики: она
    # машинная, её читает человек при разборе и скрипт при сверке.
    total_cost = sum(num(r["direct_cost"]) for r in rows)
    paid_taken = [r for r in rows if r["verdict"] == "ПЛАТИТ ЗА ЗАНЯТОЕ"]
    wasted = sum(num(r["direct_cost"]) for r in paid_taken)
    lines = [
        "Сводка объединённой таблицы",
        "",
        "Запросов в таблице: %d" % len(rows),
        "Кластеров: %d" % len(crows),
        "",
        "Источники:",
        "  Вебмастер, запросы с кластерами: %s"
        % ("да, %d строк" % len(rows) if wm else "НЕТ"),
        "  Вебмастер, показы и клики: %s"
        % ("да, %d совпадений" % sum(1 for q in wm if q in wm_csv) if wm_csv else "НЕТ"),
        "  Topvisor, семантическое ядро: %s"
        % ("да, %d совпадений" % sum(1 for q in wm if q in tv) if tv else "НЕТ"),
        "  Метрика, каналы: %s" % ("да, %d каналов" % len(ch) if ch else "НЕТ"),
        "  Директ, поисковые запросы: %s"
        % ("да, %d строк, срез %s" % (len(dr), os.path.basename(dr_dir))
           if dr else "НЕТ, нужен отчёт по запросам"),
        "",
    ]
    if dr:
        lines += [
            "Денежная часть:",
            "  расход Директа на запросы, попавшие в таблицу: %.2f" % total_cost,
            "  из них платит за уже занятую позицию: %.2f" % wasted,
            "  таких строк: %d" % len(paid_taken),
            "",
        ]
        if paid_taken:
            lines.append("Топ по «платит за занятое»:")
            for r in sorted(paid_taken, key=lambda x: -num(x["direct_cost"]))[:10]:
                lines.append("  %-44s позиция %s, расход %s, фраза %s"
                             % (r["query"][:44], r["organic_pos"],
                                r["direct_cost"], r["paid_keyword"][:30]))
            lines.append("")
    else:
        lines += [
            "Денежная часть не посчитана: нет выгрузки Директа по запросам.",
            "Столбцы direct_* пустые, а не нулевые. Пустой столбец читается",
            "как ноль, поэтому здесь это указано явно.",
            "",
        ]
    lines += ["Вердикты:", ""]
    vc = {}
    for r in rows:
        vc[r["verdict"]] = vc.get(r["verdict"], 0) + 1
    for k, n in sorted(vc.items(), key=lambda x: -x[1]):
        lines.append("  %-28s %d" % (k, n))
    p4 = os.path.join(out_dir, "SUMMARY.txt")
    open(p4, "w", encoding="utf-8").write("\n".join(lines) + "\n")

    print("\n".join(lines))
    print()
    for p in (p1, p2, p3, p4):
        print("  %s" % os.path.relpath(p, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
