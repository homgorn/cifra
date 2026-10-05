#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Проверка собранного лендинга. Гейты, а не советы.

Зачем скрипт, если есть глаза: часть проверок человек не делает физически.
Например «нет остаточных плейсхолдеров {{ }}» — их надо искать по всем шести
файлам вывода, а не только по index.html; а «все id, которые ищет JS,
существуют в HTML» — это пересечение двух наборов, которое считается, но не
проверяется взглядом. Глаза ловят «страница выглядит нормально», и они ловут
не всё: восемь h1 на странице тоже выглядят нормально.

Каждый гейт ловит свой класс ошибок, и ни один не заменяет остальные.
Ненулевой код возврата означает «лендинг нельзя публиковать».

Запуск из корня проекта:
  python landings/validate_landing.py landings/kvartalnyy-kalendar-2027
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

OK = "\u2713"
FAIL = "\u2717"

results: list[tuple[str, bool, str]] = []


def gate(name: str, passed: bool, detail: str = "") -> None:
    results.append((name, passed, detail))


def metrika_counter() -> str:
    """Счётчик Метрика из .env в корне проекта.

    Файл опциональный: без него гейт 4 честно падает с «НЕТ в .env»,
    а не подставляет значение по умолчанию. Подстановка «на всякий
    случай» здесь была бы тем же плейсхолдером, только замаскированным.
    """
    env = Path(__file__).resolve().parent.parent / ".env"
    if not env.is_file():
        return ""
    for line in env.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.strip() == "METRIKA_COUNTER_ID":
            return value.strip().strip("\"'")
    return ""


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python landings/validate_landing.py <папка лендинга>")
        return 2
    landing = Path(sys.argv[1])
    dist = landing / "dist"
    if not dist.is_dir():
        print(f"Нет папки {dist}. Сначала node render.js config.json dist/")
        return 2

    html = (dist / "index.html").read_text(encoding="utf-8")
    script = (dist / "script.js").read_text(encoding="utf-8")
    catalog_js = (dist / "catalog.js").read_text(encoding="utf-8")
    styles = (dist / "styles.css").read_text(encoding="utf-8")
    privacy = (dist / "privacy.html").read_text(encoding="utf-8")
    server = (dist / "backend" / "server.js").read_text(encoding="utf-8")

    # ---- 1. Синтаксис JS. node --check на шаблоне не годится: в шаблоне
    # лежит плейсхолдер {{YMETRIKA_ID}}, он невалиден как JS. Проверяем
    # ТОЛЬКО собранные файлы, где подстановка уже произошла. ----
    bad = []
    for name in ("script.js", "catalog.js", "backend/server.js"):
        r = subprocess.run(["node", "--check", str(dist / name)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            bad.append(f"{name}: {r.stderr.strip().splitlines()[:1]}")
    gate("1. node --check на собранных JS", not bad,
         "; ".join(bad) if bad else "script.js, catalog.js, backend/server.js")

    # ---- 2. Ни одного незамещённого плейсхолдера в выводе ----
    outs = {"index.html": html, "script.js": script, "catalog.js": catalog_js,
            "styles.css": styles, "privacy.html": privacy,
            "backend/server.js": server}
    residue = [f"{n} x{len(re.findall(r'{{[A-Z_]+}}', t))}"
               for n, t in outs.items() if re.search(r"{{[A-Z_]+}}", t)]
    gate("2. Нет остаточных плейсхолдеров {{...}}", not residue,
         ", ".join(residue) if residue else "чисто во всех 6 файлах")

    # ---- 3. Ровно один h1 ----
    h1 = len(re.findall(r"<h1\b", html))
    gate("3. Ровно один h1", h1 == 1, f"найдено {h1}")

    # ---- 4. Счётчик Метрики: он и в HTML, и в целях ----
    # Значение берётся из .env, а не зашито сюда. Предыдущая версия
    # сравнивала с литералом прямо в коде, и гейт с названием «из .env»
    # на самом деле ничего из .env не читал. Значит, значение жило в двух
    # местах одновременно, .env и литерал здесь, и расхождение замечал
    # только человек: гейт проходил по старому литералу и не защищал от
    # того, что реально уедет в сборку. Теперь источник один.
    counter = metrika_counter()
    init_ids = re.findall(r'ym\((\d+),\s*"init"', html)
    goal_ids = re.findall(r"ym\((\d+),\s*'reachGoal'", script)
    # Заглушка это не «любое число», а повторяющиеся цифры: 1111111,
    # 0000000, 1234567. Такое значение .env пропустить может, и гейт
    # обязан это ловить, иначе проверка не значит ничего.
    placeholder = bool(counter) and re.fullmatch(r"(\d)\1{3,}", counter) is not None
    gate("4. Счётчик Метрики из .env, не заглушка",
         bool(counter) and not placeholder
         and init_ids == [counter] and set(goal_ids) == {counter},
         f"ожидался {counter or 'НЕТ в .env'}, "
         f"init={init_ids or 'нет'}, reachGoal={sorted(set(goal_ids)) or 'нет'}")

    # ---- 5. Цены ----
    cfg = json.loads((landing / "config.json").read_text(encoding="utf-8"))
    show = cfg.get("catalog", {}).get("showPrices") is True
    rub = sum(t.count("\u20bd") for t in (html, catalog_js))
    tags = len(re.findall(r"price-tag", html + catalog_js))
    if show:
        gate("5. Цены включены и присутствуют", rub > 0, f"₽: {rub}, price-tag: {tags}")
    else:
        gate("5. Цены выключены и не попали в вывод", rub == 0 and tags == 0,
             f"₽: {rub}, price-tag: {tags}")

    # ---- 6. Перекрёстная проверка id: всё, что ищет JS, есть в HTML ----
    wanted = sorted(set(re.findall(r"getElementById\('([^']+)'\)", script)))
    missing = [i for i in wanted if f'id="{i}"' not in html]
    gate("6. Все id из JS есть в HTML", not missing,
         f"нет в HTML: {missing}" if missing else f"{len(wanted)} идентификаторов сходятся")

    # ---- 7. Ссылки-anchors: на что ведут кнопки ----
    anchors = sorted(set(re.findall(r'href="#([\w-]+)"', html)))
    broken = [a for a in anchors if f'id="{a}"' not in html]
    gate("7. Якоря кнопок ведут на существующие секции", not broken,
         f"битые: {broken}" if broken else f"{len(anchors)} якорей: {', '.join(anchors)}")

    # ---- 8. Юридический слой: согласие, cookie-баннер, политика, реквизиты ----
    legal = {
        "чекбокс согласия в квизе": 'id="q-consent"' in html and 'required' in html,
        "чекбокс согласия в форме": 'id="f-consent"' in html,
        "cookie-баннер": 'id="cookie-banner"' in html,
        "ссылка на политику": html.count('href="privacy.html"') >= 3,
        "privacy.html отдан": "Политика обработки" in privacy or "персональных данных" in privacy,
        "JSON-LD LocalBusiness": '"LocalBusiness"' in html,
        "JSON-LD FAQPage": '"FAQPage"' in html,
        "реквизиты оператора ПДн": "TODO" not in privacy,
    }
    missing_legal = [k for k, ok in legal.items() if not ok]
    gate("8. Юридический слой на месте", not missing_legal,
         f"не хватает: {missing_legal}" if missing_legal else "все 8 пунктов")

    # ---- 9. Em-dash в текстах, которые читает человек ----
    # Проверяется ТОЛЬКО видимый текст. Комментарии в разметке и код внутри
    # <script>/<style> посетителю не показываются, и их правка бессмысленна:
    # em-dash в служебной части не нарушает правило проекта, которое запрещает
    # его в текстах для клиента. Раньше гейт смотрел на весь файл целиком и
    # therefore ругался на подписи блоков в HTML-комментариях.
    def visible_text(markup: str) -> str:
        out = re.sub(r"<!--.*?-->", " ", markup, flags=re.S)
        out = re.sub(r"<script\b.*?</script>", " ", out, flags=re.S | re.I)
        out = re.sub(r"<style\b.*?</style>", " ", out, flags=re.S | re.I)
        out = re.sub(r"<[^>]+>", " ", out)
        return out

    vis = visible_text(html) + " " + visible_text(privacy)
    # JSON-LD попадает в видимый текст как данные, и это правильно: ответы
    # нейросетей читают именно его, знак там виден пользователю тоже.
    em_vis = vis.count("\u2014")
    em_all = html.count("\u2014") + catalog_js.count("\u2014")
    gate("9. Нет em-dash в текстах для клиента", em_vis == 0,
         f"в видимом тексте {em_vis}, всего в файле {em_all} (комментарии и код не считаются)")

    # ---- 10. Контактные ссылки: телефон и почта не должны быть заглушками ----
    phone = cfg.get("contact", {}).get("phoneTel", "")
    mail = cfg.get("contact", {}).get("email", "")
    gate("10. Контакты заполнены по сайту клиента",
         phone.count("+") == 1 and len(phone) >= 12 and "@" in mail,
         f"тел {phone}, почта {mail}")

    # ---- 10b. Реквизиты оператора ПДн подтверждены, а не скопированы ----
    # Гейт 8 проверяет, что реквизиты вообще есть. Этот проверяет, что они
    # подтверждены: в конфиг вписывается поле confirmedBy с датой. Без
    # него страница формально полна, а по сути наполнена данными из
    # демо-конфига блюпринта, а те выглядят точь-в-точь как настоящие.
    # Глазом это не отличить, значит обязан гейт.
    legal_cfg = cfg.get("business", {}).get("legalEntity") or {}
    confirmed = str(legal_cfg.get("confirmedBy", "")).strip()
    need = ("fullName", "inn", "ogrn")
    gaps = [f for f in need if not str(legal_cfg.get(f, "")).strip()]
    has_confirm = bool(confirmed) and re.search(r"\d{4}-\d{2}-\d{2}", confirmed) is not None
    gate("10b. Реквизиты ИП подтверждены письменно", not gaps and has_confirm,
         f"нет полей: {gaps}" if gaps else
         (f"подтверждено: {confirmed}" if has_confirm else "нет confirmedBy с датой"))

    # ---- 11. Мессенджеры: каждая ссылка должна быть проверенной ----
    # Белый список: какие домены мессенджеров вообще допустимы. Гейт 23
    # проверяет другое: есть ли у канала источник. Список не доказывает,
    # что ссылка рабочая, а источник не доказывает, что домен допустим, и
    # потому нужны оба. Пересечение намеренное: непроштатный канал падает
    # здесь, а непроисследённый допустимый канал падает в гейте 23.
    allowed_prefixes = ("https://wa.me/", "https://vk.com/", "https://max.ru/")
    channels = cfg.get("contactChannels", [])
    ok_ch = bool(channels) and all(
        str(c.get("url", "")).startswith(allowed_prefixes) for c in channels)
    gate("11. Ссылки на мессенджеры из белого списка", ok_ch,
         f"{len(channels)} каналов" if ok_ch else f"каналы: {channels}")

    # ---- 12. Идентификатор лендинга в бэкенде: лиды должны быть различимы ----
    slug = cfg.get("landing", {}).get("slug")
    title = cfg.get("landing", {}).get("title")
    in_title = bool(title) and title in server
    in_slug = bool(slug) and slug in (landing / "config.json").read_text(encoding="utf-8")
    gate("12. Лендинг идентифицируется в лидах", in_title and in_slug,
         f"title в server.js: {in_title}, slug в конфиге: {in_slug}")

    # ---- 13. Ни одной позиции каталога без картинки ----
    groups = cfg.get("catalog", {}).get("groups", [])
    items = [it for g in groups for it in g.get("items", [])]
    no_img = [it.get("id") for it in items if not it.get("img")]
    gate("13. У всех позиций есть фотография", bool(items) and not no_img,
         f"позиций {len(items)}, без фото: {no_img}" if no_img else f"{len(items)} позиций")

    # ---- 14. Локальные картинки существуют на диске ----
    local = sorted({it["img"] for it in items
                    if it.get("img", "").startswith("assets/")}
                   | ({cfg["hero"]["photo"]} if cfg.get("hero", {}).get("photo", "").startswith("assets/") else set()))
    absent = [p for p in local if not (landing / p).exists()]
    gate("14. Локальные фотографии существуют", bool(local) and not absent,
         f"нет файлов: {absent}" if absent else f"{len(local)} файлов на месте")

    # ---- 14c. Карта: картинка есть и скопирована в dist ----
    # Раньше карта вставлялась iframe'ом с Яндекс.Картами, и она не
    # показывалась никогда: yandex.ru отдаёт 301 на yandex.com, а у
    # него X-Frame-Options: DENY. Гейт про iframe молчал, потому что
    # разметка была корректной, а браузер отказывался её показывать.
    # Проверяем то, что видно пользователю: картинка есть на диске,
    # она в dist, и в разметке больше нет iframe с чужим доменом.
    map_img = cfg.get("contact", {}).get("mapImage", "")
    map_ok = False
    if map_img:
        src_ok = (landing / map_img).exists() and (dist / map_img).exists()
        map_ok = src_ok
    iframes = re.findall(r"<iframe[^>]+src=\"([^\"]+)\"", html)
    third_party = [u for u in iframes if "yandex" in u or "google" in u]
    gate("14c. Карта показана, iframe со сторонним доменом убран",
         map_ok and not third_party,
         f"картинка {map_img or 'не задана'}, сторонних iframe: {len(third_party)}")

    # ---- 14b. Те же фото должны быть в СОБРАННОМ dist ----
    # Гейт 14 смотрел в папку лендинга, а страницу обслуживает dist.
    # Рендер копировал туда только html, css и js, поэтому все превью в
    # собранном лендинге были битыми, и гейт этого не замечал: файлы-то
    # существовали, просто не там, откуда их грузит браузер.
    dist_local = [p for p in local if not (dist / p).exists()]
    gate("14b. Фотографии скопированы в dist", bool(local) and not dist_local,
         f"нет в dist: {len(dist_local)} из {len(local)}, пример {dist_local[:2]}" if dist_local
         else f"{len(local)} файлов в dist")

    # ---- 19b. На странице нет повторов между группами ----
    # Повтор внутри группы ловит отбор, а повтор между группами той же
    # страницы никто не ловил. Три группы кружек, термокружек и бутылок
    # брали позиции из одного подраздела сайта, и каждая брала первые: на
    # странице оказывалось три копии одной кружки под тремя разными
    # подписями, а подпись под «Термокружки» могла оказаться обычной
    # кружкой. Гейт 15 проверяет уникальность id, но id у копий разные.
    seen_src: dict[str, str] = {}
    dups: list[str] = []
    for g in cfg.get("catalog", {}).get("groups", []):
        for it in g.get("items", []):
            src = it.get("src")
            if not src:
                continue
            if src in seen_src and seen_src[src] != g["id"]:
                dups.append(f'{it.get("id")} есть в «{seen_src[src]}» и «{g["id"]}»')
            seen_src.setdefault(src, g["id"])
    gate("19b. Нет повторов между группами страницы", not dups,
         "; ".join(sorted(set(dups))[:3]) if dups else "повторов нет")

    # ---- 21. Нет тёмного текста на тёмном фоне ----
    # Проверка идёт по собранному CSS, а не по скриншоту. Скриншот
    # показывает дефект, но не объясняет его: в блюпринте общий селектор
    # `p` задавал тёмный цвет, и тёмные блоки, задавая себе белый, всё
    # равно получали тёмные абзацы, потому что правило для `p` сильнее
    # наследования от родителя. Текст про cookie был тёмно-серым на
    # чёрном, и гейт на текст его не видел: буквы верные, нечитаема
    # только краска.
    css_text = ""
    for cand in sorted(dist.glob("*.css")):
        css_text += cand.read_text(encoding="utf-8", errors="replace")
    html_text = (dist / "index.html").read_text(encoding="utf-8", errors="replace")
    js_text = ""
    for cand in sorted(dist.glob("*.js")):
        js_text += cand.read_text(encoding="utf-8", errors="replace")

    def var_value(name: str) -> str:
        m = re.search(rf"--{name}\s*:\s*(#[0-9a-fA-F]{{3,8}})", css_text)
        return m.group(1).lower() if m else ""

    def luminance(color: str) -> float | None:
        m = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{6})", color)
        if not m:
            return None
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    contrast_ok = True
    detail = "контраст в норме"

    # 1. Токены: тёмный фон и тёмный текст не должны совпадать по тону.
    dark_bg = var_value("forest-900")
    dark_ink = var_value("ink")
    if dark_bg and dark_ink:
        lb, li = luminance(dark_bg), luminance(dark_ink)
        if lb is not None and li is not None and abs(lb - li) < 0.12:
            contrast_ok = False
            detail = f"фон {dark_bg} и текст {dark_ink} почти одного тона"

    # 2. Каждый ЖИВОЙ блок с тёмным фоном обязан задавать себе цвет.
    #
    # Живым считается селектор, чей класс или id встречается либо в
    # собранном HTML, либо в скриптах. Проверяются только живые, и это
    # не упрощение: `#quiz-final-summary` создаётся скриптом в финале
    # квиза и в статической разметке не виден, а `.price-tag`
    # вставляется скриптом при заполненной цене, то есть сейчас не
    # вставляется. Поиск только по разметке объявил бы оба мёртвыми и
    # правка в неиспользуемой секции выглядела бы как проверка.
    #
    # Не задавать цвет нельзя: правило для `p` сильнее наследования, и
    # без явного цвета абзац внутри тёмного блока получит цвет из
    # общих правил, то есть тёмный.
    # Комментарии вырезаются до разбора правил. Без этого в сообщение
    # попадал не селектор, а последняя строка комментария над ним:
    # «у .usp убран свой цвет» печаталось как «у /* ===== USP STR
    css_nc = re.sub(r"/\*.*?\*/", "", css_text, flags=re.S)

    dark_rules = []
    for m in re.finditer(r"([^{}]+)\{([^}]*)\}", css_nc):
        body = m.group(2)
        if not re.search(r"background(?:-color)?\s*:\s*(var\(--forest-900\)|#000000)",
                         body):
            continue
        for one in m.group(1).split(","):
            sel = one.strip()
            if re.match(r"^[a-z]+\s*$|^[a-z]+\s+[a-z]+$", sel):
                continue  # теги вроде "section p", не блоки-контейнеры
            dark_rules.append((sel, body))

    def is_live(sel: str) -> bool:
        token = None
        mid = re.search(r"#([\w-]+)", sel)
        if mid:
            token = mid.group(1)
        else:
            mcl = re.search(r"\.([\w-]+)", sel)
            token = mcl.group(1) if mcl else None
        if not token:
            return False
        return (token in html_text) or (token in js_text)

    live_dark, no_color = [], []
    for sel, body in dark_rules:
        if not is_live(sel):
            continue
        live_dark.append(sel)
        if "color" not in body:
            no_color.append(sel)

    if not live_dark:
        # Молчание здесь хуже ошибки: страница без тёмных блоков прошла бы
        # гейт, ни разу не проверив ничего. Значит разбор css сломался.
        contrast_ok = False
        detail = "не найден ни один тёмный блок, проверка не выполнялась"
    elif no_color:
        contrast_ok = False
        detail = ("тёмный фон без своего цвета у " + ", ".join(sorted(no_color)[:3]))
    elif not contrast_ok:
        pass
    else:
        detail = f"живых тёмных блоков {len(live_dark)}, все задают свой цвет"

    # 3. Баннер проверяется отдельно и жёстче остальных: он поверх любой
    # страницы и поверх фотографий, полагаться на один только порядок
    # каскада здесь рискованно.
    m_cb = re.search(r"\.cookie-banner p\{([^}]*)\}", css_text)
    if m_cb and "color" not in m_cb.group(1):
        contrast_ok = False
        detail = "у .cookie-banner p нет явного цвета"

    gate("21. Нет тёмного текста на тёмном фоне", contrast_ok, detail)

    # ---- 22. Диапазоны в текстах не противоречат позициям ----
    # На лендинге с кружками шапка обещала «от 330 до 500 мл», карточка
    # ниже перечисляла 330, 350, 400, 420, 480, 500, 600 и 700 мл, и на
    # странице лежали бутылки на 600 и 700 мл. Два числа стояли рядом и
    # противоречили друг другу. Гейт на текст это не видел: буквы верные.
    #
    # Проверяется НЕ покрытие, а согласованность. Первая версия гейта
    # требовала, чтобы каждое предложение со словами «от N до M» покрывало
    # все позиции, и сразу заругалась на исправленный текст: «Кружки от
    # 330 до 500 мл» верно про кружки, а бутылки на 700 мл упомянуты
    # отдельной фразой. Предложение про подгруппу не обязано покрывать
    # всю страницу, и требовать этого нельзя.
    #
    # Чего гейт НЕ ловит: сужение в одном тексте при широком другом. В
    # шапке «от 330 до 500 мл», когда карточка ниже говорит «до 700 мл», это
    # не ложь о каталоге: страница в целом обещает верный диапазон, шапка
    # просто говорит меньше. Проверка пыталась ловить и это, ложно ругалась
    # на исправленный текст и была переписана. Понятия «здесь обещают
    # больше, чем обещают рядом» не имеют фактического основания: разделы
    # страницы законно описывают разные подмножества.
    #
    # Настоящий дефект был в том, что самое широкое заявленное на странице
    # число не дотягивало до реальных позиций. Поэтому сравнивается самый
    # широкий диапазон по каждой единице со всеми позициями этой единицы.
    unit_re = r"(?:мл|шт|см|мм|м\b|дюйм\w*|размер\w*|вида|вариант\w*|цвет\w*)"
    range_re = re.compile(rf"(\d+)\s*(?:[–—-]|\bдо\b)\s*(\d+)\s*({unit_re})", re.I)

    item_names = " | ".join(
        card.get("name", "")
        for grp in cfg.get("catalog", {}).get("groups", [])
        for card in grp.get("items", []))

    widest: dict[str, tuple[int, int, str]] = {}
    for section in ("hero", "usp", "trustBadges"):
        blob = json.dumps(cfg.get(section, {}), ensure_ascii=False)
        for m in range_re.finditer(blob):
            lo, hi, unit = int(m.group(1)), int(m.group(2)), m.group(3).lower()
            cur = widest.get(unit)
            # Размах берётся по обоим концам, иначе «до 700 мл» не
            # расширит диапазон, заявленный как «330–500 мл».
            if cur is None:
                widest[unit] = (lo, hi, section)
            else:
                widest[unit] = (min(cur[0], lo), max(cur[1], hi), cur[2])

    ranges_ok = True
    ranges_detail = "диапазоны согласованы с позициями"
    for unit, (lo, hi, section) in sorted(widest.items()):
        real = sorted({int(x) for x in re.findall(
            rf"(\d+)\s*{re.escape(unit)}", item_names, re.I)})
        if len(real) < 2:
            continue
        # Первая сторона: страница обещает меньше, чем на ней есть, или
        # два текста противоречат друг другу. Ловится по самому широкому
        # заявленному диапазону.
        if lo > min(real) or hi < max(real):
            ranges_ok = False
            ranges_detail = (
                f"самое широкое заявленное: {lo}–{hi} {unit} ({section}), "
                f"а на странице {min(real)}–{max(real)} {unit}")
            break
        # Вторая сторона: страница обещает больше, чем на ней есть. Отдельно
        # от первой: сузить текст можно осознанно, а вот обещать 800 мл при
        # максимуме 700 это уже неправда о собственном каталоге.
        if hi > max(real):
            ranges_ok = False
            ranges_detail = (
                f"обещано до {hi} {unit} ({section}), "
                f"а в каталоге максимум {max(real)} {unit}")
            break
    if widest and ranges_ok:
        parts = ", ".join(f"{lo}–{hi} {u}" for u, (lo, hi, _) in sorted(widest.items()))
        ranges_detail = f"согласовано: {parts}"
    gate("22. Диапазоны в текстах не противоречат позициям", ranges_ok, ranges_detail)

    # ---- 23. Каналы связи имеют источник ----
    # На странице показаны три канала: WhatsApp, VK и MAX. VK и MAX есть на
    # сайте заказчика, а WhatsApp там не встречается ни разу: ссылка
    # собрана из второго телефона. Ссылка может вести в никуда, если WhatsApp
    # на этом номере не заведён, и по умолчанию об этом нигде не сказано.
    #
    # Проверяется не «есть ли канал», а «известно ли, откуда он взялся».
    # Проверка на сайт делается по сырой выкачке: если адрес канала не
    # встречается в выкачанных страницах, он обязан быть помечен в
    # sources.customerProvided как непроверенный.
    RAW = Path(__file__).resolve().parent / "_scrape" / "raw"
    channels = cfg.get("contactChannels", [])
    cust = cfg.get("sources", {}).get("customerProvided", {})
    raw_blob = ""
    if RAW.is_dir():
        for f in sorted(RAW.glob("*.html")):
            raw_blob += f.read_text(encoding="utf-8", errors="replace")

    ch_ok = True
    ch_detail = f"каналов {len(channels)}, у всех есть источник"
    if not channels:
        ch_ok = False
        ch_detail = "каналов связи нет ни одного"
    else:
        unproven = []
        for ch in channels:
            url = str(ch.get("url", ""))
            host = re.sub(r"^https?://([^/]+).*$", r"\1", url)
            if raw_blob and host in raw_blob:
                continue  # канал есть на сайте заказчика
            # Пометка ищется по имени канала, а не просто «есть ли хоть
            # одна». Иначе пометка про WhatsApp оправдывала любой канал:
            # добавленный Telegram проходил, потому что рядом лежала
            # запись про другой мессенджер. Проверено подстановкой.
            marker = re.sub(r"[^a-z]", "", str(ch.get("label", "")).lower())
            if marker in cust:
                continue
            unproven.append(ch.get("label", "?"))
        if unproven:
            ch_ok = False
            ch_detail = ("без источника и без пометки: "
                         + ", ".join(sorted(unproven)))
        elif raw_blob:
            ch_detail = (f"каналов {len(channels)}; на сайте "
                         f"{sum(1 for c in channels if re.sub(r'^https?://([^/]+).*$', r'\1', str(c.get('url',''))) in raw_blob)}, "
                         f"остальные помечены в sources.customerProvided")
    gate("23. У каналов связи есть источник", ch_ok, ch_detail)

    # ---- 24. Данные каталога экранированы при вставке в разметку ----
    # Четыре позиции календарей называются с кавычками:
    # КВАРТАЛЬНЫЙ КАЛЕНДАРЬ "PREMIUM" 1 рекл. поле светодиодный. Имя
    # вставлялось в разметку строкой шаблона без экранирования, и атрибут
    # alt обрывался на первой кавычке: оставалось «КВАРТАЛЬНЫЙ КАЛЕНДАРЬ »,
    # а остаток имени утекал в разметку как посторонние атрибуты. Проверки
    # на текст это не видели: буквы верные, испорчен только атрибут.
    #
    # Проверяется, что в собранном скрипте нет подстановки данных позиции
    # без esc(). Список полей закрытый, а не «любое ${»: новые поля
    # добавляются в движок, и незамеченная подстановка прошла бы мимо.
    # Список идентификаторов, которые попадают в разметку извне: данные
    # каталога, поля конфигурации квиза и то, что ввёл посетитель.
    # state.notes добавлен после того, как пожелания пользователя оказались
    # в innerSummary без экранирования, а opt.label добавлен, потому что при
    # первой правкеradio его потеряли и подпись исчезла.
    esc_fields = ("item.name", "item.img", "item.specs", "item.method",
                  "item.priceFrom", "g.title", "opt.value", "opt.label",
                  "groupName", "l")
    #
    # Проверяются только поля внутри ШАБЛОННЫХ СТРОК С РАЗМЕТКОЙ.
    # Первая версия проверяла каждое употребление поля в файле и ругалась
    # на объект, который уходит в бэкенд: там { group: g.title } это
    # значение запроса, а не текст страницы. Экранировать его вредно,
    # заказчик получил бы «Бизнес+» вместо «БИЗНЕС+» с сущностями.
    #
    # Правило проверки то же, что у атрибута alt: перед именем поля должно
    # стоять esc(). Условие тернарника пропускается: {item.priceFrom ? ... : ''}
    # проверяет поле на наличие, а не вставляет его.
    raw_sites = []
    for cand in sorted(dist.glob("*.js")):
        body = cand.read_text(encoding="utf-8", errors="replace")
        # Шаблонные строки с разметкой: обратная кавычка, внутри есть <.
        # Признак разметки: < сразу за буквой или слешем. Проверка на любой <
        # захватывала область между соседними обратными кавычками и
        # накрывала объект payload, который уходит в бэкенда, а не в
        # разметку: там экранирование не нужно и вредно.
        for tm in re.finditer(r"`([^`]*<[A-Za-z/][^`]*)`", body, re.S):
            chunk = tm.group(1)
            for f in esc_fields:
                for m in re.finditer(rf"(?<![\w.]){re.escape(f)}\b", chunk):
                    before = chunk[max(0, m.start() - 5):m.start()]
                    if before.endswith("esc("):
                        continue
                    after = chunk[m.end():m.end() + 3]
                    if re.match(r"\s*\?", after):
                        continue
                    line = body[:tm.start() + m.start()].count("\n") + 1
                    raw_sites.append(f"{cand.name}:{line} {f}")
    esc_ok = not raw_sites
    esc_detail = ("все подстановки данных каталога в разметку экранированы"
                  if esc_ok else "без esc(): " + ", ".join(sorted(set(raw_sites))[:4]))
    gate("24. Данные каталога экранированы", esc_ok, esc_detail)

    # ---- 25. Мета для ссылок и индексации на месте ----
    # Без og-тегов ссылка, отправленная в VK или MAX, то есть ровно туда,
    # куда ведут кнопки «Написать в мессенджер», показывается голой строкой
    # адреса. Без canonical дубли возникают сами при открытии страницы с
    # параметром или якорем. og:image обязан быть абсолютным: относительный
    # не понимает ни одна площадка, и превью просто не будет.
    meta_need = {
        "robots": r'<meta name="robots"[^>]*content="[^"]*index',
        "canonical": r'<link rel="canonical" href="(https?://[^"]+)"',
        "og:title": r'<meta property="og:title"[^>]*content="([^"]*)"',
        "og:description": r'<meta property="og:description"[^>]*content="([^"]*)"',
        "og:image": r'<meta property="og:image"[^>]*content="([^"]*)"',
        "og:url": r'<meta property="og:url"[^>]*content="([^"]*)"',
        "og:site_name": r'<meta property="og:site_name"',
        "twitter:card": r'<meta name="twitter:card"',
    }
    missing = [k for k, pat in meta_need.items()
               if not re.search(pat, html, re.I)]
    # Картинка должна отдаваться из каталога самой страницы. Сравнение по
    # «родительским» папкам через rsplit давало ложную тревогу: canonical
    # кончается слешем, и его директория считалась на уровень выше.
    # Проверяется проще и строже: картинка начинается с адреса страницы.
    canon = re.search(meta_need["canonical"], html, re.I)
    og_img = re.search(meta_need["og:image"], html, re.I)
    same_dir = True
    if canon and og_img:
        same_dir = og_img.group(1).startswith(canon.group(1))
    meta_ok = not missing and same_dir
    meta_detail = "мета на месте"
    if missing:
        meta_detail = "нет тегов: " + ", ".join(sorted(missing))
    elif not same_dir:
        meta_detail = "og:image указывает не в ту папку, что canonical"
    gate("25. Мета для ссылок и индексации на месте", meta_ok, meta_detail)

    # ---- 20. Числительные согласованы с существительными ----
    # На странице было «3 групп товаров» и «31 позиций». В русском языке
    # форма слова зависит от числа: 1 позиция, 2 позиции, 5 позиций, но
    # 21 позиция и 31 позиция снова в единственном числе. Это видно сразу
    # и стоит больше, чем кажется: неграмотный исполнитель отталкивает.
    #
    # Проверка ловит расхождение формы, а не сам факт числа. Словарь
    # ограничен теми существительными, которые встречаются в подписях
    # лендинга: общего решения тут нет, а список открытый, поэтому новые
    # слова просто не проверяются, и это честнее, чем имитировать
    # полноту.
    forms = {
        "группа": ("группа", "группы", "групп"),
        "позиция": ("позиция", "позиции", "позиций"),
        "товар": ("товар", "товара", "товаров"),
        "способ": ("способ", "способы", "способов"),
        "менеджер": ("менеджер", "менеджера", "менеджеров"),
        "форма": ("форма", "формы", "форм"),
        "вариант": ("вариант", "варианта", "вариантов"),
        "ступень": ("ступень", "ступени", "ступеней"),
        "день": ("день", "дня", "дней"),
    }
    # Проверяется только видимый текст: в коде и комментариях эти слова
    # встречаются как угодно и к грамматике страницы отношения не имеют.
    visible = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->",
                     " ", html, flags=re.S | re.I)
    visible = re.sub(r"<[^>]+>", " ", visible)
    visible = re.sub(r"\s+", " ", visible)

    def wrong_form(n: int) -> int:
        """Индекс формы, верной для числа n: 0 одна, 1 две, 2 много."""
        if n % 10 == 1 and n % 100 != 11:
            return 0
        if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
            return 1
        return 2

    bad_forms = []
    for lemma, trio in forms.items():
        for want in range(3):
            # Регистр здесь значим, и это не опечатка. Шаги квиза
            # подписаны прописными: «2 ТОВАР», «3 ПАРАМЕТРЫ». Это названия
            # шагов, а не количество, и регистр их отличает от подписи
            # с числом, где слово всегда строчное: «31 позиция».
            # С регистронезависимым поиском гейт срабатывал на всех
            # одиннадцати лендингах на пустом месте.
            pat = re.compile(rf"(\d+)\s+{trio[want]}(?![а-яё])")
            for m in pat.finditer(visible):
                n = int(m.group(1))
                if wrong_form(n) != want:
                    bad_forms.append(m.group(0))
    gate("20. Числительные согласованы с существительными",
         not bad_forms,
         ("расхождений: " + "; ".join(sorted(set(bad_forms))[:5]))
         if bad_forms else "расхождений нет")

    # ---- 14c. У карточек есть адрес исходной фотографии ----
    # Без поля src скачивание не знает, что качать: искать позицию по id
    # нельзя, id совпадает у 15 позиций каталога. Проверка ловит
    # спецификацию без этого поля до того, как лендинг уедет с битой
    # фотографией.
    cards = [c for g in cfg.get("catalog", {}).get("groups", [])
             for c in g.get("items", [])]
    no_src = [c.get("id") for c in cards if not c.get("src")]
    gate("14c. У карточек есть адрес исходного фото",
         bool(cards) and not no_src,
         f"карточек {len(cards)}, без src: {len(no_src)}"
         + (f" ({', '.join(no_src[:3])})" if no_src else ""))

    # ---- 15. Идентификатор позиций уникален: дубли ломают выбор в квизе ----
    ids = [it.get("id") for it in items]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    gate("15. id позиций уникальны", not dupes,
         f"дубли: {dupes}" if dupes else f"{len(ids)} уникальных id")

    # ---- 16. Кавычки в данных не ломают атрибуты (экранирование на месте) ----
    raw_attr = re.findall(r'(?:src|alt|href)="[^"]*"[^"<>\n]*"', html)
    quote_leak = [m for m in re.findall(r'(?:src|alt|href)="([^"]*)"', html)
                  if '"' in m]
    gate("16. Экранирование кавычек в атрибутах", not quote_leak,
         f"подозрительные атрибуты: {quote_leak[:3]}" if quote_leak else "чисто")

    # ---- вывод ----
    print(f"Проверка лендинга: {landing.name}")
    print(f"Каталог: {len(groups)} групп, {len(items)} позиций\n")
    width = max(len(n) for n, _, _ in results)
    for name, passed, detail in results:
        mark = OK if passed else FAIL
        print(f"  {mark} {name:<{width}}  {detail}")
    failed = [n for n, p, _ in results if not p]
    print()
    if failed:
        print(f"НЕ ПРОЙДЕНО: {len(failed)} из {len(results)}. Публиковать нельзя.")
        for n in failed:
            print(f"  - {n}")
        return 1
    print(f"Все {len(results)} гейтов пройдены.")
    print("Осталось проверить руками и на живой инсталляции:")
    print("  - mailto-ссылки декодировать и прочитать глазами (кириллица в кодировке)")
    print("  - живой curl-тест backend, включая честный 502 при обрыве обоих каналов")
    print("  - lead.php на сервере сайта, все три канала по-настоящему")
    print("  - визуально в браузере: гейт не видит вёрстку")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
