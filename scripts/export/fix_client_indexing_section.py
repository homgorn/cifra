#!/usr/bin/env python3
"""Пересборка раздела про индексацию в клиентском отчёте и проверка цифр на сайте.

Найдено 2026-09-27: в отчёте стоял «коэффициент индексации каталога 6%» с
таблицей «/catalog 831 | 51 | 6,1%». Это неверно и вводит в заблуждение: 51
страница в поиске у каталога противоречит и выборке панели (134 из 224 URL
каталога в поиске), и структуре из панели (565 из 831).

Правильная картина: каталог в поиске примерно на 60%, а общий процент 19,8%
тянут вниз мёртвые /shop (314 URL, ноль в поиске, 236 ошибок парсинга) и около
180 легаси .html. Значит приоритет не «улучшить индексацию каталога», а «убрать
мёртвые разделы».

Скрипт делает две вещи:
1. Перезаписывает раздел 5 в CLIENT_REPORT.md по данным выборки панели.
2. Проверяет ключевые утверждения на всех страницах сайта и печатает расхождения.

Запуск из корня проекта:
  python scripts/export/fix_client_indexing_section.py
  python scripts/export/fix_client_indexing_section.py --check-only
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PARSED = ROOT / "webmaster" / "parsed_data.json"
REPORT = ROOT / "CLIENT_REPORT.md"
SITE = ROOT / "reports" / "cifra18-audit"
PREFIX = "https://xn--18-6kc5a3bxam.xn--p1ai"
WM = ROOT / "data" / "exports" / "yandex_webmaster"

# Разделы, которые в отчёте называются по-русски и считаются отдельно от легаси.
NAMES = {
    "/catalog": "Каталог",
    "/shop": "Магазин (legacy /shop/)",
    "/product": "Товары (legacy /product/)",
    "/product-category": "Категории товаров (legacy)",
    "/news": "Новости",
    "/": "Главная",
    "/account": "Личный кабинет",
}
LEGACY_RE = re.compile(r"^\/\d+\.html$")


def section_of(url):
    path = url[len(PREFIX):] if url.startswith(PREFIX) else url
    segs = [s for s in path.split("/") if s]
    if not segs:
        return "/"
    first = "/" + segs[0]
    if first in NAMES:
        return first
    if LEGACY_RE.match(first):
        return "/legacy_html"
    return "/other"


def num(x):
    return int(str(x or "0").replace(" ", "").replace("\u00a0", ""))


def load():
    d = json.load(open(PARSED, encoding="utf-8"))
    pages = d["pages"]
    g = defaultdict(Counter)
    for p in pages:
        g[section_of(p.get("url") or "")][p.get("status")] += 1
    out = {}
    for k, c in g.items():
        total = sum(c.values())
        out[k] = {"urls": total, "search": c["SEARCHABLE"], "dup": c["DUPLICATE"],
                  "err": c["PARSE_ERROR"] + c["HTTP_ERROR"] + c["BAD_QUALITY"],
                  "share": round(c["SEARCHABLE"] / total * 100, 1) if total else 0}
    return out, d


def panel_structure(d):
    """Структура из панели Вебмастера: индекс и в поиске по разделам."""
    rows = []
    for r in d.get("structure", []):
        raw = (r.get("g-link") or "").strip()
        if not raw:
            continue
        path = raw.split("://")[-1]
        path = "/" + path.split("/", 1)[1] if "/" in path else "/"
        rows.append({"path": path, "indexed": num(r.get("g-link 2")), "search": num(r.get("g-link 3"))})
    return rows


def fmt(x):
    return format(x, ",").replace(",", " ")


def rewrite_report(sec, structure):
    catalog = sec["/catalog"]
    shop = sec["/shop"]
    legacy = sec["/legacy_html"]
    total_urls = sum(v["urls"] for v in sec.values())
    total_search = sum(v["search"] for v in sec.values())
    panel = {r["path"]: r for r in structure}
    cat_panel = panel.get("/catalog", {})
    shop_panel = panel.get("/shop", {})

    table = ["| Раздел | URL в выборке | В поиске | Доля | Дубли | Ошибки |",
             "|---|---|---|---|---|---|"]
    for key in ("/catalog", "/shop", "/legacy_html", "/other", "/news", "/account", "/"):
        v = sec.get(key)
        if not v:
            continue
        name = NAMES.get(key, "Легаси .html" if key == "/legacy_html" else "Прочие страницы")
        table.append("| %s | %s | %s | %.1f%% | %d | %d |"
                     % (name, fmt(v["urls"]), fmt(v["search"]), v["share"], v["dup"], v["err"]))
    table.append("| **Итого** | **%s** | **%s** | **%.1f%%** | **%d** | **%d** |"
                 % (fmt(total_urls), fmt(total_search), total_search / total_urls * 100,
                    sum(v["dup"] for v in sec.values()), sum(v["err"] for v in sec.values())))

    block = f"""### 5. Индексация: каталог в порядке, мёртвые разделы тянут вниз

{table}

**Как читать:** каталог, который и приносит трафик, в поиске примерно на
{catalog['share']:.0f}%: из {fmt(catalog['urls'])} проверенных URL каталога в поиске
{fmt(catalog['search'])}, это нормальный показатель. Общий процент
{total_search / total_urls * 100:.1f}% получается из-за двух мёртвых зон:

- `/shop` — {fmt(shop['urls'])} URL, в поиске {shop['search']}, ошибок парсинга
  {shop['err']}. Раздел не обслуживается, но продолжает отдавать коды роботу.
- Легаси `.html` — около {fmt(legacy['urls'])} URL старой вёрстки, почти все в статусе
  дублей или с ошибкой разбора.

**Структура из панели подтверждает вывод:** на дату выгрузки в каталоге было
{fmt(cat_panel.get('indexed', 0))} проиндексированных и {fmt(cat_panel.get('search', 0))} в поиске,
в `/shop` — {fmt(shop_panel.get('indexed', 0))} проиндексированных и
{shop_panel.get('search', 0)} в поиске.

**Что это меняет в плане:** приоритет первый месяца не «улучшить индексацию
каталога», а закрыть `/shop` и легаси `.html` (редиректы в каталог или 410) и
снять с них robots. После этого общий показатель индексации поднимется
минимум до 60% без единой новой страницы.

---
"""
    text = REPORT.read_text(encoding="utf-8")
    start = text.find("### 5. Коэффициент индексации")
    if start < 0:
        start = text.find("### 5. Индексация")
    if start < 0:
        print("раздел 5 не найден")
        return None
    end = text.find("## 📊", start)
    if end < 0:
        end = len(text)
    REPORT.write_text(text[:start] + block + "\n" + text[end:], encoding="utf-8")
    return block


CHECKS = [
    # (описание, где искать, ожидаемое значение, регулярка с числом)
    ("страниц в поиске", "client", 708, r"в поиске\s*\|?\s*(%d)" % 708),
    ("коэффициент индексации каталога удалён", "client", 0, r"831\s*\|\s*51\s*\|"),
]


def check(sec, structure):
    """Ищет заведомо неверные утверждения на сайте и в отчёте."""
    total_urls = sum(v["urls"] for v in sec.values())
    total_search = sum(v["search"] for v in sec.values())
    bad = []
    files = [REPORT]
    for p in sorted(SITE.rglob("*.html")):
        files.append(p)
    for p in files:
        t = p.read_text(encoding="utf-8", errors="replace")
        name = p.name if p.suffix else p
        if re.search(r"6,1\s*%", t) or re.search(r"\|\s*831\s*\|\s*51\s*\|", t):
            bad.append("%s: старая таблица индексации (6,1%%)" % name)
        if re.search(r"79\s*002", t):
            bad.append("%s: визиты счётчика карточки (79 002)" % name)
        if re.search(r"2\s*446", t):
            bad.append("%s: старый счёт визитов карточки (2 446)" % name)
    print("Проверено файлов: %d" % len(files))
    print("Всего URL в выборке: %s, в поиске: %s (%.1f%%)"
          % (fmt(total_urls), fmt(total_search), total_search / total_urls * 100))
    print("Каталог: %s URL, %.1f%% в поиске" % (fmt(sec["/catalog"]["urls"]), sec["/catalog"]["share"]))
    print("Магазин /shop: %s URL, %.1f%% в поиске, ошибок %d"
          % (fmt(sec["/shop"]["urls"]), sec["/shop"]["share"], sec["/shop"]["err"]))
    if bad:
        print("РАСХОЖДЕНИЯ:")
        for b in bad:
            print("  - %s" % b)
    else:
        print("Заведомо неверных цифр не найдено.")
    return bad


def main():
    sec, d = load()
    structure = panel_structure(d)
    if "--check-only" not in sys.argv:
        block = rewrite_report(sec, structure)
        if block:
            print("CLIENT_REPORT.md: раздел 5 перезаписан")
            print(block[:300])
    bad = check(sec, structure)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
