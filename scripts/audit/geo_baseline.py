#!/usr/bin/env python3
"""
GEO Baseline — измерение citability score для ключевых страниц
Запуск: python3 scripts/audit/geo_baseline.py
Результат: brain/wiki/audits/geo_baseline_YYYY-MM-DD.md + JSON
"""

import asyncio
import aiohttp
import json
import re
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

BASE_URL = "https://xn--18-6kc5a3bxam.xn--p1ai"
OUTPUT_DIR = Path("brain/wiki/audits")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Ключевые страницы для GEO baseline (money pages + статьи)
TARGET_URLS = [
    f"{BASE_URL}/",
    f"{BASE_URL}/catalog/poligrafiya/vizitki/",
    f"{BASE_URL}/catalog/poligrafiya/vizitki/vizitki-na-krafte/",
    f"{BASE_URL}/catalog/shirokoformatnaya-pechat/",
    f"{BASE_URL}/catalog/suvenirnaya-produktsiya/",
    f"{BASE_URL}/catalog/mobilnye-stendy/",
    f"{BASE_URL}/about/",
    f"{BASE_URL}/news/",
]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Cifra18GEO/1.0)"}
SEMAPHORE = asyncio.Semaphore(3)

def clean_text(text: str) -> str:
    if not text: return ""
    return re.sub(r'\s+', ' ', text.strip())

def count_answer_first_passages(soup, visible_text):
    """Pillar 1: Answer-first passages — H2 as question, first paragraph as answer"""
    score = 0
    details = []
    for h2 in soup.select('h2'):
        h2_text = clean_text(h2.get_text())
        # Проверяем, похоже ли на вопрос
        is_question = any(h2_text.lower().startswith(q) for q in ['как ', 'что ', 'почему ', 'где ', 'когда ', 'сколько ', 'какой ', 'какая ', 'какие ']) or h2_text.endswith('?')
        if is_question:
            # Находим первый параграф после H2
            next_p = h2.find_next('p')
            if next_p:
                p_text = clean_text(next_p.get_text())
                word_count = len(p_text.split())
                if 30 <= word_count <= 80:  # Идеальный ответ 40-60 слов
                    score += 1
                    details.append({"h2": h2_text[:80], "answer_words": word_count})
    return min(score * 20, 20), details  # Max 20 points

def count_stats_quotes(soup, visible_text):
    """Pillar 2: Stats & Quotes — цифры с источниками"""
    # Паттерны: "X%", "X руб", "по данным", "по ГОСТ", "исследование показало", "X из Y"
    patterns = [
        r'\d+[%₽]',
        r'\d+\s*(?:руб|шт|м|км|г|кг|мм|см)',
        r'по\s+(?:данным|ГОСТ|ИСО|исследован|статистик)',
        r'\d+\s*(?:из|из)\s*\d+',
        r'\d+[.,]\d+',
    ]
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, visible_text, re.IGNORECASE))
    # Минимум 2 статистики = 20 баллов
    score = min(20, count * 5)
    return score, {"stats_found": count}

def count_tables_lists(soup):
    """Pillar 3: Tables & Lists"""
    tables = len(soup.select('table'))
    lists = len(soup.select('ul, ol'))
    has_definition_list = len(soup.select('dl')) > 0
    score = 0
    if tables >= 1: score += 10
    if lists >= 2: score += 10
    if has_definition_list: score += 5
    return min(score, 20), {"tables": tables, "lists": lists}

def count_question_headings(soup):
    """Pillar 4: Question Headings — H2/H3 как вопросы"""
    count = 0
    for h in soup.select('h2, h3'):
        text = clean_text(h.get_text()).lower()
        if any(text.startswith(q) for q in ['как ', 'что ', 'почему ', 'где ', 'когда ', 'сколько ', 'какой ', 'какая ', 'какие ', 'можно ли ', 'нужно ли ']) or text.endswith('?'):
            count += 1
    # Минимум 3 вопросительных заголовка = 20 баллов
    score = min(20, count * 5)
    return score, {"question_headings": count}

def count_eat_signals(soup, visible_text):
    """Pillar 5: E-E-A-T Signals"""
    score = 0
    details = {}
    # Author
    author_selectors = ['[itemprop="author"]', '.author', '[class*="author"]', '[rel="author"]', 'meta[name="author"]']
    has_author = any(soup.select(sel) for sel in author_selectors)
    if has_author: score += 5; details['author'] = True
    # Date modified
    date_selectors = ['[itemprop="dateModified"]', '[datetime]', '.date-modified', '[class*="date"]']
    has_date_modified = any(soup.select(sel) for sel in date_selectors)
    if has_date_modified: score += 5; details['date_modified'] = True
    # Expert quotes / references
    expert_patterns = ['эксперт', 'технолог', 'специалист', 'по опыту', 'наша практика', 'мы рекомендуем']
    has_expert = any(p in visible_text.lower() for p in expert_patterns)
    if has_expert: score += 5; details['expert_voice'] = True
    # Case studies / production photos
    case_patterns = ['кейс', 'пример', 'проект', 'заказчик', 'клиент']
    has_cases = any(p in visible_text.lower() for p in case_patterns)
    if has_cases: score += 5; details['cases'] = True
    return score, details

async def fetch(session, url):
    async with SEMAPHORE:
        try:
            async with session.get(url, headers=HEADERS, timeout=30) as resp:
                return resp.status, await resp.text()
        except Exception as e:
            return 0, str(e)

async def analyze_page(session, url):
    status, html = await fetch(session, url)
    if status != 200:
        return {"url": url, "status": status, "error": f"HTTP {status}", "score": 0}
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Удаляем скрипты/стили/навигацию
    for tag in soup(['script', 'style', 'noscript', 'header', 'footer', 'nav', 'aside']):
        tag.decompose()
    
    # Основной контент
    main = soup.select_one('main, article, .content, .main-content, [role="main"]')
    if main:
        visible_text = clean_text(main.get_text())
    else:
        visible_text = clean_text(soup.get_text())
    
    # 5 Pillars
    p1_score, p1_details = count_answer_first_passages(soup, visible_text)
    p2_score, p2_details = count_stats_quotes(soup, visible_text)
    p3_score, p3_details = count_tables_lists(soup)
    p4_score, p4_details = count_question_headings(soup)
    p5_score, p5_details = count_eat_signals(soup, visible_text)
    
    total = p1_score + p2_score + p3_score + p4_score + p5_score
    
    # Schema check
    has_article_schema = False
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and data.get('@type') in ['Article', 'BlogPosting', 'NewsArticle']:
                has_article_schema = True
                break
        except:
            pass
    
    return {
        "url": url,
        "status": status,
        "word_count": len(visible_text.split()),
        "total_score": total,
        "pillars": {
            "answer_first": {"score": p1_score, "details": p1_details},
            "stats_quotes": {"score": p2_score, "details": p2_details},
            "tables_lists": {"score": p3_score, "details": p3_details},
            "question_headings": {"score": p4_score, "details": p4_details},
            "eat_signals": {"score": p5_score, "details": p5_details}
        },
        "has_article_schema": has_article_schema,
        "has_canonical": bool(soup.select_one('link[rel="canonical"]')),
        "meta_description": clean_text(soup.select_one('meta[name="description"]') or {}).get('content', '')[:160],
        "h1": clean_text(soup.select_one('h1') or {}).get_text(),
        "h2_count": len(soup.select('h2')),
        "h3_count": len(soup.select('h3')),
        "images": len(soup.select('img')),
        "internal_links": len([a for a in soup.select('a[href]') if BASE_URL in a.get('href', '')]),
    }

async def main():
    print(f"=== ЦИФРА18 GEO Baseline ===")
    print(f"Target URLs: {len(TARGET_URLS)}")
    print(f"Started: {datetime.now()}")
    
    async with aiohttp.ClientSession() as session:
        tasks = [analyze_page(session, url) for url in TARGET_URLS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    processed = []
    for r in results:
        if isinstance(r, Exception):
            processed.append({"url": "ERROR", "error": str(r), "score": 0})
        else:
            processed.append(r)
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # JSON
    json_path = OUTPUT_DIR / f"geo_baseline_{date_str}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            "date": date_str,
            "base_url": BASE_URL,
            "pages_analyzed": len(processed),
            "avg_score": sum(r.get('total_score', 0) for r in processed) / len(processed) if processed else 0,
            "results": processed
        }, f, ensure_ascii=False, indent=2)
    
    # Markdown
    md_path = OUTPUT_DIR / f"geo_baseline_{date_str}.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# GEO Baseline — {date_str}\n\n")
        f.write(f"**Base URL:** {BASE_URL}\n")
        f.write(f"**Pages analyzed:** {len(processed)}\n")
        f.write(f"**Average score:** {sum(r.get('total_score', 0) for r in processed) / len(processed):.1f}/100\n\n")
        
        f.write("## 5-Pillar Scoring\n\n")
        f.write("| Pillar | Max | Description |\n|---|---|---|\n")
        f.write("| Answer-First | 20 | H2=question, 1st paragraph=direct answer (40-60 words) |\n")
        f.write("| Stats & Quotes | 20 | ≥2 statistics with sources (ГОСТ, internal data, expert) |\n")
        f.write("| Tables & Lists | 20 | ≥1 table OR ≥2 lists (ul/ol/dl) |\n")
        f.write("| Question Headings | 20 | ≥3 H2/H3 formulated as user questions |\n")
        f.write("| E-E-A-T Signals | 20 | Author, dateModified, expert voice, cases |\n\n")
        
        f.write("## Results by Page\n\n")
        f.write("| URL | Score | P1 | P2 | P3 | P4 | P5 | Words | Schema | Canonical | H1 |\n|---|---|---|---|---|---|---|---|---|---|---|\n")
        
        for r in processed:
            if 'error' in r:
                f.write(f"| {r.get('url', 'ERROR')} | ERROR | - | - | - | - | - | - | - | - | - |\n")
                continue
            
            p = r['pillars']
            f.write(f"| {r['url'][:60]} | **{r['total_score']}** | {p['answer_first']['score']} | {p['stats_quotes']['score']} | {p['tables_lists']['score']} | {p['question_headings']['score']} | {p['eat_signals']['score']} | {r['word_count']} | {'✅' if r['has_article_schema'] else '❌'} | {'✅' if r['has_canonical'] else '❌'} | {r['h1'][:40]} |\n")
        
        # Рекомендации
        f.write("\n## Recommendations\n\n")
        low_score = [r for r in processed if r.get('total_score', 0) < 60]
        if low_score:
            f.write(f"### Pages needing improvement ({len(low_score)}):\n\n")
            for r in low_score:
                f.write(f"- **{r['url']}** (score: {r['total_score']}/100)\n")
                p = r['pillars']
                if p['answer_first']['score'] < 20: f.write(f"  - Add answer-first passages (H2=question, direct answer)\n")
                if p['stats_quotes']['score'] < 20: f.write(f"  - Add statistics with sources\n")
                if p['tables_lists']['score'] < 20: f.write(f"  - Add comparison table or lists\n")
                if p['question_headings']['score'] < 20: f.write(f"  - Reformulate H2/H3 as questions\n")
                if p['eat_signals']['score'] < 20: f.write(f"  - Add author, dateModified, expert quotes, cases\n")
                if not r['has_article_schema']: f.write(f"  - Add Article JSON-LD schema\n")
    
    print(f"\nJSON: {json_path}")
    print(f"Markdown: {md_path}")
    print(f"Avg score: {sum(r.get('total_score', 0) for r in processed) / len(processed):.1f}/100")
    print(f"=== Completed: {datetime.now()} ===")

if __name__ == "__main__":
    asyncio.run(main())