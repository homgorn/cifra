#!/usr/bin/env python3
"""
GEO Tracking — измерение AI visibility
Еженедельно: брендовые упоминания, citability score, share of voice
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("brain/wiki/audits/monitoring")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BRAND_PROMPTS = [
    "Какие типографии в Ижевске печатают визитки быстро?",
    "Где заказать баннеры в Ижевске?",
    "Лучшая типография для мерча в Удмуртии",
    "Цифра типография Ижевск отзывы",
    "Стоимость печати листовок в Ижевск",
]

async def check_brand_mentions():
    """Ручной/полуавтомат: запускать промпты, парсить ответы"""
    results = {}
    # Для автоматизации нужен доступ к API или browser automation
    # MVP: ручной запуск раз в неделю, сохранение в JSON
    pass

def calculate_citability_score(page_data):
    """5-пилярный скор (0-100) по geo-visibility skill"""
    score = 0
    # Answer-first passages
    if page_data.get('has_answer_first'): score += 20
    # Stats & quotes
    if page_data.get('stats_count', 0) >= 2: score += 20
    # Tables & lists
    if page_data.get('has_tables') or page_data.get('has_lists'): score += 20
    # Question headings
    if page_data.get('question_headings', 0) >= 3: score += 20
    # E-E-A-T
    if page_data.get('has_author') and page_data.get('has_date_modified'): score += 20
    return score

def main():
    print(f"=== ЦИФРА18 GEO Tracker ===")
    print(f"Started: {datetime.now()}")
    
    # 1. Загрузить GA4 AI traffic (через API или ручной экспорт)
    # 2. Проверить брендовые упоминания (ручной/полуавтомат)
    # 3. Посчитать citability score для топ-20 страниц
    # 4. Сохранить отчёт
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    out_dir = Path("brain/wiki/audits/monitoring")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    report = {
        "date": date_str,
        "ai_traffic": {"sessions": 0, "sources": {}},
        "brand_mentions": {"chatgpt": 0, "perplexity": 0, "yandex": 0, "total": 0},
        "citability_scores": {},
        "avg_citability": 0,
    }
    
    # Сохранить
    out_dir = Path("brain/wiki/audits/monitoring")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    with open(out_dir / f"geo_report_{datetime.now().strftime('%Y-%m-%d')}.json", 'w') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    with open(out_dir / f"geo_report_{datetime.now().strftime('%Y-%m-%d')}.md", 'w') as f:
        f.write(f"# GEO Report — {datetime.now().strftime('%Y-%m-%d')}\n\n")
        f.write("## AI Traffic\n\n")
        f.write("- Sessions: 0\n")
        f.write("- Sources: {}\n\n")
        f.write("## Brand Mentions\n\n")
        f.write("- ChatGPT: 0\n")
        f.write("- Perplexity: 0\n")
        f.write("- Yandex: 0\n")
        f.write("- Total: 0\n\n")
        f.write("## Citability Scores\n\n")
        f.write("| URL | Score | P1 | P2 | P3 | P4 | P5 |\n|---|---|---|---|---|---|---|\n")
    
    print(f"GEO baseline saved to brain/wiki/audits/monitoring/geo_report_{datetime.now().strftime('%Y-%m-%d')}.md")
    print("GEO tracker template ready. Manual execution needed for AI prompts.")

if __name__ == "__main__":
    from datetime import datetime
    main()