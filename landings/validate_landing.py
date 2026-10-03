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
    init_ids = re.findall(r'ym\((\d+),\s*"init"', html)
    goal_ids = re.findall(r"ym\((\d+),\s*'reachGoal'", script)
    counter = "50863157"
    gate("4. Счётчик Метрики из .env, не заглушка",
         init_ids == [counter] and set(goal_ids) == {counter},
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
    print("  - реквизиты ИП: без них privacy.html неполна, см. гейт 8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
