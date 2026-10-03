#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Полная выкачка каталога цифра18.рф для сборки лендингов.

Что делает:
  1. читает sitemap.xml, и все sitemap-iblock-*.xml;
  2. оставляет только страницы каталога (detail.php, /catalog/...);
  3. обходит их с задержкой из robots.txt, кладёт HTML в _scrape/raw/;
  4. вытаскивает название, цену, описание, свойства, фото;
  5. пишет out/catalog.json, out/catalog.csv, out/summary.md.

Зачем свой скрипт, а не full_catalog_parser_v2.py из scripts/audit:
  тот парсер писался под асинхронный aiohttp, кладёт результат в
  brain/wiki/entities/full_catalog и не сохраняет фото. Для лендингов
  нужны именно фотографии и цены рядом с описанием.

Запуск из корня проекта:
  python landings/_scrape/fetch_catalog.py
python landings/_scrape/fetch_catalog.py --parse-only

Прерываемость: состояние в out/progress.json, повторный запуск
продолжает с места обрыва.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://xn--18-6kc5a3bxam.xn--p1ai"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
OUT = ROOT / "out"
IMG = OUT / "images"
RAW.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
IMG.mkdir(parents=True, exist_ok=True)

# robots.txt отдаёт Crawl-delay: 3. Держимся, это не наш сайт.
DELAY = 3.0
TIMEOUT = 45

S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9"})


def log(*a):
    print(*a, flush=True)


def clean(t: str | None) -> str:
    if not t:
        return ""
    t = re.sub(r"\s+", " ", t)
    return t.replace(" ", " ").replace("", "").strip()


def parse_price(raw: str) -> dict:
    """Разбирает «от 240 ₽/шт.» в {raw, value, unit, is_from}."""
    if not raw:
        return {"raw": "", "value": None, "unit": "", "isFrom": False}
    out = {"raw": clean(raw), "value": None, "unit": "", "isFrom": False}
    m = re.search(r"от\s+([\d\s ]+)\s*₽\s*/\s*([^\s,]+)", raw)
    if not m:
        m = re.search(r"([\d\s ]+)\s*₽\s*/\s*([^\s,]+)", raw)
    if m:
        try:
            out["value"] = int(re.sub(r"\D", "", m.group(1)))
            out["unit"] = clean(m.group(2))
        except ValueError:
            pass
    out["isFrom"] = bool(re.search(r"\bот\b", raw, re.I))
    return out


def read_sitemaps() -> list[str]:
    """Все URL из sitemap.xml и вложенных sitemap-iblock-*.xml."""
    urls: set[str] = set()
    idx_url = f"{BASE}/sitemap.xml"
    r = S.get(idx_url, timeout=TIMEOUT)
    r.raise_for_status()
    children = re.findall(r"<loc>([^<]+)</loc>", r.text)
    if not children:
        return []
    for loc in children:
        if not loc.endswith(".xml"):
            continue
        time.sleep(0.5)
        try:
            rr = S.get(loc, timeout=TIMEOUT)
            rr.raise_for_status()
        except Exception as e:
            log(f"  ! sitemap недоступен {loc}: {e}")
            continue
        urls.update(re.findall(r"<loc>([^<]+)</loc>", rr.text))
        time.sleep(0.5)
    return sorted(urls)


def is_catalog_page(u: str) -> bool:
    """Страница товара или раздела каталога. Новости и словари мимо."""
    if "/news/" in u or "/dict/" in u:
        return False
    return "/catalog/" in u


def local_name(u: str) -> str:
    """Имя файла из URL без query, чтобы не было коллизий detail.php."""
    p = urllib.parse.urlparse(u).path.strip("/")
    q = urllib.parse.urlparse(u).query
    slug = re.sub(r"[^a-zA-Z0-9а-яА-Я._-]+", "-", p).strip("-")
    if q:
        qs = re.sub(r"[^a-zA-Z0-9=_-]+", "", q)
        slug = f"{slug}--{qs}"
    return (slug or "index") + ".html"


def extract_price_tiers(soup: BeautifulSoup) -> list[dict]:
    """Тиражная лестница цен из блока калькулятора товара.

    На карточке товара цена не одна строка, а лестница: 20 шт по 360 ₽/шт,
    100 шт по 290 ₽/шт, 1000 шт по 210 ₽/шт. Это данные с сайта клиента,
    а не оценка. Для лендинга календарей это самый сильный блок: человек видит
    реальную экономию от тиража, и она снимает вопрос «а сколько стоит».

    Берётся только из .product-calculate, то есть из карточки ЭТОГО товара.
    """
    tiers: list[dict] = []
    for row in soup.select(".product-calculate .tirazh-inline-list .rsm_option"):
        name_el = row.select_one(".rsm_option-name, .value")
        qty: int | None = None
        if name_el:
            m = re.search(r"(\d[\d\s\u00a0]*)", name_el.get_text(" "))
            if m:
                qty = int(re.sub(r"\D", "", m.group(1)))
        per_el = row.select_one(".price-per-pc")
        per = parse_price(per_el.get_text(" ") if per_el else "")
        total: int | None = None
        tot_el = row.select_one(".price-total")
        if tot_el:
            m = re.search(r"([\d\s\u00a0]+)\s*\u20bd", tot_el.get_text(" "))
            if m:
                total = int(re.sub(r"\D", "", m.group(1)))
        if qty is not None and per["value"]:
            tiers.append({"qty": qty, "perPc": per["value"], "total": total})
    return tiers


def extract_product_price(soup: BeautifulSoup, tiers: list[dict]) -> dict:
    """Цена ЭТОГО товара. Никогда не из блока «Избранные товары».

    Здесь была ошибка, которая тихо портила весь каталог. Фолбэк искал строку
    вида «от N ₽/шт.» по всему тексту страницы, а первыми на странице идут
    карточки блока «Избранные товары» в шапке. В итоге КАЖДОЙ позиции каталога
    приписывалась цена первого избранного товара: у страницы с квартальным
    календарём 2027 получалась «от 0 ₽/шт.», потому что избранным был ROLL-UP.
    Данные выглядели правдоподобно и были чужими.

    Теперь источник только один: лестница тиражей карточки товара.
    """
    if not tiers:
        return {"raw": "", "value": None, "unit": "", "isFrom": False,
                "isPlaceholder": False, "source": "нет калькулятора на карточке"}
    cheapest = min(t["perPc"] for t in tiers)
    unit = parse_price(f"{cheapest} \u20bd / шт.")["unit"] or "шт."
    return {
        "raw": f"от {cheapest} \u20bd/{unit}",
        "value": cheapest,
        "unit": unit,
        "isFrom": True,
        "isPlaceholder": cheapest == 0,
        "source": f"лестница тиражей, {len(tiers)} позиций, от {cheapest} \u20bd/{unit}",
    }


def extract(soup: BeautifulSoup, url: str) -> dict:
    """Достаёт данные карточки товара.

    Шаблон сайта: product / product-gallery / product-tabs / product-calculate.
    Прежний парсер искал классы catalog-item__* и не находил ничего, кроме
    цен из блока избранного. Селекторы ниже проверены на странице квартального
    календаря 2027, файл _scrape/raw/catalog-poligrafiya-kalendari-
    kvartalnyy-kalendar-2027-biznes-3-reklamnykh-polya.html.
    """
    d: dict = {"url": url}

    h1 = soup.find("h1")
    d["name"] = clean(h1.get_text(" ") if h1 else "") or clean(
        soup.title.get_text() if soup.title else "")
    if not d["name"] and soup.title:
        d["name"] = clean(soup.title.get_text()).split(" - ")[0]

    og = soup.find("meta", property="og:title")
    d["ogTitle"] = clean(og.get("content")) if og else ""

    desc = soup.find("meta", attrs={"name": "description"})
    d["description"] = clean(desc.get("content")) if desc else ""
    ogd = soup.find("meta", property="og:description")
    if ogd and len(ogd.get("content", "")) > len(d["description"]):
        d["description"] = clean(ogd.get("content"))
    d["metaDescription"] = d["description"]

    # Описание товара и требования к макетам лежат во вкладках product-tabs,
    # а не в meta. Для лендинга важнее вкладка, чем meta-описание.
    tabs = soup.select(".product-tabs__content-inner")
    d["richText"] = clean(tabs[0].get_text(" ")) if tabs else ""
    d["layoutRequirements"] = clean(tabs[1].get_text(" ")) if len(tabs) > 1 else ""

    # Цена: только лестница тиражей карточки, см. extract_product_price.
    d["priceTiers"] = extract_price_tiers(soup)
    d["price"] = extract_product_price(soup, d["priceTiers"])

    # Фото товара: gallery карточки, og:image как запасной источник.
    photos: list[str] = []
    for im in soup.select(".product-gallery img"):
        src = im.get("src") or im.get("data-src") or im.get("data-original") or ""
        if "/upload/" in src:
            photos.append(src)
    ogi = soup.find("meta", property="og:image")
    if ogi and ogi.get("content"):
        photos.insert(0, ogi["content"])
    seen, uniq = set(), []
    for p in photos:
        full = urllib.parse.urljoin(BASE, p)
        if full in seen:
            continue
        seen.add(full)
        uniq.append(full)
    d["photos"] = uniq[:12]

    # Характеристики: dl и таблицы внутри вкладок карточки.
    props: list[dict] = []
    scope = soup.select_one(".product__content") or soup
    for tr in scope.select(".product-property tr, .bx-property tr, .catalog-item__property tr"):
        tds = tr.find_all(["td", "th"])
        if len(tds) >= 2:
            k = clean(tds[0].get_text(" "))
            v = clean(tds[1].get_text(" "))
            if k and v:
                props.append({"key": k, "value": v})
    for dl in scope.select("dl"):
        dts, dds = dl.find_all("dt"), dl.find_all("dd")
        for a, b in zip(dts, dds):
            k, v = clean(a.get_text(" ")), clean(b.get_text(" "))
            if k and v:
                props.append({"key": k, "value": v})
    d["properties"] = props

    # Хлебные крошки дают раздел и подкатегорию.
    crumbs = [clean(a.get_text(" ")) for a in soup.select(".bx-breadcrumb-item")]
    d["breadcrumbs"] = [c for c in crumbs if c]
    seg = [s for s in urllib.parse.urlparse(url).path.split("/") if s]
    d["section"] = seg[1] if len(seg) > 1 else ""
    d["subsection"] = seg[2] if len(seg) > 2 else ""
    return d

def fetch_html(u: str) -> str | None:
    p = RAW / local_name(u)
    if p.exists() and p.stat().st_size > 2000:
        return p.read_text(encoding="utf-8", errors="replace")
    try:
        r = S.get(u, timeout=TIMEOUT)
    except Exception as e:
        log(f"  ! {e}")
        return None
    if r.status_code != 200:
        return None
    r.encoding = r.encoding or "utf-8"
    p.write_text(r.text, encoding="utf-8")
    return r.text


def write_outputs(items: list[dict], targets_total: int) -> None:
    """Пишет catalog.json, catalog.csv и summary.md по уже разобранным позициям.

    Вызывается в процессе обхода, а не только в конце. Причина конкретная:
    ночной прогон на 457 страниц упирается в ConnectTimeout примерно на
    180-й странице, и при старом коде на диск не попадало ничего: ни
    catalog.json, ни summary.md, ни одной разобранной позиции. Всё, что уже
    разобрано, полезно само по себе, в том числе для первого лендинга.
    """
    (OUT / "catalog.json").write_text(
        json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")

    cols = ["url", "section", "subsection", "name", "price_raw", "price_value",
            "price_unit", "is_from", "n_tiers", "price_min_per_pc", "price_max_per_pc",
            "description", "n_photos", "n_props", "has_layout_req"]
    with (OUT / "catalog.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for it in items:
            t = it.get("priceTiers") or []
            pers = [x["perPc"] for x in t if x.get("perPc")]
            w.writerow([
                it["url"], it["section"], it["subsection"], it["name"],
                it["price"]["raw"], it["price"]["value"], it["price"]["unit"],
                it["price"]["isFrom"], len(t),
                min(pers) if pers else "", max(pers) if pers else "",
                it["description"][:400],
                len(it["photos"]), len(it["properties"]),
                bool(it.get("layoutRequirements")),
            ])

    with_prices = [i for i in items if i["price"]["value"]]
    zero_prices = [i for i in items if i["price"]["value"] == 0 and i["price"]["raw"]]
    sections: dict[str, int] = {}
    for i in items:
        sections[i["section"] or "?"] = sections.get(i["section"] or "?", 0) + 1

    md = [
        "# Выкачка каталога цифра18.рф",
        "",
        f"Дата: {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC",
        "",
        "## Итоги",
        "",
        f"- страниц каталога в sitemap: {targets_total}",
        f"- скачано и разобрано: {len(items)}",
        f"- с ценой: {len(with_prices)}",
        f"- без цены: {len(items) - len(with_prices)}",
        f"- с ценой 0, это заглушка на сайте, а не оферта: {len(zero_prices)}",
        f"- с фотографиями: {sum(1 for i in items if i['photos'])}",
        f"- со свойствами: {sum(1 for i in items if i['properties'])}",
        "",
        "## По разделам",
        "",
        "| Раздел | Страниц |",
        "|---|---:|",
    ]
    for k in sorted(sections):
        md.append(f"| {k} | {sections[k]} |")
    md += ["", "## Что дальше", "",
           "Цены выгружены вместе со всем остальным и лежат в `catalog.json`",
           "полем `price`. На лендингах они отключаются одним флагом",
           "`showPrices: false`, данные при этом не теряются.",
           "Позиции с ценой 0 — заглушки сайта, на лендинг они не идут.",
           "Подробности в `landings/reports/05_PRICES.md`."]
    (OUT / "summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def parse_only() -> int:
    """Разбор уже скачанного HTML, без единого сетевого запроса.

    Нужен, когда сайт не отвечает: сырой HTML лежит в raw/, обход ничего к
    нему не добавит, а разобрать накопленное можно офлайн. Для первого
    лендинга, квартальные календари, весь нужный раздел уже скачан.
    """
    prog_path = OUT / "progress.json"
    if not prog_path.exists():
        log("Нет out/progress.json: разбирать нечего, сначала нужен обход.")
        return 1
    done = json.loads(prog_path.read_text(encoding="utf-8"))
    log(f"Офлайн-разбор, {len(done)} скачанных страниц, сеть не трогается")
    items: list[dict] = []
    missing = 0
    for url, fname in sorted(done.items()):
        p = RAW / fname
        if not p.exists():
            missing += 1
            log(f"  ! нет файла {fname} для {url}")
            continue
        try:
            items.append(extract(
                BeautifulSoup(p.read_text(encoding="utf-8", errors="replace"), "lxml"), url))
        except Exception as e:
            log(f"  ! разбор не удался {url}: {e}")
    if missing:
        log(f"  пропущено файлов: {missing}")
    write_outputs(items, len(done))
    log(f"Готово. Разобрано {len(items)}, "
        f"с ценой {sum(1 for i in items if i['price']['value'])}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Выкачка каталога цифра18.рф для сборки лендингов.")
    ap.add_argument("--parse-only", action="store_true",
                    help="только разобрать уже скачанный HTML, без сети")
    args = ap.parse_args()
    if args.parse_only:
        return parse_only()

    log(f"Старт {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    log("Читаю sitemap...")
    all_urls = read_sitemaps()
    log(f"  всего URL в sitemap: {len(all_urls)}")

    targets = [u for u in all_urls if is_catalog_page(u)]
    log(f"  из них страниц каталога: {len(targets)}")

    prog_path = OUT / "progress.json"
    done: dict = {}
    if prog_path.exists():
        done = json.loads(prog_path.read_text(encoding="utf-8"))
        log(f"  уже скачано ранее: {len(done)}")

    t0 = time.time()
    items: list[dict] = []
    for i, u in enumerate(targets, 1):
        h = fetch_html(u)
        if h:
            try:
                items.append(extract(BeautifulSoup(h, "lxml"), u))
            except Exception as e:
                log(f"  ! разбор не удался {u}: {e}")
            done[u] = local_name(u)
        if i % 10 == 0 or i == len(targets):
            prog_path.write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")
            rate = (time.time() - t0) / i
            left = rate * (len(targets) - i)
            log(f"  {i}/{len(targets)}  {rate:.1f}с/стр  осталось {left/60:.0f} мин")
        # Раз в 25 страниц фиксируем разобранное, а не только в конце: обход
        # обрывается по таймауту сайта, и несохранённый прогон не даёт ничего.
        if i % 25 == 0:
            write_outputs(items, len(targets))
        time.sleep(DELAY)

    write_outputs(items, len(targets))

    log(f"Готово. Скачано {len(items)}, "
        f"с ценой {sum(1 for i in items if i['price']['value'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
