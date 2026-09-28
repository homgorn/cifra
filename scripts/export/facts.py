#!/usr/bin/env python3
"""Единый источник чисел для текстов проекта.

Зачем этот файл: числа разъезжались трижды. Сначала страница плана и
клиентский отчёт говорили «535 запросов по 8 группам», потом синхронизатор
подставил «22 группы» и получилось «627 запросов по 22 группы», потому
что число фраз он брал из CSV импорта Topvisor, а число групп из
wm-data.js. Это разные множества, и подстановка их друг в друга дала
правдоподобную, но неверную фразу.

Правило, которое отсюда следует: у каждого числа есть имя, знаменатель
и источник. Число без знаменателя не публикуется.

Источники:
  wm-data.js              кластеры, позиции, статусы. Сборка build_wm_data.py
  topvisor/exports/*.csv  корзины релевантности, снимок проекта
  webmaster_analytics CSV  сырая выгрузка панели, 535 строк

Запуск из корня проекта:
  python scripts/export/facts.py
"""
import collections
import csv
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WM_DATA = os.path.join(ROOT, "reports", "cifra18-audit", "js", "wm-data.js")
TV_EXPORT = os.path.join(ROOT, "topvisor", "exports")
WM_EXPORT = os.path.join(ROOT, "brain", "wiki", "webmaster_analytics", "exports")
TV_DB = os.path.join(ROOT, "topvisor", "db", "topvisor.db")
WM_API = os.path.join(ROOT, "data", "exports", "yandex_webmaster")

OTHER_GROUP = "Прочие"
UNASSIGNED_HINT = "не попали ни в один кластер"


def newest(prefix, want=None):
    """Самая свежая папка выгрузки по дате.

    want задаёт обязательный файл внутри. Без него берётся просто
    последняя папка, а она может оказаться неполной: сегодняшний срез
    создаётся роботом проверки robots.txt и лежит рядом со вчерашним
    полным, и тогда данные молча пропадают.
    """
    if not os.path.isdir(prefix):
        return None
    days = sorted(d for d in os.listdir(prefix)
                  if os.path.isdir(os.path.join(prefix, d)))
    for d in reversed(days):
        p = os.path.join(prefix, d)
        if want is None or os.path.isfile(os.path.join(p, want)):
            return p
    return None


def yandex_diagnostics():
    """Вердикт самой панели по 33 проверкам качества.

    Независимое подтверждение. Из 33 проверок Яндекс считает проблемными
    три, и две из них, дубли атрибутов и дубли страниц, совпадают с
    нашими выводами по canonical. Остальные ABSENT, включая те, что мы
    находим сами, но это не противоречие: панель проверяет выборку, мы
    разбираем страницы.

    Файл лежал непрочитанным, хотя это единственный источник, где
    оценку даёт сама поисковая система, а не наш скрипт.
    """
    day = newest(WM_API, want="diagnostics.json")
    p = os.path.join(day, "diagnostics.json") if day else ""
    if not (p and os.path.isfile(p)):
        return {"checked": False, "total": 0, "present": [], "reason": "нет diagnostics.json"}
    probs = json.load(open(p, encoding="utf-8")).get("problems") or {}
    present = [{"id": k, "severity": v.get("severity"),
                "updated": (v.get("last_state_update") or "")[:10]}
               for k, v in probs.items() if v.get("state") == "PRESENT"]
    present.sort(key=lambda x: {"FATAL": 0, "CRITICAL": 1,
                                "POSSIBLE_PROBLEM": 2}.get(x["severity"], 3))
    return {"checked": True, "day": os.path.basename(day), "total": len(probs),
            "present": present, "absent": len(probs) - len(present)}


def robots_state():
    """Живое состояние robots.txt: сколько строк Sitemap и сколько отдают 404.

    В отчёте стояло 23, проверка показала 19, и все 19 отдают 404. Число
    из текста протухает само, поэтому оно приходит из проверки, а не из
    памяти. Дата проверки едет вместе с числом.
    """
    day = newest(WM_API)
    p = os.path.join(day, "robots_state.json") if day else ""
    if p and os.path.isfile(p):
        d = json.load(open(p, encoding="utf-8"))
        d["source"] = "fetch_robots_state.py, проверено %s" % d.get("checked_at", "?")
        return d
    return {"sitemap_lines": None, "sitemap_404": None, "disallow_count": None,
            "checked_at": None, "source": "нет проверки, запусти fetch_robots_state.py"}


def wm():
    t = open(WM_DATA, encoding="utf-8").read()
    return json.loads(t[t.index("{"):].rstrip().rstrip(";"))


def plural(n, one, few, many):
    """Русское склонение по числу: 1 запрос, 2 запроса, 5 запросов.

    Условие для «few» проверяет, что сотни не попали в 12-14. Без этого
    12, 13, 14 получают «запроса», а 2, 3, 4 получают «запросов», то
    есть ровно наоборот. Такая ошибка не падает, а тихо печатает
    неграмотный текст клиенту, поэтому здесь она закреплена тестом в
    validate_report.py.
    """
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def in_groups(n):
    """Предложный падеж: «в 22 группах», «в 21 группе».

    Отдельная функция, а не перегрузка plural: падеж определяет концовка,
    и «в 23 групп» это ровно та ошибка, из-за которой страница плана
    выглядела правдоподобно и была неверна.
    """
    if n % 10 == 1 and n % 100 != 11:
        return "группе"
    return "группах"


def _sp(n):
    """Разделитель тысяч неразрывным пробелом, как в отчёте: 2 423."""
    return "{:,}".format(int(n)).replace(",", " ")


def read_csv(path):
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _section(d, name, key):
    for s in d.get("sections") or []:
        if s.get("section") == name:
            return s.get(key) or 0
    return 0


def collect():
    d = wm()
    qs = d.get("queryStats") or {}
    clusters = d.get("clusters") or []
    qc = d.get("queryClusters") or []

    by_group = collections.Counter(x.get("c") for x in qc)
    cluster_names = [c["name"] for c in clusters]

    # Кластеры сайта плюс корзина «Прочие»: это и есть число групп, в
    # которые разложено ядро. Публиковать только 22, нельзя: 53 запроса
    # в «Прочие» куда-то денутся, и клиент посчитает сам.
    core_groups = len(cluster_names) + (1 if OTHER_GROUP in by_group else 0)
    import_groups = sorted(set(r["group"] for r in read_csv(
        os.path.join(TV_EXPORT, "import_queries.csv")) if r.get("group")))

    raw = read_csv(os.path.join(WM_EXPORT, "top_queries_by_cluster.csv"))
    raw_pos = []
    for r in raw:
        try:
            raw_pos.append(float(r["Avg_Position"]))
        except (KeyError, TypeError, ValueError):
            pass
    core_pos = [float(x["p"]) for x in qc
                if isinstance(x.get("p"), (int, float)) and 1 <= float(x["p"]) <= 100]

    keep = read_csv(os.path.join(TV_EXPORT, "import_queries.csv"))
    review = read_csv(os.path.join(TV_EXPORT, "review_queries.csv"))
    blocked = read_csv(os.path.join(TV_EXPORT, "blocked_queries.csv"))
    fresh = sum(1 for r in keep if (r.get("in_topvisor") or "").strip().lower() == "нет")

    rb = robots_state()
    f = {
        "diag": yandex_diagnostics(),
        # robots.txt и карты сайта, проверка живьём
        "robots": rb,
        "sitemap_404": rb["sitemap_404"] if rb["sitemap_404"] is not None else -1,

        # индексация: два знаменателя, оба публикуются с подписью
        "idx_known": sum(int(s.get("indexed") or 0) for s in (d.get("sections") or [])),
        "idx_searchable": sum(int(s.get("searchable") or 0) for s in (d.get("sections") or [])),
        "idx_downloaded": sum(int(s.get("downloaded") or 0) for s in (d.get("sections") or [])),
        "idx_cat_known": _section(d, "/catalog", "indexed"),
        "idx_cat_searchable": _section(d, "/catalog", "searchable"),
        "idx_cat_rate": _section(d, "/catalog", "rate"),

        # ядро
        "core_rows": qs.get("rows", d["meta"]["totalQueries"]),
        "core_junk": qs.get("junk", 0),
        "core_queries": qs.get("total", 0),
        "core_assigned": sum(c["queries"] for c in clusters),
        "core_unassigned": qs.get("other", 0),
        "core_clusters": len(cluster_names),
        "core_groups": core_groups,
        "clusters": clusters,
        "cluster_names": cluster_names,
        "group_sizes": dict(by_group),
        "groups_not_in_site": [g for g in import_groups if g not in cluster_names],

        # позиции: два честных основания, оба публикуются с подписью
        "top10_rows": sum(1 for p in raw_pos if 1 <= p <= 10),
        "top10_rows_base": len(raw_pos),
        "top10_core": sum(1 for p in core_pos if 1 <= p <= 10),
        "top10_core_base": len(core_pos),
        "top3_core": sum(1 for p in core_pos if 1 <= p <= 3),
        "top1_core": sum(1 for p in core_pos if 1 <= p <= 1),

        # Topvisor
        "tv_keep": len(keep),
        "tv_fresh": fresh,
        "tv_already": len(keep) - fresh,
        "tv_review": len(review),
        "tv_blocked": len(blocked),
        "tv_groups": len(import_groups),
        "tv_group_names": import_groups,
        "tv_keywords": 0,
        "tv_groups_api": 0,
        "tv_group_name_api": "",
        "tv_balance": None,
        "tv_snapshot": None,
    }

    for num, base in (("top10_rows", "top10_rows_base"),
                      ("top10_core", "top10_core_base"),
                      ("top3_core", "top10_core_base"),
                      ("top1_core", "top10_core_base")):
        f[num + "_pct"] = round(f[num] / f[base] * 100, 1) if f[base] else 0

    # Индексация от знаменателя «все страницы, известные роботу». Рядом с ней
    # в отчёте живёт 60% от знаменателя «проверенная выборка». Оба верны,
    # и без подписи знаменателя они читаются как противоречие.
    f["idx_of_known_pct"] = (round(f["idx_searchable"] / f["idx_known"] * 100, 1)
                             if f["idx_known"] else 0)

    _tv_project(f)
    return f


def _tv_project(f):
    """Снимок проекта Topvisor из локальной базы. Дата обязательна:
    число без даты протухает незаметно."""
    import sqlite3
    if not os.path.isfile(TV_DB):
        return
    try:
        c = sqlite3.connect(TV_DB)
        f["tv_keywords"] = c.execute(
            "select count(*) from keywords").fetchone()[0]
        # Группы в самом проекте Topvisor. Считаем по keywords.group_id,
        # отдельной таблицы групп в базе нет.
        f["tv_groups_api"] = c.execute(
            "select count(distinct group_id) from keywords").fetchone()[0]
        f["tv_group_name_api"] = (c.execute(
            "select group_name from keywords limit 1").fetchone() or ["-"])[0]
        b = c.execute(
            "select balance_all, ts from balance_snapshots order by ts desc limit 1").fetchone()
        if b:
            f["tv_balance"] = float(b[0])
            f["tv_snapshot"] = str(b[1])[:10]
        c.close()
    except Exception as e:
        print("Topvisor db: %s" % e, file=sys.stderr)


def phrases():
    """Готовые формулировки. Один раз формулируем, везде одинаково."""
    f = collect()
    n_imp, n_cl = f["core_queries"], f["core_groups"]
    return {
        "core": "%d %s в %d %s" % (
            n_imp, plural(n_imp, "запрос", "запроса", "запросов"),
            n_cl, in_groups(n_cl)),
        "core_dat": "%d %s в %d %s, из них %d в корзине «%s»" % (
            n_imp, plural(n_imp, "запрос", "запроса", "запросов"),
            n_cl, in_groups(n_cl), f["core_unassigned"], OTHER_GROUP),
        "import": "%d %s в %d %s" % (
            f["tv_keep"], plural(f["tv_keep"], "фраза", "фразы", "фраз"),
            f["tv_groups"], in_groups(f["tv_groups"])),
        "top10_rows": "%d из %d строк выгрузки (%.0f%%)" % (
            f["top10_rows"], f["top10_rows_base"], f["top10_rows_pct"]),
        "top10_core": "%d из %d (%.0f%%)" % (
            f["top10_core"], f["top10_core_base"], f["top10_core_pct"]),
        "idx_known": "%d из %s страниц, известных роботу (%.1f%%)" % (
            f["idx_searchable"], _sp(f["idx_known"]), f["idx_of_known_pct"]),
        "robots": ("%d строк Sitemap в robots.txt, отдают 404 все %d, проверено %s"
                   % (f["robots"]["sitemap_lines"], f["robots"]["sitemap_404"],
                      f["robots"]["checked_at"]))
        if f["robots"]["sitemap_lines"] else
        "состояние robots.txt не проверено, запусти fetch_robots_state.py",
    }


def main():
    f = collect()
    p = phrases()
    print("=== ИНДЕКСАЦИЯ ===")
    print("  в поиске                 %d" % f["idx_searchable"])
    print("  известно роботу          %d" % f["idx_known"])
    print("  от известных             %s" % p["idx_known"])
    print("  каталог: в поиске %s от %s известных, %.1f%%"
          % (f["idx_cat_searchable"], f["idx_cat_known"], f["idx_cat_rate"]))
    print("  скачано роботом          %d" % f["idx_downloaded"])
    print()
    print("=== ЯДРО (Вебмастер) ===")
    print("  строк выгрузки            %d" % f["core_rows"])
    print("  из них мусор              %d" % f["core_junk"])
    print("  реальных запросов         %d" % f["core_queries"])
    print("  разложено по кластерам    %d в %d кластерах" % (f["core_assigned"], f["core_clusters"]))
    print("  «%s» без кластера        %d" % (OTHER_GROUP, f["core_unassigned"]))
    print("  групп всего               %d" % f["core_groups"])
    print("  ТОП-10 по выгрузке        %s" % p["top10_rows"])
    print("  ТОП-10 по ядру            %s" % p["top10_core"])
    print()
    print("=== TOPVISOR ===")
    print("  корзина KEEP              %d (новых %d, уже в проекте %d)"
          % (f["tv_keep"], f["tv_fresh"], f["tv_already"]))
    print("  корзина REVIEW            %d" % f["tv_review"])
    print("  корзина BLOCK             %d" % f["tv_blocked"])
    print("  групп в CSV импорта       %d" % f["tv_groups"])
    print("  ключей в проекте Topvisor %d в %d %s (%s)"
          % (f["tv_keywords"], f["tv_groups_api"],
             plural(f["tv_groups_api"], "группе", "группах", "группах"),
             f["tv_group_name_api"] or "без названия"))
    if f["tv_balance"] is not None:
        print("  баланс                    %.0f руб, снимок %s"
              % (f["tv_balance"], f["tv_snapshot"]))
    if f["groups_not_in_site"]:
        print("  группы не на сайте        %s" % ", ".join(f["groups_not_in_site"]))
    print()
    print("=== ДИАГНОСТИКА ПАНЕЛИ (вердикт Яндекса) ===")
    dg = f["diag"]
    if dg["checked"]:
        print("  проверено проблем      %d, из них Яндекс считает проблемными %d"
              % (dg["total"], len(dg["present"])))
        for x in dg["present"]:
            print("     %-28s %-18s %s" % (x["id"], x["severity"], x["updated"]))
    else:
        print("  НЕ ПРОВЕРЕНО: %s" % dg["reason"])

    print()
    print("=== ROBOTS.TXT (проверка живьём) ===")
    r = f["robots"]
    if r.get("checked_at"):
        print("  проверено             %s" % r["checked_at"])
        print("  строк Sitemap         %s" % r["sitemap_lines"])
        print("  из них отдают 404     %s" % r["sitemap_404"])
        print("  рабочих правил Disallow %s" % r["disallow_count"])
        print("  источник              %s" % r["source"])
    else:
        print("  НЕ ПРОВЕРЕНО: %s" % r["source"])
    print()
    print("=== ФОРМУЛИРОВКИ ===")
    for k, v in p.items():
        print("  %-12s %s" % (k, v))
    return 0


if __name__ == "__main__":
    sys.exit(main())
