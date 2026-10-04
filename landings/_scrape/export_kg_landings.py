#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Экспорт лендингов в граф знаний RDF.

Зачем. В `brain/wiki/knowledge_graph` лежат сущности услуг по подразделам
сайта, но лендингов там не было вообще: пятнадцать собранных страниц не
были отражены в машинно-читаемой базе, и по графу нельзя было понять,
какая услуга на какой странице показывается и что по ней уже сделано.

Экспорт идёт из `config.json`, а не из ручного списка. Иначе через месяц
граф разойдётся с реальностью, и это будет выглядеть как правда о проекте:
сущности-то красивые, а страниц давно нет.

ЧТО ЭКСПОРТ НЕ ДЕЛАЕТ. Не дописывает недостающие сущности услуг. Описание
услуги это авторский текст, и выдумывать его значит внести в базу вымысел.
Вместо этого пишется список задач: каких подразделов в графе нет и на
каких лендингах они встречаются.

СТАТУС. У всех лендингов один и он честный: страницы собраны и проверены
гейтами, но ни одна не выложена. Значение называется `not_published`, а не
`built_not_deployed`: прежнее заканчивалось на `deployed`, и при беглом
чтении выглядело как «опубликован», то есть наоборот.

Запуск из корня проекта:
  python landings/_scrape/export_kg_landings.py            отчёт
  python landings/_scrape/export_kg_landings.py --apply    записать
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
LANDINGS = ROOT.parent
CATALOG = ROOT / "out" / "catalog.json"
KG = LANDINGS.parent / "brain" / "wiki" / "knowledge_graph" / "entities"
TARGET = KG / "landings.ttl"
GAPS = KG.parent / "landings_subsections_without_service.md"
COMBINED = KG.parent / "cifra18_knowledge_graph.ttl"

BUILD_DATE = "2026-10-04"
STATUS = "not_published"


def subsection_iri(sub: str, known: dict[str, str]) -> str | None:
    return known.get(sub)


def known_service_ids(subsections: set[str]) -> dict[str, str]:
    """Подраздел каталога → идентификатор сущности услуги в графе.

    Сопоставление идёт по суффиксу, а не по сборке полного имени. В графе
    идентификаторы строятся как
    `cifra:service_suvenirnaya_pechat_na_ruchkakh`: раздел подписан
    сокращённо, `suvenirnaya` вместо `suvenirnaya-produktsiya`, поэтому
    сборка имени по образцу дала 62 висячие ссылки из 214.

    Ключ строится суффиксом целиком, а не по последнему подчёркиванию. У
    того же идентификатора хвост `ruchkakh`, а подраздел называется
    `pechat_na_ruchkakh`, и словарь по хвосту получался почти пустым: ноль
    ссылок у лендинга с кружками. Поэтому сначала собираются все
    идентификаторы, потом каждый подраздел ищется в них суффиксом.
    """
    iris: list[str] = []
    for p in KG.glob("*.ttl"):
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            if '"@id"' not in line or "cifra:service" not in line:
                continue
            iris.append(line.split('"')[3].strip())

    out: dict[str, str] = {}
    for sub in subsections:
        tail = sub.replace("-", "_")
        hit = next((i for i in iris if i.endswith("_" + tail)), None)
        if hit:
            out[sub] = hit
    return out


def collect() -> list[dict]:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    by_src: dict[str, dict] = {}
    for i in catalog:
        if i.get("photos"):
            by_src.setdefault(i["photos"][0], i)

    out: list[dict] = []
    for folder in sorted(LANDINGS.iterdir()):
        cfg_path = folder / "config.json"
        if not cfg_path.is_file():
            continue
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        items = [c for g in cfg.get("catalog", {}).get("groups", [])
                 for c in g.get("items", [])]
        subs: list[str] = []
        seen: set[str] = set()
        for card in items:
            item = by_src.get(card.get("src"))
            if not item or not item.get("subsection"):
                continue
            if item["subsection"] in seen:
                continue
            seen.add(item["subsection"])
            subs.append(item["subsection"])
        out.append({
            "slug": cfg["landing"]["slug"],
            "title": cfg["landing"]["title"],
            "section": cfg.get("sources", {}).get("landingSection", ""),
            "groups": len(cfg.get("catalog", {}).get("groups", [])),
            "items": len(items),
            "demand": cfg.get("sources", {}).get("demand", ""),
            "subs": subs,
        })
    return out


def build_entity(d: dict, known: dict[str, str],
                 unmatched: dict[str, set[str]]) -> dict:
    """Одна сущность лендинга как словарь.

    Сущность собирается словарём, а не склейкой строк. При склейке
    обязательная запятая после последнего свойства попадала в файл, JSON
    висячие запятые не допускает, и весь граф переставал разбираться.
    json.dumps снимает класс ошибок целиком, а не один его случай.
    """
    node = {
        "@id": f"cifra:landing_{d['slug'].replace('-', '_')}",
        "@type": "cifra:Landing",
        "schema:name": d["title"],
        "cifra:slug": d["slug"],
        "cifra:groupCount": str(d["groups"]),
        "cifra:itemCount": str(d["items"]),
        "cifra:status": f"cifra:landing_status_{STATUS}",
        # Дата строкой, а не литералом ^^xsd:date: литерал допустим в
        # Turtle, но весь остальной граф написан как JSON-LD без
        # типизированных литералов и перестаёт разбираться json.load.
        "cifra:builtOn": BUILD_DATE,
    }
    if d["section"]:
        node["schema:about"] = d["section"]
    if d["demand"]:
        node["rdfs:comment"] = d["demand"]

    refs = []
    for sub in d["subs"]:
        iri = subsection_iri(sub, known)
        if iri:
            refs.append({"@id": iri})
        else:
            unmatched.setdefault(sub, set()).add(d["slug"])
    if refs:
        node["cifra:coversSubsection"] = refs
    return node


def build_ttl(data: list[dict], known: dict[str, str]) -> tuple[str, dict]:
    # Какие подразделы не нашли сущность услуги и на каких лендингах они
    # встречаются. Пишется списком, а не счётчиком: по счётчику нельзя
    # понять, что именно чинить в графе.
    unmatched: dict[str, set[str]] = {}
    graph = [build_entity(d, known, unmatched) for d in data]
    doc = {
        "@context": {
            "cifra": "https://cifra18.ru/ontology#",
            "schema": "https://schema.org/",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "xsd": "http://www.w3.org/2001/XMLSchema#",
            # Значения статуса объявлены здесь, а не описаны в комментарии:
            # иначе потребитель графа вынужден угадывать, что значит
            # cifra:landing_status_not_published.
            STATUS: f"cifra:landing_status_{STATUS}",
        },
        "@graph": graph,
    }
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n", unmatched


def write_gaps_report(unmatched: dict[str, set[str]],
                      total_subs: int, covered_subs: int) -> None:
    """Список подразделов, для которых в графе нет услуги.

    Молча пропустить разрыв нельзя: в графе тогда просто нет части услуг,
    и по нему нельзя понять, что знание неполное. Заполнить пропуски
    автоматически тоже нельзя: описание услуги это авторский текст.
    Поэтому это список задач, а не заготовка.
    """
    lines = [
        "# Подразделы каталога без сущности услуги в графе",
        "",
        "Сгенерировано: `landings/_scrape/export_kg_landings.py --apply` "
        f"({BUILD_DATE}).",
        "Перегенерировать после того, как допишешь описания.",
        "",
        "## Что это",
        "",
        f"Выкачка сайта содержит {total_subs} подразделов. Описание услуги в "
        f"графе есть для {covered_subs} из них, нет для "
        f"{total_subs - covered_subs}.",
        "",
        f"Из этих {total_subs - covered_subs} на лендингах встречаются "
        f"{len(unmatched)}; оставшийся "
        f"{total_subs - covered_subs - len(unmatched)} не попал ни на одну "
        "страницу и в списке ниже не нужен.",
        "",
        "Из-за этого `entities/landings.ttl` ссылается только на те услуги,",
        "которые в графе есть, и молчит про остальные. Число ссылок в графе",
        "не равно числу подразделов каталога: один подраздел может",
        "покрываться несколькими лендингами, и наоборот.",
        "",
        "Цифры считаются при генерации, а не написаны здесь руками:",
        "текст с зашитым «меньше половины» продержался одну правку и стал",
        "враньём, когда сопоставление подразделов починили.",
        "",
        "## Чего не хватает",
        "",
        "| Подраздел каталога | На каких лендингах |",
        "|---|---|",
    ]
    for sub in sorted(unmatched):
        lines.append(f"| `{sub}` | {', '.join(sorted(unmatched[sub]))} |")
    lines += [
        "",
        "## Что делать",
        "",
        "Дописать сущности в соответствующие файлы:",
        "`entities/suvenirnaya_services.ttl`, `entities/poligrafiya_services.ttl`,",
        "`entities/inzhenernaya_services.ttl`, `entities/stendy_services.ttl`,",
        "`entities/mobilnye_stendy_services.ttl`, `entities/interer_services.ttl`,",
        "`entities/shirokoformatnaya_services.ttl`.",
        "",
        "Идентификатор по образцу соседей: `cifra:service_<раздел>_<подраздел>`,",
        "где раздел подписан сокращённо: `suvenirnaya` вместо",
        "`suvenirnaya-produktsiya`. После этого экспорт запускается ещё раз,",
        "и ссылки появляются сами.",
    ]
    io.open(GAPS, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print(f"записано: {GAPS.name} ({len(unmatched)} подразделов без услуги)")


def patch_combined(doc_graph: list[dict]) -> int:
    """Добавляет сущности лендингов в сводный граф.

    `cifra18_knowledge_graph.ttl` это снимок, а не сборка: скрипта,
    который его собирает, в проекте нет, и файл отстаёт от `entities/`
    уже давно. Молча оставить лендинги только в `entities/` нельзя, в
    сводном графе их тогда просто нет, а именно сводный читают.

    Перезаписывается только список сущностей: чужие узлы не трогаются,
    добавляются или заменяются лишь те, чей `@id` начинается с
    `cifra:landing_`. Иначе повторный запуск экспорта размножал бы
    лендинги.
    """
    if not COMBINED.exists():
        return 0
    try:
        doc = json.loads(io.open(COMBINED, encoding="utf-8").read())
    except json.JSONDecodeError as e:
        print(f"! сводный граф не разбирается, пропущен: {e}")
        return 0

    graph = doc.get("@graph")
    if not isinstance(graph, list):
        print("! в сводном графе нет списка @graph, пропущен")
        return 0

    kept = [n for n in graph
            if not str(n.get("@id", "")).startswith("cifra:landing_")]
    added = len(doc_graph)
    doc["@graph"] = kept + doc_graph
    ctx = doc.setdefault("@context", {})
    if isinstance(ctx, dict):
        ctx[STATUS] = f"cifra:landing_status_{STATUS}"

    io.open(COMBINED, "w", encoding="utf-8", newline="\n").write(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
    return added


def main() -> int:
    ap = argparse.ArgumentParser(description="Экспорт лендингов в граф знаний.")
    ap.add_argument("--apply", action="store_true", help="записать файлы")
    args = ap.parse_args()

    if not CATALOG.exists():
        print("Нет out/catalog.json. Сначала fetch_catalog.py --parse-only")
        return 1

    data = collect()
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    all_subs = {i["subsection"] for i in catalog if i.get("subsection")}
    known = known_service_ids(all_subs)
    ttl, unmatched = build_ttl(data, known)

    print(f"лендингов: {len(data)}")
    for d in data:
        print(f"  {d['slug']:<30} групп {d['groups']:>2}  позиций {d['items']:>3}  "
              f"подразделов {len(d['subs']):>2}")
    print(f"подразделов в выкачке: {len(all_subs)}")
    print(f"подразделов, для которых в графе есть услуга: {len(known)}")
    print(f"ссылок, которые не нашли свою сущность услуги: "
          f"{sum(len(v) for v in unmatched.values())}")
    if unmatched:
        print("Подразделы без описания услуги в графе:")
        for sub in sorted(unmatched):
            print(f"  {sub:<40} на лендингах: {', '.join(sorted(unmatched[sub]))}")
        print("Это не ошибка сборки, а дыры в графе. Дописать описания")
        print("услуг, и ссылки появятся сами при следующем запуске экспорта.")

    # Файл должен разбираться как JSON: весь остальной граф написан так
    # же, и потребители открывают его json.load. Невалидный файл в графе
    # хуже отсутствующего: он выглядит как обновлённые данные.
    try:
        json.loads(ttl)
    except json.JSONDecodeError as e:
        print(f"! выгруженный файл не разбирается как JSON: {e}")
        return 1

    if not args.apply:
        print("\nЭто был отчёт. Повторить с --apply, чтобы записать.")
        return 0

    KG.mkdir(parents=True, exist_ok=True)
    # Запись идёт целиком в память и только потом на диск: открытие файла
    # на запись обрезает его сразу, и упавшая запись оставляет файл пустым.
    # Так потерялся сам этот скрипт, когда в него попал `io.open(p, "w")`
    # перед исключением.
    payload = ttl
    io.open(TARGET, "w", encoding="utf-8", newline="\n").write(payload)
    print(f"\nзаписано: {TARGET} ({len(ttl) // 1024} КБ)")
    added = patch_combined(json.loads(ttl)["@graph"])
    if added:
        print(f"обновлён сводный граф {COMBINED.name}: сущностей лендингов {added}")
    write_gaps_report(unmatched, len(all_subs), len(known))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())