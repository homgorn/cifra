#!/usr/bin/env python3
"""Сверяет числа в клиентских документах с фактами из данных.

Зачем: рассинхрон happened трижды, и каждый раз гейт был зелёным.

  1. Классификатор расширили с 8 групп до 22, страница плана и отчёт
     продолжали писать «8 групп».
  2. Синхронизатор подставил «22 группы», но число фраз взял из CSV
     импорта Topvisor, а число групп из wm-data.js. Получилось
     «627 запросов по 22 группы»: разные множества, правдоподобный текст.
  3. Текущий гейт ловил только литерал «8». Скажи документу «23 группы»,
     и гейт остаётся зелёным.

Поэтому здесь нет списка запрещённых чисел. Есть факты из facts.py, и
проверка идёт по месту в тексте: где стоит «запросов», там должно быть
core_queries, где «групп», там core_groups, где «фраз», там tv_keep.
Число не совпало с фактом, а не совпало с чёрным списком.

Режим --check ничего не пишет и возвращает 1 при расхождении. Режим
по умолчанию правит документы, но только те места, где число стоит в
известном контексте: подстановка вслепую ломает чужие числа вроде
«62 битые ссылки».

Запуск из корня проекта:
  python scripts/export/sync_cluster_counts.py --check
  python scripts/export/sync_cluster_counts.py
"""
import argparse
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import facts as F  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PLAN = os.path.join(ROOT, "reports", "cifra18-audit", "pages", "plan-3m.html")
REPORT = os.path.join(ROOT, "CLIENT_REPORT.md")

# Место в тексте -> факты. Формат: (регулярное выражение, [(факт, группа
# захвата), ...]). Группы нумеруются с единицы, как в re. Правило срабатывает
# не когда встретилось запрещённое число, а когда число стоит не на своём
# месте: подставили «23 группы» вместо «24», и гейт это видит.
RULES = [
    (r"(\d+)\s+запросов\s+в\s+(\d+)\s+группах",
     [("core_queries", 1), ("core_groups", 2)]),
    (r"(\d+)\s+реальных\s+запросов", [("core_queries", 1)]),
    (r"(\d+)\s+строк\s+выгрузки\s+панели", [("core_rows", 1)]),
    (r"из\s+(\d+)\s+строк\s+выгрузки", [("core_rows", 1)]),
    (r"(\d+)\s+из\s+(\d+)\s+реальных\s+запросов",
     [("top10_core", 1), ("top10_core_base", 2)]),
    (r"(\d+)\s+фраз\s+в\s+(\d+)\s+группах",
     [("tv_keep", 1), ("tv_groups", 2)]),
    (r"(\d+)\s+групп\s+L1", [("core_clusters", 1)]),
]


def expected(fx, key):
    return fx[key]


def scan(path, fx):
    """Возвращает список расхождений: (файл, строка, правило, фрагмент,
    число в тексте, число в данных)."""
    text = open(path, encoding="utf-8").read()
    bad = []
    for pat, slots in RULES:
        for m in re.finditer(pat, text):
            parts = m.groups()
            for key, g in slots:
                if g > len(parts) or parts[g - 1] is None:
                    continue
                got, exp = int(parts[g - 1]), fx[key]
                if got != exp:
                    line = text[:m.start()].count("\n") + 1
                    bad.append((os.path.relpath(path, ROOT), line, key,
                                re.sub(r"\s+", " ", m.group(0))[:90], got, exp))
    return bad


def fix(path, fx):
    """Подставляет факты вместо чисел в известных местах."""
    text = open(path, encoding="utf-8").read()
    hits = [0]

    def rebuild(m, slots):
        parts = list(m.groups())
        for key, g in slots:
            if g <= len(parts) and parts[g - 1] is not None:
                parts[g - 1] = str(fx[key])
        hits[0] += 1
        return m.expand(parts)

    out = text
    for pat, slots in RULES:
        out = re.sub(pat, lambda m, s=slots: rebuild(m, s), out)
    return out, hits[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="только проверить, ничего не писать")
    args = ap.parse_args()

    fx = F.collect()
    ph = F.phrases()
    print("факты: ядро %s, импорт %s, кластеров %d, ТОП-10 %s"
          % (ph["core_dat"], ph["import"], fx["core_clusters"], ph["top10_core"]))

    bad = []
    for path in (PLAN, REPORT):
        if not os.path.isfile(path):
            continue
        bad.extend(scan(path, fx))
        if args.check:
            continue
        new, hits = fix(path, fx)
        if new != open(path, encoding="utf-8").read():
            open(path, "w", encoding="utf-8").write(new)
            print("прав  %s: мест %d" % (os.path.relpath(path, ROOT), hits))
        else:
            print("ok    %s" % os.path.relpath(path, ROOT))

    if bad:
        print()
        for f, line, key, snip, got, exp in bad:
            print("FAIL  %s:%d  [%s] %s  -> в тексте %d, в данных %d"
                  % (f, line, key, snip, got, exp))
        print("SYNC FAILED: расхождений %d" % len(bad))
        return 1
    print("SYNC OK: числа в документах совпадают с фактами")
    return 0


if __name__ == "__main__":
    sys.exit(main())
