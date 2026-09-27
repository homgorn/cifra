#!/usr/bin/env python3
"""
Comprehensive Cifra18 Catalog Parser
Парсит ВСЕ услуги/товары с сайта: категории, подкатегории, товары, все свойства, фото, цены, описания
Сохраняет в markdown + JSON + CSV
SSL verification disabled for self-signed certs
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
from typing import Dict, List, Optional, Set
import sys

BASE_URL = "https://xn--18-6kc5a3bxam.xn--p1ai"
OUTPUT_DIR = Path("brain/wiki/entities/full_catalog")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}

SEMAPHORE = asyncio.Semaphore(3)
REQUEST_DELAY = 0.3

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text.strip())
    return text.replace('\u00a0', ' ').replace('\u200b', '')

def extract_price(text: str) -> dict:
    if not text:
        return {"raw": "", "value": None, "unit": ""}
    m = re.search(r'от\s+([\d\s]+)\s*₽/([^\s]+)', text)
    if m:
        return {"raw": text, "value": int(m.group(1).replace(' ', '')), "unit": m.group(2)}
    m = re.search(r'([\d\s]+)\s*₽/([^\s]+)', text)
    if m:
        return {"raw": text, "value": int(m.group(1).replace(' ', '')), "unit": m.group(2)}
    return {"raw": text, "value": None, "unit": ""}

def create_session():
    """Create aiohttp session with SSL disabled"""
    connector = aiohttp.TCPConnector(ssl=False, limit=10, limit_per_host=5)
    timeout = aiohttp.ClientTimeout(total=60, connect=20)
    return aiohttp.ClientSession(connector=connector, timeout=timeout, headers=HEADERS)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}

SEMAPHORE = asyncio.Semaphore(4)
REQUEST_DELAY = 0.3

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text.strip())
    return text.replace('\u00a0', ' ').replace('\u200b', '')

def extract_price(text: str) -> dict:
    if not text:
        return {"raw": "", "value": None, "unit": ""}
    m = re.search(r'от\s+([\d\s]+)\s*₽/([^\s]+)', text)
    if m:
        return {"raw": text, "value": int(m.group(1).replace(' ', '')), "unit": m.group(2)}
    m = re.search(r'([\d\s]+)\s*₽/([^\s]+)', text)
    if m:
        return {"raw": text, "value": int(m.group(1).replace(' ', '')), "unit": m.group(2)}
    return {"raw": text, "value": None, "unit": ""}

def parse_category_tree(html: str) -> List[Dict]:
    """Парсит меню категорий из HTML главной страницы"""
    soup = BeautifulSoup(html, 'html.parser')
    categories = []
    
    for nav in soup.select('nav.js-production-group'):
        title_link = nav.select_one('a.menu__list-title')
        if not title_link:
            continue
        
        cat_name = clean_text(title_link.get_text())
        cat_url = urljoin(BASE_URL, title_link.get('href', ''))
        
        subcats = []
        for ol in nav.select('ol.menu__list-grid, ol.menu__list-column'):
            for li in ol.select('li a'):
                sub_name = clean_text(li.get_text())
                sub_url = urljoin(BASE_URL, li.get('href', ''))
                subcats.append({"name": sub_name, "url": sub_url})
        
        categories.append({
            "name": cat_name,
            "url": cat_url,
            "subcategories": subcats
        })
    
    return categories

async def fetch(session, url):
    async with SEMAPHORE:
        await asyncio.sleep(REQUEST_DELAY)
        try:
            async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                html = await resp.text()
                return resp.status, html, str(resp.url)
        except Exception as e:
            return 0, str(e), url

async def get_all_product_urls_from_category(session, cat_url: str) -> List[str]:
    """Получает все URL товаров в категории (с пагинацией)"""
    product_urls = set()
    page = 1
    
    while True:
        paged_url = f"{cat_url}?PAGEN_1={page}" if page > 1 else cat_url
        status, html, final_url = await fetch(session, paged_url)
        
        if status != 200:
            break
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Ищем товары в каталоге
        found = 0
        
        for link in soup.select('a.news-card, a.catalog-item__link, .catalog-item a[href*="/catalog/"]'):
            href = link.get('href')
            if href and '/catalog/' in href:
                full = urljoin(BASE_URL, href)
                if full.count('/') >= 5:
                    product_urls.add(full.rstrip('/'))
                    found += 1
        
        # Fallback: все ссылки в каталоге
        if found == 0:
            for link in soup.select('a[href*="/catalog/"]'):
                href = link.get('href')
                if href:
                    full = urljoin(BASE_URL, href)
                    if full.count('/') >= 5:
                        product_urls.add(full.rstrip('/'))
                        found += 1
        
        if found == 0:
            break
        
        # Проверяем пагинацию
        next_page = soup.select_one('.pagination .next:not(.disabled), .pagen .next:not(.disabled), a[rel="next"]')
        if not next_page:
            pages = soup.select('.pagination a, .pagen a')
            max_page = max([int(p.get_text()) for p in pages if p.get_text().isdigit()], default=1)
            if page >= max_page:
                break
        
        page += 1
        if page > 100:
            break
    
    return sorted(product_urls)

async def parse_product_page(session, url: str) -> Optional[Dict]:
    """Парсит страницу товара/услуги - ВСЁ содержимое"""
    status, html, final_url = await fetch(session, url)
    
    if status != 200:
        return {"url": url, "status": status, "error": f"HTTP {status}", "final_url": final_url}
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Базовые SEO
    title_tag = soup.select_one('title')
    title = clean_text(title_tag.get_text()) if title_tag else ""
    
    meta_desc_tag = soup.select_one('meta[name="description"]')
    meta_desc = clean_text(meta_desc_tag.get('content', '')) if meta_desc_tag else ""
    
    meta_kw_tag = soup.select_one('meta[name="keywords"]')
    meta_kw = clean_text(meta_kw_tag.get('content', '')) if meta_kw_tag else ""
    
    # H1
    h1_tags = soup.select('h1')
    h1_texts = [clean_text(h.get_text()) for h in h1_tags]
    
    # Все заголовки
    headings = []
    for h in soup.select('h1, h2, h3, h4, h5, h6'):
        headings.append({"level": h.name, "text": clean_text(h.get_text())})
    
    # Canonical
    canonical_tag = soup.select_one('link[rel="canonical"]')
    canonical = canonical_tag.get('href') if canonical_tag else None
    
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
    
    # Хлебные крошки
    breadcrumbs = []
    for el in soup.select('.bx-breadcrumb-item a, .breadcrumb a, [class*="breadcrumb"] a'):
        breadcrumbs.append({"text": clean_text(el.get_text()), "url": urljoin(BASE_URL, el.get('href', ''))})
    
    # Извлекаем данные из JCCatalogItem
    product_data = {}
    scripts = soup.find_all('script', text=re.compile(r'JCCatalogItem'))
    for script in scripts:
        if script.string:
            match = re.search(r'JCCatalogItem\(\s*(\{.*?\})\s*\)', script.string, re.DOTALL)
            if match:
                try:
                    js_text = match.group(1)
                    product_data['js_id'] = re.search(r"'ID':\s*'(\d+)'", js_text).group(1) if re.search(r"'ID':\s*'(\d+)'", js_text) else None
                    product_data['js_name'] = re.search(r"'NAME':\s*'([^']+)'", js_text).group(1) if re.search(r"'NAME':\s*'([^']+)'", js_text) else None
                except:
                    pass
    
    # Убираем скрипты/стили для текста
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    
    # Основной контент
    main_content = soup.select_one('.news-detail, .detail-text, .catalog-element, .catalog-element__content, [class*="detail"], article, main, .content')
    if main_content:
        visible_text = clean_text(main_content.get_text())
    else:
        visible_text = clean_text(soup.get_text())
    
    word_count = len(visible_text.split())
    em_dashes = visible_text.count('—')
    en_dashes = visible_text.count('–')
    
    # Изображения
    images = []
    for img in soup.select('img'):
        src = img.get('src') or img.get('data-src')
        alt = img.get('alt', '')
        if src:
            images.append({
                "src": urljoin(BASE_URL, src), 
                "alt": clean_text(alt), 
                "has_alt": bool(alt.strip()),
                "width": img.get('width'),
                "height": img.get('height')
            })
    
    # Цена
    price_text = ""
    for el in soup.select('.price, .calculator, [class*="price"], [class*="cost"], .news-card__type, .catalog-item__price, .catalog-item__price-old, .catalog-item__price-new'):
        price_text += " " + clean_text(el.get_text())
    price_info = extract_price(price_text)
    
    # Свойства товара
    properties = {}
    for prop_block in soup.select('.properties, .props, .catalog-item__props, [class*="prop"]'):
        for row in prop_block.select('tr, .row, .prop-row'):
            cells = row.select('td, .name, .value, .prop-name, .prop-value')
            if len(cells) >= 2:
                name = clean_text(cells[0].get_text())
                value = clean_text(cells[1].get_text())
                if name:
                    properties[name] = value
    
    for el in soup.select('[data-prop], [data-property]'):
        for attr, val in el.attrs.items():
            if attr.startswith('data-'):
                properties[attr[5:]] = val
    
    # Ссылки
    internal_links = []
    external_links = []
    for a in soup.select('a[href]'):
        href = a.get('href', '')
        if href.startswith('http'):
            if BASE_URL in href:
                internal_links.append({"url": href, "text": clean_text(a.get_text())})
            else:
                external_links.append({"url": href, "text": clean_text(a.get_text())})
        elif href.startswith('/'):
            internal_links.append({"url": urljoin(BASE_URL, href), "text": clean_text(a.get_text())})
    
    # Кнопки/формы
    has_calculator = bool(soup.select('.calculator, [class*="calculator"], #calculator, .js-calculator'))
    has_order_form = bool(soup.select('form[action*="order"], .order-form, [class*="order-form"], .js-order'))
    has_quick_order = bool(soup.select('.quick-order, [class*="quick-order"], .one-click, .js-quick-order'))
    has_buy_button = bool(soup.select('button[type="submit"][name*="buy"], .buy-btn, .js-buy, [class*="buy"]'))
    
    # Описание
    description = ""
    for sel in ['.preview-text, .description, .detail-text, [class*="description"], .catalog-item__description']:
        el = soup.select_one(sel)
        if el:
            description = clean_text(el.get_text())[:3000]
            break
    
    # Теги
    tags = []
    for el in soup.select('.tags a, .tag a, [class*="tag"] a, [itemprop="keywords"]'):
        tags.append(clean_text(el.get_text()))
    
    return {
        "url": url,
        "final_url": final_url,
        "status": 200,
        "title": title,
        "title_len": len(title),
        "meta_description": meta_desc,
        "meta_desc_len": len(meta_desc),
        "meta_keywords": meta_kw,
        "h1_count": len(h1_texts),
        "h1_texts": " | ".join(h1_texts),
        "headings_count": len(headings),
        "headings": headings,
        "canonical": canonical,
        "has_canonical": canonical is not None,
        "json_ld_count": len(json_ld),
        "json_ld": json_ld,
        "og_title": og.get('og:title', ''),
        "og_description": og.get('og:description', ''),
        "og_image": og.get('og:image', ''),
        "images_count": len(images),
        "images": images,
        "images_no_alt": sum(1 for i in images if not i['has_alt']),
        "word_count": word_count,
        "em_dashes": visible_text.count('—'),
        "en_dashes": visible_text.count('–'),
        "price_raw": extract_price(price_text)['raw'],
        "price_value": extract_price(price_text)['value'],
        "price_unit": extract_price(price_text)['unit'],
        "properties": properties,
        "breadcrumbs": breadcrumbs,
        "internal_links_count": len(internal_links),
        "external_links_count": len(external_links),
        "has_calculator": has_calculator,
        "has_order_form": has_order_form,
        "has_quick_order": has_quick_order,
        "has_buy_button": has_buy_button,
        "description_preview": description[:1000],
        "tags": ", ".join(tags),
        "visible_text_preview": visible_text[:2000],
        "parsed_at": datetime.now().isoformat(),
    }

async def get_all_categories(session) -> List[Dict]:
    """Получает все категории из меню"""
    status, html, _ = await fetch(session, BASE_URL)
    if status != 200:
        return []
    return parse_category_tree(html)

async def fetch(session, url):
    async with SEMAPHORE:
        await asyncio.sleep(REQUEST_DELAY)
        try:
            async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                html = await resp.text()
                return resp.status, html, str(resp.url)
        except Exception as e:
            return 0, str(e), url

async def get_all_product_urls_from_category(session, cat_url: str) -> List[str]:
    """Получает все URL товаров в категории (с пагинацией)"""
    product_urls = set()
    page = 1
    
    while True:
        paged_url = f"{cat_url}?PAGEN_1={page}" if page > 1 else cat_url
        status, html, final_url = await fetch(session, paged_url)
        
        if status != 200:
            break
        
        soup = BeautifulSoup(html, 'html.parser')
        
        found = 0
        for link in soup.select('a.news-card, a.catalog-item__link, .catalog-item a[href*="/catalog/"]'):
            href = link.get('href')
            if href and '/catalog/' in href:
                full = urljoin(BASE_URL, href)
                if full.count('/') >= 5:
                    product_urls.add(full.rstrip('/'))
                    found += 1
        
        if found == 0:
            for link in soup.select('a[href*="/catalog/"]'):
                href = link.get('href')
                if href:
                    full = urljoin(BASE_URL, href)
                    if full.count('/') >= 5:
                        product_urls.add(full.rstrip('/'))
                        found += 1
        
        if found == 0:
            break
        
        next_page = soup.select_one('.pagination .next:not(.disabled), .pagen .next:not(.disabled), a[rel="next"]')
        if not next_page:
            pages = soup.select('.pagination a, .pagen a')
            max_page = max([int(p.get_text()) for p in pages if p.get_text().isdigit()], default=1)
            if page >= max_page:
                break
        
        page += 1
        if page > 100:
            break
    
    return sorted(product_urls)

async def main():
    print(f"=== ЦИФРА18 Full Catalog Parser ===")
    print(f"Base: {BASE_URL}")
    print(f"Started: {datetime.now()}")
    print(f"Output: {OUTPUT_DIR}")
    
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), timeout=aiohttp.ClientTimeout(total=60)) as session:
        # 1. Получаем все категории из меню
        print("\n1. Получение категорий из меню...")
        status, html, _ = await fetch(session, BASE_URL)
        if status != 200:
            print("Failed to fetch main page")
            return
        categories = parse_category_tree(html)
        print(f"   Найдено категорий: {len(categories)}")
        
        all_categories = []
        for cat in categories:
            all_categories.append({"name": cat["name"], "url": cat["url"], "parent": None})
            for sub in cat["subcategories"]:
                all_categories.append({"name": f"{cat['name']} > {sub['name']}", "url": sub["url"], "parent": cat["name"]})
        
        print(f"   Всего категорий для парсинга: {len(all_categories)}")
        
        # 2. Для каждой категории собираем товары
        print("\n2. Сбор товаров по категориям...")
        all_products = {}
        total_products = 0
        
        for cat in all_categories:
            print(f"   Парсинг: {cat['name']} ({cat['url']})")
            products = await get_all_product_urls_from_category(session, cat['url'])
            all_products[cat['name']] = products
            total_products += len(products)
            print(f"     -> {len(products)} товаров")
        
        print(f"\n   Всего товаров/услуг: {total_products}")
        
        # 3. Аудит каждой страницы товара
        print("\n3. Аудит страниц товаров...")
        all_results = []
        tasks = []
        
        for cat_name, products in all_products.items():
            for prod_url in products:
                tasks.append(parse_product_page(session, prod_url))
        
        batch_size = 15
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i+batch_size]
            print(f"   Бач {i//batch_size + 1}/{(len(tasks)-1)//batch_size + 1} ({len(batch)} urls)...")
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            for r in batch_results:
                if isinstance(r, Exception):
                    all_results.append({"url": "ERROR", "error": str(r)})
                else:
                    all_results.append(r)
        
        # 4. Сохранение результатов
        date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
        
        json_path = OUTPUT_DIR / f"full_catalog_{date_str}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "parsed_at": datetime.now().isoformat(),
                "base_url": BASE_URL,
                "categories": categories,
                "total_categories": len(all_categories),
                "total_products": len(all_results),
                "products": all_results
            }, f, ensure_ascii=False, indent=2)
        
        # CSV
        csv_path = OUTPUT_DIR / f"full_catalog_{date_str}.csv"
        if all_results:
            fieldnames = list(all_results[0].keys())
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                for row in all_results:
                    row_copy = row.copy()
                    for k, v in row_copy.items():
                        if isinstance(v, (list, dict)):
                            row_copy[k] = json.dumps(v, ensure_ascii=False)
                    writer.writerow(row_copy)
        
        # Markdown отчёт
        md_path = OUTPUT_DIR / f"full_catalog_{date_str}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# Полный каталог ЦИФРА18 — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            f.write(f"**Базовый URL:** {BASE_URL}\n")
            f.write(f"**Дата парсинга:** {datetime.now()}\n")
            f.write(f"**Категорий:** {len(categories)}\n")
            f.write(f"**Подкатегорий:** {len(all_categories) - len(categories)}\n")
            f.write(f"**Всего товаров/услуг:** {len(all_results)}\n\n")
            
            f.write("## Структура каталога\n\n")
            for cat in categories:
                f.write(f"### {cat['name']} ({len(cat['subcategories'])} подкатегорий)\n")
                for sub in cat['subcategories']:
                    count = len(all_products.get(f"{cat['name']} > {sub['name']}", []))
                    f.write(f"- **{sub['name']}** — {count} товаров — {sub['url']}\n")
                f.write("\n")
            
            # Статистика проблем
            issues = {
                "Нет canonical": sum(1 for r in all_results if not r.get('has_canonical')),
                "Meta description = заглушка": sum(1 for r in all_results if r.get('meta_description') in ['Description', '']),
                "Meta description пуста/короткая (<50)": sum(1 for r in all_results if r.get('meta_desc_len', 0) < 50),
                "Нет H1 или >1 H1": sum(1 for r in all_results if r.get('h1_count', 0) != 1),
                "Нет JSON-LD": sum(1 for r in all_results if r.get('json_ld_count', 0) == 0),
                "Есть em-dash": sum(1 for r in all_results if r.get('em_dashes', 0) > 0),
                "Мало слов (<300)": sum(1 for r in all_results if r.get('word_count', 0) < 300),
                "Нет калькулятора": sum(1 for r in all_results if not r.get('has_calculator')),
                "Нет быстрой заявки": sum(1 for r in all_results if not r.get('has_quick_order')),
                "Картинок без alt": sum(r.get('images_no_alt', 0) for r in all_results),
                "Нет кнопки покупки": sum(1 for r in all_results if not r.get('has_buy_button')),
                "Нет цены": sum(1 for r in all_results if r.get('price_value') is None),
            }
            
            f.write("| Проблема | Кол-во страниц |\n|---|---|\n")
            for issue, count in sorted(issues.items(), key=lambda x: -x[1]):
                if count > 0:
                    f.write(f"| {issue} | {count} |\n")
            
            # Детали по товарам (первые 100)
            f.write("\n## Детали товаров (первые 100)\n\n")
            f.write("| URL | Title | H1 | Words | Price | JSON-LD | Calc | Quick | Buy | Issues |\n|---|---|---|---|---|---|---|---|---|---|\n")
            for r in all_results[:100]:
                issues_list = []
                if not r.get('has_canonical'): issues_list.append("no-canon")
                if r.get('meta_description') in ['Description', '']: issues_list.append("placeholder")
                if r.get('h1_count', 0) != 1: issues_list.append(f"h1:{r.get('h1_count',0)}")
                if r.get('json_ld_count', 0) == 0: issues_list.append("no-schema")
                if r.get('em_dashes', 0) > 0: issues_list.append("em-dash")
                if r.get('word_count', 0) < 300: issues_list.append("thin")
                if not r.get('has_calculator'): issues_list.append("no-calc")
                if not r.get('has_quick_order'): issues_list.append("no-quick")
                if not r.get('has_buy_button'): issues_list.append("no-buy")
                if r.get('price_value') is None: issues_list.append("no-price")
                
                title_short = r.get('title', '')[:40]
                h1_short = r.get('h1_texts', '')[:30]
                
                f.write(f"| {r.get('url','')[:55]} | {title_short} | {h1_short} | {r.get('word_count',0)} | {r.get('price_value','-')} {r.get('price_unit','')} | {'✅' if r.get('json_ld_count',0)>0 else '❌'} | {'✅' if r.get('has_calculator') else '❌'} | {'✅' if r.get('has_quick_order') else '❌'} | {'✅' if r.get('has_buy_button') else '❌'} | {', '.join(issues_list)} |\n")
            
            f.write("\n## Распределение товаров по категориям\n\n")
            f.write("| Категория | Товаров |\n|---|---|\n")
            for cat_name, products in sorted(all_products.items(), key=lambda x: -len(x[1])):
                f.write(f"| {cat_name} | {len(products)} |\n")
        
        print(f"\nJSON: {json_path}")
        print(f"CSV: {csv_path}")
        print(f"Markdown: {md_path}")
        print(f"\n=== Парсинг завершён: {datetime.now()} ===")

if __name__ == "__main__":
    asyncio.run(main())