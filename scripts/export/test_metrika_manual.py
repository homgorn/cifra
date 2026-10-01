"""Проверки к правилам metrika_manual.

Три свойства, которые ломались по ходу работы и которые нельзя
подтвердить глазами на выгрузке:

1. Разные периоды в одной папке не считаются расхождением.
2. Файл с неизвестным периодом не сверяется с чужой базой.
3. Проверка одинаковых чисел смотрит на долю итога, а не на сам
   факт повтора.

Запуск:

    python scripts/export/test_metrika_manual.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

import metrika_manual as M                                     # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    mark = "ок" if cond else "НЕ ПРОЙДЕНО"
    print("  %-58s %s" % (name, mark))
    if not cond:
        FAILS.append(name)
        if detail:
            print("      %s" % detail)


def fake(kind, visits, visitors=None, rows=None, total_row=True):
    spec = M.KINDS[kind]
    p = {"kind": kind, "rows": rows or [], "measures": {},
         "total_row": {} if total_row else None, "header": [],
         "file": "x", "problem": None}
    p["measures"]["visits"] = visits
    if "visitors" in spec["measures"]:
        p["measures"]["visitors"] = visitors
    return p


def main():
    print("1. РАЗНЫЕ ПЕРИОДЫ В ОДНОЙ ПАПКЕ")
    quarter = {"from": "2026-07-02", "to": "2026-10-01", "days": 92,
               "source": "колонка дат"}
    years = {"from": "2021-10-02", "to": "2026-10-01", "days": 1826,
             "source": "колонка дат"}

    a = fake("visits_daily", 5036, 2540)
    b = fake("sources", 5036, 2540)
    c = fake("visits_daily", 184000, 91000)
    d = fake("search_phrases", 41000, 33000)

    r1 = M.reconcile([a, b], quarter)
    r2 = M.reconcile([c, d], years)
    check("квартал сходится", r1["ok"], r1.get("problem", ""))
    check("пять лет сходятся", r2["ok"], r2.get("problem", ""))
    check("база квартала 5036", r1["base"] == 5036, str(r1["base"]))
    check("база пяти лет 184000", r2["base"] == 184000, str(r2["base"]))

    r3 = M.reconcile([a, d], quarter)
    check("разные периоды в одной сверке дают ошибку",
          not r3["ok"], "и должны, если их смешать")

    print()
    print("2. НЕИЗВЕСТНЫЙ ПЕРИОД")
    e = fake("sources", 5036, 2540)
    e["period"] = None
    check("ключ периода для пустого равен неизвестен",
          M.period_key(None) == "неизвестен")
    check("ключ периода собирается из дат",
          M.period_key(quarter) == "2026-07-02..2026-10-01",
          M.period_key(quarter))

    print()
    print("3. ОДИНАКОВЫЕ ЧИСЛА, МЕРЯЕТСЯ ДОЛЯ")
    small = fake("devices", 5036, 2540, rows=[
        {"Тип устройства": "Смартфоны", "visits": 3, "visitors": 3}
        for _ in range(16)])
    check("хвост из шестнадцати строк по три визита не считается ошибкой",
          M.duplicate_measure(small) is None)

    big = fake("search_phrases", 32865, 23279, rows=[
        {"Поисковая фраза": "фраза %d" % i, "visits": 1369,
         "visitors": 1369} for i in range(18)])
    got = M.duplicate_measure(big)
    check("восемнадцать строк по 1369 считается ошибкой", got is not None)
    if got:
        check("доля посчитана верно, около 75 процентов",
              0.7 <= got["share"] <= 0.8, "%.3f" % got["share"])

    four = fake("search_phrases", 32865, 23279, rows=[
        {"Поисковая фраза": "фраза %d" % i, "visits": 1369,
         "visitors": 1369} for i in range(4)])
    check("четыре строки по 1369 не считаются ошибкой",
          M.duplicate_measure(four) is None)

    print()
    print("4. РАЗБОР ЧИСЕЛ")
    check("1 234 разряда через неразрывный пробел", M.to_number("1\u00a0234") == 1234)
    check("процент превращается в долю", M.to_number("1,49\u00a0%") == 0.0149,
          str(M.to_number("1,49\u00a0%")))
    check("время 00:08:45 в секунды", M.to_number("00:08:45") == 525,
          str(M.to_number("00:08:45")))
    check("мусор даёт None, а не ноль", M.to_number("Не определено") is None)
    check("пустая строка даёт None", M.to_number("") is None)

    print()
    print("5. ОПОЗНАНИЕ ВИДА ПО КОЛОНКАМ, А НЕ ПО ИМЕНИ")
    check("цели по колонкам",
          M.detect_kind(["Цель", "Визиты", "Посетители"]) == "goals")
    check("время на site's первый столбец это срез",
          M.detect_kind(["Время на сайте", "Визиты", "Посетители",
                         "Отказы"]) == "time_on_site")
    check("глубина не съедается временем",
          M.detect_kind(["Глубина просмотра", "Визиты", "Посетители",
                         "Отказы"]) == "depth")
    check("возраст узнаётся по классу css",
          M.detect_kind(["text-overflow", "numeric-cell__value",
                         "numeric-cell__add-value"]) == "ages")
    check("поисковые фразы узнаются",
          M.detect_kind(["Поисковая фраза", "Поисковая система",
                         "Визиты"]) == "search_phrases")

    print()
    if FAILS:
        print("НЕ ПРОШЛИ: %d" % len(FAILS))
        for f in FAILS:
            print("  %s" % f)
        return 1
    print("ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")
    return 0


if __name__ == "__main__":
    sys.exit(main())