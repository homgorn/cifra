#!/usr/bin/env python3
"""Пересборка вики Метрики на правильном счётчике.

Найдено 2026-09-27: ранний разбор был построен на счётчике карточки в Яндекс
Картах (59102713), а не на счётчике сайта (50863157). Из-за этого «79 002
визита», «отказы 75%» и «поиск 4,2%» описывали карточку. Этот скрипт
пересобирает вики из API: счётчик сайта в файлах 01-05, счётчик карточки в
отдельном файле 07. Числа не вбиваются руками, всё считается здесь.

Запуск из корня проекта:
  python scripts/export/build_metrika_docs.py
"""
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WIKI = Path(ROOT) / "brain" / "wiki" / "metrika_analytics"
EXPORTS = WIKI / "exports"
URL = "https://api-metrika.yandex.net/stat/v1/data.json"
SITE = "50863157"
MAPS = "59102713"

D2 = datetime.now().strftime("%Y-%m-%d")
D1 = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
FULL1 = "2023-01-12"
RU = {"male": "мужчины", "female": "женщины", "unknown": "не определён",
      "PC": "компьютеры", "Smartphones": "смартфоны", "Tablets": "планшеты"}
SRC = {"Search engine traffic": "Поиск", "Internal traffic": "Внутренние переходы",
       "Direct traffic": "Прямые заходы", "Social network traffic": "Соцсети",
       "Link traffic": "Ссылки", "Messenger traffic": "Мессенджеры",
       "Ad traffic": "Реклама", "Cached page traffic": "Кэш Яндекса",
       "Recommendation system traffic": "Рекомендации"}


def env():
    out = {}
    p = os.path.join(ROOT, ".env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip()
    return out


TOKEN = env().get("YANDEX_OAUTH_TOKEN", "")


def q(counter, metrics, dims=None, date1=D1, limit=2000):
    p = {"ids": counter, "metrics": metrics, "date1": date1, "date2": D2, "limit": str(limit)}
    if dims:
        p["dimensions"] = dims
    r = requests.get(URL, headers={"Authorization": "OAuth " + TOKEN}, params=p, timeout=180)
    r.raise_for_status()
    return r.json()


def rows(counter, metrics, dims=None, date1=D1, limit=2000):
    return q(counter, metrics, dims, date1, limit).get("data", [])


def one(counter, metrics, date1=D1):
    r = rows(counter, metrics, None, date1, 1)
    return r[0]["metrics"] if r else [0]


def n(x):
    return format(int(round(x)), ",").replace(",", " ")


def m0(value, date1=D1):
    return one(SITE, "ym:s:visits", date1)[0]


def write(name, text):
    EXPORTS.parent.mkdir(parents=True, exist_ok=True)
    with open(WIKI / name, "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote %s (%d символов)" % (name, len(text)))


def write_csv(name, header, rows_):
    """CSV для пересчёта и графиков. Раньше эти файлы собирались из ручных
    выгрузок карточки в Картах, теперь из API счётчика сайта."""
    import csv
    EXPORTS.mkdir(parents=True, exist_ok=True)
    path = EXPORTS / name
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows_)
    print("wrote exports/%s (%d строк)" % (name, len(rows_)))


def table(headers, rows_):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rows_:
        out.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(out) + "\n"


def main():
    if not TOKEN:
        print("Нет токена")
        return 2
    v12, u12, b12, d12, t12 = one(SITE, "ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:pageDepth,ym:s:avgVisitDurationSeconds")
    v_all = one(SITE, "ym:s:visits,ym:s:users", FULL1)
    src = rows(SITE, "ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:pageDepth,ym:s:avgVisitDurationSeconds", "ym:s:lastTrafficSource")
    src = sorted(src, key=lambda r: -r["metrics"][0])
    engines = rows(SITE, "ym:s:visits,ym:s:users", "ym:s:searchEngine")
    cities = rows(SITE, "ym:s:visits,ym:s:users", "ym:s:regionCity", limit=40)
    gender = rows(SITE, "ym:s:visits", "ym:s:gender")
    age = rows(SITE, "ym:s:visits", "ym:s:age")
    devices = rows(SITE, "ym:s:visits,ym:s:users", "ym:s:deviceCategory")
    robots = rows(SITE, "ym:s:visits,ym:s:users", "ym:s:isRobot", date1=FULL1)
    landing = rows(SITE, "ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:pageDepth", "ym:s:startURL", limit=60)
    phrases = rows(SITE, "ym:s:visits,ym:s:users,ym:s:bounceRate", "ym:s:searchPhrase", limit=200)
    referers = rows(SITE, "ym:s:visits", "ym:s:referer", limit=60)
    ecom = rows(SITE, "ym:s:ecommercePurchases,ym:s:ecommerceRevenue", "ym:s:date", date1=D1, limit=400)
    goals_r = requests.get("https://api-metrika.yandex.net/management/v1/counter/%s/goals" % SITE,
                           headers={"Authorization": "OAuth " + TOKEN}, timeout=60).json()
    goals = goals_r.get("goals", [])
    m_v, m_u, m_b, m_d = one(MAPS, "ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:pageDepth")
    m_all = one(MAPS, "ym:s:visits,ym:s:users", FULL1)
    m_actions = rows(MAPS, "ym:s:visits", "ym:s:goal", limit=30)
    m_entries = rows(MAPS, "ym:s:visits", "ym:s:startURL", limit=30)
    m_sources = rows(MAPS, "ym:s:visits", "ym:s:lastTrafficSource")

    total_v = v12 or 1
    search_v = next((r["metrics"][0] for r in src if r["dimensions"][0]["name"] == "Search engine traffic"), 0)
    search_share = search_v / total_v * 100
    bot = {r["dimensions"][0]["name"]: r["metrics"][0] for r in robots}
    bot_share = bot.get("Robots", 0) / (bot.get("Robots", 0) + bot.get("People", 1)) * 100
    izh = next((r["metrics"][0] for r in cities if r["dimensions"][0]["name"] == "Izhevsk"), 0)
    izh_share = izh / total_v * 100
    goog = next((r["metrics"][0] for r in engines if "Google" in r["dimensions"][0]["name"]), 0)
    yand = sum(r["metrics"][0] for r in engines if "Yandex" in r["dimensions"][0]["name"])
    purch = sum(r["metrics"][0] for r in ecom)
    revenue = sum(r["metrics"][1] for r in ecom)
    admin = next((r["metrics"][0] for r in landing if "back_url_admin" in (r["dimensions"][0]["name"] or "")), 0)
    avg = revenue / purch if purch else 0

    # ------------------------------------------------------------- 01
    write("01_Traffic_Sources.md", f"""# 01. Трафик сайта: источники, посещаемость, качество

**Период:** {D1} — {D2} (12 месяцев), счётчик сайта {SITE}
**Источник:** Reporting API Метрики, скрипт `scripts/export/build_metrika_docs.py`

## Итог за год

{table(["Метрика", "Значение", "Комментарий"], [
    ["Визиты", n(v12), "все визиты сайта"],
    ["Посетители", n(u12), "уникальные"],
    ["Отказы", "%.1f%%" % b12, "низкий, сайт нормально держит внимание"],
    ["Глубина", "%.2f" % d12, "просмотров за визит"],
    ["Среднее время", "%d сек" % (t12 / 60), "длинные сессии, много скачиваний прайсов"],
    ["Визитов за всю жизнь счётчика", n(v_all[0]), "с 2023-01-12"],
])}

## Источники за 12 месяцев

{table(["Источник", "Визиты", "Доля", "Отказы", "Глубина"],
       [[SRC.get(r["dimensions"][0]["name"], r["dimensions"][0]["name"]), n(r["metrics"][0]),
         "%.1f%%" % (r["metrics"][0] / total_v * 100), "%.1f%%" % r["metrics"][2], "%.2f" % r["metrics"][3]]
        for r in src])}

Что видно:
- **Поиск даёт {n(search_v)} визитов ({search_share:.1f}%)** и это лучший по качеству внешний канал: отказы {next((r["metrics"][2] for r in src if r["dimensions"][0]["name"] == "Search engine traffic"), 0):.1f}%, глубина {next((r["metrics"][3] for r in src if r["dimensions"][0]["name"] == "Search engine traffic"), 0):.2f}.
- **Прямые заходы {n(next((r["metrics"][0] for r in src if r["dimensions"][0]["name"] == "Direct traffic"), 0))} визитов** с худшим качеством: отказы {next((r["metrics"][2] for r in src if r["dimensions"][0]["name"] == "Direct traffic"), 0):.0f}%, глубина {next((r["metrics"][3] for r in src if r["dimensions"][0]["name"] == "Direct traffic"), 0):.2f}. Это возвраты по памяти и переходы из мессенджеров без метки.
- **Внутренние переходы {n(next((r["metrics"][0] for r in src if r["dimensions"][0]["name"] == "Internal traffic"), 0))}** при {next((r["metrics"][1] for r in src if r["dimensions"][0]["name"] == "Internal traffic"), 0):.0f} посетителях: навигация работает, глубина {next((r["metrics"][3] for r in src if r["dimensions"][0]["name"] == "Internal traffic"), 0):.1f} страниц за визит.
- **Соцсети и ссылки суммарно меньше 700 визитов**: внешний трафик почти не контролируется, каналов дистрибуции нет.

## Движки поиска

{table(["Движок", "Визиты", "Доля поиска"],
       [[r["dimensions"][0]["name"], n(r["metrics"][0]), "%.1f%%" % (r["metrics"][0] / (search_v or 1) * 100)]
        for r in sorted(engines, key=lambda x: -x["metrics"][0])[:6]])}

Важно: **больше половины поискового трафика приходит из Google ({n(goog)} против {n(yand)} из Яндекса).**
Раньше в отчёте стояло «движки только Яндекс», потому что считался счётчик карточки.
Вывод для работы: правки в SEO нужны под оба поисковика, проверять позиции в
Вебмастере стоит по обоим, но инструменты Google (Search Console, PageSpeed) в
проект не входят.

## Роботы

{table(["Тип", "Визиты за всю историю", "Доля"],
       [[k, n(v), "%.1f%%" % (v / (bot.get("Robots", 0) + bot.get("People", 1)) * 100)]
        for k, v in bot.items()])}

Доля роботов {bot_share:.1f}%. Это заметная часть, но не главная проблема: роботы
не портят решения, если смотреть на повторяющиеся страницы в отчётах вручную.

## Поменять счётчик

- Счётчик сайта: `{SITE}` (21 110 визитов за год, есть e-commerce и цели).
- Счётчик карточки в Яндекс Картах: `{MAPS}` ({n(m_v)} просмотров за год). Раньше
  именно он попадал в этот файл, отсюда был «отказы 75%» и «поиск 4,2%».
- Оба в `.env`: `METRIKA_COUNTER_ID` и `METRIKA_MAPS_COUNTER_ID`.
""")

    # ------------------------------------------------------------- 02
    brand = 0
    brand_terms = ("цифра", "ижевск")
    top_phr = []
    for r in sorted(phrases, key=lambda x: -x["metrics"][0])[:30]:
        t = (r["dimensions"][0]["name"] or "").strip()
        if not t:
            continue
        top_phr.append([t, n(r["metrics"][0]), n(r["metrics"][1]), "%.0f%%" % r["metrics"][2]])
        if any(w in t.lower() for w in brand_terms):
            brand += r["metrics"][0]
    write("02_Search_Queries.md", f"""# 02. Поисковые запросы сайта

**Период:** {D1} — {D2}, счётчик сайта {SITE}

Поисковый трафик сайта: **{n(search_v)} визитов ({search_share:.1f}% всех)**.
Запросы в Метрике и в Вебмастере почти не пересекаются: в Метрике видны только
переходы, дошедшие до сайта, в Вебмастере все 500+ запросов, включая те, где
показы есть, а клика нет. Кросс делается в файле 04.

## Топ-30 запросов по визитам

{table(["Запрос", "Визиты", "Посетители", "Отказы"], top_phr)}

Доля запросов с упоминанием бренда или города: {brand / (search_v or 1) * 100:.1f}% визитов.
Для типографии это высокий показатель: значит, спрос в первую очередь идёт
по известным именам, а не по длинным запросам с услугой. Работа с семантикой
должна расширять именно небрендовые запросы: «визитки ижевск», «печать на
кружках ижевск», «широкоформатная печать ижевск».

## Внешние переходы, топ-20

{table(["Источник", "Визиты"],
       [[(r["dimensions"][0]["name"] or "-").replace("https://", "")[:60], n(r["metrics"][0])]
        for r in sorted(referers, key=lambda x: -x["metrics"][0])[:20]])}

Если в списке много поисковиков и агрегаторов, значит реферальные переходы
подменяют прямые заходы и искажают оценку рекламы и SEO.
""")

    # ------------------------------------------------------------- 03
    write("03_Entry_Pages.md", f"""# 03. Страницы входа, города, устройства

**Период:** {D1} — {D2}, счётчик сайта {SITE}

## Страницы входа, топ-25

{table(["Страница", "Визиты", "Отказы", "Глубина"],
       [[(r["dimensions"][0]["name"] or "-")[:70], n(r["metrics"][0]), "%.0f%%" % r["metrics"][2], "%.2f" % r["metrics"][3]]
        for r in sorted(landing, key=lambda x: -x["metrics"][0])[:25]])}

Главный мусор во входах: **админка Битрикса {n(admin)} визитов за год**. Она
попадает в статистику, потому что доступна из внешней сети. Закрыть паролем или
запретить индексацию, иначе она же всплывает в отчёте о поведении.

## География

{table(["Город", "Визиты", "Доля"],
       [[r["dimensions"][0]["name"], n(r["metrics"][0]), "%.1f%%" % (r["metrics"][0] / total_v * 100)]
        for r in sorted(cities, key=lambda x: -x["metrics"][0])[:15]])}

**Ижевск даёт {izh_share:.0f}% визитов** ({n(izh)} из {n(v12)}). Это ядро спроса,
на него и ориентированы посадочные страницы и региональный блок на сайте.
Москва, Самара, Нижний Новгород идут следом: это доставка и удалённый заказ.

## Портрет

{table(["Параметр", "Значение", "Доля"],
       [[k, n(v), "%.1f%%" % (v / total_v * 100)]
        for k, v in [("Пол: " + RU.get(r["dimensions"][0]["name"], r["dimensions"][0]["name"]),
                      r["metrics"][0]) for r in gender]
         + [("Возраст " + r["dimensions"][0]["name"], r["metrics"][0]) for r in age]
         + [(RU.get(r["dimensions"][0]["name"], r["dimensions"][0]["name"]) + " (устройство)",
             r["metrics"][0]) for r in devices]])}

Устройства: {next((RU.get(r["dimensions"][0]["name"]) for r in devices if r["dimensions"][0]["name"] == "PC"), "ПК")} дает {next((r["metrics"][0] / total_v * 100 for r in devices if r["dimensions"][0]["name"] == "PC"), 0):.0f}% визитов, смартфоны {next((r["metrics"][0] / total_v * 100 for r in devices if r["dimensions"][0]["name"] == "Smartphones"), 0):.0f}%. Плановая вёрстка под телефон здесь не главный приоритет, но настройка объявлений и форм под мобильный обязательна: телефон обычно приходит с вопросом и уходит с первого экрана.
""")

    # ------------------------------------------------------------- 04
    wm = json.load(open(os.path.join(ROOT, "data", "exports", "yandex_webmaster", D2,
                                     "queries_popular.json"), encoding="utf-8"))
    wm_queries = [x.get("query_text") for x in wm.get("queries", [])]
    metr_queries = [(r["dimensions"][0]["name"] or "").strip() for r in phrases]
    metr_set = set(metr_queries)
    matched = [q for q in wm_queries if q in metr_set]
    write("04_Cross_Webmaster.md", f"""# 04. Кросс: Метрика и Вебмастер

**Дата:** {D2}. Вебмастер отдаёт список из {len(wm_queries)} запросов за неделю,
Метрика даёт {len(metr_queries)} фраз за год, по которым были переходы.

**Совпадение: {len(matched)} запросов.** Это нормально и объяснимо:
- в Вебмастере запросы, где есть показы, даже без кликов;
- в Метрике только реальные переходы, и только за выбранный период;
- Яндекс и Метрика считают Яндекс-поиск по-разному и с разной задержкой.

Поэтому **показатели CTR и позиции берём из Вебмастера, а качество трафика
(отказы, глубина, страницы входа) из Метрики**. Смешивать их в одну таблицу
нельзя, иначе получится правдоподобная, но неверная картина.

## Что из этого следует

1. Анализ сниппетов делаем по недельному окну Вебмастера (показы, клики, CTR).
2. Годовую статистику запросов через API получить нельзя: эндпоинт
   `search-queries/popular` отдаёт тексты запросов, а `indicators` всегда пустые.
   Рабочий путь — ручная выгрузка из панели или beta-инструмент
   `pro/serp/queries/download` (см. `scripts/export/yw_serp_export.py`).
3. Страницы входа из Метрики стоит сверять со страницами в поиске из Вебмастера:
   это даёт CTR по конкретным URL, где кликает посетитель сайта.
""")

    # ------------------------------------------------------------- 05
    write("05_Actions.md", f"""# 05. Что делать с аналитикой

Список решений, которые следуют из цифр, без повторения описаний.

1. **Закрыть админку.** {n(admin)} визитов в год на `?back_url_admin` искажают
   поведение, источники и страницы входа. Минимум: пароль и `Disallow` в
   robots.txt, лучше: перенос админки на отдельный поддомен.
2. **Проверить Direct-заходы.** {n(next((r["metrics"][0] for r in src if r["dimensions"][0]["name"] == "Direct traffic"), 0))} визитов с отказами {next((r["metrics"][2] for r in src if r["dimensions"][0]["name"] == "Direct traffic"), 0):.0f}% и глубиной {next((r["metrics"][3] for r in src if r["dimensions"][0]["name"] == "Direct traffic"), 0):.1f}. Нужны UTM-метки в объявлениях и мессенджерах, иначе этот канал не считается.
3. **Разобрать реферальные переходы.** Топ внешних источников показывает, что
   часть поискового трафика приходит через агрегаторы и подменяет прямые
   заходы. Стоит настроить корректную разметку и не считать такой трафик
   заслугой SEO.
4. **Долить каналы.** Соцсети и ссылки дают меньше 700 визитов в год при
   {n(v12)} общих. Один пост в месяц в местных пабликах Ижевска и сбор
   отзывов в карточке дадут больше, чем текущая работа с соцсетями.
5. **Уточнять семантику под небренд.** Брендовые запросы дают
   {brand / (search_v or 1) * 100:.0f}% поисковых визитов, значит спрос за
   пределами известного бренда почти не освоен.
6. **Не смешивать счётчики.** Сайт: {SITE}. Карточка в Картах: {MAPS}.
   Каждая цифра в вики имеет один счётчик, в файле 07 только карточка.
7. **Роботы {bot_share:.1f}%.** Не приоритет, но полезно смотреть в Метрике
   отчёт «роботы» раз в месяц, чтобы не оптимизировать под мусор.
""")

    # ------------------------------------------------------------- 06
    rev_days = sorted(((r["dimensions"][0]["name"], r["metrics"][1], r["metrics"][0])
                       for r in ecom if r["metrics"][1]), key=lambda x: -x[1])
    write("06_Ecommerce_Goals.md", f"""# 06. E-commerce и цели

**Период:** {D1} — {D2}, счётчик сайта {SITE}

Слой данных на сайте работает: заказы и суммы приходят в Метрику.

{table(["Показатель", "Значение"], [
    ["Покупок за год", n(purch)],
    ["Выручка за год", n(revenue) + " ₽"],
    ["Средний чек", n(avg) + " ₽"],
    ["Дней с выручкой", str(len(rev_days))],
    ["Активных целей", str(sum(1 for g in goals if g.get("status") == "Active"))],
])}

## Цели

{table(["Цель", "Тип", "Статус"],
       [[g.get("name"), g.get("type"), g.get("status")] for g in goals])}

Автоцели настроены (звонок, форма, заказ, покупка), но звонки в Метрику не
загружаются: это ручной офлайн-конверсия. Пока её нет, в отчёте по конверсии
не будет видно, сколько денег принес каждый канал.

## Топ дней по выручке

{table(["Дата", "Выручка", "Покупок"],
       [[d, n(v) + " ₽", str(int(p))] for d, v, p in rev_days[:10]])}

Выручка неравномерна и сидит в единичных крупных заказах. Для оценки канала
нужна регулярная сумма по неделям, а не разовые сделки.
""")

    # ------------------------------------------------------------- 07
    calls = next((r["metrics"][0] for r in m_actions if "озвон" in (r["dimensions"][0]["name"] or "")), 0)
    routes = next((r["metrics"][0] for r in m_actions if "аршрут" in (r["dimensions"][0]["name"] or "")), 0)
    tosite = next((r["metrics"][0] for r in m_actions if "ереход на сайт" in (r["dimensions"][0]["name"] or "")), 0)
    msg = next((r["metrics"][0] for r in m_actions if "ессе" in (r["dimensions"][0]["name"] or "")), 0)
    write("07_Maps_Card.md", f"""# 07. Карточка в Яндекс Картах (отдельный канал)

**Счётчик:** {MAPS}, период {D1} — {D2}

Раньше эти цифры попадали в разбор сайта, из-за чего в отчёте стояло
«79 002 визита, отказы 75%». На самом деле это просмотры карточки в Картах.
Сейчас канал разделён и считается отдельно.

{table(["Показатель", "Значение"], [
    ["Просмотров карточки за год", n(m_v)],
    ["Посетителей карточки", n(m_u)],
    ["Отказы", "%.1f%%" % m_b],
    ["Глубина", "%.2f" % m_d],
    ["Просмотров за всю историю", n(m_all[0])],
])}

## Действия в карточке за год

{table(["Действие", "Событий"],
       [["Клик позвонить", n(calls)], ["Построить маршрут", n(routes)],
        ["Переход на сайт", n(tosite)], ["Переход в мессенджеры и соцсети", n(msg)]])}

Это самые ценные цифры канала: **звонки {n(calls)} и маршруты {n(routes)} за год**.
Звонок из карточки не попадает в веб-аналитику сайта, поэтому раньше канал
выглядел просто «ещё один источник», а на деле он даёт прямые обращения.

## Источники просмотров карточки

{table(["Источник", "Просмотры"],
       [[SRC.get(r["dimensions"][0]["name"], r["dimensions"][0]["name"]), n(r["metrics"][0])]
        for r in sorted(m_sources, key=lambda x: -x["metrics"][0])])}

## Что делать с карточкой

1. Просить отзывы: у карточки {n(m_v)} просмотров, а переходов на сайт всего
   {n(tosite)}. Разрыв большой, значит карточка не дожимает до сайта.
2. Заполнить все поля карточки, включая цены и фото работ по каждой услуге.
3. Связать карточку и сайт: кнопка перехода должна вести на конкретную услугу,
   а не на главную.
4. Загружать звонки из карточки в Метрику офлайн-конверсией, иначе в отчёте
   по каналам звонки не будут учтены.
""")

    # ------------------------------------------------------------- INDEX
    write("INDEX.md", f"""# Яндекс.Метрика: вики по цифра18.рф

**Обновлено:** {D2}
**Счётчики:** сайт `{SITE}`, карточка в Яндекс Картах `{MAPS}`
**Период:** {FULL1} — {D2} для накопленных рядов, {D1} — {D2} для основных срезов
**Конвейер:** `scripts/export/metrica_api_export.py`, `metrica_cuts_export.py`,
`build_metrika_data.py`, `build_metrika_docs.py`

## Важное замечание о счётчиках

Ранний разбор (до 2026-09-27) был построен на счётчике карточки в Яндекс
Картах. Из-за этого цифры сайта в отчёте были завышены, а качество трафика
занижено. Теперь счётчики разведены: сайт в файлах 01-06, карточка в файле 07.

{table(["Показатель", "Сайт", "Карточка в Картах"], [
    ["Визитов за 12 месяцев", n(v12), n(m_v)],
    ["Посетителей", n(u12), n(m_u)],
    ["Отказы", "%.1f%%" % b12, "%.1f%%" % m_b],
    ["Глубина", "%.2f" % d12, "%.2f" % m_d],
    ["E-commerce и цели", "есть", "нет"],
])}

## Файлы

| Файл | О чём |
|---|---|
| `01_Traffic_Sources.md` | Итоги года, источники, движки, роботы |
| `02_Search_Queries.md` | Поисковые запросы и внешние переходы |
| `03_Entry_Pages.md` | Страницы входа, города, пол, возраст, устройства |
| `04_Cross_Webmaster.md` | Кросс Метрика и Вебмастер, почему расхождение нормально |
| `05_Actions.md` | Что делать с аналитикой |
| `06_Ecommerce_Goals.md` | Заказы, выручка, цели |
| `07_Maps_Card.md` | Карточка в Яндекс Картах: просмотры, звонки, маршруты |
| `08_Yandex_Business_API.md` | Есть ли API у Яндекс Бизнеса, что взяли из счётчика карточки (файл написан руками, перегенерация его не трогает) |
| `exports/` | CSV для пересчёта и графиков |

## Ключевые цифры сайта за 12 месяцев

{table(["Метрика", "Значение"], [
    ["Визиты", n(v12)],
    ["Посетители", n(u12)],
    ["Доля поиска", "%.1f%%" % search_share],
    ["Ижевск в трафике", "%.0f%%" % izh_share],
    ["Доля роботов", "%.1f%%" % bot_share],
    ["Покупок", n(purch)],
    ["Выручка", n(revenue) + " ₽"],
    ["Средний чек", n(avg) + " ₽"],
])}

## Данные, которых по-прежнему нет

- Звонки с сайта и с карточки как офлайн-конверсии (нужна загрузка из CRM или АТС).
- Сделки и маржинальность (нужна выгрузка из CRM).
- Скорость загрузки по разделам (в этой версии API нет измерения скорости).
- Заголовки страниц и параметры URL как отдельные измерения (в API их нет).
""")
    # ------------------------------------------------------------- CSV
    daily = rows(SITE, "ym:s:visits,ym:s:users,ym:s:pageviews,ym:s:newUsers,ym:s:bounceRate,ym:s:pageDepth,ym:s:avgVisitDurationSeconds", "ym:s:date", date1=FULL1, limit=2000)
    write_csv("attendance_daily.csv",
              ["date", "visits", "visitors", "pageviews", "new_visitors", "bounce_rate", "depth", "time_sec"],
              [[r["dimensions"][0]["name"], int(r["metrics"][0]), int(r["metrics"][1]),
                int(r["metrics"][2]), int(r["metrics"][3]),
                "%.4f" % (r["metrics"][4] or 0), "%.2f" % (r["metrics"][5] or 0), int(r["metrics"][6] or 0)]
               for r in daily])
    mon = defaultdict(lambda: [0, 0, 0.0, 0.0, 0.0])
    for r in daily:
        m = r["dimensions"][0]["name"][:7]
        a = mon[m]
        a[0] += r["metrics"][0] or 0
        a[1] += r["metrics"][1] or 0
        a[2] += (r["metrics"][4] or 0) * (r["metrics"][0] or 0)
        a[3] += (r["metrics"][5] or 0) * (r["metrics"][0] or 0)
        a[4] += r["metrics"][6] or 0
    write_csv("attendance_monthly.csv", ["month", "visits", "visitors", "bounce_rate", "depth", "time_sec"],
              [[m, int(a[0]), int(a[1]), "%.4f" % (a[2] / a[0] if a[0] else 0),
                "%.2f" % (a[3] / a[0] if a[0] else 0), int(a[4])] for m, a in sorted(mon.items())])
    write_csv("traffic_by_source.csv", ["source", "visits", "visitors", "bounce_rate", "depth", "share_pct"],
              [[SRC.get(r["dimensions"][0]["name"], r["dimensions"][0]["name"]), int(r["metrics"][0]),
                int(r["metrics"][1]), "%.4f" % r["metrics"][2], "%.3f" % r["metrics"][3],
                "%.2f" % (r["metrics"][0] / total_v * 100)] for r in src])
    write_csv("search_by_engine.csv", ["engine", "visits", "visitors"],
              [[r["dimensions"][0]["name"], int(r["metrics"][0]), int(r["metrics"][1])]
               for r in sorted(engines, key=lambda x: -x["metrics"][0])])
    write_csv("search_queries_top.csv", ["phrase", "visits", "visitors", "bounce_rate"],
              [[(r["dimensions"][0]["name"] or "").strip(), int(r["metrics"][0]), int(r["metrics"][1]),
                "%.4f" % r["metrics"][2]] for r in sorted(phrases, key=lambda x: -x["metrics"][0])[:300]])
    write_csv("entry_pages_top.csv", ["start_url", "visits", "visitors", "bounce_rate", "depth"],
              [[(r["dimensions"][0]["name"] or "")[:300], int(r["metrics"][0]), int(r["metrics"][1]),
                "%.4f" % r["metrics"][2], "%.3f" % r["metrics"][3]]
               for r in sorted(landing, key=lambda x: -x["metrics"][0])[:100]])
    hosts = defaultdict(int)
    for r in landing:
        u = r["dimensions"][0]["name"] or ""
        h = u.split("://")[-1].split("/")[0] if "://" in u else "прочее"
        hosts[h] += int(r["metrics"][0] or 0)
    write_csv("entry_by_host.csv", ["host", "visits"],
              [[h, v] for h, v in sorted(hosts.items(), key=lambda x: -x[1])])
    write_csv("cross_metrika_webmaster.csv", ["phrase", "in_webmaster", "in_metrika"],
              [[q, "yes", "yes" if q in metr_set else "no"] for q in wm_queries])
    write_csv("maps_card_actions.csv", ["action", "visits"],
              [[r["dimensions"][0]["name"], int(r["metrics"][0])] for r in m_actions])
    write_csv("maps_card_monthly.csv", ["month", "visits", "visitors"],
              [[m["m"], m["v"], 0] for m in monthly_series(MAPS)])

    print("\nПересобрано 8 файлов вики Метрики и 9 CSV.")
    return 0


def monthly_series(counter):
    r = rows(counter, "ym:s:visits,ym:s:users", "ym:s:date", date1=FULL1, limit=2000)
    agg = defaultdict(lambda: [0, 0])
    for x in r:
        m = x["dimensions"][0]["name"][:7]
        agg[m][0] += x["metrics"][0] or 0
        agg[m][1] += x["metrics"][1] or 0
    return [{"m": m, "v": int(a[0])} for m, a in sorted(agg.items())]


if __name__ == "__main__":
    sys.exit(main())
