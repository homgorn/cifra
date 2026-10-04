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
