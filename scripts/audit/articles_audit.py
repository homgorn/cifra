#!/usr/bin/env python3
"""
Аудит 290 статей — ЦИФРА18
Запуск: python3 scripts/audit/articles_audit.py
Результат: brain/wiki/audits/content_audit_290_YYYY-MM-DD.md + CSV
"""

import asyncio
import aiohttp
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup

BASE_URL = "https://xn--18-6kc5a3bxam.xn--p1ai"
NEWS_URL = f"{BASE_URL}/news/"
OUTPUT_DIR = Path("brain/wiki/audits")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Cifra18Audit/1.0)"}
SEMAPHORE = asyncio.Semaphore(5)

def clean_text(text: str) -> str:
    if not text: return ""
    return re.sub(r'\s+', ' ', text.strip())

async def fetch(session, url):
    async with SEMAPHORE:
        try:
            async with session.get(url, headers=HEADERS, timeout=30) as resp:
                return resp.status, await resp.text()
        except Exception as e:
            return 0, str(e)

async def get_all_article_urls(session):
    """Собирает URL всех статей из /news/ с пагинацией"""
    urls = set()
    page = 1
    
    while True:
        paged_url = f"{NEWS_URL}?PAGEN_1={page}" if page > 1 else NEWS_URL
        status, html = await fetch(session, paged_url)
        if status != 200:
            break
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Ссылки на статьи (паттерны Битрикс news.list/detail)
        found = 0
        for link in soup.select('a[href*="/news/"]'):
            href = link.get('href')
            if href:
                full = urljoin(BASE_URL, href)
                # Статья обычно глубже: /news/YYYY-MM-DD-slug/ или /news/detail/ID/
                if full.count('/') > NEWS_URL.count('/') + 1:
                    urls.add(full.rstrip('/'))
                    found += 1
        
        if found == 0:
            break
        
        # Пагинация
        next_page = soup.select_one('.pagination .next, .pagen .next, a[rel="next"]')
        if not next_page:
            pages = soup.select('.pagination a, .pagen a')
            max_page = max([int(p.get_text()) for p in pages if p.get_text().isdigit()], default=1)
            if page >= max_page:
                break
        
        page += 1
        if page > 100:
            break
    
    return sorted(urls)

async def audit_article(session, url):
    status, html = await fetch(session, url)
    if status != 200:
        return {"url": url, "status": status, "error": f"HTTP {status}"}
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # SEO basics
    title = soup.select_one('title')
    title_text = clean_text(title.get_text()) if title else ""
    title_len = len(title_text)
    
    meta_desc = soup.select_one('meta[name="description"]')
    meta_desc_text = clean_text(meta_desc.get('content', '')) if meta_desc else ""
    meta_desc_len = len(meta_desc_text)
    
    # H1
    h1s = soup.select('h1')
    h1_texts = [clean_text(h.get_text()) for h in h1s]
    h1_count = len(h1_texts)
    
    # Заголовки структура
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
    
    # Article-specific JSON-LD
    article_schema = None
    for j in json_ld:
        if isinstance(j, dict) and j.get('@type') in ['Article', 'BlogPosting', 'NewsArticle']:
            article_schema = j
            break
    
    # Open Graph
    og = {}
    for meta in soup.select('meta[property^="og:"]'):
        og[meta.get('property')] = meta.get('content')
    
    # Картинки в статье
    article_images = []
    for img in soup.select('article img, .news-detail img, .detail-text img, [class*="content"] img'):
        src = img.get('src') or img.get('data-src')
        alt = img.get('alt', '')
        if src:
            article_images.append({"src": urljoin(BASE_URL, src), "alt": clean_text(alt), "has_alt": bool(alt.strip())})
    
    # Видимый текст статьи
    for tag in soup(['script', 'style', 'noscript', 'header', 'footer', 'nav', 'aside']):
        tag.decompose()
    
    # Ищем основной контент
    main_content = soup.select_one('article, .news-detail, .detail-text, [class*="content"], main')
    if main_content:
        visible_text = clean_text(main_content.get_text())
    else:
        visible_text = clean_text(soup.get_text())
    
    word_count = len(visible_text.split())
    
    # Em/En dashes
    em_dashes = visible_text.count('—')
    en_dashes = visible_text.count('–')
    
    # Дата публикации
    date_published = ""
    for sel in ['[itemprop="datePublished"]', '.news-date', '.date', 'time[datetime]', '[class*="date"]']:
        el = soup.select_one(sel)
        if el:
            date_published = el.get('datetime') or el.get('content') or clean_text(el.get_text())
            break
    
    # Автор
    author = ""
    for sel in ['[itemprop="author"]', '.author', '[class*="author"]']:
        el = soup.select_one(sel)
        if el:
            author = clean_text(el.get_text())
            break
    
    # Хлебные крошки
    breadcrumbs = []
    for el in soup.select('.breadcrumb a, .breadcrumbs a, [class*="breadcrumb"] a'):
        breadcrumbs.append(clean_text(el.get_text()))
    
    # Внутренние ссылки в теле статьи
    body_links = 0
    if main_content:
        body_links = len([a for a in main_content.select('a[href]') if BASE_URL in a.get('href', '')])
    
    # Связанные материалы / теги
    tags = []
    for el in soup.select('.tags a, .tag a, [class*="tag"] a, [itemprop="keywords"]'):
        tags.append(clean_text(el.get_text()))
    
    # Есть ли CTA / форма заявки в статье
    has_cta = bool(soup.select('article .button, .news-detail .button, [class*="content"] .button, form[action*="order"]'))
    
    # Структура: есть ли списки, таблицы, FAQ
    has_lists = bool(main_content and main_content.select('ul, ol'))
    has_tables = bool(main_content and main_content.select('table'))
    has_faq = bool(soup.select('[class*="faq"], [itemprop="mainEntity"]'))
    
    return {
        "url": url,
        "status": status,
        "title": title_text,
        "title_len": title_len,
        "meta_description": meta_desc_text,
        "meta_desc_len": meta_desc_len,
        "h1_count": h1_count,
        "h1_texts": " | ".join(h1_texts),
        "headings_count": len(headings),
        "headings_structure": json.dumps([h['level'] for h in headings], ensure_ascii=False),
        "canonical": canonical_href,
        "has_canonical": canonical_href is not None,
        "has_article_schema": article_schema is not None,
        "article_schema_type": article_schema.get('@type') if article_schema else None,
        "json_ld_count": len(json_ld),
        "og_title": og.get('og:title', ''),
        "og_description": og.get('og:description', ''),
        "og_image": og.get('og:image', ''),
        "images_count": len(article_images),
        "images_no_alt": sum(1 for i in article_images if not i['has_alt']),
        "word_count": word_count,
        "em_dashes": em_dashes,
        "en_dashes": en_dashes,
        "date_published": date_published,
        "author": author,
        "breadcrumbs": " > ".join(breadcrumbs),
        "body_internal_links": body_links,
        "tags": ", ".join(tags),
        "has_cta": has_cta,
        "has_lists": has_lists,
        "has_tables": has_tables,
        "has_faq": has_faq,
        "preview": visible_text[:500],
    }

async def main():
    print(f"=== ЦИФРА18 Articles Audit (290 статей) ===")
    print(f"News URL: {NEWS_URL}")
    print(f"Started: {datetime.now()}")
    
    async with aiohttp.ClientSession() as session:
        # 1. Собираем все URL статей
        print("\n1. Сбор URL статей...")
        articles = await get_all_article_urls(session)
        print(f"Найдено статей: {len(articles)}")
        
        if len(articles) == 0:
            print("Статьи не найдены! Проверьте селекторы.")
            return
        
        # 2. Аудит каждой статьи
        print("\n2. Аудит статей...")
        tasks = [audit_article(session, url) for url in articles]
        results = []
        
        batch_size = 30
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i+batch_size]
            print(f"  Бач {i//batch_size + 1}/{(len(tasks)-1)//batch_size + 1}...")
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            for r in batch_results:
                if isinstance(r, Exception):
                    results.append({"url": "ERROR", "error": str(r)})
                else:
                    results.append(r)
        
        # 3. Сохранение
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # CSV
        csv_path = OUTPUT_DIR / f"content_audit_290_{date_str}.csv"
        if results:
            fieldnames = list(results[0].keys())
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
            print(f"\nCSV: {csv_path}")
        
        # Markdown отчёт
        md_path = OUTPUT_DIR / f"content_audit_290_{date_str}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# Аудит 290 статей ЦИФРА18 — {date_str}\n\n")
            f.write(f"**Всего статей:** {len(results)}\n")
            f.write(f"**Дата аудита:** {datetime.now()}\n\n")
            
            # Сводка проблем
            issues = {
                "Нет canonical": sum(1 for r in results if not r.get('has_canonical')),
                "Meta description = Description": sum(1 for r in results if r.get('meta_description') == 'Description'),
                "Meta description пуста/короткая (<70)": sum(1 for r in results if r.get('meta_desc_len', 0) < 70),
                "Нет H1 или >1 H1": sum(1 for r in results if r.get('h1_count', 0) != 1),
                "Нет Article JSON-LD": sum(1 for r in results if not r.get('has_article_schema')),
                "Есть em-dash": sum(1 for r in results if r.get('em_dashes', 0) > 0),
                "Мало слов (<800)": sum(1 for r in results if r.get('word_count', 0) < 800),
                "Нет CTA": sum(1 for r in results if not r.get('has_cta')),
                "Нет внутренних ссылок в теле": sum(1 for r in results if r.get('body_internal_links', 0) == 0),
                "Нет списков/таблиц": sum(1 for r in results if not r.get('has_lists') and not r.get('has_tables')),
                "Картинок без alt": sum(r.get('images_no_alt', 0) for r in results),
                "Нет тегов": sum(1 for r in results if not r.get('tags')),
                "Нет даты публикации": sum(1 for r in results if not r.get('date_published')),
            }
            
            f.write("## Топ проблем\n\n")
            f.write("| Проблема | Кол-во |\n|---|---|\n")
            for issue, count in sorted(issues.items(), key=lambda x: -x[1]):
                if count > 0:
                    f.write(f"| {issue} | {count} |\n")
            
            # Статистика по словам
            word_counts = [r.get('word_count', 0) for r in results if r.get('word_count', 0) > 0]
            if word_counts:
                f.write(f"\n## Статистика объема\n")
                f.write(f"- Минимум: {min(word_counts)} слов\n")
                f.write(f"- Максимум: {max(word_counts)} слов\n")
                f.write(f"- Медиана: {sorted(word_counts)[len(word_counts)//2]} слов\n")
                f.write(f"- Среднее: {sum(word_counts)//len(word_counts)} слов\n")
            
            # Даты
            dates = [r.get('date_published', '') for r in results if r.get('date_published')]
            if dates:
                f.write(f"\n## Даты публикаций\n")
                f.write(f"- Самая старая: {min(dates)}\n")
                f.write(f"- Самая новая: {max(dates)}\n")
            
            # Детализация (первые 50)
            f.write("\n## Детали по статьям (первые 50)\n\n")
            f.write("| URL | Title | H1 | Words | Schema | CTA | Links | Tags | Issues |\n|---|---|---|---|---|---|---|---|---|\n")
            for r in results[:50]:
                issues_list = []
                if not r.get('has_canonical'): issues_list.append("no-canon")
                if r.get('meta_description') == 'Description': issues_list.append("placeholder")
                if r.get('h1_count', 0) != 1: issues_list.append(f"h1:{r.get('h1_count',0)}")
                if not r.get('has_article_schema'): issues_list.append("no-schema")
                if r.get('em_dashes', 0) > 0: issues_list.append("em-dash")
                if r.get('word_count', 0) < 800: issues_list.append("thin")
                if not r.get('has_cta'): issues_list.append("no-cta")
                if r.get('body_internal_links', 0) == 0: issues_list.append("no-links")
                
                title_short = r.get('title', '')[:40]
                h1_short = r.get('h1_texts', '')[:30]
                tags_short = r.get('tags', '')[:30]
                
                f.write(f"| {r.get('url','')[:50]} | {title_short} | {h1_short} | {r.get('word_count',0)} | {'✅' if r.get('has_article_schema') else '❌'} | {'✅' if r.get('has_cta') else '❌'} | {r.get('body_internal_links',0)} | {tags_short} | {', '.join(issues_list)} |\n")
            
            # Кандидаты на переработку (thin content, нет схемы, нет CTA)
            candidates = [r for r in results if r.get('word_count', 0) < 800 and not r.get('has_article_schema') and not r.get('has_cta')]
            f.write(f"\n## Кандидаты на переработку/удаление ({len(candidates)} шт.)\n\n")
            for r in candidates[:30]:
                f.write(f"- {r.get('url')} — {r.get('word_count',0)} слов, H1: {r.get('h1_texts', '')[:50]}\n")
        
        print(f"\nMarkdown: {md_path}")
        print(f"\n=== Аудит статей завершён: {datetime.now()} ===")

if __name__ == "__main__":
    asyncio.run(main())