#!/usr/bin/env python3
"""Синхронизация раздела семантики в клиентском отчёте с расчётами.

Что было не так на 2026-09-27: таблица кластеров в отчёте была вбита руками и
разошлась с расчётом (например, визитки 35 запросов со средней позицией 3,8
против фактических 32 и 6,1). Кластеры теперь считаются в `build_wm_data.py`,
здесь берёмся тот же расчёт, плюс уточняется число запросов: 535 строк в
выгрузке, 492 реальных запроса, 43 строки мусора.

Запуск из корня проекта:
  python scripts/export/fix_client_semantic_section.py
"""
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
REPORT = ROOT / "CLIENT_REPORT.md"
WMDATA = ROOT / "reports" / "cifra18-audit" / "js" / "wm-data.js"
CORE_ROWS = 535

START = "## 📊 Семантическое ядро"
END = "## 🔴 Топ-10 пробелов контента"


def load():
    t = WMDATA.read_text(encoding="utf-8")
    d = json.loads(t[t.index("{"):].rstrip().rstrip(";"))
    return d


def main():
    d = load()
    clusters = d.get("clusters") or []
    qc = d.get("queryClusters") or []
    total = len(qc)
    junk = CORE_ROWS - total
    cnt = Counter(r["c"] for r in qc)
    commercial = sum(cnt.get(c["name"], 0) for c in clusters)
    local = cnt.get("Локальные", 0)
    brand = cnt.get("Бренд", 0)
    info = cnt.get("Информационные", 0) + cnt.get("Прочие", 0)
    with_target = sum(1 for r in qc if r.get("u"))

    intro = (f"## 📊 Семантическое ядро ({total} запросов, 7 дней мониторинга)\n"
             f"\nИз {CORE_ROWS} строк выгрузки панели {junk} оказались мусором: телефоны и длинные\n"
             f"описания товаров. Реальных запросов {total}, из них коммерческих {commercial},\n"
             f"локальных {local}, брендовых {brand}, информационных и прочих {info}.\n"
             f"Целевая страница определена у {with_target} запросов, у остальных её нет вообще.\n")

    table = ["### Позиции", ""]
    qt = d.get("queryTops") or {}
    for label, key in (("ТОП-1", "top1"), ("ТОП-3", "top3"), ("ТОП-10", "top10"), ("ТОП-20", "top20")):
        v = qt.get(key)
        if v is None:
            continue
        cnt_v = len(v) if isinstance(v, list) else v
        share = (cnt_v / CORE_ROWS * 100) if isinstance(cnt_v, int) else 0
        table.append("- **%s:** %d запросов (%.0f%%)" % (label, cnt_v, share))
    table.append("")
    table.append("### Топ коммерческих кластеров")
    table.append("")
    table.append("| Кластер | Запросов | Ср. позиция | В ТОП-10 | Целевая страница |")
    table.append("|---|---|---|---|---|")
    for c in clusters:
        url = next((r["u"] for r in qc if r["c"] == c["name"] and r.get("u")), "")
        table.append("| **%s** | %d | %.1f | %d%% | %s |"
                     % (c["name"], c["queries"], c["avg"], c["top10"],
                        ("`%s`" % url) if url else "нужна страница"))
    table.append("")
    table.append("Календари и мобильные стенды просели: средняя позиция выше 13, значит по ним нужны")
    table.append("отдельные страницы и работа с внутренними ссылками, а не только заголовки.")
    block = intro + "\n".join(table) + "\n\n---\n\n"

    text = REPORT.read_text(encoding="utf-8")
    i = text.find(START)
    if i < 0:
        print("раздел не найден")
        return 1
    j = text.find(END, i)
    if j < 0:
        j = len(text)
    REPORT.write_text(text[:i] + block + text[j:], encoding="utf-8")
    print("раздел семантики перезаписан: %d запросов, %d кластеров, мусора отсеяно %d"
          % (total, len(clusters), junk))
    return 0


if __name__ == "__main__":
    sys.exit(main())
