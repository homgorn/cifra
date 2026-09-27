#!/usr/bin/env python3
"""Пакет для Topvisor: что загрузить, что настроить и в каком порядке.

Топвизор сейчас наполнен на 5%: 154 ключа в одной группе «Новая группа»,
без целевых страниц, последний сбор позиций 2026-09-14, один регион.
При этом ядро уже собрано: 535 запросов с кластерами в вики, 500 запросов
из API Вебмастера за неделю и за год, и первые строки с показами, кликами
и позициями из beta-инструмента.

Скрипт собирает из этого готовый пакет и пишет план работы с сервисом.

Запуск из корня проекта:
  python scripts/export/build_topvisor_package.py
"""
import csv
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
WIKI = ROOT / "brain" / "wiki" / "webmaster_analytics" / "exports"
WM = ROOT / "data" / "exports" / "yandex_webmaster"
OUT = ROOT / "topvisor" / "exports"
DB = ROOT / "topvisor" / "db" / "topvisor.db"
PLAN = ROOT / "brain" / "wiki" / "topvisor_plan.md"

# Куда целевые страницы по кластерам. Соответствует структуре сайта из панели
# Вебмастера, раздел «каталог» исключён из /shop как мёртвый.
CLUSTER_TARGETS = {
    "Визитки": "/catalog/poligrafiya/vizitki/",
    "Кружки и магниты": "/catalog/suvenirnaya-produktsiya/pechat-na-kruzhkakh",
    "Календари": "/catalog/poligrafiya/kalendari/",
    "Листовки и флаеры": "/catalog/poligrafiya/listovki-tsifrovaya-pechat/",
    "Широкоформатная печать": "/catalog/reklama/",
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
    "Информационные": "",
    "Сравнения": "",
    "Локальные": "",
    "Прочие": "",
}
# Кластеры, у которых нет своей страницы: под них нужно создавать.
# «Локальные» попал сюда 2026-09-27: 51 запрос вида «печать ижевск»,
# «типография в ижевске» не имеет посадочной, весь локальный спрос
# размазан по продуктовым страницам без городского сигнала.
NEEDS_PAGE = {"Сравнения", "Локальные", "Информационные", "Общий спрос"}

# Классификатор берём тот же, что и в build_wm_data.py, иначе группы в
# Topvisor и на сайте разойдутся.
import importlib.util as _ilu  # noqa: E402

_spec = _ilu.spec_from_file_location(
    "wm_build", str(Path(__file__).resolve().parent / "build_wm_data.py"))


def _load_classifier():
    """Достаём cluster_of из build_wm_data.py, не выполняя весь скрипт."""
    import re as _re
    src = (Path(__file__).resolve().parent / "build_wm_data.py").read_text(encoding="utf-8")
    ns = {}
    start = src.find("CLUSTER_RULES = [")
    end = src.find("CLUSTER_PAGE = {")
    if start < 0 or end < 0:
        return lambda q: "Прочие"
    exec(src[start:end], ns)
    return ns["cluster_of"]


classify = _load_classifier()


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def existing_queries():
    if not DB.is_file():
        return set()
    c = sqlite3.connect(str(DB))
    rows = c.execute("select name from keywords").fetchall()
    c.close()
    return {r[0] for r in rows}


def core():
    """Ядро с пофразовой разбивкой по кластерам.

    Раньше брали top_queries_by_cluster.csv, где колонка Cluster_L1 во всех
    535 строках равна TODO: пофразовой кластеризации в репозитории не было.
    Теперь она считается в build_wm_data.py и лежит в wm-data.js."""
    import json
    p = ROOT / "reports" / "cifra18-audit" / "js" / "wm-data.js"
    if not p.is_file():
        return []
    t = p.read_text(encoding="utf-8")
    d = json.loads(t[t.index("{"):].rstrip().rstrip(";"))
    out = []
    for r in d.get("queryClusters") or []:
        out.append({
            "Query": r.get("q", ""),
            "Avg_Position": r.get("p", 0),
            "Cluster_L1": r.get("c", "Прочие"),
            "Target_Page": r.get("u", ""),
        })
    return out


def webmaster_queries():
    """Запросы из API Вебмастера: за год по кликам и по показам.

    Больше не берём срезом `[:200]`. Срез без проверки был источником
    мусора: в первые 200 попадали внутренний поиск, синтаксис операторов
    и URL чужих сайтов, вбитые в поисковую строку. Теперь годовой топ
    проходит через filter_topvisor_queries.py, и решает он, а не
    порядок строк в файле."""
    out = []
    base = WM
    if not base.is_dir():
        return out
    import json
    days = sorted(p.name for p in base.iterdir() if p.is_dir())
    if not days:
        return out
    f = base / days[-1] / "queries_12m" / "q_popular_shows_12m.json"
    if not f.is_file():
        return out
    data = json.load(open(f, encoding="utf-8"))

    from filter_topvisor_queries import classify_phrase
    for q in data.get("queries", []):
        t = (q.get("query_text") or "").strip()
        if not t:
            continue
        verdict, _code, _reason = classify_phrase(t)
        if verdict == "KEEP":
            out.append(t)
    return out


def serp_positions():
    """Строки с реальными показами, кликами и позициями."""
    out = []
    if not WM.is_dir():
        return out
    day = sorted(p.name for p in WM.iterdir() if p.is_dir())[-1]
    f = WM / day / "serp_queries" / "serp_queries_raw.csv"
    if not f.is_file():
        return out
    with open(f, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            q = (r.get("query") or "").strip()
            if not q or re.match(r"^[\x00-\x7F\s]{20,}$", q):
                continue
            out.append({"q": q, "path": (r.get("path") or "").strip(),
                        "c": int(r.get("click") or r.get("clicks") or 0),
                        "i": int(r.get("impressions") or 0),
                        "p": float(r.get("position") or 0)})
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = core()
    have = existing_queries()
    serp = serp_positions()
    serp_by_q = defaultdict(list)
    for s in serp:
        serp_by_q[s["q"]].append(s)

    # Сколько фраз отсеяно и почему. Считаем здесь же, чтобы план
    # показывал правду, а не только то, что решили загрузить.
    from filter_topvisor_queries import (classify_phrase, load_queries,
                                        read_classifier)
    all_rows = load_queries()
    cluster_fn = read_classifier()
    blocked, review = [], []
    for r in all_rows:
        verdict, code, reason = classify_phrase(r["phrase"])
        if verdict == "KEEP":
            g = r.get("group") or cluster_fn(r["phrase"])
            if g == "Прочие":
                verdict, code, reason = "REVIEW", "R10", "релевантна, но без кластера"
        if verdict == "BLOCK":
            blocked.append((r["phrase"], code, reason))
        elif verdict == "REVIEW":
            review.append((r["phrase"], code, reason))

    # 1. Импорт: всё ядро плюс запросы из Вебмастера, которых в ядре нет.
    # Фильтр релевантности обязателен: ядро тоже содержит мусор из панели
    # (внутренний поиск, операторы, чужие организации), а «Прочие» грузить
    # в Topvisor нельзя, это свалка.
    from filter_topvisor_queries import classify_phrase
    import_rows = []
    seen = set()
    for r in rows:
        q = (r.get("Query") or "").strip()
        if not q or q in seen:
            continue
        verdict, _c, _rs = classify_phrase(q)
        if verdict != "KEEP":
            continue
        group = r.get("Cluster_L1") or "Прочие"
        if group == "Прочие":
            group = classify(q)
        if group == "Прочие":
            continue
        seen.add(q)
        import_rows.append({
            "phrase": q,
            "group": group,
            "avg_position": r.get("Avg_Position") or "",
            "in_topvisor": "да" if q in have else "нет",
            "target_url": r.get("Target_Page") or CLUSTER_TARGETS.get(group, ""),
        })
    extra = 0
    for q in webmaster_queries():
        q = q.strip()
        if not q or q in seen:
            continue
        c = classify(q)
        if c == "Прочие":
            continue
        seen.add(q)
        extra += 1
        import_rows.append({"phrase": q, "group": c, "avg_position": "",
                            "in_topvisor": "да" if q in have else "нет",
                            "target_url": CLUSTER_TARGETS.get(c, "")})
    imp = OUT / "import_queries.csv"
    with open(imp, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(import_rows[0].keys()))
        w.writeheader()
        w.writerows(import_rows)

    # 2. Целевые страницы. Строим по import_rows, а не по ядру: раньше файл
    # покрывал только 492 строки ядра, а в Core попадали ещё и годовые
    # запросы, из-за чего 122 фразы импорта оставались без цели.
    tgt = []
    for r in import_rows:
        q = r["phrase"]
        cluster = r["group"]
        actual = serp_by_q.get(q)
        if actual:
            best = min(actual, key=lambda s: s["p"] or 999)
            url = best["path"]
            source = "факт из Вебмастера"
        else:
            url = r.get("target_url") or CLUSTER_TARGETS.get(cluster, "")
            source = "по кластеру" if url else "нужна новая страница"
        tgt.append({
            "phrase": q,
            "group": cluster,
            "target_url": url,
            "target_source": source,
            "avg_position": r.get("avg_position") or "",
            "needs_page": "да" if (not url and cluster in NEEDS_PAGE) else "нет",
        })
    tf = OUT / "keyword_targets.csv"
    with open(tf, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(tgt[0].keys()))
        w.writeheader()
        w.writerows(tgt)

    # 3. Сводка по группам
    grp = Counter(r["group"] for r in import_rows)
    need = [r for r in tgt if r["needs_page"] == "да"]
    with_target = sum(1 for r in tgt if r["target_url"])

    # 4. План
    fresh = sum(1 for r in import_rows if r["in_topvisor"] == "нет")
    plan = f"""# Topvisor: что загрузить и как работать дальше

**Дата:** {datetime.now().strftime('%Y-%m-%d')}
**Проект:** 32490624, сайт `цифра18.рф`, регион Россия (225), поисковик Яндекс
**Баланс:** см. `topvisor/scripts/tv.py balance` (последний снимок в базе проекта)

## Что в сервисе сейчас

- 154 ключа, все в группе «Новая группа», без целевых страниц.
- Позиции собраны один раз, {read_last_sync()}, большая часть ключей без позиции.
- 2 конкурента, один регион.
- Баланс покрывает сбор позиций и кластеризацию по релевантным (бесплатные методы).

## Что загрузить (готово в файлах)

| Файл | Что внутри | Сколько |
|---|---|---|
| `topvisor/exports/import_queries.csv` | Фразы, группа, средняя позиция, целевая страница, отметка «уже в сервисе» | {len(import_rows)} строк, новых {fresh} |
| `topvisor/exports/keyword_targets.csv` | Фраза, группа, целевая страница, источник цели, нужна ли новая страница | {len(tgt)} строк |
| `topvisor/exports/review_queries.csv` | Не грузим, ждут решения, с причиной | {len(review)} строк |
| `topvisor/exports/blocked_queries.csv` | Точно не наш спрос, с причиной | {len(blocked)} строк |

Из запросов Вебмастера добавлено {extra} фраз, которых не было в ядре.
Целевая страница определена у {with_target} из {len(tgt)} фраз: там, где есть
фактические данные из beta-выгрузки Вебмастера, берётся реальный URL, остальные
получают страницу по кластеру.

## Почему файла три, а не один

Первая версия пакета грузила всё подряд: 626 фраз, из них 165 в группе
«Прочие» и часть мусора внутри осмысленных групп. Причин было три,
и все три лечатся по-разному.

1. **Годовой топ брался срезом.** Первые 200 строк выгрузки по показам
   шли в импорт без единой проверки. Туда попали внутренний поиск сайта
   («1 рекл»), синтаксис операторов Яндекса («<принт> в ижевске»), чужие
   домены, вбитые в поисковую строку, и запросы других типографий.
2. **«Прочие» не разбирали.** Это свалка всего, что не описано правилом.
   Грузить её в сервис бессмысленно: аналитика нечитаемая, проверка
   позиций платная.
3. **Кластеризация отвечает на другой вопрос.** Она говорит «о чём фраза»,
   но не «наша ли она». Релевантность проверяется отдельно, и порядок
   проверок важен: сначала ищется маркер услуги, и только потом чужие
   отрасли. В обратном порядке «визитки для стоматолога» вылетает как
   запрос к стоматологу.

Сейчас в Core не попадает ни одна фраза из файлов `review_` и `blocked_`.
Любую строку из них можно вернуть в импорт, исправив одну строку кода.

{table_reasons(review, "REVIEW: ждут решения человека")}
{table_reasons(blocked, "BLOCK: точно не наш спрос")}

## Порядок действий

1. **Создать группы.** По именам кластеров из `import_queries.csv`, порядок по
   объёму спроса. Группы в Topvisor работают как папки внутри проекта.
2. **Импортировать фразы.** Файл `import_queries.csv`, колонка `phrase`.
   Метод `add/keywords_2/keywords.import` бесплатный, проверки позиций не запускает.
3. **Разложить по группам.** `edit/keywords_2/keywords.move` или массовая правка
   при импорте, если формат файла это позволяет.
4. **Назначить целевые страницы.** `edit/keywords_2/keywords.*` с параметром
   `target`, значения из `keyword_targets.csv`.
5. **Кластеризация по целевым** (бесплатно, `edit/keywords_2/claster.bytarget`)
   сверит наши группы с фактическими и покажет, где мы ошиблись.
6. **Сбор позиций.** Платный, сначала запрос цены:
   `tv.py price positions --project-id 32490624`, запуск с подтверждением.
   Порядок: Yandex по России, раз в неделю, этого хватит.
7. **Добавить конкурентов** (платно) только если хватит бюджета: сейчас
   2 конкурента, для контроля динамики достаточно их плюс один по позициям.

## Группы и объём

{table_groups(grp)}

## Фразы без страницы

{len(need)} фраз попадают в кластеры без целевых страниц: сравнения, локальные
запросы и информационные вопросы. Это ровно работа месяца 2 из плана на
три месяца: страницы под эти фразы и есть основной контентный результат.

## Регламент

- Раз в неделю: `refresh_all.bat` (обновляет API и данные сайта), затем
  сбор позиций в Topvisor, затем сверка: что упало ниже 10 и почему.
- Раз в месяц: отчёт по позициям, оценка эффекта закрытых задач.
- Каждую новую страницу из плана сразу добавлять в ядро и в Topvisor с
  целевой страницей, иначе она останется без запросов.

## Чего не делать

- Не запускать платные модули (частотность, магнит слов, аудит сайта) без
  проверки цены: на балансе {read_balance()} руб., каждый запуск съедает его целиком.
- Не мешать 154 старых ключей с 800 новыми без групп: аналитика станет
  нечитаемой, а сравнение позиций невозможным.
"""
    PLAN.parent.mkdir(parents=True, exist_ok=True)
    PLAN.write_text(plan, encoding="utf-8")
    print("wrote %s (%d строк)" % (imp.relative_to(ROOT), len(import_rows)))
    print("wrote %s (%d строк)" % (tf.relative_to(ROOT), len(tgt)))
    print("wrote %s" % PLAN.relative_to(ROOT))
    print("групп: %d, фраз без страницы: %d, новых фраз: %d" % (len(grp), len(need), extra))
    return 0


def table_groups(grp):
    out = ["| Группа | Фраз |", "|---|---|"]
    for g, c in grp.most_common():
        out.append("| %s | %d |" % (g, c))
    return "\n".join(out) + "\n"


def table_reasons(items, title):
    """Сводка отсева по причинам: сколько фраз и почему."""
    if not items:
        return ""
    by = Counter((code, reason) for _p, code, reason in items)
    out = ["### %s" % title, "", "| Код | Причина | Фраз | Примеры |",
           "|---|---|---|---|"]
    for (code, reason), n in by.most_common():
        ex = [p for p, c, _r in items if c == code and _r == reason][:3]
        out.append("| %s | %s | %d | %s |"
                   % (code, reason, n, ", ".join("«%s»" % e for e in ex)))
    return "\n".join(out) + "\n"


def read_last_sync():
    if not DB.is_file():
        return "дата неизвестна"
    c = sqlite3.connect(str(DB))
    r = c.execute("select v from meta where k='last_sync'").fetchone()
    c.close()
    return r[0][:10] if r and r[0] else "дата неизвестна"


def read_balance():
    if not DB.is_file():
        return "не проверен"
    c = sqlite3.connect(str(DB))
    r = c.execute("select balance_all from balance_snapshots order by ts desc limit 1").fetchone()
    c.close()
    return ("%.0f" % float(r[0])).replace(".", ",") if r and r[0] is not None else "не проверен"


if __name__ == "__main__":
    sys.exit(main())
