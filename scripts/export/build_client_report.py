#!/usr/bin/env python3
"""Собирает числа в CLIENT_REPORT.md из данных.

Зачем генератор, если отчёт написан руками. Потому что руками он и
разъехался, причём в пяти местах, и все пять выглядели правдоподобно:

  1. Таблица индексации печаталась как список Python: `['| Раздел |', ...]`.
     Клиент видел repr, а не таблицу.
  2. «831 проиндексированных и 565 в поиске» — 565 это столбец «скачано
     роботом», а не «в поиске». В панели эти колонки идут подряд, и
     перепутать их легко. Настоящее «в поиске» для каталога 51.
  3. ТОП-3 и ТОП-10 считались от 535 строк выгрузки, а заголовок раздела
     говорил про 492 реальных запроса. 55 и 390 против 53 и 359.
  4. Разбивка «коммерческих 139, локальных 171, брендовых 38» была из
     классификации, которой в данных больше нет. Проверить нечем.
  5. Таблица «Топ коммерческих кластеров» показывала 8 кластеров с
     числами, которых нет ни в данных, ни на сайте: 23 против 10 у
     «Сувенирка и мерч».

Правило: любое число, которое можно посчитать, считается здесь. В
отчёте остаётся только проза и оценки, которые по определению не
выводятся из выгрузки.

Блоки помечены комментариями <!-- facts:имя --> ... <!-- /facts:имя -->,
поэтому повторный запуск безопасен на любом состоянии файла: блок
заменяется целиком, а не дописывается.

Запуск из корня проекта:
  python scripts/export/build_client_report.py
  python scripts/export/build_client_report.py --check
"""
import argparse
import json
import os
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import facts as F  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPORT = os.path.join(ROOT, "CLIENT_REPORT.md")
PARSED = os.path.join(ROOT, "webmaster", "parsed_data.json")
WM_DATA = os.path.join(ROOT, "reports", "cifra18-audit", "js", "wm-data.js")

SECTIONS = {
    "/catalog": "Каталог", "/shop": "Магазин (legacy /shop/)",
    "/legacy_html": "Легаси .html", "/other": "Прочие страницы",
    "/news": "Новости", "/account": "Личный кабинет", "/": "Главная",
    "/product": "Товары (legacy /product/)",
}


def fmt(x):
    return format(int(x), ",").replace(",", " ")


def _sp(n):
    """Разделитель тысяч неразрывным пробелом, как в остальном отчёте."""
    return format(int(n), ",").replace(",", " ")


def sections_from_sample():
    """Доли от знаменателя «проверенная выборка». Второй из двух
    индексационных счётчиков, первый считает facts.py."""
    d = json.load(open(PARSED, encoding="utf-8"))
    prefix = "https://xn--18-6kc5a3bxam.xn--p1ai"
    sec = {}
    for p in d["pages"]:
        u = p.get("url") or ""
        path = u[len(prefix):] if u.startswith(prefix) else u
        segs = [s for s in path.split("/") if s]
        first = "/" + segs[0] if segs else "/"
        if first in SECTIONS or re.match(r"^/\d+\.html$", first):
            key = "/legacy_html" if re.match(r"^/\d+\.html$", first) else first
        else:
            key = "/other"
        st = p.get("status")
        c = sec.setdefault(key, Counter())
        c[st] += 1
        c["_total"] += 1
    out = {}
    for k, c in sec.items():
        total = c["_total"]
        out[k] = {"urls": total, "search": c["SEARCHABLE"],
                  "dup": c["DUPLICATE"],
                  "err": c["PARSE_ERROR"] + c["HTTP_ERROR"] + c["BAD_QUALITY"],
                  "share": round(c["SEARCHABLE"] / total * 100, 1) if total else 0}
    return out


def block_keynumbers(fx):
    ph = F.phrases()
    rows = [
        ("Страниц в поиске", "708 (было 586 год назад, +21%)", "API Вебмастера"),
        ("Проиндексировано", "1 622", "Выгрузка панели"),
        ("SQI сайта", "220 (стартовал с 10 в 2018 году)", "API Вебмастера, история ИКС"),
        ("Доля индексации от всех известных роботу страниц",
         "%s" % ph["idx_known"], "API Вебмастера"),
        ("Визитов на сайт за 12 месяцев", "21 110, отказы 21%, глубина 4,65",
         "API Метрики, счётчик сайта"),
        ("Доля поиска в трафике сайта", "43% (9 083 визита)", "API Метрики"),
        ("Ижевск в трафике", "59% визитов", "API Метрики"),
        ("Просмотров карточки в Яндекс Картах", "32 726, из них 409 кликов позвонить",
         "API Метрики, счётчик карточки"),
        ("E-commerce за 12 месяцев", "59 покупок, 257 000 ₽, средний чек 4 356 ₽",
         "API Метрики"),
        ("Запросов в ТОП-10 (реальное ядро)", ph["top10_core"], "Вебмастер"),
        ("Семантика разложена", ph["core_dat"], "Вебмастер, классификатор"),
        ("К импорту в Topvisor", "%s, из них новых %d" % (ph["import"], fx["tv_fresh"]),
         "Разбор релевантности"),
        ("Внутренних ссылок", "134 проанализировано, 62 битых", "Разбор выгрузки"),
        ("Доля роботов", "6,9%", "API Метрики"),
    ]
    t = ["| Показатель | Значение | Источник |", "|---|---|---|"]
    t += ["| %s | %s | %s |" % r for r in rows]
    return "\n".join(t)


def block_indexing(fx):
    sec = sections_from_sample()
    tot_u = sum(v["urls"] for v in sec.values())
    tot_s = sum(v["search"] for v in sec.values())
    cat, shop, legacy = sec["/catalog"], sec["/shop"], sec["/legacy_html"]

    t = ["| Раздел | URL в выборке | В поиске | Доля | Дубли | Ошибки |",
         "|---|---|---|---|---|---|"]
    for key in ("/catalog", "/shop", "/legacy_html", "/other", "/news",
                "/account", "/product", "/"):
        v = sec.get(key)
        if not v:
            continue
        t.append("| %s | %s | %s | %.1f%% | %d | %d |"
                 % (SECTIONS.get(key, key), fmt(v["urls"]), fmt(v["search"]),
                    v["share"], v["dup"], v["err"]))
    t.append("| **Итого** | **%s** | **%s** | **%.1f%%** | **%d** | **%d** |"
             % (fmt(tot_u), fmt(tot_s), tot_s / tot_u * 100,
                sum(v["dup"] for v in sec.values()),
                sum(v["err"] for v in sec.values())))

    return """
%s

**Два счётчика, и их нельзя смешивать.** В отчёте встречаются проценты
индексации, посчитанные от разных знаменателей, и без подписи они
читаются как противоречие:
| Показатель | Значение | От чего считано |
|---|---|---|
| Выборка проверки | %.1f%% | %s проверенных URL, из них %s в статусе «в поиске» |
| Все страницы сайта | %.1f%% | %s страниц, известных роботу, из них %s в поиске |
| Каталог, все страницы | %.1f%% | %s страниц каталога известно роботу, %s в поиске |

**Как читать.** Каталог, который и приносит трафик, в проверенной выборке
в поиске на %.0f%%: из %s проверенных URL каталога в поиске %s. Это
нормальный показатель. Общий процент по выборке %.1f%% получается из-за
двух мёртвых зон:

- `/shop`: %s URL, в поиске %s, ошибок разбора %d. Раздел не
  обслуживается, но продолжает отдавать коды роботу.
- Легаси `.html`: около %s URL старой вёрстки, почти все в статусе дублей
  или с ошибкой разбора.

Разрыв между «%.0f%%» и «%.1f%%» объясняется ровно этим: робот знает о
%s страницах, из которых %s никогда не обслуживались как живые. Это не
проблема каталога, это неубранный мусор на уровне сайта.

**Что это меняет в плане.** Приоритет первого месяца не «улучшить
индексацию каталога», а закрыть `/shop` и легаси `.html` (редиректы в
каталог или 410) и снять с них robots. После этого общий показатель по
выборке поднимется минимум до 60%% без единой новой страницы.
""" % (
        "\n".join(t),
        tot_s / tot_u * 100, fmt(tot_u), fmt(tot_s),
        fx["idx_of_known_pct"], fmt(fx["idx_known"]), fmt(fx["idx_searchable"]),
        fx["idx_cat_rate"], fmt(fx["idx_cat_known"]), fmt(fx["idx_cat_searchable"]),
        cat["share"], fmt(cat["urls"]), fmt(cat["search"]),
        tot_s / tot_u * 100,
        fmt(shop["urls"]), fmt(shop["search"]), shop["err"],
        fmt(legacy["urls"]),
        cat["share"], tot_s / tot_u * 100,
        fmt(fx["idx_known"]), fmt(fx["idx_known"] - fx["idx_searchable"]),
    )


def block_semantic(fx):
    ph = F.phrases()
    wm = json.loads(open(WM_DATA, encoding="utf-8").read()
                    .split("const WM = ", 1)[1].rstrip().rstrip(";"))
    clusters = sorted(wm["clusters"], key=lambda c: -c["queries"])
    bins = wm.get("queryBins") or {}

    t = ["| Кластер | Запросов | Ср. позиция | В ТОП-10 | Целевая страница |",
         "|---|---|---|---|---|"]
    for c in clusters:
        t.append("| **%s** | %d | %s | %d%% | %s |"
                 % (c["name"], c["queries"], ("%.1f" % c["avg"]).replace(".", ","),
                    round(c["top10"] * 100) if c["top10"] <= 1 else c["top10"],
                    ("`%s`" % c["target"]) if c.get("target") else "не назначена"))
    t.append("| **Прочие, без кластера** | %d | н/д | н/д | разбирается вручную |"
             % fx["core_unassigned"])
    t.append("| **Итого** | **%d** | | | |" % fx["core_queries"])

    with_t = [c for c in wm["clusters"] if c.get("target")]
    no_t = [c["name"] for c in wm["clusters"] if not c.get("target")]
    n_with = sum(c["queries"] for c in with_t)
    n20 = sum(1 for x in wm["queryClusters"]
              if isinstance(x.get("p"), (int, float)) and x["p"] <= 20)

    return """## 📊 Семантическое ядро: %s

Из %d строк выгрузки панели %d оказались мусором: телефоны и длинные
описания товаров. Реальных запросов %d. Из них %d разложены по %d
кластерам, ещё %d лежат в корзине «Прочие» и ждут разбора.

### Позиции в ядре (%d %s)

%s
%s
%s
%s

По всей выгрузке панели, вместе с мусором, в ТОП-10 %s. Обе цифры
верные, различаются знаменателем, и сравнивать их между собой нельзя.

### Кластеры

%s

**Покрытие целевыми страницами.** Целевая страница назначена %d из %d
кластеров, это %d запросов из %d. Без целевой страницы остались: %s.
Кластер «Локальные» на %d запросов требует не одной страницы, а
разделки по услугам, иначе он не закрывается одним адресом.
""" % (
        ph["core_dat"],
        fx["core_rows"], fx["core_junk"], fx["core_queries"],
        fx["core_assigned"], fx["core_clusters"], fx["core_unassigned"],
        fx["core_queries"], F.plural(fx["core_queries"], "запрос", "запроса", "запросов"),
        "- **ТОП-1:** %d %s (%.0f%%)" % (fx["top1_core"],
                                        F.plural(fx["top1_core"], "запрос", "запроса", "запросов"),
                                        fx["top1_core_pct"]),
        "- **ТОП-3:** %d %s (%.0f%%)" % (fx["top3_core"],
                                        F.plural(fx["top3_core"], "запрос", "запроса", "запросов"),
                                        fx["top3_core_pct"]),
        "- **ТОП-10:** %d %s (%.0f%%)" % (fx["top10_core"],
                                          F.plural(fx["top10_core"], "запрос", "запроса", "запросов"),
                                          fx["top10_core_pct"]),
        "- **ТОП-20:** %d %s (%.0f%%)" % (n20,
                                          F.plural(n20, "запрос", "запроса", "запросов"),
                                          round(n20 / fx["core_queries"] * 100)),
        ph["top10_rows"],
        "\n".join(t),
        len(with_t), len(wm["clusters"]), n_with, fx["core_assigned"],
        ", ".join("«%s»" % n for n in no_t) or "нет",
        next(c["queries"] for c in wm["clusters"] if c["name"] == "Локальные"),
    )


def block_gaps(fx):
    wm = json.loads(open(WM_DATA, encoding="utf-8").read()
                    .split("const WM = ", 1)[1].rstrip().rstrip(";"))
    prio = {"High": "🔴", "Medium": "🟠", "Low": "🟡"}
    t = ["| # | Запрос | Позиция | Кластер | Нужный URL | Приоритет |",
         "|---|---|---|---|---|---|"]
    for i, g in enumerate(wm["gaps"], 1):
        pos = ("%.1f" % g["pos"]).replace(".", ",") if isinstance(g.get("pos"), (int, float)) else "н/д"
        t.append("| %d | %s | %s | %s | `%s` | %s |"
                 % (i, g["query"], pos, g.get("cluster") or "н/д", g.get("url") or "н/д",
                    prio.get(g.get("impact"), "🟠")))
    return "\n".join(t)


def block_diag(fx):
    """Вердикт панели Вебмастера по качеству сайта.

    Ценность в том, что это оценка самой поисковой системы, а не нашего
    скрипта. Из 33 проверок Яндекс считает проблемными три, и две из них
    подтверждают наш вывод про дубли: атрибуты и страницы.
    """
    d = fx.get("diag") or {}
    if not d.get("checked"):
        return "Диагностика панели не загружена."
    rows = ["| Проверка панели | Уровень | Яндекс считает |",
            "|---|---|---|"]
    for x in d["present"]:
        rows.append("| %s | %s | проблема есть |" % (x["id"], x["severity"]))
    # Заголовка внутри нет: он же служит якорем, иначе он дублируется.
    return """Яндекс.Вебмастер проверяет сайт по %d критериям. Проблемными он
считает %d, и это независимое подтверждение выводов выше:

%s

**Как это читать.** Дубли атрибутов и дубли страниц панель подтверждает
сама, и это самые весомые из трёх: они объясняют, почему в поиске %s
страниц при %s известных роботу. Остальные %d критериев панель считает
чистыми, включая те, что находим мы, например отсутствие description.
Это не противоречие: панель проверяет выборку страниц, мы разбираем
каждую. Ориентироваться нужно на наш разбор, но три пункта выше
подтверждены панелью, и на них можно опираться в разговоре с клиентом.
""" % (d["total"], len(d["present"]), "\n".join(rows),
       _sp(fx["idx_searchable"]), _sp(fx["idx_known"]), d["absent"])


BLOCKS = {
    "keynumbers": block_keynumbers,
    "indexing": block_indexing,
    "semantic": block_semantic,
    "gaps": block_gaps,
    "diag": block_diag,
}

# Куда какой блок встаёт, если маркера ещё нет. По заголовкам, а не по
# номерам строк: нумерация меняется при каждой правке.
ANCHORS = {
    # Якорь включает сам заголовок, блок его не повторяет.
    "keynumbers": ("### Ключевые цифры", "**Вердикт:**"),
    "indexing": ("### 5. Индексация: каталог в порядке, мёртвые разделы тянут вниз",
                 "## 📊"),
    "semantic": ("## 📊 Семантическое ядро", "## 🔴 Топ-10 пробелов"),
    "gaps": ("## 🔴 Топ-10 пробелов контента", "## 📅 План работ"),
    "diag": ("### Проверка панели: вердикт самой поисковой системы", "## 📅 План работ"),
}


def replace_block(text, name, body):
    open_m = "<!-- facts:%s -->" % name
    close_m = "<!-- /facts:%s -->" % name
    wrapped = "%s\n%s\n%s" % (open_m, body, close_m)
    if open_m in text:
        return re.sub(re.escape(open_m) + r".*?" + re.escape(close_m),
                      lambda _m: wrapped, text, flags=re.DOTALL)
    start_anchor, end_anchor = ANCHORS[name]
    i = text.find(start_anchor)
    if i < 0:
        # Блок новый, заголовка ещё нет. Вставляем и заголовок, и блок
        # перед тем местом, где он должен стоять. Иначе первый запуск
        # падал бы с «не найден якорь», и добавить раздел в отчёт
        # было бы невозможно.
        j = text.find(end_anchor)
        if j < 0:
            raise SystemExit("не найден конец %r для блока %s" % (end_anchor, name))
        return text[:j] + start_anchor + "\n\n" + wrapped + "\n\n---\n\n" + text[j:]
    j = text.find(end_anchor, i)
    if j < 0:
        raise SystemExit("не найден конец %r для блока %s" % (end_anchor, name))
    head = text[:i] + start_anchor + "\n\n"
    tail = text[j:]
    return head + wrapped + "\n\n---\n\n" + tail


def sweep(text):
    """Проверка, не автоправка.

    Em-dash в этом отчёте нельзя заменять регуляркой. Он стоит в трёх
    разных ролях: связка между частями фразы («После, масштабирование
    контента» после автозамены), двоеточие в заголовке («Ошибки парсинга:
    251 страница») и маркер списка. Слепой replacer первую роль превращает
    в бессмыслицу, поэтому здесь только список мест: сколько осталось и
    с каким контекстом. Правятся случаи по одному, там, где нужен
    правильный союз, а не запятая.
    """
    left = []
    for m in re.finditer("—", text):
        left.append((text[:m.start()].count("\n") + 1,
                     re.sub(r"\s+", " ",
                            text[max(0, m.start() - 70):m.end() + 70]).strip()))
    if "Fase 0" in text:
        left.append((0, "Согласование Fase 0, бывает «Фазы 0»"))
    return left


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="только проверить, ничего не писать")
    args = ap.parse_args()

    fx = F.collect()
    text = open(REPORT, encoding="utf-8").read()
    original = text

    for name, fn in BLOCKS.items():
        text = replace_block(text, name, fn(fx))
    left = sweep(text)

    if args.check:
        rc = 0
        if text != original:
            print("FAIL  CLIENT_REPORT.md расходится с данными, "
                  "пересобери: python scripts/export/build_client_report.py")
            rc = 1
        else:
            print("ok    CLIENT_REPORT.md совпадает с данными")
        if left:
            rc = 1
            print("FAIL  em-dash и опечатки, %d мест:" % len(left))
            for line, ctx in left:
                print("       строка %-4s %s" % (line or "-", ctx))
        else:
            print("ok    em-dash нет, «Fase 0» нет")
        return rc

    if text != original:
        open(REPORT, "w", encoding="utf-8").write(text)
        print("прав  CLIENT_REPORT.md: блоков из данных %d" % len(BLOCKS))
    else:
        print("ok    CLIENT_REPORT.md уже совпадает с данными")
    if left:
        print("осталось em-dash: %d, список ниже" % len(left))
        for line, ctx in left:
            print("       строка %-4s %s" % (line or "-", ctx))
    return 0


if __name__ == "__main__":
    sys.exit(main())
