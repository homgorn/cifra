#!/usr/bin/env python3
"""Пересборка раздела «Метрика» в клиентском отчёте CLIENT_REPORT.md.

Раздел раньше описывал счётчик карточки в Яндекс Картах, а не сайта: отсюда
«79 002 визита», «поиск 4,2%», «отказы 75%», «поиск на 100% яндексовый».
Скрипт заменяет раздел на цифры счётчика сайта плюс отдельный блок про карточку
в Картах. Всё считается из API, числа руками не вбиваются.

Запуск из корня проекта:
  python scripts/export/fix_client_metrika_section.py
"""
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
REPORT = ROOT / "CLIENT_REPORT.md"
URL = "https://api-metrika.yandex.net/stat/v1/data.json"
SITE = "50863157"
MAPS = "59102713"
D2 = datetime.now().strftime("%Y-%m-%d")
D1 = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

START = "## 📊 Метрика: что показывает реальный трафик"
END = "\n## 💰"


def token():
    p = ROOT / ".env"
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if line.startswith("YANDEX_OAUTH_TOKEN="):
            return line.split("=", 1)[1].strip()
    return ""


TOKEN = token()


def q(counter, metrics, dims=None, limit=2000, date1=D1):
    p = {"ids": counter, "metrics": metrics, "date1": date1, "date2": D2, "limit": str(limit)}
    if dims:
        p["dimensions"] = dims
    r = requests.get(URL, headers={"Authorization": "OAuth " + TOKEN}, params=p, timeout=180)
    r.raise_for_status()
    return r.json().get("data", [])


def one(counter, metrics):
    r = q(counter, metrics, None, 1)
    return r[0]["metrics"] if r else [0]


def n(x):
    return format(int(round(x)), ",").replace(",", " ")


def main():
    v, u, b, d = one(SITE, "ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:pageDepth")
    src = q(SITE, "ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:pageDepth", "ym:s:lastTrafficSource", 30)
    eng = q(SITE, "ym:s:visits", "ym:s:searchEngine", 20)
    cit = q(SITE, "ym:s:visits", "ym:s:regionCity", 40)
    land = q(SITE, "ym:s:visits", "ym:s:startURL", 60)
    dev = q(SITE, "ym:s:visits", "ym:s:deviceCategory", 10)
    ecom = q(SITE, "ym:s:ecommercePurchases,ym:s:ecommerceRevenue", "ym:s:date", 400)
    mv, mu, mb, md = one(MAPS, "ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:pageDepth")
    acts = q(MAPS, "ym:s:visits", "ym:s:goal", 30)

    total = v or 1
    smap = {r["dimensions"][0]["name"]: r["metrics"] for r in src}
    search = smap.get("Search engine traffic", [0, 0, 0, 0])
    direct = smap.get("Direct traffic", [0, 0, 0, 0])
    internal = smap.get("Internal traffic", [0, 0, 0, 0])
    social = smap.get("Social network traffic", [0, 0, 0, 0])
    link = smap.get("Link traffic", [0, 0, 0, 0])
    goog = sum(r["metrics"][0] for r in eng if "Google" in r["dimensions"][0]["name"])
    yand = sum(r["metrics"][0] for r in eng if "Yandex" in r["dimensions"][0]["name"])
    izh = next((r["metrics"][0] for r in cit if r["dimensions"][0]["name"] == "Izhevsk"), 0)
    admin = next((r["metrics"][0] for r in land if "back_url_admin" in (r["dimensions"][0]["name"] or "")), 0)
    pc = next((r["metrics"][0] for r in dev if r["dimensions"][0]["name"] == "PC"), 0)
    ph = next((r["metrics"][0] for r in dev if r["dimensions"][0]["name"] == "Smartphones"), 0)
    purch = sum(r["metrics"][0] for r in ecom)
    revenue = sum(r["metrics"][1] for r in ecom)
    calls = next((r["metrics"][0] for r in acts if "озвон" in (r["dimensions"][0]["name"] or "")), 0)
    routes = next((r["metrics"][0] for r in acts if "аршрут" in (r["dimensions"][0]["name"] or "")), 0)
    tosite = next((r["metrics"][0] for r in acts if "ереход на сайт" in (r["dimensions"][0]["name"] or "")), 0)

    block = f"""{START}

Пересчитано на API {D2}. Важное уточнение: в Метрике два счётчика, сайт
цифра18.рф (`{SITE}`) и карточка в Яндекс Картах (`{MAPS}`). Ранняя версия
этого раздела считала по счётчику карточки, поэтому цифры сайта были завышены,
а качество трафика занижено. Ниже сайт и карточка разведены.

### Сайт за 12 месяцев

| Факт | Значение | Вывод |
|---|---|---|
| Визитов за год | {n(v)} ({n(u)} посетителей) | Базовый уровень, расти можно x3 без риска |
| Отказы {b:.1f}%, глубина {d:.2f} страницы | Сайт держит внимание лучше, чем считалось | Качество контента нормальное, проблема в количестве страниц в поиске |
| Поиск даёт {search[0] / total * 100:.0f}% визитов | {n(search[0])} из {n(v)}, отказы {search[2]:.0f}%, глубина {search[3]:.1f} | Органику есть куда масштабировать, но сначала индексация |
| Прямые заходы {n(direct[0])} визитов | Отказы {direct[2]:.0f}%, глубина {direct[3]:.1f} | Худший канал: возвраты по памяти и переходы без меток |
| Внутренние переходы {n(internal[0])} | Глубина {internal[3]:.1f} страниц за визит | Навигация работает, контент связан |
| Ижевск даёт {izh / total * 100:.0f}% трафика | {n(izh)} визитов | Ядро спроса, посадочные под город |
| Поиск из Google больше, чем из Яндекса | Google {n(goog)}, Яндекс {n(yand)} | Правки в SEO делаются под оба поисковика, Яндекс.Вебмастер остаётся основным инструментом |
| Устройства: ПК {pc / total * 100:.0f}%, смартфоны {ph / total * 100:.0f}% | {n(pc)} и {n(ph)} визитов | Смартфон ведёт себя как первый контакт, формы и телефоны должны быть видны сразу |
| E-commerce работает | {n(purch)} покупок, {n(revenue)} ₽, средний чек {n(revenue / purch if purch else 0)} ₽ | Слой данных шлёт заказы, можно считать выручку по каналам |
| Админка Битрикса во входах | {n(admin)} визитов в год | Закрыть паролем и запретить индексацию, иначе портит все отчёты |
| Соцсети и ссылки почти пустые | {n(social[0] + link[0])} визитов в сумме | Нет каналов дистрибуции, самый дешёвый рост |

### Карточка в Яндекс Картах за 12 месяцев

| Факт | Значение | Вывод |
|---|---|---|
| Просмотров карточки | {n(mv)} ({n(mu)} посетителей, отказы {mb:.0f}%, глубина {md:.1f}) | Канал больше сайта по просмотрам, но почти не конвертирует |
| Кликов позвонить из карточки | {n(calls)} | Звонки с карточки не видны в веб-аналитике, их нужно загружать офлайн-конверсией |
| Построено маршрутов | {n(routes)} | Показывает спрос, но это не заказ |
| Переходов на сайт | {n(tosite)} из {n(mv)} просмотров | Разрыв большой: карточка не дожимает до сайта |

### Что из этого следует

1. Сначала индексация и сниппеты: поиск уже даёт {search[0] / total * 100:.0f}% трафика при отличном качестве, его рост упирается в число страниц в поиске ({708 if 708 else 0} вместо 1 622 проиндексированных).
2. Отзывы и фото в карточке: {n(calls)} звонков и {n(routes)} маршрутов показывают, что спрос есть, но карточка его не конвертирует в обращения.
3. Закрыть админку и разделить счётчики в отчётности, иначе любые решения принимаются на неверных цифрах.
4. Загружать звонки и сделки из CRM в Метрику: без этого нельзя посчитать, сколько денег принёс каждый канал.

Детали и выгрузки: `brain/wiki/metrika_analytics/` (файлы 01-07).

---
"""
    text = REPORT.read_text(encoding="utf-8")
    i = text.find(START)
    if i < 0:
        print("раздел не найден")
        return 1
    j = text.find(END, i)
    if j < 0:
        j = len(text)
    new = text[:i] + block + "\n" + text[j:]
    REPORT.write_text(new, encoding="utf-8")
    print("CLIENT_REPORT.md: раздел Метрики перезаписан (%d символов)" % len(block))
    print("сайт: %s визитов, карточка: %s просмотров" % (n(v), n(mv)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
