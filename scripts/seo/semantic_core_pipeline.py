#!/usr/bin/env python3
"""
Free SEO Tools Pipeline - No API Keys Required
Uses only free/public APIs and web scraping
"""

import requests
import json
import re
import csv
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from collections import defaultdict
from collections import Counter
import urllib.parse

BASE_DIR = Path("/Users/user/Projects/цифра 2025/2026")
OUTPUT_DIR = Path("/Users/user/Projects/цифра 2025/2026/brain/wiki/research/keywords")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# ─── Free API Functions ──────────────────────────────────────────────

def google_suggest(query):
    """Google Autocomplete - free, no key needed"""
    url = "https://suggestqueries.google.com/complete/search"
    params = {"client": "chrome", "q": query}
    try:
        r = requests.get("https://suggestqueries.google.com/complete/search", 
                         params={"client": "chrome", "q": query}, timeout=5)
        data = r.json()
        return data[1] if len(data) > 1 else []
    except:
        return []

def yandex_suggest(query):
    """Yandex Suggest - free"""
    try:
        r = requests.get("https://suggest.yandex.ru/suggest-ff.cgi", 
                        params={"part": query, "format": "json"}, timeout=5)
        data = r.json()
        return data[1] if len(data) > 1 else []
    except:
        return []

def bing_suggest(query):
    """Bing Autosuggest - free"""
    try:
        r = requests.get("https://api.bing.com/osjson.aspx", 
                        params={"query": query}, timeout=5)
        data = r.json()
        return data[1] if len(data) > 1 else []
    except:
        return []

def duckduckgo_instant_answer(query):
    """DuckDuckGo Instant Answer API - free"""
    try:
        r = requests.get("https://api.duckduckgo.com/", 
                        params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}, timeout=10)
        return r.json()
    except:
        return {}

def yandex_suggest(query):
    """Yandex Suggest - free"""
    try:
        r = requests.get("https://suggest.yandex.ru/suggest-ff.cgi", 
                        params={"part": query, "format": "json"}, timeout=5)
        data = r.json()
        return data[1] if len(data) > 1 else []
    except:
        return []

def duckduckgo_html(query):
    """DuckDuckGo HTML scrape"""
    try:
        r = requests.get("https://html.duckduckgo.com/html/", 
                        params={"q": query}, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        results = []
        for result in soup.select('.result__snippet'):
            text = result.get_text(strip=True)
            if text:
                yield text[:200]
    except:
        return []

# ─── Intent Classification ────────────────────────────────────────

INTENT_PATTERNS = {
    "transactional": [
        r'\b(купить|заказать|цена|стоимость|заказать|купить|оплатить|оплата|доставка|сдэк|сдек|пвз|самовывоз)\b',
        r'\b(заказать|приобрести|купить|оформить)\b'
    ],
    "commercial": [
        r'\b(лучший|лучшие|топ|рейтинг|обзор|сравнение|vs|против|выбрать|выбор|альтернатива|аналог)\b',
        r'\b(цена|стоимость|ценообразование|прайс|прайс-лист|тариф)\b',
        r'\b(какой выбрать|что лучше|что выбрать)\b'
    ],
    "informational": [
        r'\b(как|как сделать|как подготовить|как выбрать|что такое|что такое|зачем|почему|где|когда|сколько)\b',
        r'\b(гайд|гайдлайн|инструкция|туториал|чек-лист|чек-лист|чек лист|инструкция|руководство|статья|обзор|гайд)\b',
        r'\b(требования|требования к|требования к макету|подготовка|подготовить)\b'
    ],
    "navigational": [
        r'\b(цифра18|цифра 18|типография цифра|цифра18|цифра 18)\b',
        r'\b(контур-фото|контур фото|принтио|prinio|ruprint)\b'
    ]
}

def classify_intent(keyword: str) -> str:
    kw_lower = keyword.lower()
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, kw_lower):
                return intent
    # Default heuristic
    if any(w in kw_lower for w in ['цена', 'стоимость', 'купить', 'заказать', 'заказать', 'купить']):
        return 'transactional'
    elif any(w in kw_lower for w in ['vs', 'vs', 'лучше', 'лучший', 'сравнение', 'альтернатива']):
        return 'commercial'
    elif any(w in kw_lower for w in ['как', 'что', 'почему', 'где', 'когда', 'сколько', 'гайд', 'инструкция']):
        return 'informational'
    else:
        return 'informational'

# ─── Keyword Collection ────────────────────────────────────────

def collect_all_keywords():
    """Collect keywords from all free sources"""
    all_keywords = set()
    
    # 1. Seed keywords from our catalog
    seed_keywords = [
        "визитки", "листовки", "баннеры", "роллапы", "кружки", "футболки", "худи",
        "блокноты", "календари", "пакеты", "бейджи", "брелки", "магниты",
        "наклейки", "стикеры", "ручки", "блокноты", "планировщики",
        "роллапы", "пресс-волл", "х-стенд", "л-стенд", "штендер",
        "баннеры", "пленка", "пленка пвх", "ткань", "меш",
        "кружки", "термосы", "термостаканы", "футболки", "худи",
        "бейджи", "брелки", "магниты", "наклейки", "стикеры",
        "плоттерная резка", "ламинация", "фольгирование", "тиснение",
        "круглы", "плоттерная резка", "уф печать", "фольгирование",
        "типография", "печатная", "печать", "полиграфия", "мерч",
        "визитки", "листовки", "баннеры", "календари", "мерч",
        "кружки", "футболки", "худи", "блокноты", "пакеты",
        "бейджи", "брелки", "магниты", "наклейки", "ручки",
        "блокноты", "планнеры", "дневники", "планнеры",
        "сувенирка", "мерч", "корп подарки", "новогодние подарки",
        "печать визиток", "печать листовок", "печать баннеров",
        "печать кружек", "печать футболок", "печать худи",
        "печатка визиток", "печатка листовок", "печатка баннеров",
        "типолрия ижевск", "типография ижевск", "ижевск типография",
        "печать ижевск", "цена печати ижевск", "типография ижевск цены",
        "визитки ижевск", "листовки ижевск", "баннеры ижевск",
        "кружки ижевск", "футболки ижевск", "худи ижевск",
        "мерч ижевск", "сувенирка ижевск", "кружки ижевск",
        "роллап ижевск", "баннеры ижевск", "стенды ижевск",
        "визитки на крафте", "визитки на дизайнерском картоне",
        "визитки на прозрачном пластике", "визитки премиум",
        "кружки с логотипом", "кружки сублимация", "кружки керамика",
        "термос с логотипом", "термокружка", "футболки с логотипом",
        "худи с логотипом", "бейджи с логотипом", "брелки с логотипом",
        "магниты с логотипом", "наклейки с логотипом", "стикеры с логотипом",
        "ручки с логотипом", "блокноты с логотипом", "блокноты а5",
        "планнеры", "дневники", "ежедневники", "планнеры",
        "календари 2025", "календари 2024", "квартальные календари",
        "подарки на новый год", "корп подарки", "новогодние подарки",
        "мерч для нг", "корп подарки", "корп мерч", "мерч для бизнеса",
        "мерч для ивентов", "мерч для выставок", "мерч для конференций",
        "welcome kit", "onboarding kit", "мерч для онбординга",
        "мерч для hr", "мерч для ивентов", "мерч для выставок",
        "бейджи с логотипом", "бейджи магнитные", "бейджи на заколку",
        "брелки", "брелоки", "магниты", "наклейки", "стикеры",
        "попсокеты", "попсокеты с логотипом", "попсокеты цена",
        "рюкзаки с логотипом", "сумки-тота", "шопперы",
        "кружки с логотипом", "кружки сублимация", "кружки керамика",
        "термосы с логотипом", "термокружки", "термостаканы",
        "футболки с логотипом", "футболки dtg", "футболки сублимация",
        "худи с логотипом", "толстовки с логотипом", "свитшоты",
        "бейджи", "бейджи магнитные", "бейджи на заколку", "бейджи на шпильке",
        "брелки", "брелоки", "ключницы", "магниты", "наклейки", "стикеры",
        "виниловые наклейки", "пвх наклейки", "бумажные наклейки",
        "ручки с логотипом", "ручки металл", "ручки пластик",
        "блокноты а5", "блокноты а6", "блокноты премиум",
        "планнеры", "планнеры а5", "дневники", "ежедневники",
        "календари", "квартальные календари", "настольные календари",
        "стеновые календари", "покет календари", "подарки календари",
        "пакеты", "крафт пакеты", "пакеты с логотипом", "бумажные пакеты",
        "подарочные пакеты", "подарочные коробки", "подарочная упаковка",
        "мерч для нг", "мерч для 8 марта", "мерч для 23 февраля",
        "мерч для 1 сентября", "мерч для выпускников",
        "мерч для ивентов", "мерч для выставок", "мерч для конференций",
        "мерч для тимбилдинга", "welcome kit", "onboarding kit",
        "корп мерч", "корп подарки", "корп мерч", "вип подарки",
        "премиум мерч", "vip мерч", "люкс мерч"
    ]
    
    return list(set(seeds))

def collect_keywords():
    """Collect keywords from all free sources"""
    print("Collecting keywords from free sources...")
    all_keywords = set()
    
    # 1. Seed keywords
    seeds = get_seed_keywords()
    print(f"Seed keywords: {len(seeds)}")
    
    # 2. Google Suggest
    print("Collecting from Google Suggest...")
    for seed in seeds[:30]:
        suggestions = google_suggest(seed)
        for s in suggestions:
            all_keywords.add(s.lower())
        time.sleep(0.1)
    
    # 2. Yandex Suggest
    print("Collecting from Yandex Suggest...")
    for seed in seeds[:30]:
        suggestions = yandex_suggest(seed)
        for s in suggestions:
            all_keywords.add(s.lower())
        time.sleep(0.1)
    
    # 3. Bing Suggest
    print("Collecting from Bing Suggest...")
    for seed in seeds[:30]:
        suggestions = bing_suggest(seed)
        for s in suggestions:
            all_keywords.add(s.lower())
        time.sleep(0.1)
    
    # 4. Yandex Suggest
    print("Collecting from Yandex Suggest...")
    for seed in seeds[:30]:
        suggestions = yandex_suggest(seed)
        for s in suggestions:
            all_keywords.add(s.lower())
        time.sleep(0.1)
    
    # 5. Bing Suggest
    print("Collecting from Bing Suggest...")
    for seed in seeds[:30]:
        suggestions = bing_suggest(seed)
        for s in suggestions:
            all_keywords.add(s.lower())
        time.sleep(0.1)
    
    # 5. DuckDuckGo Instant Answer
    print("Collecting from DuckDuckGo...")
    for seed in seeds[:20]:
        result = duckduckgo_instant_answer(seed)
        if result.get('Abstract'):
            all_keywords.add(result['Abstract'].lower())
        if result.get('RelatedTopics'):
            for topic in result['RelatedTopics'][:5]:
                if isinstance(topic, dict) and 'Text' in topic:
                    all_keywords.add(topic['Text'].lower())
    
    # 6. DuckDuckGo HTML scrape
    for seed in seeds[:10]:
        for snippet in duckduckgo_html(seed):
            # Extract potential keywords from snippets
            words = re.findall(r'\b[а-яa-z]{3,}\b', snippet.lower())
            for w in words:
                if len(w) > 3:
                    all_keywords.add(w)
    
    # 6. Google Suggest for seed + city combinations
    cities = ["ижевск", "москва", "санкт-петербург", "екатеринбург", "новосибирск", 
              "казань", "нижний новгород", "челябинск", "омск", "самара",
              "ростов-на-дону", "уфа", "красноярск", "воронеж", "пермь",
              "вольгоград", "сарапул", "глазов", "воткинск", "можега"]
    
    main_services = ["визитки", "листовки", "баннеры", "роллапы", "кружки", 
                     "футболки", "худи", "блокноты", "календари", "пакеты",
                     "мерч", "сувенирка", "бейджи", "брелки", "магниты",
                     "наклейки", "ручки", "блокноты", "планнеры", "дневники",
                     "пакеты", "кружки", "футболки", "худи", "толстовки",
                     "бейджи", "брелки", "магниты", "наклейки", "ручки",
                     "блокноты", "планнеры", "дневники", "планнеры",
                     "календари", "подарки", "мерч", "корп подарки"]
    
    print("Generating city+service combinations...")
    for city in ["ижевск", "москва", "санкт-петербург", "екатеринбург", "новосибирск", 
                  "казань", "нижний новгород", "челябинск", "омск", "самара"]:
        for service in ["визитки", "листовки", "баннеры", "роллапы", "кружки", 
                        "футболки", "худи", "блокноты", "календари", "пакеты"]:
            all_keywords.add(f"{service} {city}")
            all_keywords.add(f"{service} {city} цена")
            all_keywords.add(f"{service} {city} заказать")
            all_keywords.add(f"{service} {city} срочно")
    
    return all_keywords

# ─── Clustering & Classification ────────────────────────────────

def classify_intent(keyword):
    kw = keyword.lower()
    
    # Transactional
    if any(w in keyword.lower() for w in ['купить', 'заказать', 'цена', 'стоимость', 'заказать', 'купить', 'оплатить', 'оплата', 'доставка', 'сдэк', 'сдек', 'пвз', 'самовывоз']):
        return 'transactional'
    if any(w in keyword.lower() for w in ['заказать', 'приобрести', 'купить', 'оформить']):
        return 'transactional'
    
    # Commercial
    if any(w in keyword.lower() for w in ['лучший', 'лучшие', 'топ', 'рейтинг', 'обзор', 'сравнение', 'vs', 'против', 'выбрать', 'выбор', 'альтернатива', 'аналог']):
        return 'commercial'
    if any(w in keyword.lower() for w in ['цена', 'стоимость', 'ценообразование', 'прайс', 'прайс-лист', 'тариф']):
        return 'commercial'
    if any(w in keyword.lower() for w in ['какой выбрать', 'что лучше', 'что выбрать']):
        return 'commercial'
    if 'vs' in keyword.lower() or 'vs' in keyword.lower():
        return 'commercial'
    
    # Informational
    if any(w in keyword.lower() for w in ['как', 'как сделать', 'как подготовить', 'как выбрать', 'что такое', 'что такое', 'зачем', 'почему', 'где', 'когда', 'сколько']):
        return 'informational'
    if any(w in keyword.lower() for w in ['гайд', 'гайдлайн', 'инструкция', 'туториал', 'чек-лист', 'чек-лист', 'чек лист', 'инструкция', 'руководство', 'статья', 'обзор', 'гайд']):
        return 'informational'
    if any(w in keyword.lower() for w in ['требования', 'требования к', 'требования к макету', 'подготовка', 'подготовить']):
        return 'informational'
    
    # Navigational
    if any(w in keyword.lower() for w in ['цифра18', 'цифра 18', 'типография цифра', 'цифра18', 'цифра 18']):
        return 'navigational'
    if any(w in keyword.lower() for w in ['контур-фото', 'контур фото', 'принтио', 'prinio', 'ruprint']):
        return 'navigational'
    
    # Local
    if any(w in keyword.lower() for w in ['ижевск', 'москва', 'спб', 'санкт-петербург', 'екатеринбург', 'новосибирск', 'казань', 'нижний новгород', 'челябинск', 'омск', 'самара', 'ростов', 'уфа', 'красноярск', 'воронеж', 'пермь', 'волгоград', 'ижевск', 'воткинск', 'глазов', 'сарапул', 'можега']):
        return 'local'
    
    # Seasonal
    if any(w in keyword.lower() for w in ['новый год', '8 марта', '23 февраля', '1 сентября', 'выпускные', 'свадьба', 'лето', 'новогодн']):
        return 'seasonal'
    
    # B2B
    if any(w in keyword.lower() for w in ['опт', 'оптовые', 'b2b', 'корп', 'корпоративн', 'франчайзи', 'тендер']):
        return 'b2b'
    
    # Urgent
    if any(w in keyword.lower() for w in ['срочно', 'вчера', 'до завтра', 'сегодня', 'экспресс', '1 час', 'срочная']):
        return 'urgent'
    
    return 'informational'

# ─── Clustering ────────────────────────────────────────────────

def cluster_keywords(keywords):
    """Cluster keywords by subcategory + intent + city"""
    clusters = defaultdict(list)
    
    for kw in keywords:
        intent = classify_intent(kw)
        
        # Determine subcategory
        subcat = determine_subcategory(kw)
        
        # Extract cities
        cities = extract_cities(kw)
        
        # Create cluster key
        key = f"{intent}|{subcat}|{tuple(sorted(cities))}"
        
        clusters[key].append({
            'keyword': kw,
            'intent': classify_intent(kw),
            'subcategory': subcat,
            'cities': cities
        })
    
    # Build clusters
    clusters = []
    for cluster_id, (key, kws) in enumerate(sorted(clusters.items()), 1):
        if len(kws) < 2:
            continue
            
        subcat = kws[0]['subcategory'] if 'subcategory' in kws[0] else 'Other'
        intent = kws[0]['intent'] if 'intent' in kws[0] else 'unknown'
        cities = list(set(c for kw in kws for c in kw.get('cities', [])))
        
        # Determine content type
        intent = kws[0]['intent'] if 'intent' in kws[0] else 'informational'
        subcat = kws[0]['subcategory'] if 'subcategory' in kws[0] else 'Other'
        content_type = determine_content_type(intent, subcat)
        
        # Priority
        priority = calculate_priority(len(kws), kw_count=len(kws))
        
        cluster = {
            'cluster_id': len(clusters) + 1,
            'name': f"{subcat} | {intent} | {', '.join(cities[:3])}",
            'keywords': [kw for kw in kws],
            'main_keyword': max(kws, key=lambda x: len(x)) if kws else '',
            'intent': intent,
            'subcategory': subcat,
            'cities': cities,
            'total_volume': 0,  # Will be filled from Topvisor
            'avg_difficulty': 0,
            'top_competitors': [],
            'content_type': determine_content_type(intent, subcategory),
            'priority': priority
        }
        clusters.append(cluster)
    
    return sorted(clusters, key=lambda c: c['priority'])

def determine_subcategory(keyword):
    kw = keyword.lower()
    for subcat, seeds in SEED_KEYWORDS.items():
        for seed in seeds:
            if seed.lower() in kw:
                return subcat
    # Fallback
    kw = kw.lower()
    if any(w in kw for w in ['футболк', 'худи', 'толстовк', 'лонгслив', 'поло', 'одежда', 'одежд']):
        return 'Apparel'
    if any(w in kw for w in ['кружк', 'термос', 'термокружк', 'стакан', 'бокал', 'бутылк']):
        return 'Drinkware'
    if any(w in kw for w in ['рюкзак', 'сумк', 'тота', 'шоппер', 'бэг', 'баг']):
        return 'Bags & Packaging'
    if any(w in kw for w in ['блокнот', 'планнер', 'дневник', 'планнер', 'ежедневник', 'ручка', 'стикер', 'бейдж', 'магнит', 'ключниц']):
        return 'Office Supplies'
    if any(w in kw for w in ['пакет', 'коробк', 'упаковк', 'подарочн', 'пакет']):
        return 'Bags & Packaging'
    if any(w in kw for w in ['кружк', 'термос', 'стакан', 'бокал']):
        return 'Drinkware'
    if any(w in kw for w in ['футболк', 'худи', 'толстовк', 'лонгслив', 'поло', 'одежда']):
        return 'Apparel'
    if any(w in kw for w in ['баннер', 'баннер', 'роллап', 'пресс-волл', 'стенд', 'штенд', 'х-бан', 'л-бан']):
        return 'Wide Format'
    if any(w in kw for w in ['визитк', 'визитка']):
        return 'Business Cards'
    if any(w in kw for w in ['календар', 'планнер', 'дневник']):
        return 'Calendars'
    if any(w in kw for w in ['листовк', 'флаер', 'еврофлаер']):
        return 'Flyers'
    if any(w in kw for w in ['бейдж', 'бейджи', 'значок', 'нагруд']):
        return 'Badges'
    if any(w in kw for w in ['наклейк', 'стикер', 'наклей']):
        return 'Stickers'
    if any(w in kw for w in ['плоттер', 'резк', 'плоттерная']):
        return 'Plotter Cutting'
    if any(w in kw for w in ['ламинац', 'фольг', 'тиснен', 'конгрев', 'скруглен']):
        return 'Postpress'
    return 'Other'

def extract_cities(keyword):
    cities = []
    kw = keyword.lower()
    for city_name, slug, pop, priority in TARGET_CITIES:
        if city_name.lower() in kw or slug in kw:
            cities.append(city_name)
    return cities

def determine_content_type(intent, subcategory):
    if intent == 'transactional':
        return 'product' if subcategory in ['Apparel', 'Drinkware', 'Bags & Packaging'] else 'service'
    elif intent == 'commercial':
        return 'comparison' if 'vs' in subcategory.lower() else 'category'
    elif intent == 'informational':
        return 'guide' if 'как' in subcategory.lower() else 'article'
    return 'article'

def calculate_priority(volume, kw_count, difficulty):
    if volume > 10000 and difficulty < 30 and kw_count > 10:
        return 1
    elif volume > 1000 and difficulty < 50 and kw_count > 5:
        return 2
    elif volume > 100 and kw_count > 2:
        return 3
    return 4

# ─── Main Pipeline ────────────────────────────────────────────

async def run_semantic_core_pipeline():
    setup_logging()
    logging.info("=== Starting Semantic Core Pipeline ===")
    
    all_keywords = set()
    
    # 1. Seed keywords
    seeds = get_seed_keywords()
    logging.info(f"Seed keywords: {len(seeds)}")
    
    # 2. Google Suggest
    print("Collecting from Google Suggest...")
    for seed in seeds[:30]:
        suggestions = google_suggest(seed)
        for s in suggestions:
            all_keywords.add(s.lower())
        await asyncio.sleep(0.1)
    
    # 2. Yandex Suggest
    print("Collecting from Yandex Suggest...")
    for seed in seeds[:30]:
        suggestions = yandex_suggest(seed)
        for s in suggestions:
            all_keywords.add(s.lower())
        await asyncio.sleep(0.1)
    
    # 3. Bing Suggest
    print("Collecting from Bing Suggest...")
    for seed in seeds[:30]:
        suggestions = bing_suggest(seed)
        for s in suggestions:
            all_keywords.add(s.lower())
        await asyncio.sleep(0.1)
    
    # 3. Yandex Suggest
    print("Collecting from Yandex Suggest...")
    for seed in seeds[:30]:
        suggestions = yandex_suggest(seed)
        for s in suggestions:
            all_keywords.add(s.lower())
        await asyncio.sleep(0.1)
    
    # 4. Bing Suggest
    print("Collecting from Bing Suggest...")
    for seed in seeds[:30]:
        suggestions = bing_suggest(seed)
        for s in suggestions:
            all_keywords.add(s.lower())
        await asyncio.sleep(0.1)
    
    # 5. DuckDuckGo Instant Answer
    print("Collecting from DuckDuckGo...")
    for seed in seeds[:20]:
        result = duckduckgo_instant_answer(seed)
        if result.get('Abstract'):
            all_keywords.add(result['Abstract'].lower())
        if result.get('RelatedTopics'):
            for topic in result['RelatedTopics'][:5]:
                if isinstance(topic, dict) and 'Text' in topic:
                    all_keywords.add(topic['Text'].lower())
        await asyncio.sleep(0.1)
    
    # 6. DuckDuckGo HTML scrape
    for seed in seeds[:10]:
        for snippet in duckduckgo_html(seed):
            words = re.findall(r'\b[а-яa-z]{3,}\b', snippet.lower())
            for w in words:
                if len(w) > 3:
                    all_keywords.add(w)
    
    # 7. City + Service combinations
    cities = ["ижевск", "москва", "санкт-петербург", "екатеринбург", "новосибирск", 
              "казань", "нижний новгород", "челябинск", "омск", "самара", "ростов", "уфа", 
              "красноярск", "воронеж", "пермь", "волгоград", "ижевск", "воткинск", "глазов", "сарапул", "можега"]
    
    main_services = ["визитки", "листовки", "баннеры", "роллапы", "кружки", "футболки", "худи", "блокноты", "календари", "пакеты", "мерч", "сувенирка", "бейджи", "брелки", "магниты", "наклейки", "ручки", "блокноты", "планнеры", "дневники", "планнеры", "календари", "подарки", "мерч", "корп подарки", "корп мерч"]
    
    for city in ["ижевск", "москва", "санкт-петербург", "екатеринбург", "новосибирск", "казань", "нижний новгород", "челябинск", "омск", "самара", "ростов", "уфа", "красноярск", "воронеж", "пермь", "волгоград", "ижевск", "воткинск", "глазов", "сарапул", "можега"]:
        for service in ["визитки", "листовки", "баннеры", "роллапы", "кружки", "футболки", "худи", "блокноты", "календари", "пакеты"]:
            all_keywords.add(f"{service} {city}")
            all_keywords.add(f"{service} {city} цена")
            all_keywords.add(f"{service} {city} заказать")
            all_keywords.add(f"{service} {city} срочно")
    
    print(f"Total unique keywords: {len(all_keywords)}")
    
    # Convert to list of dicts for clustering
    keywords_list = []
    for kw in all_keywords:
        keywords_list.append({
            'keyword': kw,
            'intent': classify_intent(kw),
            'subcategory': determine_subcategory(kw),
            'cities': extract_cities(kw)
        })
    
    # Cluster
    clusters = cluster_keywords(keywords_list)
    
    # Save results
    date_str = datetime.now().strftime("%Y-%m-%d")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save clusters
    with open(OUTPUT_DIR / f"clusters_{date_str}.json", 'w', encoding='utf-8') as f:
        json.dump([asdict(c) for c in clusters], f, ensure_ascii=False, indent=2)
    
    # Save keywords
    with open(OUTPUT_DIR / f"keywords_{date_str}.json", 'w', encoding='utf-8') as f:
        json.dump([{'keyword': k, 'intent': classify_intent(k), 'subcategory': determine_subcategory(k), 'cities': extract_cities(k)} for k in all_keywords], f, ensure_ascii=False, indent=2)
    
    # Save CSV
    with open(f"keyword_map_{date_str}.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Keyword', 'Intent', 'Subcategory', 'Cities'])
        for kw in all_keywords:
            writer.writerow([kw, classify_intent(kw), determine_subcategory(kw), ', '.join(extract_cities(kw))])
    
    print(f"\nTotal keywords: {len(all_keywords)}")
    print(f"Total clusters: {len(clusters)}")
    print(f"Results saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    asyncio.run(main())