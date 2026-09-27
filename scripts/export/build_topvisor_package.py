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
    "Листовки и флаеры": "/catalog/poligrafiya/listovki/",
    "Широкоформатная печать": "/catalog/poligrafiya/shirokoformatnaya-pechat/",
    "Широкоформат": "/catalog/poligrafiya/shirokoformatnaya-pechat/",
    "Мобильные стенды": "/catalog/mobilnye-stendy/",
    "Сувенирка и мерч": "/catalog/suvenirnaya-produktsiya/",
    "Инженерная печать": "/inzhenernaya-pechat/",
    "Бренд": "/",
    "Информационные": "",
    "Сравнения": "",
    "Локальные": "",
    "Прочие": "",
}
# Кластеры, у которых нет своей страницы: под них нужно создавать.
NEEDS_PAGE = {"Сравнения", "Локальные", "Информационные"}

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

    Их не импортируем подряд: это 1000+ строк, проверка позиций по ним съест
    весь баланс Topvisor. Берём только те, что уже видны в ядре, плюс первые
    200 из годового топа по показам с порогом отсечения."""
    out = []
    base = WM
    if not base.is_dir():
        return out
    import json
    day = sorted(p.name for p in base.iterdir() if p.is_dir())[-1]
    f = base / day / "queries_12m" / "q_popular_shows_12m.json"
    if f.is_file():
        data = json.load(open(f, encoding="utf-8"))
        for q in data.get("queries", [])[:200]:
            t = (q.get("query_text") or "").strip()
            if t:
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

    # 1. Импорт: всё ядро плюс запросы из Вебмастера, которых в ядре нет
    import_rows = []
    seen = set()
    for r in rows:
        q = (r.get("Query") or "").strip()
        if not q or q in seen:
            continue
        seen.add(q)
        import_rows.append({
            "phrase": q,
            "group": r.get("Cluster_L1") or "Прочие",
            "avg_position": r.get("Avg_Position") or "",
            "in_topvisor": "да" if q in have else "нет",
            "target_url": r.get("Target_Page") or "",
        })
    extra = 0
    for q in webmaster_queries():
        q = q.strip()
        if not q or q in seen:
            continue
        seen.add(q)
        extra += 1
        c = classify(q)
        import_rows.append({"phrase": q, "group": c, "avg_position": "",
                            "in_topvisor": "да" if q in have else "нет",
                            "target_url": CLUSTER_TARGETS.get(c, "")})
    imp = OUT / "import_queries.csv"
    with open(imp, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(import_rows[0].keys()))
        w.writeheader()
        w.writerows(import_rows)

    # 2. Целевые страницы: из кластера плюс фактические пути из SERP-выгрузки
    tgt = []
    for r in rows:
        q = (r.get("Query") or "").strip()
        if not q:
            continue
        cluster = r.get("Cluster_L1") or "Прочие"
        actual = serp_by_q.get(q)
        if actual:
            best = min(actual, key=lambda s: s["p"] or 999)
            url = best["path"]
            source = "факт из Вебмастера"
        else:
            url = r.get("Target_Page") or CLUSTER_TARGETS.get(cluster, "")
            source = "по кластеру" if url else "нужна новая страница"
        tgt.append({
            "phrase": q,
            "group": cluster,
            "target_url": url,
            "target_source": source,
            "avg_position": r.get("Avg_Position") or "",
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

Из запросов Вебмастера добавлено {extra} фраз, которых не было в ядре.
Целевая страница определена у {with_target} из {len(tgt)} фраз: там, где есть
фактические данные из beta-выгрузки Вебмастера, берётся реальный URL, остальные
получают страницу по кластеру.

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
