#!/usr/bin/env python3
"""
Полный аудит каталога 300+ услуг — ЦИФРА18
Запуск: python3 scripts/audit/full_catalog_audit.py
Результат: brain/wiki/audits/full_service_audit_YYYY-MM-DD.md + CSV
"""

import asyncio
import aiohttp
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import pandas as pd

# ========== КОНФИГ ==========
BASE_URL = "https://xn--18-6kc5a3bxam.xn--p1ai"
CATALOG_URL = f"{BASE_URL}/catalog/"
OUTPUT_DIR = Path("brain/wiki/audits")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Cifra18Audit/1.0; +https://cifra18.rf)"
}

# Семафор для ограничения параллельности
SEMAPHORE = asyncio.Semaphore(5)

# ========== УТИЛИТЫ ==========
def clean_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.strip())

def extract_price(text: str) -> dict:
    """Извлекает цену из текста: от X руб/шт, X руб/м2 и т.д."""
    if not text:
        return {"raw": "", "value": None, "unit": ""}
    # Паттерны: "от 47 ₽/шт.", "250 ₽/шт.", "350 ₽/м2"
    m = re.search(r'от\s+([\d\s]+)\s*₽/([^\s]+)', text)
    if m:
        return {"raw": text, "value": int(m.group(1).replace(' ', '')), "unit": m.group(2)}
    m = re.search(r'([\d\s]+)\s*₽/([^\s]+)', text)
    if m:
        return {"raw": text, "value": int(m.group(1).replace(' ', '')), "unit": m.group(2)}
    return {"raw": text, "value": None, "unit": ""}

# ========== СБОР URL ВСЕХ УСЛУГ ==========
async def fetch(session, url):
    async with SEMAPHORE:
        try:
            async with session.get(url, headers=HEADERS, timeout=30) as resp:
                html = await resp.text()
                return resp.status, html
        except Exception as e:
            return 0, str(e)

async def get_all_category_urls(session):
    """Получает все URL категорий каталога из меню/страницы каталога"""
    status, html = await fetch(session, CATALOG_URL)
    if status != 200:
        print(f"Ошибка каталога: {status}")
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    urls = set()
    
    # Из меню (js-production-group)
    for link in soup.select('.menu__list-grid a, .menu__list-column a'):
        href = link.get('href')
        if href and '/catalog/' in href:
            urls.add(urljoin(BASE_URL, href))
    
    # Из футера/других блоков
    for link in soup.select('a[href*="/catalog/"]'):
        href = link.get('href')
        if href:
            urls.add(urljoin(BASE_URL, href))
    
    # Фильтруем только страницы разделов (не товары)
    category_urls = [u for u in urls if u.count('/') >= 5 and not u.endswith('/')]
    # Нормализуем
    category_urls = list(set([u.rstrip('/') + '/' for u in category_urls]))
    
    print(f"Найдено категорий: {len(category_urls)}")
    return sorted(category_urls)

async def get_all_product_urls_from_category(session, cat_url):
    """Получает все URL товаров/услуг внутри категории (с пагинацией)"""
    product_urls = set()
    page = 1
    
    while True:
        # Пагинация в Битриксе обычно ?PAGEN_1=N или /page-N/
        paged_url = f"{cat_url}?PAGEN_1={page}" if page > 1 else cat_url
        status, html = await fetch(session, paged_url)
        if status != 200:
            break
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Товары в каталоге (news-card-wrap, result-card, item)
        found = 0
        for link in soup.select('a[href*="/catalog/"]'):
            href = link.get('href')
            if href and '/catalog/' in href:
                full = urljoin(BASE_URL, href)
                # Проверяем что это товар/услуга (глубже категории)
                if full.count('/') > cat_url.count('/'):
                    product_urls.add(full.rstrip('/'))
                    found += 1
        
        if found == 0:
            break
        
        # Проверяем есть ли следующая страница
        next_page = soup.select_one('.pagination .next, .pagen .next, a[rel="next"]')
        if not next_page:
            # Пробуем найти номера страниц
            pages = soup.select('.pagination a, .pagen a')
            max_page = max([int(p.get_text()) for p in pages if p.get_text().isdigit()], default=1)
            if page >= max_page:
                break
        
        page += 1
        if page > 50:  # защита
            break
    
    return list(product_urls)

# ========== АУДИТ ОДНОЙ СТРАНИЦЫ УСЛУГИ ==========
async def audit_service_page(session, url):
    """Аудит одной страницы услуги/товара"""
    status, html = await fetch(session, url)
    if status != 200:
        return {"url": url, "status": status, "error": f"HTTP {status}"}
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Базовые SEO элементы
    title = soup.select_one('title')
    title_text = clean_text(title.get_text()) if title else ""
    title_len = len(title_text)
    
    meta_desc = soup.select_one('meta[name="description"]')
    meta_desc_text = clean_text(meta_desc.get('content', '')) if meta_desc else ""
    meta_desc_len = len(meta_desc_text)
    
    meta_keywords = soup.select_one('meta[name="keywords"]')
    meta_kw_text = clean_text(meta_keywords.get('content', '')) if meta_keywords else ""
    
    # H1
    h1s = soup.select('h1')
    h1_texts = [clean_text(h.get_text()) for h in h1s]
    h1_count = len(h1_texts)
    
    # Все заголовки
    headings = []
    for h in soup.select('h1, h2, h3, h4, h5, h6'):
        headings.append({"level": h.name, "text": clean_text(h.get_text())})
    
    # Canonical
    canonical = soup.select_one('link[rel="canonical"]')
    canonical_href = canonical.get('href') if canonical else None
    
    # JSON-LD
    json_ld = []
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            json_ld.append(json.loads(script.string))
        except:
            pass
    
    # Open Graph
    og = {}
    for meta in soup.select('meta[property^="og:"]'):
        og[meta.get('property')] = meta.get('content')
    
    # Картинки
    images = []
    for img in soup.select('img'):
        src = img.get('src') or img.get('data-src')
        alt = img.get('alt', '')
        if src:
            images.append({"src": urljoin(BASE_URL, src), "alt": clean_text(alt), "has_alt": bool(alt.strip())})
    
    # Контент (видимый текст)
    # Удаляем скрипты/стили
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    visible_text = clean_text(soup.get_text())
    word_count = len(visible_text.split())
    
    # Em/En dashes
    em_dashes = visible_text.count('—')
    en_dashes = visible_text.count('–')
    
    # Цена / Калькулятор
    price_text = ""
    for el in soup.select('.price, .calculator, [class*="price"], [class*="cost"]'):
        price_text += " " + clean_text(el.get_text())
    price_info = extract_price(price_text)
    
    # Хлебные крошки
    breadcrumbs = []
    for el in soup.select('.breadcrumb a, .breadcrumbs a, [class*="breadcrumb"] a'):
        breadcrumbs.append(clean_text(el.get_text()))
    
    # Внутренние ссылки
    internal_links = len([a for a in soup.select('a[href]') if BASE_URL in a.get('href', '')])
    external_links = len([a for a in soup.select('a[href]') if BASE_URL not in a.get('href', '') and a.get('href', '').startswith('http')])
    
    # Наличие калькулятора/формы заявки
    has_calculator = bool(soup.select('.calculator, [class*="calculator"], #calculator'))
    has_order_form = bool(soup.select('form[action*="order"], .order-form, [class*="order-form"]'))
    has_quick_order = bool(soup.select('.quick-order, [class*="quick-order"], .one-click'))
    
    # Описание услуги (основной контент)
    description = ""
    for sel in ['.description, .content, .detail-text, [class*="description"], article, main']:
        el = soup.select_one(sel)
        if el:
            description = clean_text(el.get_text())[:2000]
            break
    
    return {
        "url": url,
        "status": status,
        "title": title_text,
        "title_len": title_len,
        "meta_description": meta_desc_text,
        "meta_desc_len": meta_desc_len,
        "meta_keywords": meta_kw_text,
        "h1_count": h1_count,
        "h1_texts": " | ".join(h1_texts),
        "headings_count": len(headings),
        "headings": json.dumps(headings, ensure_ascii=False),
        "canonical": canonical_href,
        "has_canonical": canonical_href is not None,
        "json_ld_count": len(json_ld),
        "json_ld_types": json.dumps([j.get('@type') for j in json_ld if isinstance(j, dict)], ensure_ascii=False),
        "og_title": og.get('og:title', ''),
        "og_description": og.get('og:description', ''),
        "og_image": og.get('og:image', ''),
        "images_count": len(images),
        "images_no_alt": sum(1 for i in images if not i['has_alt']),
        "word_count": word_count,
        "em_dashes": em_dashes,
        "en_dashes": en_dashes,
        "price_raw": price_info['raw'],
        "price_value": price_info['value'],
        "price_unit": price_info['unit'],
        "breadcrumbs": " > ".join(breadcrumbs),
        "internal_links": internal_links,
        "external_links": external_links,
        "has_calculator": has_calculator,
        "has_order_form": has_order_form,
        "has_quick_order": has_quick_order,
        "description_preview": description[:500],
    }

# ========== MAIN ==========
async def main():
    print(f"=== ЦИФРА18 Full Catalog Audit ===")
    print(f"Base: {BASE_URL}")
    print(f"Started: {datetime.now()}")
    
    async with aiohttp.ClientSession() as session:
        # 1. Собираем все категории
        print("\n1. Сбор категорий...")
        categories = await get_all_category_urls(session)
        
        # 2. Для каждой категории собираем товары
        print("\n2. Сбор товаров/услуг по категориям...")
        all_products = {}
        for cat in categories:
            print(f"  {cat}...")
            products = await get_all_product_urls_from_category(session, cat)
            all_products[cat] = products
            print(f"    -> {len(products)} товаров")
        
        total_products = sum(len(v) for v in all_products.values())
        print(f"\nВсего товаров/услуг: {total_products}")
        
        # 3. Аудит каждой страницы
        print("\n3. Аудит страниц товаров...")
        results = []
        tasks = []
        
        for cat, products in all_products.items():
            for prod_url in products:
                tasks.append(audit_service_page(session, prod_url))
        
        # Выполняем батчами
        batch_size = 50
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i+batch_size]
            print(f"  Бач {i//batch_size + 1}/{(len(tasks)-1)//batch_size + 1} ({len(batch)} urls)...")
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            for r in batch_results:
                if isinstance(r, Exception):
                    results.append({"url": "ERROR", "error": str(r)})
                else:
                    results.append(r)
        
        # 4. Сохранение результатов
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # CSV
        csv_path = OUTPUT_DIR / f"full_service_audit_{date_str}.csv"
        if results:
            fieldnames = list(results[0].keys())
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
            print(f"\nCSV сохранён: {csv_path}")
        
        # Markdown отчёт
        md_path = OUTPUT_DIR / f"full_service_audit_{date_str}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# Полный аудит каталога ЦИФРА18 — {date_str}\n\n")
            f.write(f"**Всего категорий:** {len(categories)}\n")
            f.write(f"**Всего товаров/услуг:** {total_products}\n")
            f.write(f"**Дата аудита:** {datetime.now()}\n\n")
            
            # Сводка по категориям
            f.write("## Категории\n\n")
            f.write("| Категория | Кол-во товаров |\n|---|---|\n")
            for cat, prods in sorted(all_products.items(), key=lambda x: -len(x[1])):
                f.write(f"| {cat} | {len(prods)} |\n")
            
            # Топ проблем
            f.write("\n## Топ проблем (по частоте)\n\n")
            
            issues = {
                "Нет canonical": sum(1 for r in results if not r.get('has_canonical')),
                "Meta description = Description": sum(1 for r in results if r.get('meta_description') == 'Description'),
                "Meta description пуста/короткая (<50)": sum(1 for r in results if r.get('meta_desc_len', 0) < 50),
                "Meta description длинная (>160)": sum(1 for r in results if r.get('meta_desc_len', 0) > 160),
                "Нет H1": sum(1 for r in results if r.get('h1_count', 0) == 0),
                "Много H1 (>1)": sum(1 for r in results if r.get('h1_count', 0) > 1),
                "Нет JSON-LD": sum(1 for r in results if r.get('json_ld_count', 0) == 0),
                "Есть em-dash": sum(1 for r in results if r.get('em_dashes', 0) > 0),
                "Мало слов (<300)": sum(1 for r in results if r.get('word_count', 0) < 300),
                "Нет калькулятора": sum(1 for r in results if not r.get('has_calculator')),
                "Нет быстрой заявки": sum(1 for r in results if not r.get('has_quick_order')),
                "Картинок без alt": sum(r.get('images_no_alt', 0) for r in results),
            }
            
            f.write("| Проблема | Кол-во страниц |\n|---|---|\n")
            for issue, count in sorted(issues.items(), key=lambda x: -x[1]):
                if count > 0:
                    f.write(f"| {issue} | {count} |\n")
            
            # Детали по каждой странице (сокращённо)
            f.write("\n## Детали по страницам (первые 50)\n\n")
            f.write("| URL | Title | H1 | MetaDesc | Words | JSON-LD | Calc | Issues |\n|---|---|---|---|---|---|---|---|\n")
            for r in results[:50]:
                issues_list = []
                if not r.get('has_canonical'): issues_list.append("no-canon")
                if r.get('meta_description') == 'Description': issues_list.append("placeholder-desc")
                if r.get('h1_count', 0) != 1: issues_list.append(f"h1:{r.get('h1_count',0)}")
                if r.get('json_ld_count', 0) == 0: issues_list.append("no-schema")
                if r.get('em_dashes', 0) > 0: issues_list.append("em-dash")
                if r.get('word_count', 0) < 300: issues_list.append("thin")
                if not r.get('has_calculator'): issues_list.append("no-calc")
                
                title_short = r.get('title', '')[:40]
                h1_short = r.get('h1_texts', '')[:30]
                meta_short = r.get('meta_description', '')[:30]
                
                f.write(f"| {r.get('url','')[:60]} | {title_short} | {h1_short} | {meta_short} | {r.get('word_count',0)} | {'✅' if r.get('json_ld_count',0)>0 else '❌'} | {'✅' if r.get('has_calculator') else '❌'} | {', '.join(issues_list)} |\n")
        
        print(f"\nMarkdown отчёт: {md_path}")
        print(f"\n=== Аудит завершён: {datetime.now()} ===")

if __name__ == "__main__":
    asyncio.run(main())