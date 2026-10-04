#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Общий генератор config.json для лендинга по категории каталога.

Зачем он общий. Первая версия делала лендинги двумя почти одинаковыми
скриптами, `build_calendar_config.py` и `build_merch_config.py`, и каждый
раз логику отбора позиций, чистки названий и подстановки локальных фото
приходилось копировать. Копия разъехалась сразу: в мерче появился
фильтр страницы-раздела, в календарях его не было, и в лендинг попадала
карточка «Печать на ручках» вместо ручки. Общий модуль убирает класс
ошибок «забыли правило в одном из двух мест».

ЧТО ВЗЯТО ОТКАТАЛЬНО. Модуль не выбирает, какие категории делать
лендингами и в каком порядке. Это решение зафиксировано в
`landings/category_specs.json` вместе с текстами, и сделано оно по
посещаемости из выгрузки Метрики, а не по размеру раздела.

ЧТО МОДУЛЬ НЕ ДЕЛАЕТ. Не публикует цены. Не придумывает характеристики.
Факты берутся из названий позиций в каталоге, и в `sources.rules`
записывается, что именно откуда. Если утверждение нельзя подтвердить
выкачкой или письменным ответом заказчика, оно не попадает в текст.

Запуск из корня проекта:
  python landings/_scrape/build_category_config.py shirokoformatnaya-i-interyer
  python landings/_scrape/build_category_config.py --list
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from plural import plural  # согласование числительных

CATALOG = ROOT / "out" / "catalog.json"
SPECS = ROOT / "category_specs.json"
LANDINGS = ROOT.parent

BASE = "https://xn--18-6kc5a3bxam.xn--p1ai"
SLICE_DATE = "2026-10-04"

# Страницы каталога по query-URL вида detail.php?ID= не товары.
# Они отдают листинг с заголовком «Каталог», фото у них ноль, и в счёт
# позиций попадать не должны. В каталоге их 71, и вместе с настоящими
# товарами они давали неверную цифру «457 позиций».
JUNK_MARKERS = ("detail.php", "index.php", "list.php")


# Аббревиатуры, которые на сайте написаны строчными и должны быть
# прописными в заголовке карточки. Список закрытый: править чужие
# названия по общим правилам означало бы догадки о том, что имелось в
# виду, а здесь только то, что написано буквами.
ACRONYMS = {
    "usb": "USB",
    "qr": "QR",
    "qr-код": "QR-код",
    "sim": "SIM",
    "vip": "VIP",
    "hd": "HD",
    "dvd": "DVD",
    "cd": "CD",
    "3d": "3D",
    "led": "LED",
    "qr-коду": "QR-коду",
}


def slugify(url: str) -> str:
    tail = url.rstrip("/").rsplit("/", 1)[-1]
    return "".join(ch if ch.isalnum() else "-" for ch in tail).strip("-").lower()


def clean_name(raw: str) -> str:
    """Приводит название к виду для карточки.

    Названия с сайта в разном регистре: «КРУЖКА БЕЛАЯ 330 МЛ» и
    «Кружка с логотипом». ВСЕ КАПСЫ на карточке выглядит как крик, а
    перед первым словом ставится большая буква. Внутренние слова не
    трогаются: «из нержавеющей стали» должно остаться строчным.

    Аббревиатуры приводятся в верхний регистр: на сайте есть «Печать на
    usb-устройствах», и строчное usb в заголовке карточки читается как
    небрежность. Список закрытый и короткий: общая нормализация слов
    означала бы правку чужих названий там, где менять нечего.
    """
    s = " ".join(str(raw or "").split()).strip(" ,.;:")
    if not s:
        return s
    if s.isupper():
        s = s.lower().capitalize()
    for low, up in ACRONYMS.items():
        s = re.sub(rf"(?<![A-Za-zА-Яа-яЁё]){low}(?![A-Za-zА-Яа-яЁё])", up, s)
    return s


def is_junk(item: dict) -> bool:
    return any(m in item["url"] for m in JUNK_MARKERS) or item["name"] == "Каталог"



def known_subsections(items: list[dict]) -> set[str]:
    return {i["subsection"] for i in items if i["subsection"]}


def check_subsections(spec: dict, items: list[dict]) -> list[str]:
    """Проверяет ключи подразделов до отбора и объясняет ошибку.

    Зачем. Ключи подразделов переносятся руками из выкачки, а выкачка
    печатается в консоль, где кириллица и длинные строки искажаются. Из
   -за этого в спецификации уже появились несуществующие ключи:
    `do-1.6m` вместо `do-1-6m`, `pechat-na-samokleyaushcheysya-plenke`
    вместо `pechat-na-samokleyashcheysya-plenke`. Молчаливый отбор по
    несуществующему ключу даёт пустую группу, и это выглядит как
    «в разделе нет позиций», то есть как правда о сайте, а не как
    опечатка в спецификации.

    Здесь несуществующий ключ останавливает сборку и печатает ближайшие
    по написанию настоящие, чтобы ключ можно было исправить сразу.
    """
    import difflib
    known = known_subsections(items)
    problems = []
    for gs in spec["groups"]:
        for sub in gs.get("subsections") or []:
            if sub not in known:
                near = difflib.get_close_matches(sub, sorted(known), n=3, cutoff=0.6)
                hint = ("\n        похожее в выкачке: " + ", ".join(near)) if near else ""
                problems.append(f"  группа {gs['id']!r}: нет подраздела {sub!r}{hint}")
        # Лимит меньше числа подразделов означает, что часть подразделов
        # не получит ни одной позиции, даже при отборе по кругу. Раньше
        # это проходило молча, и подраздел выпадал со страницы целиком.
        subs = gs.get("subsections") or []
        limit = gs.get("limit", 3)
        if len(subs) > limit:
            problems.append(
                f"  группа {gs['id']!r}: подразделов {len(subs)}, а limit {limit}. "
                f"Подразделы без позиций: "
                + ", ".join(subs[limit:][:4])
                + (" и ещё" if len(subs) - limit > 4 else ""))
    return problems


def pick_group(items: list[dict], spec: dict, landing_excludes: set[str] | None = None) -> list[dict]:
    """Позиции одной группы по подразделу, без дублей по фотографии.

    Дедупликация обязательна. В «Магнитах виниловых» на сайте десять
    позиций с размерами 5х5, 7х7, 10х15 и так далее, но фотография у них
    одна: это один товар с вариантами. Без проверки в блок попадали две
    карточки с одинаковым снимком под разными именами, и человек видел
    два «разных» магнита, а потом переставал доверять остальному каталогу.

    Порядок отбора: позиции с калькулятором тиражей первыми, потому что
    у них есть цена и человек чаще приходит именно за ними, дальше по
    алфавиту, чтобы выбор был воспроизводимым между прогонами.
    """
    subs = spec.get("subsections") or []
    out = []
    for sub in subs:
        out += [i for i in items
                if i["subsection"] == sub and i.get("photos")]
    out = [i for i in out if not is_junk(i)]

    # Страницы подразделов исключаются на уровне лендинга, а не группы.
    #
    # Раньше excludeNames действовал только в своей группе, и страница
    # подраздела «Кружки, термосы, термостаканы», исключённая из группы
    # «Кружки», тут же всплывала в группе «Термокружки и термобутылки»:
    # фильтр и набор позиций общий, а исключение применялось позже и не
    # везде. На странице появлялась карточка, названная именем раздела.
    excluded = set(spec.get("excludeNames") or []) | (landing_excludes or set())
    if excluded:
        out = [i for i in out if clean_name(i["name"]) not in excluded]

    # Семантическое деление внутри одного подраздела.
    #
    # Зачем. На сайте подраздел «Печать на кружках» один, а на лендинге
    # это кружки, термокружки и бутылки для воды, три группы с разными
    # подписями. Без фильтра все три брали первые позиции подраздела по
    # алфавиту, то есть одни и те же карточки попадали на страницу по
    # два-три раза, а подписи под ними не соответствовали содержимому.
    #
    # `nameIncludes` и `nameExcludes` работают по подстроке, без
    # регулярных выражений: регулярка в JSON-спецификации требует
    # экранирования, а опечатка в ней молча убирает группу с позициями.
    low = lambda t: " ".join(str(t or "").split()).lower()
    inc = spec.get("nameIncludes")
    if inc:
        needles = [low(x) for x in inc]
        out = [i for i in out if any(n in low(i["name"]) for n in needles)]
    exc = spec.get("nameExcludes")
    if exc:
        needles = [low(x) for x in exc]
        out = [i for i in out
               if not any(n in low(i["name"]) for n in needles)]

    # Дедупликация по названию и по фотографии. Обе нужны, и они ловят
    # разное.
    #
    # По названию: каталог перечисляет один товар дважды, если он лежит
    # в двух подразделах. Таких пар в выкачке 15: «Карты пластиковые»
    # дважды, «Лекала, выкройки» дважды, «Постпечатные работы» дважды.
    # Если лендинг накрывает оба подраздела, на странице появляются две
    # одинаковые карточки, и человек думает, что это два разных товара.
    #
    # По фотографии: «Магниты виниловые» это один товар с десятью
    # размерами и одной общей фотографией. Названия у вариантов разные,
    # снимок один.
    seen_name: set[str] = set()
    seen: set[str] = set()
    picked: list[dict] = []

    # Отбор по кругу, а не одним проходом по отсортированному списку.
    #
    # Зачем. Список позиций склеивается из всех подразделов группы и
    # сортируется по алфавиту, а лимит применяется один раз в конце. В
    # группе «Подарочные наборы и игры» два подраздела, десять игр и девять
    # подарков, лимит 3. Игры по алфавиту шли раньше, и девять позиций
    # «Корпоративных подарков» не попали на страницу ни одной, хотя
    # подраздел был честно прописан в спецификации. Выглядело это так,
    # будто подарков в каталоге нет.
    #
    # По кругу каждый подраздел получает свою первую позицию, и только
    # потом лимит распределяется на остальные. Подраздел не может
    # остаться пустым, если позиций в нём есть.
    buckets: dict[str, list[dict]] = {}
    for i in sorted(out, key=lambda x: (0 if x.get("priceTiers") else 1, x["name"])):
        name = clean_name(i["name"])
        photo = i["photos"][0]
        if name in seen_name or photo in seen:
            continue
        seen_name.add(name)
        seen.add(photo)
        buckets.setdefault(i["subsection"], []).append(i)

    limit = spec.get("limit", 3)
    round_no = 0
    while len(picked) < limit:
        added = False
        for sub in subs:
            bucket = buckets.get(sub)
            if not bucket or round_no >= len(bucket):
                continue
            picked.append(bucket[round_no])
            added = True
            if len(picked) >= limit:
                break
        if not added:
            break
        round_no += 1
    return picked


def photo_src(item: dict, web_dir: Path, card_id: str) -> str:
    """Локальная веб-копия, иначе адрес на сайте заказчика.

    Префикс имени файла берётся из card_id, того же, что и в скачивании.
    Раньше он здесь пересчитывался из URL позиции, а скачивание брало из
    id карточки. Как только id переименовывался для уникальности, пути
    расходились: файл лежал на диске под одним именем, а страница
    ссылалась на удалённый адрес. Три источника имени дали три разных
    ответа на один вопрос.

    Расширения перебираются явно: оптимизатор пишет .jpg, а до его
    работы рядом лежит оригинал, у которого расширение как на сайте,
    включая .gif с заглавной буквы.
    """
    url = item["photos"][0]
    from fetch_images import safe_name
    stem = safe_name(url, card_id, 0).rsplit(".", 1)[0]
    for ext in ("jpg", "jpeg", "png", "webp", "gif"):
        local = web_dir / f"{stem}.{ext}"
        if local.exists():
            return f"assets/web/{local.name}"
    return url


def variants_of(items: list[dict], item: dict) -> list[str]:
    """Названия позиций с той же фотографией: варианты одного товара.

    Ими имеют смысл назвать в карточке, иначе человек не поймёт, что
    входит в заказ. У виниловых магнитов это размеры 5х5, 7х7, 10х15 и
    так далее, у одежды иногда цвета.
    """
    photo = item["photos"][0]
    names = []
    for i in items:
        if i["subsection"] != item["subsection"] or is_junk(i):
            continue
        if i.get("photos") and i["photos"][0] == photo:
            names.append(clean_name(i["name"]))
    return names


def fill(value: str, nums: dict[str, int]) -> str:
    """Подставляет в текст числа, посчитанные из выкачки.

    Плейсхолдеры вида {picked}, {subs}, {section}. Пока числа писались
    руками, в бейджах разъехались: у лендинга про визитки стояло «20
    позиций», а в выкачке у трёх подразделов вместе 28. Такое число
    выглядит правдой, и проверить его нечем, поэтому теперь любое
    число в текстах обязано прийти из данных.
    """
    for key, val in nums.items():
        value = value.replace("{" + key + "}", str(val))
    # {word} не считается неподставленным: его подменяет badge() позже,
    # формой, согласованной с посчитанным числом.
    left = [x for x in re.findall(r"\{[a-z_]+\}", value) if x != "{word}"]
    if left:
        raise SystemExit(f"  ! в тексте остались неподставленные числа: {left}")
    return value


def badge(spec_badge: dict, nums: dict[str, int]) -> dict:
    """Собирает бейдж: число из данных плюс слово в нужной форме.

    Зачем отдельная функция. Число в бейдже подставляется в поле value, а
    существительное живёт в поле label, и по умолчанию там стоит форма
    «позиций». Для 12 это верно, для 31 нет: должно быть «31 позиция».
    Раньше форма бралась из текста спецификации и поэтому была неверной
    ровно там, где число оканчивается на 1, то есть чаще всего в первый
    же показ.

    Спецификация задаёт три формы полем word и плейсхолдер {word} в
    подписи. Скрипт подставляет форму по тому числу, которое сам же и
    посчитал, поэтому подпись не может разойтись с числом.
    """
    out = {"value": fill(spec_badge["value"], nums),
           "label": fill(spec_badge["label"], nums)}
    forms = spec_badge.get("word")
    if forms:
        if not isinstance(forms, list) or len(forms) != 3:
            raise SystemExit(f"  ! в бейдже «{out['label']}» поле word должно "
                             f"быть списком из трёх форм, а это {forms!r}")
        # Число берётся из уже подставленного value, если оно числовое,
        # иначе из {subs}: подпись и число обязаны считаться от одного.
        n = nums.get("subs", 0)
        if out["value"].isdigit():
            n = int(out["value"])
        if "{word}" not in out["label"]:
            raise SystemExit(f"  ! в бейдже «{out['label']}» нет плейсхолдера "
                             f"{{word}}, а поле word задано")
        out["label"] = out["label"].replace(
            "{word}", plural(n, forms[0], forms[1], forms[2]))
    return out


def build(spec: dict, items: list[dict]) -> dict:
    slug = spec["slug"]
    landing_dir = LANDINGS / slug
    web_dir = landing_dir / "assets" / "web"

    problems = check_subsections(spec, items)
    if problems:
        raise SystemExit("  ! В спецификации несуществующие подразделы:\n"
                         + "\n".join(problems))

    groups = []
    total = 0
    # id делаются уникальными ДО того, как ищутся фотографии. Порядок
    # важен: префикс имени файла это id карточки, и если переименовать
    # id позже, пути разойдутся. Так и было: карточка переименовывалась в
    # `konverty-1`, а фотография искалась по `konverty`, файл лежал на
    # диске под другим именем, и страница ссылалась на удалённый адрес.
    # Общий для всего лендинга список исключений: объединение excludeNames
    # всех его групп.
    landing_excludes = {n for gs in spec["groups"]
                        for n in (gs.get("excludeNames") or [])}
    picks: list[tuple[dict, dict]] = []
    for gs in spec["groups"]:
        picked = pick_group(items, gs, landing_excludes)
        if not picked:
            raise SystemExit(f"  ! группа {gs['id']}: подходящих позиций нет. "
                             f"Проверь subsections в category_specs.json и выкачку.")
        total += len(picked)
        for i in picked:
            picks.append((gs, i))

    used: dict[str, int] = {}
    ids: list[str] = []
    for _gs, i in picks:
        base = slugify(i["url"])
        if base not in used:
            used[base] = 0
            ids.append(base)
        else:
            used[base] += 1
            ids.append(f"{base}-{used[base]}")

    # Повторов между группами одной страницы быть не должно. Фильтры
    # выше снимают most частый случай, но если две группы заданы без
    # них, одна позиция может попасть в обе. Здесь отбор доводится до
    # конца: уже взятая позиция пропускается, а не показывается дважды.
    used_src: set[str] = set()
    clean_picks: list[tuple[dict, dict]] = []
    for gs, i in picks:
        if i["photos"][0] in used_src:
            continue
        used_src.add(i["photos"][0])
        clean_picks.append((gs, i))
    ids = ids[:len(clean_picks)]
    picks = clean_picks
    total = len(picks)

    for (gs, i), card_id in zip(picks, ids):
        same = variants_of(items, i)
        own = clean_name(i["name"])
        extra = [n for n in same if n != own]
        if extra:
            specs = "Варианты: " + ", ".join(extra[:5])
            if len(extra) > 5:
                specs += f" и ещё {len(extra) - 5}"
        else:
            specs = "Тираж и размер по расчёту"
        g = next((g for g in groups if g["id"] == gs["id"]), None)
        if g is None:
            g = {"id": gs["id"], "title": gs["title"],
                 "intro": gs.get("intro", ""), "items": []}
            groups.append(g)
        g["items"].append({
            "id": card_id,
            # Адрес исходника едет вместе с карточкой. Скачивание
            # берёт его отсюда, а не ищет позицию заново по id: id это
            # последний сегмент URL, он совпадает у 15 позиций, и поиск
            # по словарю оставлял бы по одному товару, из-за чего одна
            # карточка получала чужую фотографию.
            "src": i["photos"][0],
            "name": own,
            "img": photo_src(i, web_dir, card_id),
            "method": gs.get("method", "Нанесение по выбору"),
            "specs": specs,
            # Цена с сайта кладётся в данные, но не публикуется:
            # render.js вырежет поле при showPrices = false.
            **({"priceFrom": i["price"]["raw"], "priceSource": i["url"]}
               if (i.get("price") or {}).get("raw") else {}),
        })

    # Число позиций считается по разделам, указанным в спецификации, а не
    # по взятой подборке. Это единственная цифра, которая попадает на
    # страницу и опирается на выкачку, поэтому она обязана считаться из
    # данных, а не писаться руками.
    #
    # Секций бывает несколько: широкоформатка и интерьер продаются
    # одним оффером, но на сайте это два разных раздела, и сумма должна
    # считаться по обоим. Подпись под цифрой тоже зависит от этого: у
    # одного раздела «в разделе», у двух «в разделах».
    sections = spec["section"]
    if isinstance(sections, str):
        sections = [sections]
    in_section = [i for i in items if i["section"] in sections and not is_junk(i)]
    # Сколько позиций лежит в подразделах этого лендинга, а не во всём
    # разделе сайта. Разница важна: у визиток раздел «Полиграфия»
    # содержит 155 позиций, а берём мы из него подразделы на 28, и
    # назвать 155 на странице про визитки было бы враньём по форме.
    wanted = {s for gs in spec["groups"] for s in (gs.get("subsections") or [])}
    in_subs = [i for i in items
               if i["subsection"] in wanted and not is_junk(i)]
    nums = {
        "picked": 0,      # проставляется после отбора
        "subs": len(in_subs),
        "section": len(in_section),
        "sections": len(in_section),
    }

    config = {
        "landing": {"slug": slug, "title": spec["title"]},
        "business": {
            "name": "Типография Цифра",
            "legalEntity": {
                "fullName": "ИП Данилов Константин Леонидович",
                "inn": "182501416864",
                "ogrn": "307183731200018",
                "policyDate": SLICE_DATE,
                "confirmedBy": "письменное подтверждение заказчика, " + SLICE_DATE,
            },
        },
        "site": {"domain": "xn--18-6kc5a3bxam.xn--p1ai"},
        "meta": {"title": spec["metaTitle"], "description": spec["metaDescription"]},
        "contact": {
            "phoneDisplay": "+7 (3412) 32-32-41",
            "phoneTel": "+73412323241",
            "phone2Display": "+7 (965) 842-32-41",
            "phone2Tel": "+79658423241",
            "email": "izhcifra@yandex.ru",
            "address": "426069, Удмуртская Респ., г. Ижевск, ул. 7-я Подлесная, д. 34",
            "mapLat": "56.869771",
            "mapLon": "53.189062",
            "mapImage": "assets/web/map.png",
        },
        "analytics": {"yandexMetrikaId": "50863157"},
        "hero": {
            "eyebrow": spec["eyebrow"],
            "h1": spec["h1"],
            "lead": spec["lead"],
            "photo": "",
            "photoAlt": "",
        },
        "heroStats": [
            {"value": str(len(groups)),
             "label": plural(len(groups), "группа товаров", "группы товаров",
                             "групп товаров") + " на странице"},
            {"value": str(total),
             "label": plural(total, "позиция", "позиции", "позиций")
             + " в блоке на странице"},
            {"value": "РФ", "label": "доставка СДЭК"},
        ],
        "usp": spec["usp"],
        "methods": spec["methods"],
        "process": spec["process"],
        "trustBadges": [badge(b, nums) for b in spec["trustBadges"]],
        "faq": spec["faq"],
        "contactChannels": [
            {"label": "WhatsApp", "url": "https://wa.me/79658423241"},
            {"label": "VK", "url": "https://vk.com/cifraprint18"},
            {"label": "MAX", "url": "https://max.ru/id182501416864_bot"},
        ],
        "catalog": {
            "showPrices": False,
            "groups": groups,
            "quizCommonFields": {
                "layoutOptions": [
                    {"value": "ready", "label": "Есть готовый макет"},
                    {"value": "need_design", "label": "Макета нет, нужна разработка"},
                    {"value": "discuss", "label": "Обсудить требования"},
                ],
                "deadlineOptions": [
                    {"value": "standard", "label": "Стандартный срок"},
                    {"value": "urgent", "label": "Нужно срочно"},
                ],
                "deliveryOptions": [
                    {"value": "izh", "label": "Ижевск, заберу сам"},
                    {"value": "russia", "label": "Другой город, доставка СДЭК"},
                ],
            },
        },
        "backend": {"mailTo": "izhcifra@yandex.ru"},
        "sources": {
            "sliceDate": SLICE_DATE,
            "catalogFile": "landings/_scrape/out/catalog.json",
            "demand": spec["demand"],
            "rules": spec["rules"],
            "customerProvided": {
                "map": {"claim": "Координаты из ссылки на карту в футере сайта, "
                                 "56.869771, 53.189062",
                        "verifiedOnSite": True},
                "delivery": {"claim": "Доставка по всей России СДЭК",
                             "givenBy": "заказчик устно, " + SLICE_DATE,
                             "verifiedOnSite": False,
                             "check": "На сайте цифра18.рф «СДЭК» не найдено ни "
                                      "разу. Подтвердить письменно вместе с "
                                      "тарифом и сроками."},
            },
            "knownAnomalies": spec.get("anomalies", []),
        },
    }

    nums["picked"] = total

    # Фото для первого экрана берётся из уже скачанных локальных файлов.
    # Пустое поле хуже серой заглушки, а заглушка с текстом «фото
    # уточняется» на первом экране продаёт хуже, чем отсутствие фото.
    for g in groups:
        for it in g["items"]:
            if it["img"].startswith("assets/"):
                config["hero"]["photo"] = it["img"]
                config["hero"]["photoAlt"] = it["name"]
                break
        if config["hero"]["photo"]:
            break
    return config


def main() -> int:
    ap = argparse.ArgumentParser(description="Собрать config.json лендинга по категории.")
    ap.add_argument("slug", nargs="?", help="ключ из category_specs.json")
    ap.add_argument("--list", action="store_true", help="показать все ключи")
    args = ap.parse_args()

    specs = json.loads(SPECS.read_text(encoding="utf-8"))
    if args.list:
        print(f"{'ключ':<28} {'раздел':<26} {'групп':>5} {'позиций':>8}")
        for key, s in specs["landings"].items():
            n = sum(g.get("limit", 3) for g in s["groups"])
            sec = s["section"]
            sec = sec if isinstance(sec, str) else " + ".join(sec)
            print(f"{key:<28} {sec:<26} {len(s['groups']):>5} {n:>8}")
        return 0

    if not args.slug:
        ap.error("нужен ключ или --list")
    if args.slug not in specs["landings"]:
        print("Нет такого ключа. Список: --list")
        return 1
    if not CATALOG.exists():
        print("Нет out/catalog.json. Сначала fetch_catalog.py --parse-only")
        return 1

    spec = specs["landings"][args.slug]
    items = json.loads(CATALOG.read_text(encoding="utf-8"))
    config = build(spec, items)

    target = LANDINGS / spec["slug"] / "config.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")

    total = sum(len(g["items"]) for g in config["catalog"]["groups"])
    sec = spec["section"]
    sec = [sec] if isinstance(sec, str) else sec
    in_section = sum(1 for i in items if i["section"] in sec and not is_junk(i))
    print(f"OK: {target}")
    print(f"  разделы на странице: {len(config['catalog']['groups'])} | "
          f"позиций: {total} из {in_section} в разделах {', '.join(sec)}")
    for g in config["catalog"]["groups"]:
        print(f"    {g['title']}: {len(g['items'])}")
    print(f"  hero-фото: {config['hero']['photo'] or 'НЕТ, положить в assets/web'}")
    print(f"  showPrices: {config['catalog']['showPrices']}")
    remote = [it["id"] for g in config["catalog"]["groups"] for it in g["items"]
              if not it["img"].startswith("assets/")]
    if remote:
        print(f"  ! удалённых фото, нужен fetch_images.py: {len(remote)}")
        for r in remote[:5]:
            print(f"      {r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())