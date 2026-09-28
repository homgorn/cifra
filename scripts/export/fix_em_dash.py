#!/usr/bin/env python3
"""Редакторский проход по em-dash в вики.

Зачем не регулярка. Тире в русском тексте стоит в нескольких ролях сразу,
и одна замена на запятую ломает грамматику по-разному в каждой:

  «После — масштабирование»      -> «После, масштабирование»   бессмыслица
  «Этап 0 — Foundation»          -> «Этап 0, Foundation»       теряется смысл
  «| Роль | — | Х |»             -> «| Роль | , | Х |»         ломает таблицу
  «├── INDEX.md — мастер-индекс»-> «├── INDEX.md , мастер»    ломает дерево

Поэтому здесь роли разбираются по месту, и у каждой своя замена:

| Место | Замена | Почему |
|---|---|---|
| блок кода, `X — Y` | `X - Y` | дефис, разделитель подписи, грамматики нет |
| ячейка таблицы, одно `—` | `н/д` | читаемый маркер пустоты, как в отчёте |
| ячейка таблицы, `X — Y` | `X: Y` | в таблице это подпись и значение |
| диапазон дат | `с X по Y` | однозначно, тире тут вообще не нужно |
| заголовок `# A — B` | `# A: B` | двоеточие, стандарт для заголовков |
| пункт `**A** — B` | `**A**: B` | подпись и значение |
| проза `Метрика — ID` | `Метрика: ID` | тоже подпись и значение |
| проза, всё остальное | `, ` | обычная запятая перед приложением |

Прогон идемпотентен: второй запуск ничего не меняет.

Запуск из корня проекта:
  python scripts/export/fix_em_dash.py --audit    # показать, что изменится
  python scripts/export/fix_em_dash.py            # применить
  python scripts/export/fix_em_dash.py --check    # ничего не писать, codes 1
"""
import argparse
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WIKI = os.path.join(ROOT, "brain", "wiki")
DASH = "\u2014"
RULES = os.path.join(ROOT, "scripts", "export")

# Строки, где тире названо как приём, а не использовано. Заменить знак в
# них значит испортить формулировку самого правила: «Fix em-dash (—) →
# comma» превратится в «Fix em-dash (,) → comma». Таких строк три, они
# проверены глазами.
MENTIONS = ("em-dash", "em dash", "тире")

DATE_RANGE = re.compile(r"(\d{4}-\d{2}-\d{2})\s*" + DASH + r"\s*(\d{4}-\d{2}-\d{2})")


def fences(lines):
    """Индексы строк внутри блоков кода."""
    inside, out = False, set()
    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            inside = not inside
            continue
        if inside:
            out.add(i)
    return out


def fix_code(line):
    """Внутри кода тире это разделитель подписи, а не знак препинания."""
    return DATE_RANGE.sub(r"с \1 по \2", line).replace(DASH, "-")


def fix_table_cell(line):
    """Ячейка: одиночное тире означает пустоту, парное означает подпись.

    Строка режется по `|`, а не ищется регекспом. Поиском неперекрывающихся
    пар `|...|` соседние ячейки делят один разделитель, и вторая из них
    остаётся без открывающей палки, то есть не находится вовсе. Именно
    так не трогались 157 тире в первый проход.
    """
    line = DATE_RANGE.sub(r"с \1 по \2", line)
    parts = line.split("|")
    for i in range(1, len(parts) - 1):
        s = parts[i].strip()
        if s == DASH:
            parts[i] = " н/д "
        elif DASH in s:
            parts[i] = " " + re.sub(r"\s*" + DASH + r"\s*", ": ", s) + " "
    return "|".join(parts)


def fix_heading(line):
    line = DATE_RANGE.sub(r"с \1 по \2", line)
    if line.lstrip().startswith("#"):
        if ":" not in line:
            line = re.sub(r"\s*" + DASH + r"\s*", ": ", line, count=1)
        else:
            line = re.sub(r"\s*" + DASH + r"\s*", ", ", line, count=1)
    return line


def fix_prose(line):
    """Обычный текст и пункты списка.

    Порядок правил важен. Сначала подпись и значение, потом всё остальное
    уходит в запятую: на этом шаге грамматику уже не испортить, потому
    что перед тире гарантированно стоит законченный член предложения.
    """
    line = DATE_RANGE.sub(r"с \1 по \2", line)
    # Подпись сразу после выделения, с пробелом или без:
    # **Метрика** — доступ, **Метрика**— доступ
    line = re.sub(r"\*\*\s*" + DASH + r"\s+", "**: ", line)
    # Подпись и значение, где слева законченный член предложения:
    # «Phase 0 — Foundation». Правая часть начинается с буквы, значит
    # это не конец предложения, а приложение, и ему идёт двоеточие.
    line = re.sub(
        r"(?<=[A-Za-zА-Яа-яЁё0-9)])[ \t]*" + DASH + r"[ \t]+(?=[A-Za-zА-Яа-яЁё])",
        ": ", line)
    # Остаток: перед тире может стоять знак конца фразы, тогда тире
    # держит новое предложение и уходит в точку.
    line = re.sub(r"([.,;:!?])\s+" + DASH + r"\s+", r"\1 ", line)
    line = re.sub(r"\s+" + DASH + r"\s+", ", ", line)
    line = re.sub(r"\s+" + DASH + r"\s*$", "", line)
    return line


def tidy(line):
    """Уборка следов замены. Без неё «X, , Y» выглядит как ошибка вёрстки.

    Пробел перед `|` и разделитель строк таблицы тут не трогаются: это
    структура, а не след замены.
    """
    line = re.sub(r",\s*,", ",", line)
    line = re.sub(r",\s*([.,;:!?])", r"\1", line)
    line = re.sub(r"([.,;:!?])\s*,", r"\1", line)
    line = re.sub(r"\(\s*,\s*", "(", line)
    line = re.sub(r",(\s*\|)", r"\1", line)
    line = re.sub(r"\|(\s*),", r"\1", line)
    line = re.sub(r"\|,\s*", "| ", line)
    line = re.sub(r":\s*([.,;:!?])", r"\1", line)
    line = re.sub(r"\|\s*:\s*\|", "| н/д |", line)
    line = re.sub(r"[ \t]{2,}", " ", line)
    line = re.sub(r"[ \t]+\n", "\n", line)
    return line


def fix_line(line, in_code):
    if DASH not in line:
        return line
    low = line.lower()
    if any(m in low for m in MENTIONS):
        return line                      # тире здесь названо, а не вставлено
    if in_code:
        out = fix_code(line)
    else:
        s = line.strip()
        if s.startswith("|") and not re.fullmatch(r"\|[\s|:-]*\|?", s):
            out = fix_table_cell(line)
        elif s.startswith("#"):
            out = fix_heading(line)
        else:
            out = fix_prose(line)
    return tidy(out)


def walk(apply_changes):
    changed_files, total = [], 0
    for dp, dns, fns in os.walk(WIKI):
        dns[:] = [d for d in dns if d != "__pycache__"]
        for fn in sorted(fns):
            if not fn.endswith(".md"):
                continue
            path = os.path.join(dp, fn)
            rel = os.path.relpath(path, ROOT)
            src = open(path, encoding="utf-8").read()
            lines = src.split("\n")
            in_code = fences(lines)
            out, hits = [], 0
            for i, line in enumerate(lines):
                if DASH not in line:
                    out.append(line)
                    continue
                new = fix_line(line, i in in_code)
                if new != line:
                    hits += 1
                    print("  %-56s %4d  %s" % (rel[:56], i + 1,
                                                re.sub(r"\s+", " ", line.strip())[:96]))
                    print("  %-56s       -> %s" % ("", re.sub(r"\s+", " ", new.strip())[:96]))
                out.append(new)
            if hits:
                total += hits
                changed_files.append((rel, hits))
                if apply_changes:
                    open(path, "w", encoding="utf-8").write("\n".join(out))
    return changed_files, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="только проверить")
    ap.add_argument("--audit", action="store_true", help="показать каждую замену")
    args = ap.parse_args()

    if args.audit:
        print("=== что изменится ===")
    files, total = walk(apply_changes=not (args.check or args.audit))
    print()
    if args.check:
        left = []
        for dp, dns, fns in os.walk(WIKI):
            dns[:] = [d for d in dns if d != "__pycache__"]
            for fn in fns:
                if fn.endswith(".md"):
                    p = os.path.join(dp, fn)
                    for i, line in enumerate(open(p, encoding="utf-8").read().split("\n"), 1):
                        if DASH in line and not any(m in line.lower() for m in MENTIONS):
                            left.append((os.path.relpath(p, ROOT), i,
                                         re.sub(r"\s+", " ", line.strip())[:90]))
        if left:
            for rel, ln, line in left[:20]:
                print("FAIL  %-52s %4d  %s" % (rel[:52], ln, line))
            print("EM-DASH FAILED: осталось %d, кроме %d строк, где тире названо"
                  % (len(left), len(MENTIONS)))
            return 1
        print("EM-DASH OK: в вики ноль вхождений, кроме строк, где тире названо")
        return 0

    print("обработано файлов: %d, замен: %d" % (len(files), total))
    for rel, n in sorted(files, key=lambda x: -x[1])[:20]:
        print("  %-58s %d" % (rel, n))
    if len(files) > 20:
        print("  ... ещё %d файлов" % (len(files) - 20))
    return 0


if __name__ == "__main__":
    sys.exit(main())
