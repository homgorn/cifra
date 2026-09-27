#!/usr/bin/env python3
"""
WP Import Prepare — подготовка CSV для WP All Import
Источники: Битрикс экспорт (статьи 290 + каталог 300+)
Выход: CSV готовые для WP All Import + ACF mapping
"""

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

BITRIX_EXPORT_DIR = Path("data/exports/bitrix/latest")
OUTPUT_DIR = Path("data/exports/wp_import")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def clean_html(html: str) -> str:
    """Очистка Битрикс HTML для WP"""
    if not html:
        return ""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Удаляем Битрикс-специфичные классы/атрибуты
    for tag in soup.find_all(True):
        # Оставляем только базовые атрибуты
        allowed_attrs = ['href', 'src', 'alt', 'title', 'width', 'height', 'class', 'id']
        attrs = dict(tag.attrs)
        for attr in attrs:
            if attr not in allowed_attrs:
                del tag[attr]
        # Удаляем пустые классы
        if tag.get('class') == ['']:
            del tag['class']
    
    # Удаляем Битрикс-обертки
    for wrapper in soup.select('[class*="bitrix"], [class*="bx-"], [id*="bx_"]'):
        wrapper.unwrap()
    
    return str(soup)

def clean_text(text: str) -> str:
    if not text: return ""
    # Заменяем em-dash на запятые (анти-AI-slop)
    text = text.replace('—', ', ').replace('–', ', ')
    # Нормализуем пробелы
    text = re.sub(r'\s+', ' ', text.strip())
    return text

def extract_faq(detail_text: str) -> list:
    """Пытается извлечь FAQ из текста статьи"""
    faq = []
    soup = BeautifulSoup(detail_text, 'html.parser')
    # Ищем паттерны Q&A
    for tag in soup.select('h2, h3, h4, strong, b'):
        q_text = clean_text(tag.get_text())
        if q_text.endswith('?') or q_text.lower().startswith(('как ', 'что ', 'почему ', 'где ', 'сколько ')):
            # Следующий параграф = ответ
            next_p = tag.find_next('p')
            if next_p:
                a_text = clean_text(next_p.get_text())
                if 30 <= len(a_text.split()) <= 200:
                    faq.append({"question": q_text, "answer": a_text})
    return faq[:5]  # макс 5

def prepare_articles_csv():
    """Подготовка CSV для статей (Posts)"""
    input_file = BITRIX_EXPORT_DIR / "articles_290.csv"
    if not input_file.exists():
        print(f"Input not found: {input_file}")
        return
    
    output_file = OUTPUT_DIR / f"wp_articles_{datetime.now().strftime('%Y-%m-%d')}.csv"
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.DictReader(infile)
        fieldnames = [
            'post_title', 'post_name', 'post_content', 'post_excerpt',
            'post_status', 'post_type', 'post_date', 'post_author',
            'tax_input_category', 'tax_input_post_tag',
            'meta__yoast_wpseo_title', 'meta__yoast_wpseo_metadesc',
            'meta__yoast_wpseo_focuskw',
            'acf_original_bitrix_url', 'acf_bitrix_id', 'acf_original_date',
            'acf_faq_json', 'acf_author_name', 'acf_author_role',
            'acf_seo_canonical', 'acf_og_image',
        ]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        
        count = 0
        for row in reader:
            # Очистка контента
            content = clean_html(row.get('detail_text', ''))
            excerpt = clean_text(row.get('preview_text', ''))[:300]
            
            # FAQ из контента
            faq = extract_faq(row.get('detail_text', ''))
            
            # Slug из URL
            url = row.get('detail_page_url', '')
            slug = url.rstrip('/').split('/')[-1] if url else row.get('name', '')[:60]
            slug = re.sub(r'[^a-zA-Z0-9а-яА-ЯёЁ\-]', '-', slug).lower()
            
            # Tags
            tags = row.get('tags', '').replace(';', ',').replace('|', ',')
            
            writer.writerow({
                'post_title': clean_text(row.get('name', '')),
                'post_name': slug[:200],
                'post_content': content,
                'post_excerpt': excerpt,
                'post_status': 'publish' if row.get('active', '').lower() in ('true', '1', 'yes') else 'draft',
                'post_type': 'post',
                'post_date': row.get('date_create', datetime.now().isoformat()),
                'post_author': 1,  # admin
                'tax_input_category': 'blog',  # или маппинг из section
                'tax_input_post_tag': tags,
                'meta__yoast_wpseo_title': clean_text(row.get('seo_title', ''))[:60],
                'meta__yoast_wpseo_metadesc': clean_text(row.get('seo_description', ''))[:160],
                'meta__yoast_wpseo_focuskw': '',  # заполнить после keyword research
                'acf_original_bitrix_url': url,
                'acf_bitrix_id': row.get('id', ''),
                'acf_original_date': row.get('date_create', ''),
                'acf_faq_json': json.dumps(faq, ensure_ascii=False) if faq else '',
                'acf_author_name': row.get('author', 'Типография «Цифра»'),
                'acf_author_role': 'Технолог / Эксперт',
                'acf_seo_canonical': row.get('canonical_url', url),
                'acf_og_image': '',  # заполнить при наличии featured image
            })
            count += 1
    
    print(f"Articles CSV: {output_file} ({count} rows)")

def prepare_programmatic_pages():
    """Подготовка CSV для программатик страниц из каталога"""
    input_file = BITRIX_EXPORT_DIR / "catalog_full.csv"
    if not input_file.exists():
        print(f"Input not found: {input_file}")
        return
    
    # Service × City pages
    output_file = OUTPUT_DIR / f"wp_service_city_{datetime.now().strftime('%Y-%m-%d')}.csv"
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.DictReader(infile)
        
        # Города для локальных лендингов
        CITIES = [
            {"name": "Ижевск", "slug": "izhevsk", "population": 640000},
            {"name": "Воткинск", "slug": "votkinsk", "population": 90000},
            {"name": "Глазов", "slug": "glazov", "population": 100000},
            {"name": "Сарапул", "slug": "sarapul", "population": 90000},
            {"name": "Можега", "slug": "mozhga", "population": 45000},
            {"name": "Кизнер", "slug": "kizner", "population": 15000},
            {"name": "Игра", "slug": "igra", "population": 10000},
            {"name": "Балезино", "slug": "balezino", "population": 12000},
            {"name": "Юкамыш", "slug": "yukamish", "population": 8000},
            {"name": "Каракулино", "slug": "karakulino", "population": 7000},
        ]
        
        # Топ-20 услуг для локальных страниц (по частотности/маржинальности)
        TOP_SERVICES = [
            "vizitki", "listovki", "bannery", "rollyapy", "kalendari",
            "pakety", "naklejki", "merch", "fotoknigi", "standy",
            "interernaya-pechat", "shirokoformatnaya-pechat", "souvenirnaya-produkciya",
            "polygrafiya", "inkzhernaya-pechat", "plotternaya-rezka",
            "uf-pechat", "laminirovanie", "folgirovanie", "breloki"
        ]
        
        fieldnames = [
            'post_title', 'post_name', 'post_content', 'post_excerpt',
            'post_status', 'post_type', 'post_author',
            'tax_input_service_category', 'tax_input_city',
            'meta__yoast_wpseo_title', 'meta__yoast_wpseo_metadesc',
            'meta__yoast_wpseo_focuskw',
            'acf_service_ref', 'acf_city_ref', 'acf_price_from', 'acf_production_time',
            'acf_delivery_available', 'acf_pickup_available',
            'acf_local_content', 'acf_schema_type',
        ]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Строим карту услуг из каталога
        services_map = {}
        for row in reader:
            props = {}
            try:
                props = json.loads(row.get('properties', '{}'))
            except:
                pass
            
            section_path = row.get('section_path', '')
            if 'Визитки' in section_path and 'vizitki' not in services_map:
                services_map['vizitki'] = {'name': 'Печать визиток', 'url': row['detail_page_url'], 'price': row['price'], 'props': props}
            elif 'Листовк' in section_path and 'listovki' not in services_map:
                services_map['listovki'] = {'name': 'Печать листовок', 'url': row['detail_page_url'], 'price': row['price'], 'props': props}
            elif 'Баннер' in section_path and 'bannery' not in services_map:
                services_map['bannery'] = {'name': 'Печать баннеров', 'url': row['detail_page_url'], 'price': row['price'], 'props': props}
            elif 'Роллап' in section_path and 'rollyapy' not in services_map:
                services_map['rollyapy'] = {'name': 'Роллапы', 'url': row['detail_page_url'], 'price': row['price'], 'props': props}
            elif 'Календар' in section_path and 'kalendari' not in services_map:
                services_map['kalendari'] = {'name': 'Печать календарей', 'url': row['detail_page_url'], 'price': row['price'], 'props': props}
            # ... добавить остальные
        
        count = 0
        for service_key in TOP_SERVICES:
            if service_key not in services_map:
                continue
            svc = services_map[service_key]
            for city in CITIES:
                # Генерируем уникальный контент для каждой комбинации
                title = f"{svc['name']} в {city['name']} — цены, сроки, заказать онлайн | Цифра18"
                slug = f"{service_key}-{city['slug']}"
                
                # Локализованный контент (шаблон + уникальные данные)
                content = f"""<!-- wp:heading --><h2>Печать {svc['name'].lower()} в {city['name']}</h2><!-- /wp:heading -->
<!-- wp:paragraph --><p>Типография «Цифра» предлагает {svc['name'].lower()} в {city['name']} с доставкой и самовывозом. Рассчитайте стоимость онлайн за 1 минуту.</p><!-- /wp:paragraph -->
<!-- wp:heading --><h3>Почему заказывают у нас</h3><!-- /wp:heading -->
<!-- wp:list --><ul><li>Собственное производство в Ижевске</li><li>Сроки от 1 часа для малых тиражей</li><li>Доставка по {city['name']} и Удмуртии</li><li>Калькулятор цен онлайн</li></ul><!-- /wp:list -->
<!-- wp:heading --><h3>Цены и сроки</h3><!-- /wp:heading -->
<!-- wp:paragraph --><p>От {svc.get('price', 'N/A')} руб. Зависит от тиража, материала, срочности. Точную стоимость узнайте в калькуляторе.</p><!-- /wp:paragraph -->"""
                
                writer.writerow({
                    'post_title': title,
                    'post_name': slug,
                    'post_content': content,
                    'post_excerpt': f"{svc['name']} в {city['name']}: калькулятор цен, доставка, примеры работ.",
                    'post_status': 'publish',
                    'post_type': 'service_page',  # CPT
                    'post_author': 1,
                    'tax_input_service_category': svc['name'],
                    'tax_input_city': city['name'],
                    'meta__yoast_wpseo_title': title[:60],
                    'meta__yoast_wpseo_metadesc': f"{svc['name']} в {city['name']} от {svc.get('price', 'N/A')} руб. Сроки от 1 часа. Доставка по Удмуртии. Рассчитать онлайн."[:160],
                    'meta__yoast_wpseo_focuskw': f"{svc['name'].lower()} {city['name'].lower()}",
                    'acf_service_ref': svc['url'],
                    'acf_city_ref': city['slug'],
                    'acf_price_from': svc.get('price', 0),
                    'acf_production_time': 'от 1 часа',
                    'acf_delivery_available': 'yes',
                    'acf_pickup_available': 'yes',
                    'acf_local_content': f"Доставка в {city['name']} 1-2 дня. Самовывоз: Ижевск, ул. 7-я Подлесная, 34.",
                    'acf_schema_type': 'Service',
                })
                count += 1
        
        print(f"Service×City CSV: {output_file} ({count} rows)")

def prepare_materials_csv():
    """Подготовка CSV для страниц материалов (справочник)"""
    input_file = BITRIX_EXPORT_DIR / "catalog_full.csv"
    if not input_file.exists():
        return
    
    output_file = OUTPUT_DIR / f"wp_materials_{datetime.now().strftime('%Y-%m-%d')}.csv"
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.DictReader(infile)
        
        fieldnames = [
            'post_title', 'post_name', 'post_content', 'post_excerpt',
            'post_status', 'post_type', 'post_author',
            'tax_input_material_category',
            'meta__yoast_wpseo_title', 'meta__yoast_wpseo_metadesc',
            'acf_material_specs_json', 'acf_suitable_for', 'acf_price_range',
            'acf_schema_type',
        ]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Собираем уникальные материалы из свойств товаров
        materials = {}
        for row in reader:
            try:
                props = json.loads(row.get('properties', '{}'))
            except:
                continue
            
            material = props.get('MATERIAL') or props.get('material') or props.get('Материал')
            if material and material not in materials:
                materials[material] = {
                    'name': material,
                    'example_url': row['detail_page_url'],
                    'example_props': props
                }
        
        count = 0
        for mat_key, mat in materials.items():
            writer.writerow({
                'post_title': f"Материал: {mat['name']} — свойства, применение, цены",
                'post_name': f"material-{mat_key.lower().replace(' ', '-').replace('/', '-')}",
                'post_content': f"<!-- wp:paragraph --><p>Подробное описание материала {mat['name']}: свойства, виды, применение в полиграфии, примеры работ, цены.</p><!-- /wp:paragraph -->",
                'post_excerpt': f"Справочник: {mat['name']} — характеристики, для чего подходит, примеры работ.",
                'post_status': 'publish',
                'post_type': 'material',  # CPT
                'post_author': 1,
                'tax_input_material_category': 'paper' if 'крафт' in mat_key.lower() or 'бумага' in mat_key.lower() or 'картон' in mat_key.lower() else 'film',
                'meta__yoast_wpseo_title': f"{mat['name']} — свойства, применение, цены | Цифра18",
                'meta__yoast_wpseo_metadesc': f"Материал {mat['name']}: характеристики, для какой полиграфии подходит, примеры работ. Цены и заказ онлайн."[:160],
                'acf_material_specs_json': json.dumps(mat['example_props'], ensure_ascii=False),
                'acf_suitable_for': 'Визитки, листовки, пакеты, календари',
                'acf_price_range': 'от 1 руб/лист',
                'acf_schema_type': 'Product',
            })
            count += 1
        
        print(f"Materials CSV: {output_file} ({count} rows)")

def main():
    print("=== WP Import Prepare ===")
    
    if not BITRIX_EXPORT_DIR.exists():
        print(f"Export directory not found: {BITRIX_EXPORT_DIR}")
        print("Run bitrix_catalog_export.py first")
        return
    
    prepare_articles_csv()
    prepare_programmatic_pages()
    prepare_materials_csv()
    
    print(f"\nOutput dir: {OUTPUT_DIR}")
    print("Next: Import via WP All Import with ACF mapping")

if __name__ == "__main__":
    main()