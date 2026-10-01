"""Факты Метрики из ручных выгрузок.

Отдельный модуль, потому что источник ручной: числа приходят из файлов,
которые сняты с экрана, а не из API. Проверки на согласованность уже
сделаны при разборе, здесь они не повторяются, а берётся готовое.

Каждое число выводится со знаменателем. Процент без знаменателя в
клиентском отчёте это «о чём это вообще», а с ним это доля от известной
величины.

Три вещи, которые пришлось решить при разборе и которые нельзя
переоткрывать здесь:

* посе��ителей по дням суммировать нельзя, человек считается один раз за
  период. Сумма 3 466 против уникальных 2 540 это повторные появления, а
  не ошибка;
* доля новых посетителей в итоговой строке 0,9717 верна. Проверено:
  новых по дням в сумме 2 468, уникальных 2 540, отношение 0,9717.
  Невзвешенное среднее дневных долей даёт 0,71 и вводит в заблуждение,
  потому что весит пустой день наравне с полным;
* глубина в итоговой строке равна просмотрам делённым на визиты ровно,
  дополнительно проверять нечего.
"""

import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"C:\susa ai\2026 cifra audit"
MM = os.path.join(ROOT, "data", "exports", "metrika_manual")


def newest():
    """Самая свежая папка разбора ручных выгрузок.

    Выбирается по дате папки, а не по времени записи: при повторном
    разборе того же дня время меняется, и это не должно менять выбор.
    """
    if not os.path.isdir(MM):
        return None
    days = sorted(d for d in os.listdir(MM)
                  if os.path.isdir(os.path.join(MM, d)))
    if not days:
        return None
    for d in reversed(days):
        if os.path.isfile(os.path.join(MM, d, "visits_daily_"
                                             "2026-07-02_2026-10-01.json")):
            return os.path.join(MM, d)
    return os.path.join(MM, days[-1])


def read(day, prefix):
    """Прочитать разобранный вид отчёта по началу имени файла."""
    if not day or not os.path.isdir(day):
        return None
    for f in sorted(os.listdir(day)):
        if f.startswith(prefix) and f.endswith(".json"):
            return json.load(open(os.path.join(day, f), encoding="utf-8"))
    return None


def pct(part, whole):
    return round(100.0 * part / whole, 1) if whole else 0.0


def build():
    """Собрать факты Метрики.

    Если ручных выгрузок нет, возвращается пусто с пометкой. Отчёт при
    этом строится: отсутствие блока о трафике не повод не отдавать
    отчёт по Вебмастеру.
    """
    day = newest()
    out = {"present": bool(day), "day": os.path.basename(day) if day else None}
    if not day:
        out["reason"] = ("нет разобранных ручных выгрузок, запусти "
                         "metrika_manual.py")
        return out

    v = read(day, "visits_daily")
    if not v:
        out["reason"] = "в разборе нет посещаемости"
        return out

    total = v["totals"]
    rows = v["rows"]
    D = "Интервал дат визита"
    out["period"] = v["period"]
    out["visits"] = int(total["visits"])
    out["visitors"] = int(total["visitors"])
    out["views"] = int(total["views"])
    out["bounce_rate"] = round(total["bounce_rate"] or 0, 4)
    out["depth"] = round(total["depth"] or 0, 2)
    out["time_on_site"] = int(total["time_on_site"] or 0)
    out["new_visitors_share"] = round(total["new_visitors_share"] or 0, 4)

    # Проверка глубины: просмотры делённые на визиты должно совпасть.
    calc_depth = out["views"] / out["visits"] if out["visits"] else 0
    out["depth_recomputed"] = round(calc_depth, 2)
    out["depth_agrees"] = abs(calc_depth - out["depth"]) < 0.01

    # Повторные появления честно считаются из разницы, а не из суммы.
    sum_daily_visitors = sum(r["visitors"] or 0 for r in rows)
    out["visitor_days"] = sum_daily_visitors
    out["repeat_appearances"] = sum_daily_visitors - out["visitors"]
    out["visits_per_visitor"] = (round(out["visits"] / out["visitors"], 2)
                                 if out["visitors"] else 0)

    # Новые посетители по дням сходятся с уникальными, а не с суммой.
    new_days = sum((r["new_visitors_share"] or 0) * (r["visitors"] or 0)
                   for r in rows)
    out["new_visitors_derived"] = round(new_days)
    out["new_share_recomputed"] = (round(new_days / out["visitors"], 4)
                                   if out["visitors"] else 0)
    out["new_share_agrees"] = (abs(out["new_share_recomputed"]
                                   - out["new_visitors_share"]) < 0.02)

    # Помесячно. Главное в этом срезе: визиты растут, просмотры падают.
    months = {}
    for r in rows:
        key = str(r.get(D, ""))[:7]
        a = months.setdefault(key, {"days": 0, "visits": 0, "views": 0,
                                    "visitors": 0})
        a["days"] += 1
        a["visits"] += r["visits"] or 0
        a["views"] += r["views"] or 0
        a["visitors"] += r["visitors"] or 0
    out["months"] = []
    for key in sorted(months):
        a = months[key]
        a["depth"] = (round(a["views"] / a["visits"], 2)
                      if a["visits"] else 0)
        a["visits_share"] = pct(a["visits"], out["visits"])
        out["months"].append(dict(key=key, **a))
    if len(out["months"]) >= 2:
        # Сравниваются только полные месяцы. Крайний месяц может
        # оказаться неполным: срез заканчивается 1 октября, значит в
        # нём один день и пять визитов. Сравнивать июль с этим даёт
        # минус сто процентов, цифру верную и бесполезную.
        full = [m for m in out["months"] if m["days"] >= 28]
        out["partial_months"] = [m["key"] for m in out["months"]
                                 if m["days"] < 28]
        if len(full) >= 2:
            first, last = full[0], full[-1]
            out["growth"] = {
                "from": first["key"], "to": last["key"],
                "visits_change": pct(last["visits"] - first["visits"],
                                     first["visits"]),
                "views_change": pct(last["views"] - first["views"],
                                    first["views"]),
                "depth_change": pct(round(last["depth"] - first["depth"], 2),
                                    first["depth"]),
            }

    # Источники: крупные площадки отдельно от общей доли.
    s = read(day, "sources")
    if s:
        out["sources"] = []
        for r in sorted(s["rows"], key=lambda x: -(x["visits"] or 0)):
            name = (r.get("Источник трафика") or "").strip()
            det = (r.get("Источник трафика (детально)") or "").strip()
            v2 = r["visits"] or 0
            if v2 <= 0:
                continue
            out["sources"].append({
                "type": name, "detail": det, "visits": int(v2),
                "share": pct(v2, out["visits"]),
                "bounce_rate": (round(r["bounce_rate"], 4)
                                if r.get("bounce_rate") is not None else None),
            })

    # География: Ижевск и Удмуртия, плюс города с заметной долей.
    g = read(day, "geo")
    if g:
        izh = sum(r["visits"] or 0 for r in g["rows"]
                  if "ижевск" in (r.get("Город") or "").lower())
        udm = sum(r["visits"] or 0 for r in g["rows"]
                  if "удмурт" in (r.get("Область") or "").lower())
        cities = {}
        for r in g["rows"]:
            c = (r.get("Город") or "").strip()
            cities[c] = cities.get(c, 0) + (r["visits"] or 0)
        out["geo"] = {
            "izhevsk": int(izh), "izhevsk_share": pct(izh, out["visits"]),
            "udmurtia": int(udm), "udmurtia_share": pct(udm, out["visits"]),
            "top": [{"city": c, "visits": int(n),
                     "share": pct(n, out["visits"])}
                    for c, n in sorted(cities.items(), key=lambda x: -x[1])
                    if n > 0][:12],
        }

    # Устройства.
    d = read(day, "devices")
    if d:
        types = {}
        for r in d["rows"]:
            name = (r.get("Тип устройства") or "").strip()
            types[name] = types.get(name, 0) + (r["visits"] or 0)
        out["devices"] = [{"type": t, "visits": int(n),
                           "share": pct(n, out["visits"])}
                          for t, n in sorted(types.items(),
                                             key=lambda x: -x[1])]

    # Глубина: доля визитов с одной страницей.
    dp = read(day, "depth")
    if dp:
        one = sum(r["visits"] or 0 for r in dp["rows"]
                  if str(r.get("Глубина просмотра", "")).strip() == "1")
        out["depth_one"] = int(one)
        out["depth_one_share"] = pct(one, out["visits"])
        out["depth_buckets"] = [
            {"bucket": str(r.get("Глубина просмотра", "-")),
             "visits": int(r["visits"] or 0),
             "share": pct(r["visits"] or 0, out["visits"])}
            for r in dp["rows"]]

    # Страницы входа: отдельно главная, отдельно служебные адреса.
    e = read(day, "entry_pages")
    if e:
        home = 0
        back = 0
        test = 0
        plain_http = 0
        http_live = 0
        top = []
        for r in e["rows"]:
            url = (r.get("Страница входа") or "").strip()
            v2 = r["visits"] or 0
            if not v2:
                continue
            if url.rstrip("/") == "https://цифра18.рф":
                home += v2
            if "back_url_admin" in url:
                back += v2
            if "beget.tech" in url:
                test += v2
            if url.startswith("http://"):
                plain_http += v2
                # http на тестовом домене это следствие того же, что
                # сам тестовый домен, и отдельно его считать значит
                # удваивать одну проблему в отчёте
                if "beget.tech" not in url:
                    http_live += v2
            top.append({"url": url, "visits": int(v2),
                        "share": pct(v2, out["visits"])})
        out["entry_pages"] = {
            "home": int(home), "home_share": pct(home, out["visits"]),
            "admin_urls": int(back),
            "admin_share": pct(back, out["visits"]),
            "test_domain": int(test),
            "test_share": pct(test, out["visits"]),
            "plain_http": int(plain_http),
            "plain_http_share": pct(plain_http, out["visits"]),
            "http_live": int(http_live),
            "http_live_share": pct(http_live, out["visits"]),
            "top": sorted(top, key=lambda x: -x["visits"])[:12],
        }

    # Цели.
    gl = read(day, "goals")
    if gl:
        t = gl["totals"]
        out["goals"] = {
            "hits": int(t.get("goal_hits") or 0),
            "target_visits": int(t.get("target_visits") or 0),
            "target_visitors": int(t.get("target_visitors") or 0),
            "conversion": round((t.get("conversion") or 0) * 100, 2),
            "days_hit": len(gl["rows"]),
            "days_total": out["period"]["days"] if out.get("period") else 0,
            "bounce_rate": t.get("bounce_rate"),
            "depth": t.get("depth"),
            "time_on_site": t.get("time_on_site"),
        }

    # Роботы.
    rb = read(day, "robots")
    if rb:
        out["robots"] = [
            {"name": (r.get("Робот") or "-").strip(), "hits": int(r["visits"])}
            for r in sorted(rb["rows"], key=lambda x: -(x["visits"] or 0))]

    # Возраст: доля визитов, где возраст известен.
    ag = read(day, "ages")
    if ag:
        known = sum(r.get("visits") or 0 for r in ag["rows"])
        out["ages"] = {
            "known_visits": int(known),
            "known_share": pct(known, out["visits"]),
            "buckets": [{"age": (r.get("Возраст") or "-").strip(),
                         "visits": int(r.get("visits") or 0),
                         "share": pct(r.get("visits") or 0, known)}
                        for r in sorted(ag["rows"],
                                        key=lambda x: -(x.get("visits") or 0))],
        }

    # Файлы, отложенные человеком, и то, что не разобралось.
    idx = read(day, "_index")
    if idx:
        out["held"] = idx.get("files_held") or []
        out["rejected"] = idx.get("files_rejected") or []
    return out


def main():
    f = build()
    if not f["present"]:
        print("ФАКТЫ МЕТРИКИ")
        print("  НЕТ: %s" % f.get("reason"))
        return 1
    print("ФАКТЫ МЕТРИКИ")
    print("  период           с %s по %s, дней %d"
          % (f["period"]["from"], f["period"]["to"], f["period"]["days"]))
    print("  визиты           %d" % f["visits"])
    print("  посетители       %d уникальных, %d появлений по дням"
          % (f["visitors"], f["visitor_days"]))
    print("  просмотры        %d" % f["views"])
    print("  глубина          %.2f, пересчитано %.2f, %s"
          % (f["depth"], f["depth_recomputed"],
             "совпало" if f["depth_agrees"] else "НЕ СОВПАЛО"))
    print("  отказы           %.1f процента" % (100 * f["bounce_rate"]))
    print("  время на сайте   %d мин %02d с"
          % (f["time_on_site"] // 60, f["time_on_site"] % 60))
    print("  доля новых       %.1f процента, выведено %.0f из %d, %s"
          % (100 * f["new_visitors_share"], f["new_visitors_derived"],
             f["visitors"],
             "совпало" if f["new_share_agrees"] else "НЕ СОВПАЛО"))
    print("  визитов на       %.2f" % f["visits_per_visitor"])
    print()
    print("  ПОМЕСЯЧНО")
    for m in f["months"]:
        print("    %s  визиты %5d (%4.1f%%), просмотры %6d, глубина %.2f"
              % (m["key"], m["visits"], m["visits_share"], m["views"],
                 m["depth"]))
    if f.get("growth"):
        g = f["growth"]
        print()
        print("  ДИНАМИКА %s к %s" % (g["from"], g["to"]))
        print("    визиты   %+.0f процентов" % g["visits_change"])
        print("    просмотры %+.0f процентов" % g["views_change"])
        print("    глубина   %+.0f процентов" % g["depth_change"])
    print()
    ep = f.get("entry_pages") or {}
    print("  ТЕХНИЧЕСКИЕ НАХОДКИ ПО ВХОДНЫМ СТРАНИЦАМ")
    print("    главная                %d визитов, %.1f процента"
          % (ep.get("home", 0), ep.get("home_share", 0)))
    print("    тестовый домен         %d визитов, %.1f процента"
          % (ep.get("test_domain", 0), ep.get("test_share", 0)))
    print("    служебные адреса       %d визитов, %.1f процента"
          % (ep.get("admin_urls", 0), ep.get("admin_share", 0)))
    print("    пришли по http, живой  %d визитов, %.1f процента"
          % (ep.get("http_live", 0), ep.get("http_live_share", 0)))
    return 0


if __name__ == "__main__":
    sys.exit(main())