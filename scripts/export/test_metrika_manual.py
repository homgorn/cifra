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
    print("6. ЛИНЕЙНЫЙ СПИСОК ЦЕЛЕЙ")
    goal_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "..", "data", "manual", "metrika",
                             "2026-09", "goals.txt")
    goal_file = os.path.normpath(goal_file)
    check("файл целей на месте", os.path.isfile(goal_file), goal_file)
    if os.path.isfile(goal_file):
        text = M.read_any(goal_file)[0]
        check("опознан как линейный список", M._looks_like_linear_goals(text))
        g = M.parse_linear_goals(goal_file, text)
        check("проблем не найдено", g["problem"] is None, g["problem"] or "")
        if g["problem"] is None:
            check("раскладка доказана суммой",
                  bool(g.get("sum_verified")), str(g.get("sum_verified")))
            check("выполнений цели 18", g["measures"]["goal_hits"] == 18,
                  str(g["measures"].get("goal_hits")))
            check("целевых визитов 17", g["measures"]["target_visits"] == 17,
                  str(g["measures"].get("target_visits")))
            check("строк по дням 12", len(g["rows"]) == 12,
                  str(len(g["rows"])))
            check("конверсия разобралась",
                  g["measures"]["conversion"] == 0.0068,
                  str(g["measures"].get("conversion")))

            # Сломанная раскладка обязана быть отвергнута, а не
            # разобрана по-разному и не замечена.
            # Портится поле, которое участвует в сверке суммой. Порча
            # конверсии прошла бы незамеченной: она в сумму не входит.
            broken = text.replace("Итого и средние\n0,68 %\n18\n100,00 %",
                                  "Итого и средние\n0,68 %\n99\n100,00 %")
            gb = M.parse_linear_goals(goal_file, broken)
            check("испорченный итог отвергнут", gb["problem"] is not None,
                  "принят молча" if not gb["problem"] else "")
            check("в отказе названа причина",
                  "сумм" in (gb["problem"] or "").lower(), gb["problem"] or "")

            short = text.replace("29 сентября\n4,00 %\n2\n11,11 %\n2\n11,76 %\n0,00 \n2\n11,76 %\n3\n11,11 %",
                                 "29 сентября\n4,00 %\n2\n11,11 %\n2\n11,76 %\n0,00 \n2\n11,76 %\n3\n1,00 %")
            gsh = M.parse_linear_goals(goal_file, short)
            check("порча в середине записи отвергнута",
                  gsh["problem"] is not None or
                  M.period_key(gsh.get("period")) is not None,
                  "разобралось молча")
            check("порча в середине не тихо прошла дальше",
                  (gsh["problem"] is not None) or
                  (gsh.get("rows") and gsh["rows"][0].get("Просмотры") == "3"),
                  "иначе данные поедут дальше с чужой разметкой")

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