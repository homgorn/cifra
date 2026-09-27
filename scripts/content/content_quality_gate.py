#!/usr/bin/env python3
"""
Content Quality Gate — Pre-publish QA (seo-helpful-content + GEO)
Вход: Черновик статьи (HTML/Markdown/текст) или URL опубликованной страницы
Выход: PASS/FAIL + детальный отчёт
"""

import sys
import re
import json
import argparse
from pathlib import Path
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class CheckResult:
    name: str
    passed: bool
    score: int
    max_score: int
    details: str
    severity: str  # critical, high, medium, low

class ContentQualityGate:
    def __init__(self, min_total_score: int = 80):
        self.min_total_score = min_total_score
        self.results: List[CheckResult] = []
    
    def add_result(self, name: str, passed: bool, score: int, max_score: int, details: str, severity: str = "medium"):
        self.results.append(CheckResult(name, passed, score, max_score, details, severity))
    
    def run_all(self, html: str, target_keyword: str = "", target_location: str = "") -> Dict[str, Any]:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Удаляем служебные теги
        for tag in soup(['script', 'style', 'noscript']):
            tag.decompose()
        
        visible_text = soup.get_text()
        visible_text = re.sub(r'\s+', ' ', visible_text).strip()
        word_count = len(visible_text.split())
        
        # === CRITICAL CHECKS (must pass) ===
        
        # 1. Meta title
        title_tag = soup.select_one('title')
        title = title_tag.get_text().strip() if title_tag else ""
        title_len = len(title)
        has_keyword_in_title = target_keyword.lower() in title.lower() if target_keyword else True
        title_ok = 30 <= title_len <= 60 and has_keyword_in_title
        self.add_result(
            "Meta Title", title_ok,
            10 if title_ok else 0, 10,
            f"Length: {title_len}, Keyword in title: {has_keyword_in_title}, Title: {title[:60]}",
            "critical" if not title_ok else "info"
        )
        
        # 2. Meta description
        meta_desc = soup.select_one('meta[name="description"]')
        desc = meta_desc.get('content', '').strip() if meta_desc else ""
        desc_len = len(desc)
        has_keyword_in_desc = target_keyword.lower() in desc.lower() if target_keyword else True
        desc_ok = 120 <= desc_len <= 160 and desc != "Description" and has_keyword_in_desc
        self.add_result(
            "Meta Description", desc_ok,
            10 if desc_ok else 0, 10,
            f"Length: {desc_len}, Not placeholder: {desc != 'Description'}, Keyword: {has_keyword_in_desc}, Desc: {desc[:80]}",
            "critical" if not desc_ok else "info"
        )
        
        # 3. H1 - exactly one, contains keyword + location
        h1s = soup.select('h1')
        h1_count = len(h1s)
        h1_text = clean_text(h1s[0].get_text()) if h1s else ""
        h1_has_keyword = target_keyword.lower() in h1_text.lower() if target_keyword else True
        h1_has_location = target_location.lower() in h1_text.lower() if target_location else True
        h1_ok = h1_count == 1 and h1_has_keyword and h1_has_location
        self.add_result(
            "H1 Tag", h1_ok,
            10 if h1_ok else 0, 10,
            f"Count: {h1_count}, Has keyword: {h1_has_keyword}, Has location: {h1_has_location}, H1: {h1_text[:60]}",
            "critical" if not h1_ok else "info"
        )
        
        # 4. Canonical
        canonical = soup.select_one('link[rel="canonical"]')
        canonical_ok = canonical is not None and canonical.get('href', '').startswith('http')
        self.add_result(
            "Canonical URL", canonical_ok,
            5 if canonical_ok else 0, 5,
            f"Present: {canonical_ok}, URL: {canonical.get('href', '')[:80] if canonical else 'missing'}",
            "critical" if not canonical_ok else "info"
        )
        
        # 5. JSON-LD Schema (Article/BlogPosting)
        has_article_schema = False
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('@type') in ['Article', 'BlogPosting', 'NewsArticle']:
                    has_article_schema = True
                    break
            except:
                pass
        self.add_result(
            "Article JSON-LD Schema", has_article_schema,
            10 if has_article_schema else 0, 10,
            f"Schema found: {has_article_schema}",
            "high" if not has_article_schema else "info"
        )
        
        # === HIGH PRIORITY CHECKS ===
        
        # 6. Word count (minimum 800 for articles, 1500 for pillar)
        min_words = 800
        wc_ok = word_count >= min_words
        self.add_result(
            f"Word Count (min {min_words})", wc_ok,
            10 if wc_ok else max(0, 10 * word_count // min_words),
            10,
            f"Words: {word_count}",
            "high" if not wc_ok else "info"
        )
        
        # 7. Heading structure (H1 → H2 → H3, no jumps)
        headings = []
        for h in soup.select('h1, h2, h3, h4, h5, h6'):
            level = int(h.name[1])
            headings.append((level, clean_text(h.get_text())))
        
        structure_ok = True
        prev_level = 0
        for level, text in headings:
            if level > prev_level + 1:
                structure_ok = False
                break
            prev_level = level
        
        h2_count = len([h for h in headings if h[0] == 2])
        h3_count = len([h for h in headings if h[0] == 3])
        has_question_h2 = any(h[1].strip().endswith('?') or h[1].lower().startswith(('как ', 'что ', 'почему ', 'где ', 'сколько ')) for h in headings if h[0] == 2)
        
        self.add_result(
            "Heading Structure", structure_ok and h2_count >= 3,
            10 if (structure_ok and h2_count >= 3) else 5,
            10,
            f"H1: {headings.count((1, ''))}, H2: {h2_count}, H3: {h3_count}, Question H2: {has_question_h2}, No jumps: {structure_ok}",
            "high" if not (structure_ok and h2_count >= 3) else "info"
        )
        
        # 8. Answer-first passages (Pillar 1 GEO)
        answer_first_score = 0
        question_h2s = 0
        for level, text in headings:
            if level == 2 and (text.strip().endswith('?') or text.lower().startswith(('как ', 'что ', 'почему ', 'где ', 'сколько '))):
                question_h2s += 1
                # Проверяем первый параграф после H2
                h2_tag = soup.select_one(f'h2:contains("{text[:30]}")')
                if h2_tag:
                    next_p = h2_tag.find_next('p')
                    if next_p:
                        p_words = len(clean_text(next_p.get_text()).split())
                        if 30 <= p_words <= 80:
                            answer_first_score += 1
        
        af_ok = answer_first_score >= 2
        self.add_result(
            "Answer-First Passages (GEO)", af_ok,
            10 if af_ok else answer_first_score * 3,
            10,
            f"Question H2s: {question_h2s}, Answer-first passages: {answer_first_score}",
            "high" if not af_ok else "info"
        )
        
        # 9. Stats & Quotes (Pillar 2 GEO)
        stats_patterns = [
            r'\d+[%₽]', r'\d+\s*(?:руб|шт|м|км|г|кг|мм|см)',
            r'по\s+(?:данным|ГОСТ|ИСО|исследован|статистик)',
            r'\d+\s*(?:из|из)\s*\d+',
        ]
        stats_count = sum(len(re.findall(p, visible_text, re.IGNORECASE)) for p in stats_patterns)
        stats_ok = stats_count >= 2
        self.add_result(
            "Stats & Quotes (GEO)", stats_ok,
            10 if stats_ok else stats_count * 3,
            10,
            f"Statistics found: {stats_count}",
            "high" if not stats_ok else "info"
        )
        
        # 10. Tables & Lists (Pillar 3 GEO)
        tables = len(soup.select('table'))
        lists = len(soup.select('ul, ol'))
        tl_ok = tables >= 1 or lists >= 2
        self.add_result(
            "Tables & Lists (GEO)", tl_ok,
            10 if tl_ok else (tables * 5 + lists * 2),
            10,
            f"Tables: {tables}, Lists (ul/ol): {lists}",
            "high" if not tl_ok else "info"
        )
        
        # 11. E-E-A-T Signals (Pillar 5 GEO)
        eat_score = 0
        eat_details = []
        
        # Author
        author_selectors = ['[itemprop="author"]', '.author', '[class*="author"]', '[rel="author"]', 'meta[name="author"]']
        has_author = any(soup.select(sel) for sel in author_selectors)
        if has_author: eat_score += 1; eat_details.append("Author")
        
        # Date modified
        date_selectors = ['[itemprop="dateModified"]', '[datetime]', '.date-modified', '[class*="date"]']
        has_date = any(soup.select(sel) for sel in date_selectors)
        if has_date: eat_score += 1; eat_details.append("DateModified")
        
        # Expert voice
        expert_patterns = ['эксперт', 'технолог', 'специалист', 'по опыту', 'наша практика', 'мы рекомендуем', 'по нашим данным']
        has_expert = any(p in visible_text.lower() for p in expert_patterns)
        if has_expert: eat_score += 1; eat_details.append("ExpertVoice")
        
        # Cases/examples
        case_patterns = ['кейс', 'пример', 'проект', 'заказчик', 'клиент', 'реализовали', 'выполнили']
        has_cases = any(p in visible_text.lower() for p in case_patterns)
        if has_cases: eat_score += 1; eat_details.append("Cases")
        
        # Production photos
        prod_photos = len(soup.select('img[alt*="производство"], img[alt*="станок"], img[alt*="цех"], img[alt*="печатн"]'))
        if prod_photos > 0: eat_score += 1; eat_details.append("ProductionPhotos")
        
        eat_ok = eat_score >= 3
        self.add_result(
            "E-E-A-T Signals (GEO)", eat_ok,
            10 if eat_ok else eat_score * 2,
            10,
            f"Score: {eat_score}/5, Signals: {', '.join(eat_details)}",
            "high" if not eat_ok else "info"
        )
        
        # === MEDIUM PRIORITY ===
        
        # 12. Images optimization
        images = soup.select('img')
        img_issues = []
        for img in images:
            alt = img.get('alt', '')
            src = img.get('src', '')
            if not alt.strip():
                img_issues.append("missing_alt")
            if not alt.strip() == "" and len(alt) < 5:
                img_issues.append("empty_alt")
            # lazyload check
            if not img.get('loading') == 'lazy':
                img_issues.append("no_lazyload")
            # width/height
            if not img.get('width') or not img.get('height'):
                img_issues.append("no_dimensions")
        
        img_ok = len(images) > 0 and len([i for i in img_issues if 'missing_alt' in i]) == 0
        self.add_result(
            "Images Optimization", img_ok,
            5 if img_ok else 2,
            5,
            f"Images: {len(images)}, Issues: {', '.join(set(img_issues)) if img_issues else 'none'}",
            "medium"
        )
        
        # 13. Internal links to money pages
        money_keywords = ['визитки', 'баннер', 'роллап', 'календар', 'листовк', 'пакет', 'мерч', 'сувенир', 'стенд', 'интерьер', 'широкоформат']
        internal_links = soup.select('a[href]')
        money_links = 0
        for link in internal_links:
            href = link.get('href', '')
            text = clean_text(link.get_text())
            if BITRIX_DOMAIN in href and any(kw in text.lower() or kw in href.lower() for kw in money_keywords):
                money_links += 1
        
        il_ok = money_links >= 3
        self.add_result(
            "Internal Links to Money Pages", il_ok,
            5 if il_ok else money_links,
            5,
            f"Total internal: {len(internal_links)}, Money page links: {money_links}",
            "medium"
        )
        
        # 14. Anti-AI-slop (em-dash check)
        em_dash_count = visible_text.count('—')
        en_dash_count = visible_text.count('–')
        ai_slop_ok = em_dash_count == 0 and en_dash_count == 0
        self.add_result(
            "Anti-AI-Slop (no em/en dashes)", ai_slop_ok,
            5 if ai_slop_ok else 0,
            5,
            f"Em-dashes: {em_dash_count}, En-dashes: {en_dash_count}",
            "medium"
        )
        
        # 15. FAQ Block + FAQPage Schema
        has_faq_section = bool(soup.select('[class*="faq"], [itemprop="mainEntity"]'))
        has_faq_schema = False
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('@type') == 'FAQPage':
                    has_faq_schema = True
                    break
            except:
                pass
        
        faq_ok = has_faq_section and has_faq_schema
        self.add_result(
            "FAQ Block + FAQPage Schema", faq_ok,
            5 if faq_ok else (3 if has_faq_section else 0),
            5,
            f"FAQ section: {has_faq_section}, FAQPage schema: {has_faq_schema}",
            "medium"
        )
        
        # === CALCULATE TOTAL ===
        total_score = sum(r.score for r in self.results)
        max_score = sum(r.max_score for r in self.results)
        passed = total_score >= self.min_total_score
        
        critical_failed = [r for r in self.results if r.severity == "critical" and not r.passed]
        high_failed = [r for r in self.results if r.severity == "high" and not r.passed]
        
        return {
            "passed": passed and len(critical_failed) == 0,
            "total_score": total_score,
            "max_score": max_score,
            "percentage": round(total_score / max_score * 100, 1) if max_score > 0 else 0,
            "critical_failed": len(critical_failed),
            "high_failed": len(high_failed),
            "results": [
                {
                    "check": r.name,
                    "passed": r.passed,
                    "score": f"{r.score}/{r.max_score}",
                    "details": r.details,
                    "severity": r.severity
                }
                for r in self.results
            ]
        }

def clean_text(text: str) -> str:
    if not text: return ""
    return re.sub(r'\s+', ' ', text.strip())

BITRIX_DOMAIN = "xn--18-6kc5a3bxam.xn--p1ai"

def main():
    parser = argparse.ArgumentParser(description="Content Quality Gate")
    parser.add_argument('input', nargs='?', help="HTML file or URL")
    parser.add_argument('--keyword', default='', help="Target keyword")
    parser.add_argument('--location', default='', help="Target location (e.g., Ижевск)")
    parser.add_argument('--min-score', type=int, default=80, help="Minimum total score to pass")
    parser.add_argument('--output', help="Output JSON file")
    args = parser.parse_args()
    
    if not args.input:
        parser.print_help()
        return
    
    # Load HTML
    if args.input.startswith('http'):
        import requests
        resp = requests.get(args.input, timeout=30)
        html = resp.text
    else:
        with open(args.input, 'r', encoding='utf-8') as f:
            html = f.read()
    
    # Run gate
    gate = ContentQualityGate(min_total_score=args.min_score)
    result = gate.run_all(html, args.keyword, args.location)
    
    # Output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"CONTENT QUALITY GATE: {'✅ PASS' if result['passed'] else '❌ FAIL'}")
    print(f"Score: {result['total_score']}/{result['max_score']} ({result['percentage']}%)")
    print(f"Critical failed: {result['critical_failed']}, High failed: {result['high_failed']}")
    print(f"{'='*60}\n")
    
    for r in result['results']:
        status = "✅" if r['passed'] else "❌"
        sev = f"[{r['severity'].upper()}]" if not r['passed'] else ""
        print(f"  {status} {r['check']}: {r['score']} {sev}")
        if not r['passed']:
            print(f"       → {r['details']}")
    
    # Exit code
    sys.exit(0 if result['passed'] else 1)

if __name__ == "__main__":
    main()