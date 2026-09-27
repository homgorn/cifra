#!/usr/bin/env python3
"""
Entity Extractor — извлечение сущностей из текста для GEO/SEO
Использует spaCy (ru_core_news_md) + правила для доменных сущностей
Вход: Текст/HTML/файл/папка с черновиками
Выход: JSON с сущностями + обновление brain/wiki/entities/
"""

import sys
import json
import re
import argparse
from pathlib import Path
from bs4 import BeautifulSoup
from collections import Counter
from typing import List, Dict, Set
from dataclasses import dataclass, asdict

try:
    import spacy
    NLP = spacy.load("ru_core_news_md")
    SPACY_AVAILABLE = True
except:
    SPACY_AVAILABLE = False
    print("Warning: spaCy not available, using regex-only extraction")

# Доменные сущности для полиграфии
DOMAIN_ENTITIES = {
    "services": {
        "keywords": [
            "визитки", "визитка", "листовки", "листовка", "баннер", "баннеры", 
            "роллап", "роллапы", "х-стенд", "хбаннер", "l-стенд", "штендер", "пресс-волл",
            "календарь", "календари", "пакет", "пакеты", "наклейка", "наклейки", "стикер",
            "мерч", "футболка", "кружка", "термос", "термостакан", "ручка", "блокнот",
            "сувенир", "сувенирка", "бейдж", "брелок", "значок", "магнит",
            "плоттерная резка", "ламинация", "фольгирование", "тиснение", "конгрев",
            "УФ печать", "УФ-печать", "белый тонер", "цифровая печать", "офсетная печать",
            "широкоформатная печать", "интерьерная печать", "фотообои", "фрески",
            "картины на холсте", "постер", "инженерная печать", "чертежи", "сканирование"
        ],
        "type": "Service"
    },
    "materials": {
        "keywords": [
            "крафт", "крафтовый", "дизайнерский картон", "дизайнерская бумага",
            "офсетная бумага", "меловка", "пленка", "пвх пленка", "полимерная пленка",
            "мономерная пленка", "ламинированная пленка", "бэклайт", "грейбек", "фронтлайн",
            "баннерная ткань", "флажная ткань", "полиэстер", "холст", "фотобумага",
            "самовсклеивающаяся бумага", "самоклеящаяся пленка", "пергамент", "трассировочная",
            "картон", "бумага", "пленка пвх", "mesh", "блэкаут"
        ],
        "type": "Material"
    },
    "equipment": {
        "keywords": [
            "hp indigo", "indigo", "epson", "canon", "ricoh", "xerox", "konica minolta",
            "плоттер", "плоттерная резка", "ламинатор", "фальцовка", "брошюровка",
            "тиснение", "конгрев", "фольгирование", "УФ-лакировка", "УФ лакировка",
            "гуillotina", "гильотина", "резак", "ксерокс", "рисо", "ризограф"
        ],
        "type": "Equipment"
    },
    "standards": {
        "keywords": [
            "гост", "iso", "iso 12647", "гост р", "технические требования", "требования к макету",
            "цветовой профиль", "cmyk", "rgb", "icc профиль", "proof", "контрактный пуф",
            "проверка макета", "препресс", "пре-пресс"
        ],
        "type": "Standard"
    },
    "locations": {
        "keywords": [
            "ижевск", "удмуртия", "удмуртская республика", "вохтинск", "глазов", "сарапул",
            "можега", "кизнер", "игра", "балезино", "юкамыш", "каракулино"
        ],
        "type": "Location"
    },
    "industries": {
        "keywords": [
            "хорека", "риелтор", "риелторы", "строй", "строительство", "медицина", "больница",
            "клиника", "образование", "школа", "университет", "ивент", "мероприятие",
            "ретейл", "ритейл", "магазин", "торговля", "агентство недвижимости"
        ],
        "type": "Industry"
    }
}

# Брендовые сущности
BRAND_ENTITIES = {
    "brand": ["цифра", "типография цифра", "ип Данилов", "Данилов Константин Леонидович"],
    "person": ["технолог", "дизайнер", "менеджер", "эксперт", "специалист"]
}

@dataclass
class Entity:
    text: str
    type: str
    subtype: str
    count: int
    contexts: List[str]
    normalized: str

def normalize_entity(text: str) -> str:
    """Нормализация названия сущности"""
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    # Удаляем предлоги в начале/конце
    text = re.sub(r'^(?:для|на|в|с|по|о|об|от|к|к)\s+', '', text)
    text = re.sub(r'\s+(?:для|на|в|с|по|о|об|от|к|к)$', '', text)
    return text

def extract_entities_regex(text: str) -> List[Entity]:
    """Извлечение через regex по доменным словарям"""
    entities = []
    text_lower = text.lower()
    
    for category, data in DOMAIN_ENTITIES.items():
        for keyword in data["keywords"]:
            # Ищем все вхождения
            pattern = re.compile(r'\b' + re.escape(keyword.lower()) + r'\b', re.IGNORECASE)
            matches = list(pattern.finditer(text_lower))
            if matches:
                contexts = []
                for m in matches[:3]:  # до 3 контекстов
                    start = max(0, m.start() - 100)
                    end = min(len(text), m.end() + 100)
                    context = text[start:end].strip()
                    contexts.append(context)
                
                entities.append(Entity(
                    text=keyword,
                    type=data["type"],
                    subtype=category,
                    count=len(matches),
                    contexts=contexts,
                    normalized=normalize_entity(keyword)
                ))
    
    # Брендовые
    for cat, keywords in BRAND_ENTITIES.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                entities.append(Entity(
                    text=kw,
                    type=cat.capitalize(),
                    subtype="brand" if cat == "brand" else "role",
                    count=text_lower.count(kw.lower()),
                    contexts=[],
                    normalized=normalize_entity(kw)
                ))
    
    return entities

def extract_entities_spacy(text: str) -> List[Entity]:
    """Извлечение через spaCy NER"""
    if not SPACY_AVAILABLE:
        return []
    
    doc = NLP(text)
    entities = []
    
    for ent in doc.ents:
        # Фильтруем только релевантные типы
        if ent.label_ in ['ORG', 'PERSON', 'LOC', 'GPE', 'PRODUCT', 'EVENT']:
            entities.append(Entity(
                text=ent.text,
                type=ent.label_,
                subtype="spacy_ner",
                count=1,
                contexts=[ent.sent.text[:200]],
                normalized=normalize_entity(ent.text)
            ))
    
    return entities

def merge_entities(regex_ents: List[Entity], spacy_ents: List[Entity]) -> List[Entity]:
    """Объединение и дедупликация"""
    merged = {}
    
    for ent in regex_ents + spacy_ents:
        key = (ent.normalized, ent.type)
        if key in merged:
            merged[key].count += ent.count
            merged[key].contexts.extend(ent.contexts)
        else:
            merged[key] = ent
    
    # Удаляем дубликаты контекстов
    for ent in merged.values():
        ent.contexts = list(dict.fromkeys(ent.contexts))[:5]
    
    return list(merged.values())

def extract_from_html(html: str) -> str:
    """Извлечение видимого текста из HTML"""
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style', 'noscript', 'header', 'footer', 'nav', 'aside']):
        tag.decompose()
    return soup.get_text()

def extract_from_file(filepath: Path) -> str:
    """Чтение файла (HTML, MD, TXT)"""
    content = filepath.read_text(encoding='utf-8')
    if filepath.suffix == '.html':
        return extract_from_html(content)
    return content

def main():
    parser = argparse.ArgumentParser(description="Entity Extractor для GEO/SEO")
    parser.add_argument('input', nargs='?', help="Файл/папка/URL/текст")
    parser.add_argument('--output', help="Выходной JSON файл")
    parser.add_argument('--update-wiki', action='store_true', help="Обновить brain/wiki/entities/")
    parser.add_argument('--min-count', type=int, default=2, help="Мин. кол-во вхождений для включения")
    args = parser.parse_args()
    
    if not args.input:
        parser.print_help()
        return
    
    # Сбор текста
    all_text = ""
    
    if args.input.startswith('http'):
        import requests
        resp = requests.get(args.input, timeout=30)
        all_text = extract_from_html(resp.text)
    elif Path(args.input).is_dir():
        for file in Path(args.input).rglob('*'):
            if file.suffix in ['.html', '.md', '.txt', '.json']:
                try:
                    all_text += "\n" + extract_from_file(file)
                except:
                    pass
    elif Path(args.input).exists():
        all_text = extract_from_file(Path(args.input))
    else:
        all_text = args.input  # прямой текст
    
    if not all_text.strip():
        print("No text to analyze")
        return
    
    print(f"Analyzing {len(all_text)} chars...")
    
    # Извлечение
    regex_ents = extract_entities_regex(all_text)
    spacy_ents = extract_entities_spacy(all_text) if SPACY_AVAILABLE else []
    all_entities = merge_entities(regex_ents, spacy_ents)
    
    # Фильтр по минимуму
    filtered = [e for e in all_entities if e.count >= args.min_count]
    
    # Сортировка: по типу, потом по частоте
    filtered.sort(key=lambda x: (x.type, -x.count))
    
    # Результат
    result = {
        "total_entities": len(filtered),
        "text_length": len(all_text),
        "spacy_used": SPACY_AVAILABLE,
        "entities": [asdict(e) for e in filtered]
    }
    
    # Группировка по типам для удобства
    by_type = {}
    for e in filtered:
        if e.type not in by_type:
            by_type[e.type] = []
        by_type[e.type].append(asdict(e))
    result["by_type"] = by_type
    
    # Вывод
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    
    # Печать сводки
    print(f"\n=== Entities Found: {len(filtered)} ===")
    for ent_type, ents in by_type.items():
        print(f"\n{ent_type} ({len(ents)}):")
        for e in ents[:10]:
            print(f"  {e['text']} (×{e['count']})")
        if len(ents) > 10:
            print(f"  ... and {len(ents) - 10} more")
    
    # Обновление wiki
    if args.update_wiki:
        wiki_dir = Path("brain/wiki/entities")
        wiki_dir.mkdir(parents=True, exist_ok=True)
        
        for ent_type, ents in by_type.items():
            # Загружаем существующий файл
            wiki_file = wiki_dir / f"{ent_type.lower()}.md"
            existing = {}
            if wiki_file.exists():
                # Парсим существующий markdown (упрощенно)
                pass
            
            # Пишем обновленный
            with open(wiki_file, 'w', encoding='utf-8') as f:
                f.write(f"# {ent_type} Entities\n\n")
                f.write(f"**Total:** {len(ents)}\n")
                f.write(f"**Updated:** {datetime.now().isoformat()}\n\n")
                f.write("| Entity | Count | Normalized |\n|---|---|---|\n")
                for e in ents:
                    f.write(f"| {e['text']} | {e['count']} | {e['normalized']} |\n")
        
        print(f"\nUpdated wiki files in {wiki_dir}")

if __name__ == "__main__":
    from datetime import datetime
    main()