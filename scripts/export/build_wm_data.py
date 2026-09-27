#!/usr/bin/env python3
"""Build js/wm-data.js for the cifra18 audit report site from webmaster exports.

Reads brain/wiki/webmaster_analytics/exports/*.csv and writes
reports/cifra18-audit/js/wm-data.js as `const WM = {...};`
All numbers on the wm-* pages and charts come from this file.
"""
import csv
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXP = os.path.join(ROOT, "brain", "wiki", "webmaster_analytics", "exports")
OUT = os.path.join(ROOT, "reports", "cifra18-audit", "js", "wm-data.js")


def read_csv(name):
    path = os.path.join(EXP, name)
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_rows(path):
    """Читает CSV по полному пути, а не по имени в каталоге экспортов."""
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def count_rows(name):
    return len(read_csv(name))


TOTAL_QUERIES = 535   # строк в выгрузке панели, до отсева мусора


# --- 1. Page statuses (one export file per status) ---
status_files = {
    "SEARCHABLE": "searchable_pages.csv",
    "DUPLICATE": "duplicate_pages.csv",
    "PARSE_ERROR": "parse_error_pages.csv",
    "REDIRECT_NOTSEARCHABLE": "redirect_pages.csv",
    "OTHER": "other_pages.csv",
    "BAD_QUALITY": "bad_quality_pages.csv",
    "HTTP_ERROR": "http_error_pages.csv",
}
statuses = {k: count_rows(v) for k, v in status_files.items()}
total_pages = sum(statuses.values())

# --- 2. Sections ---
sections = []
for r in read_csv("site_structure.csv"):
    try:
        sections.append({
            "section": r["Section"],
            "indexed": int(r["Indexed"]),
            "downloaded": int(r["Downloaded"]),
            "searchable": int(r["Searchable"]),
            "rate": float(r["Indexation_Rate_%"]),
        })
    except (ValueError, KeyError):
        continue
sections_by_indexed = sorted(
    [s for s in sections if not s["section"].startswith("http")],
    key=lambda s: s["indexed"], reverse=True)[:8]

# --- 3. Queries (positions + shows + clicks + CTR) ---
queries = []
for r in read_csv("all_queries_positions.csv"):
    try:
        queries.append({
            "q": r["Query"],
            "avg": float(r["Avg_Position"]),
            "mn": float(r["Min_Position"]),
            "mx": float(r["Max_Position"]),
            "days": int(r["Days_With_Data"]),
            "shows": int(r["Shows_Total"]),
            "clicks": int(r["Clicks_Total"]),
            "ctr": float(r["CTR_%"]),
            "detail": r["Positions_Detail"],
        })
    except (ValueError, KeyError):
        continue

DAYS = ["2026-09-14", "2026-09-15", "2026-09-16", "2026-09-17",
        "2026-09-18", "2026-09-19", "2026-09-20"]
shows_daily = {d: 0 for d in DAYS}
clicks_daily = {d: 0 for d in DAYS}
for r in read_csv("query_shows_daily.csv"):
    for d in DAYS:
        try:
            shows_daily[d] += int(r[d] or 0)
        except (ValueError, KeyError):
            pass
for r in read_csv("query_clicks_daily.csv"):
    for d in DAYS:
        try:
            clicks_daily[d] += int(r[d] or 0)
        except (ValueError, KeyError):
            pass

bins = {"1": 0, "1-3": 0, "3-5": 0, "5-10": 0, "10-20": 0, "20+": 0}
for q in queries:
    a = q["avg"]
    if a <= 1.0:
        bins["1"] += 1
    elif a <= 3.0:
        bins["1-3"] += 1
    elif a <= 5.0:
        bins["3-5"] += 1
    elif a <= 10.0:
        bins["5-10"] += 1
    elif a <= 20.0:
        bins["10-20"] += 1
    else:
        bins["20+"] += 1
top1 = bins["1"]
top3 = bins["1"] + bins["1-3"]
top10 = top3 + bins["3-5"] + bins["5-10"]

by_q = {q["q"]: q for q in queries}
MONEY = ["визитки ижевск", "печать визиток ижевск", "типография ижевск",
         "типография цифра", "печать визиток", "ксерокопия ижевск",
         "печатный салон ижевск", "пакеты на заказ", "печать на пакетах ижевск",
         "цифра ижевск", "полиграфия ижевск", "пресс волл"]
money = [dict(by_q[k], q=k) for k in MONEY if k in by_q][:10]

trend = []
for m in money[:6]:
    series = {d: None for d in DAYS}
    for part in (m["detail"] or "").split(";"):
        part = part.strip()
        if ":" in part:
            d, v = part.split(":", 1)
            d = d.strip()
            if d in series:
                try:
                    series[d] = float(v)
                except ValueError:
                    pass
    trend.append({"q": m["q"], "series": [series[d] for d in DAYS]})

def classify_pattern(url):
    u = url or ""
    if u.startswith("https://xn--18-6kc5a3bxam.xn--p1ai/"):
        u = u[len("https://xn--18-6kc5a3bxam.xn--p1ai/") - 1:]
    import re
    if re.match(r"^/\d+\.html", u):
        return "numericHtml"
    if "detail.php" in u:
        return "detailPhp"
    if "/shop/" in u:
        return "shop"
    return "other"


def pattern_counts(rows):
    from collections import Counter
    c = Counter(classify_pattern(r.get("URL", "")) for r in rows)
    return {"numericHtml": c.get("numericHtml", 0), "detailPhp": c.get("detailPhp", 0),
            "shop": c.get("shop", 0), "other": c.get("other", 0)}


dupPatterns = pattern_counts(read_csv("duplicate_pages.csv"))
parsePatterns = pattern_counts(read_csv("parse_error_pages.csv"))

events_add = 0
events_delete = 0
for r in read_csv("indexing_events.csv"):
    if r.get("Event") == "ADD":
        events_add += 1
    elif r.get("Event") == "DELETE":
        events_delete += 1

# --- 4. Gaps ---
gaps = []
for r in read_csv("content_gaps_prioritized.csv"):
    try:
        gaps.append({
            "query": r["Query"],
            "pos": float(r["Avg_Position"]),
            "cluster": r["Cluster"],
            "kind": r["Missing_Page_Type"],
            "url": r["Suggested_URL"],
            "effort": r["Effort"],
            "impact": r["Impact"],
        })
    except (ValueError, KeyError):
        continue

# --- 5. Internal links ---
link_status = {r["Status"]: int(r["Count"]) for r in read_csv("internal_links_by_status.csv")}
link_total = sum(link_status.values())
link_broken = {k: v for k, v in link_status.items() if k in ("404", "500", "502")}


def short_url(u):
    u = (u or "").rstrip("/")
    return "/" + u.split("xn--18-6kc5a3bxam.xn--p1ai/")[-1] if "xn--" in u else u


broken_targets = []
for r in read_csv("internal_links_target_summary.csv")[:8]:
    try:
        broken_targets.append({"url": short_url(r["Target_URL"]),
                               "count": int(r["Broken_Inbound_Count"])})
    except (ValueError, KeyError):
        continue
image_hotlinks = count_rows("internal_links_image_hotlinks.csv")
typos = count_rows("internal_links_typos.csv")

# --- 6. Clusters ---
# Важно: раньше агрегаты по кластерам были вбиты руками в этом файле, а
# пофразовая разбивка нигде не сохранялась. Из-за этого кластеризацию нельзя
# было ни показать клиенту, ни загрузить в Topvisor. Теперь разбивка считается
# правилами по тексту запроса, агрегаты выводятся из неё же.
CLUSTER_RULES = [
    # (кластер, слова-маркеры) — порядок важен: более специфичное раньше.
    # Правила дополнены 2026-09-27 по разбору 163 фраз, которые падали
    # в «Прочие», хотя были живым спросом: уф-печать, ризография,
    # плоттерная резка, ламинация, пакеты, фотопечать, общий спрос.
    ("Мобильные стенды", ["стенд", "стенда", "стенды", "стендов", "роллап", "рол-ап",
                          "ролл", "пресс волл", "прессволл", "press wall", "павильон",
                          "выставочн", "мобильн", "ротационный", "шторка"]),
    ("Инженерная печать", ["инженерн", "чертёж", "чертёжн", "чертеж", "чертёжей",
                            "печать схем", "изготовление чертежей", "миллиметровк"]),
    ("УФ-печать и спецпечать", ["уф печат", "уф-печат", "ультрафиолет",
                                "печать на пластик", "печать на стекл", "печать на флешк",
                                "печать на металл", "печать на ткан", "тиснени",
                                "фольгирован", "выборочн", "скруглен", "софт тач",
                                "soft touch", "soft-touch", "лайтбокс", "объёмн",
                                "объемн", "световой"]),
    ("Плоттерная резка и ризография", ["плоттер", "ризограф", "лазерн резк",
                                        "лазерная резка", "вырубк", "гравиров",
                                        "фрезер", "раскрой"]),
    # Форматы и крупноформатная печать. «а2 ижевск», «печать а1», «распечатка».
    # Раньше такие фразы падали в «Локальные» или «Прочие», хотя у клиента
    # есть раздел цифровой печати.
    ("Форматы и плоттерная печать", ["распечатк", "распечата", "формат а", "формата",
                                     "листах а", "лист а", "а0", "а1", "а2", "а3",
                                     "а4", "а5", "а6", "s2", "s3", "iso а", "iso a",
                                     "по водорастворим", "флизелин", "крупноформат",
                                     "большой формат", "широкоформатн печат"]),
    ("Ламинирование", ["ламинац", "ламинир", "ламинат", "вклейк", "скрепк",
                        "переплёт", "переплет", "брошюр"]),
    ("Пакеты и упаковка", ["пакет", "пакета", "пакетах", "коробк", "упаковк",
                           "тубус", "подарочн"]),
    ("Наклейки и плёнки", ["наклейк", "стикер", "самокле", "пленк", "плёнк",
                           "пленки", "плёнки", "аппликац"]),
    ("Фотопечать", ["фотопечат", "фото на холст", "фото куб", "фотоколлаж",
                    "фотопанно", "фотообо", "пазл", "фотограф"]),
    ("Конверты", ["конверт"]),
    ("Пластиковые карты", ["пластиков карт", "карты пластиков", "кредитн карт",
                           "визитн карт пластик", "сити"]),
    ("Цифровая печать", ["цифровая печат", "цифровая типография", "цифровой принт",
                         "печать блым тонер", "печать белым тонер", "лазерн печат"]),
    ("Блокноты", ["блокнот"]),
    ("Бейджи", ["бейдж"]),
    ("Кружки и магниты", ["кружк", "магнит", "керамическ", "бутылк"]),
    ("Календари", ["календар", "ежедневник", "планинг", "недельник"]),
    ("Визитки", ["визитк", "визитн", "визит"]),
    ("Листовки и флаеры", ["листовк", "флаер", "флаеры", "флаэрок", "буклет",
                           "трафарет", "схема метро", "купоны"]),
    ("Широкоформат", ["широкоформат", "баннер", "растяжк", "холст", "постер",
                     "афиш", "лайтбокс"]),
    ("Сувенирка и мерч", ["сувенир", "хенди", "мерч", "футболк", "экосумк",
                          "ручк", "значк", "медал", "кубок", "значк"]),
    # Общий спрос: «типография», «печать», «салон печати». Идёт после
    # тематик, чтобы «визитки ижевск» осталось в «Визитках», а не здесь.
    ("Общий спрос", ["типограф", "салон печати", "печатный салон", "студия печати",
                     "услуги типографии", "мелкая типография", "печатн продукц",
                     "печатная продукция", "где печат", "где делать печат",
                     "заказать печат", "быстрая печать", "печать на заказ",
                     "печать дешево", "типография дешево", "цены на печать"]),
    ("Сравнения", [" или ", " vs ", "против", "чем отличается", "разница между",
                   "сравнение"]),
    ("Локальные", ["ижевск", "ижевска", "ижевке", "удмурт"]),
]
INFO_MARKERS = ["что такое", "что значит", "как сделать", "как печатать", "своими руками",
                "сколько стоит", "сколько времени", "какие требования", "как выбрать",
                "как отличить", "зачем нужен", "где заказать", "чем отличается",
                "как настроить", "как открыть", "как правильно", "нужно ли", "стоит ли"]


def cluster_of(q):
    t = (q or "").lower().strip()
    if not t:
        return "Прочие"
    if "цифра" in t or "цифр" in t.split() or "типо" in t and "цифра" in t:
        return "Бренд"
    for name, marks in CLUSTER_RULES:
        if any(m in t for m in marks):
            return name
    if any(m in t for m in INFO_MARKERS) or t.startswith("как ") or t.startswith("что "):
        return "Информационные"
    return "Прочие"


def is_real_query(q):
    """Отсев мусора из выгрузки панели.

    В 535 строках ядра реально сидят телефоны («+7905874-00-85»), длинные
    описания товаров и символьные свалки. Их нельзя ни показывать клиенту,
    ни загружать в Topvisor: проверка позиций по ним стоит денег."""
    t = (q or "").strip()
    if len(t) < 2 or len(t) > 90:
        return False
    if t.count(" ") > 6:
        return False
    if re.match(r"^[\+\-\d\s()]+$", t):          # только цифры и символы
        return False
    letters = sum(ch.isalpha() for ch in t)
    if letters < max(2, len(t) * 0.4):            # меньше 40% букв
        return False
    if re.search(r"[а-яa-z]{10,}\s*[а-яa-z]{10,}", t) and " " in t:
        return False                             # склейка двух длинных слов
    return True


# Целевая страница по кластеру. Разделы взяты из структуры сайта в панели
# Вебмастера; /shop исключён, он мёртвый.
CLUSTER_PAGE = {
    "Визитки": "/catalog/poligrafiya/vizitki/",
    "Кружки и магниты": "/catalog/suvenirnaya-produktsiya/pechat-na-kruzhkakh",
    "Календари": "/catalog/poligrafiya/kalendari/",
    "Листовки и флаеры": "/catalog/poligrafiya/listovki-tsifrovaya-pechat/",
    "Широкоформат": "/catalog/reklama/",
    "Мобильные стенды": "/catalog/mobilnye-stendy/",
    "Сувенирка и мерч": "/catalog/suvenirnaya-produktsiya/",
    "Инженерная печать": "/catalog/inzhenernaya-pechat/",
    "УФ-печать и спецпечать": "/catalog/poligrafiya/uf-pechat1/",
    "Плоттерная резка и ризография": "/catalog/poligrafiya/plotternaya-rezka/",
    "Форматы и плоттерная печать": "/catalog/poligrafiya/tsifrovaya-pechat/",
    "Ламинирование": "/catalog/poligrafiya/laminirovanie/",
    "Пакеты и упаковка": "/catalog/poligrafiya/pakety/",
    "Наклейки и плёнки": "/catalog/poligrafiya/pechat-na-samokleyashchikhsya-materialakh/",
    "Фотопечать": "/catalog/suvenirnaya-produktsiya/fotopaneli",
    "Конверты": "/catalog/poligrafiya/konverty/",
    "Пластиковые карты": "/catalog/poligrafiya/karty-plastikovye/",
    "Цифровая печать": "/catalog/poligrafiya/tsifrovaya-pechat/",
    "Блокноты": "/catalog/poligrafiya/bloknoty/",
    "Бейджи": "/catalog/poligrafiya/beydzhi/",
    "Общий спрос": "/catalog/poligrafiya/",
    "Бренд": "/",
    "Локальные": "",
    "Сравнения": "",
    "Информационные": "",
}

query_clusters = []
_by_cluster = {}
junk = 0
for r in queries:
    q = r.get("q") or ""
    if not is_real_query(q):
        junk += 1
        continue
    pos = r.get("avg") or 0.0
    c = cluster_of(q)
    _by_cluster.setdefault(c, []).append(pos)
    query_clusters.append({"q": q, "c": c, "p": pos, "u": CLUSTER_PAGE.get(c, "")})

# Сколько страниц раздела реально в поиске. Раньше эти числа стояли в коде
# руками и разошлись с данными. Считаем по выгрузке статусов из панели.
# Первая версия читала parsed_data.json, которого в проекте нет, из-за чего
# колонка «страниц» везде показывала 0. Источник: searchable_pages.csv.
SEARCHABLE_CSV = os.path.normpath(os.path.join(
    ROOT, "brain", "wiki", "webmaster_analytics", "exports", "searchable_pages.csv"))


def searchable_urls():
    """Пути страниц, которые панель Вебмастера считает находящимися в поиске."""
    out = set()
    if not os.path.isfile(SEARCHABLE_CSV):
        return out
    for r in read_rows(SEARCHABLE_CSV):
        u = (r.get("URL") or "").strip()
        if not u:
            continue
        for host in ("https://xn--18-6kc5a3bxam.xn--p1ai", "https://цифра18.рф"):
            if u.startswith(host):
                u = u[len(host):]
                break
        out.add(u)
    return out


_clusters_searchable = searchable_urls()
# Кластеры строим по факту: берём все, что реально встретилось в запросах,
# а не жёсткий список из восьми имён. Иначе новые кластеры
# (УФ-печать, ризография, ламинация) в таблицу не попадали.
_clusters_order = [g for g in sorted(set(r["c"] for r in query_clusters))
                   if g != "Прочие"]
clusters = []
for name in _clusters_order:
    pos = _by_cluster.get(name) or []
    if not pos:
        continue
    in_top10 = sum(1 for p in pos if 0 < p <= 10)
    target = CLUSTER_PAGE.get(name, "")
    prefix = target.rstrip("/") if target else ""
    pages = sum(1 for u in _clusters_searchable
                if prefix and (u == prefix or u.startswith(prefix + "/")))
    clusters.append({
        "name": name,
        "queries": len(pos),
        "avg": round(sum(pos) / len(pos), 1),
        "top10": int(round(in_top10 / len(pos) * 100)),
        "pages": pages,
        "target": target,
    })
clusters.sort(key=lambda c: -c["queries"])

query_groups = sorted(set(r["c"] for r in query_clusters))
query_total = len(query_clusters)
query_junk = TOTAL_QUERIES - query_total
query_other = sum(1 for r in query_clusters if r["c"] == "Прочие")

# --- 7. ICE top actions (from 10_Priority_Matrix.md; Yandex-only wording) ---
ice = [
    {"action": "Карта сайта: генерация, путь /sitemap.xml, robots.txt", "score": 9.7},
    {"action": "Canonical глобально + Clean-param", "score": 9.4},
    {"action": "Блокировка /shop/ и *.html (PARSE_ERROR)", "score": 9.3},
    {"action": "Длинные тире заменить запятыми", "score": 8.8},
    {"action": "Подкатегории визиток и широкоформата (6 шт.)", "score": 8.4},
    {"action": "JSON-LD: организация, адрес, хлебные крошки", "score": 8.4},
    {"action": "Локальные лендинги Ижевск (3 шт.)", "score": 8.1},
    {"action": "Уникальные title и meta для страниц в поиске", "score": 8.0},
    {"action": "Метрика + Вебмастер: цели, переобход", "score": 7.7},
    {"action": "IndexNow для мгновенной индексации", "score": 6.9},
]

# --- 8. Forecast ---
forecast = {
    "labels": ["Старт", "1 мес", "2 мес", "3 мес", "6 мес", "12 мес"],
    "searchable": [142, 220, 350, 500, 800, 1100],
}

WM = {
    "meta": {"totalPages": total_pages, "totalQueries": len(queries),
             "linkTotal": link_total, "generated": "2026-09-23"},
    "statuses": statuses,
    "dupPatterns": dupPatterns,
    "parsePatterns": parsePatterns,
    "events": {"add": events_add, "delete": events_delete},
    "sections": sections,
    "sectionsTop": sections_by_indexed,
    "queryBins": bins,
    "queryTops": {"top1": top1, "top3": top3, "top10": top10},
    "money": [{"q": m["q"], "avg": round(m["avg"], 2), "days": m["days"],
               "shows": m["shows"], "clicks": m["clicks"], "ctr": m["ctr"]} for m in money],
    "trendDays": [d[5:] for d in DAYS],
    "trend": trend,
    "showsDaily": [shows_daily[d] for d in DAYS],
    "clicksDaily": [clicks_daily[d] for d in DAYS],
    "gaps": gaps,
    "linkStatus": link_status,
    "linkBroken": link_broken,
    "brokenTargets": broken_targets,
    "imageHotlinks": image_hotlinks,
    "typos": typos,
    "clusters": clusters,
    "queryClusters": query_clusters,
    "queryStats": {"total": query_total, "rows": TOTAL_QUERIES, "junk": query_junk,
                   "groups": len(query_groups), "other": query_other},
    "ice": ice,
    "forecast": forecast,
}

with open(OUT, "w", encoding="utf-8") as f:
    f.write("/* Generated by scripts/export/build_wm_data.py. Do not edit by hand. */\n")
    f.write("const WM = ")
    json.dump(WM, f, ensure_ascii=False)
    f.write(";\n")

print("Wrote %s" % OUT)
print("pages=%d queries=%d links=%d" % (total_pages, len(queries), link_total))
print("statuses=%s" % (statuses,))
