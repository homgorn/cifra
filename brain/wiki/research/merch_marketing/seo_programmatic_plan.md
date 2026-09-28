# SEO Programmatic Plan: ЦИФРА18 Merch

**Date:** 2026-09-12  
**Goal:** Deploy 200+ programmatic pages for merch + 200 for core services

---

## 🎯 Programmatic Strategy Overview

| Page Type | Count | Pattern | Target Keywords |
|---|---|---|---|
| **Service × City (Merch)** | 200 | /services/merch-{service}-{city}/ | "мерч с логотипом {city}", "футболки с логотипом {city}" |
| **Service × City (Print)** | 200 | /services/print-{service}-{city}/ | "печать визиток {city}", "баннеры {city}" |
| **Comparison Pages** | 50 | /compare/{a}-vs-{b}/ | "{a} vs {b}", "{a} или {b}" |
| **Alternatives Pages** | 30 | /alternatives/to-{competitor}/ | "альтернатива {competitor}", "аналоги {competitor}" |
| **Best-for Pages** | 30 | /best-{service}-for-{segment}/ | "лучшие {service} для {segment}" |
| **Material Pages** | 50 | /materials/{material}/ | "{material} для мерча", "свойства {material}" |
| **Glossary** | 200 | /glossary/{term}/ | "{term} определение", "{term} что это" |
| **FAQ Pages** | 100 | /faq/{question-slug}/ | "{question}?" |
| **Material Comparison** | 30 | /compare/materials/{a}-vs-{b}/ | "{material_a} vs {material_b}" |

**Total Target: ~860 programmatic pages**

---

## 🏙️ Service × City Matrix

### Top 20 Cities (by population + business activity)

| Rank | City | Population | Business Hub | Priority |
|---|---|---|---|---|
| 1 | Москва | 13M | National HQ | 🔴 Critical |
| 2 | Санкт-Петербург | 5.6M | Major HQ | 🔴 Critical |
| 3 | Новосибирск | 1.6M | Siberia hub | 🔴 Critical |
| 4 | Екатеринбург | 1.5M | Urals hub | 🔴 Critical |
| 5 | Казань | 1.3M | Volga hub | 🟠 High |
| 6 | Нижний Новгород | 1.2M | Volga hub | 🟠 High |
| 7 | Челябинск | 1.2M | Urals | 🟠 High |
| 8 | Омск | 1.1M | Siberia | 🟠 High |
| 9 | Самара | 1.1M | Volga | 🟠 High |
| 10 | Ростов-на-Дону | 1.1M | South | 🟠 High |
| 11 | Уфа | 1.1M | Bashkortostan | 🟡 Medium |
| 12 | Красноярск | 1.1M | Siberia | 🟡 Medium |
| 13 | Воронеж | 1.0M | Central | 🟡 Medium |
| 14 | Пермь | 1.0M | Urals | 🟡 Medium |
| 15 | Волгоград | 1.0M | South | 🟡 Medium |
| 16 | **Ижевск** | 0.6M | **Home base** | 🔴 Critical |
| 17 | Воткинск | 0.09M | Udmurtia | 🟢 Low |
| 18 | Глазов | 0.1M | Udmurtia | 🟢 Low |
| 19 | Сарапул | 0.1M | Udmurtia | 🟢 Low |
| 20 | Можега | 0.05M | Udmurtia | 🟢 Low |

### Services for Service×City (Top 10 by volume)

| Service | Search Volume (est.) | Competition | Priority |
|---|---|---|---|
| мерч с логотипом | 5,000 | High | 🔴 |
| футболки с логотипом | 3,500 | High | 🔴 |
| кружки с логотипом | 3,000 | High | 🔴 |
| толстовки с логотипом | 2,500 | High | 🔴 |
| рюкзаки с логотипом | 1,500 | Medium | 🟠 |
| сумки-тоты с логотипом | 1,200 | Medium | 🟠 |
| блокноты с логотипом | 1,000 | Medium | 🟠 |
| ручки с логотипом | 800 | Low | 🟢 |
| рюкзаки с логотипом | 1,500 | Medium | 🟠 |
| сумки-тоты с логотипом | 1,200 | Medium | 🟠 |

---

## 🛠 Technical Implementation

### Page Template Structure

```html
<!DOCTYPE html>
<html lang="ru">
<head>
 <title>{Service} в {City} - цены, сроки, доставка СДЭК | Цифра18</title>
  <meta name="description" content="{Service} в {City} от Цифра18: цены от {price}₽, сроки от 1 часа, доставка СДЭК по России. Калькулятор онлайн.">
  <link rel="canonical" href="https://cifra18.ru/services/{service}-{city}/" />
  
  <!-- JSON-LD -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Service",
    "name": "{Service} в {City}",
    "description": "Профессиональная {service} в {city} от типографии Цифра18. Сроки от 1 часа, доставка СДЭК по России.",
    "provider": {
      "@type": "LocalBusiness",
      "name": "Типография «Цифра»",
      "address": {
        "@type": "PostalAddress",
        "addressLocality": "Ижевск",
        "addressRegion": "Удмуртская Республика"
      }
    },
    "areaServed": {
      "@type": "City",
      "name": "{City}"
    },
    "offers": {
      "@type": "Offer",
      "price": "{price}",
      "priceCurrency": "RUB",
      "availability": "https://schema.org/InStock"
    }
  }
  </script>
</head>
<body>
  <!-- Hero -->
 <h1>{Service} в {City} - цены, сроки, заказать онлайн</h1>
  <p class="lead">Профессиональная {service} в {city} с доставкой СДЭК по России. Калькулятор онлайн, сроки от 1 часа.</p>
  
  <!-- Calculator Embed -->
  <div id="merch-calculator" data-service="{service}" data-city="{city}"></div>
  
  <!-- Benefits -->
  <h2>Почему выбирают Цифру18 для {service} в {city}</h2>
  <ul class="benefits">
 <li>Собственное производство в Ижевске - контроль качества</li>
 <li>Цены ниже маркетплейсов - без посредников</li>
 <li>СДЭК доставка по России - 1-3 дня</li>
 <li>Калькулятор онлайн - точная стоимость за 30 сек</li>
    <li>Помощь с макетом бесплатно</li>
  </ul>
  
  <!-- Calculator Widget -->
  <div id="calculator-widget" data-service="{service}" data-city="{city}"></div>
  
  <!-- FAQ -->
  <h2>Частые вопросы про {service} в {city}</h2>
  <div class="faq" itemscope itemtype="https://schema.org/FAQPage">
    <details itemprop="mainEntity" itemtype="https://schema.org/Question">
      <summary itemprop="name">Сколько стоит {service} в {city}?</summary>
      <div itemprop="acceptedAnswer" itemtype="https://schema.org/Answer">
        <p itemprop="text">Цена от {price}₽. Точную стоимость рассчитает калькулятор выше.</p>
      </div>
    </details>
    <details itemprop="mainEntity" itemtype="https://schema.org/Question">
      <summary itemprop="name">Какие сроки доставки в {city}?</summary>
      <div itemprop="acceptedAnswer" itemtype="https://schema.org/Answer">
 <p itemprop="text">СДЭК доставка 1-3 дня. Самовывоз из Ижевска - 1 час.</p>
      </div>
    </details>
    <details itemprop="mainEntity" itemtype="https://schema.org/Question">
      <summary itemprop="name">Как заказать {service} в {city}?</summary>
      <div itemprop="acceptedAnswer" itemtype="https://schema.org/Answer">
        <p itemprop="text">Рассчитайте стоимость в калькуляторе, нажмите "Заказать", менеджер свяжется за 15 мин.</p>
      </div>
    </details>
  </div>
  
  <!-- Local Content -->
  <h2>{Service} в {city}: особенности</h2>
  <p>Уникальный контент для {city} (адреса ПВЗ СДЭК, примеры заказов, кейсы клиентов из {city})</p>
  
  <!-- Internal Links -->
  <h3>Популярные услуги в {city}</h3>
  <ul>
    <li><a href="/services/merch-{service}-{city}/">{Service}</a></li>
    <li><a href="/services/print-{service}-{city}/">Печать {service}</a></li>
  </ul>
</body>
```

---

## 🔧 Generator Script (Python)

```python
# scripts/programmatic/generate_service_city.py

import jinja2
import csv
import json
from pathlib import Path

# Load data
with open('data/cities.csv') as f:
    cities = list(csv.DictReader(f))

with open('data/services.csv') as f:
    services = list(csv.DictReader(f))

# Load template
env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
template = env.get_template('service_city.html')

OUTPUT_DIR = Path('output/service_city')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for city in cities:
    for service in services:
        # Skip low-priority combinations
        if service['priority'] == 'Low' and city['priority'] == 'Low':
            continue
            
        context = {
            'service': service['name'],
            'service_slug': service['slug'],
            'city': city['name'],
            'city_slug': city['slug'],
            'price': service['base_price'],
            'city_pvz': city['pvz_addresses'][:3],
            'delivery_days': city['delivery_days'],
        }
        
        html = template.render(**context)
        
        output_path = OUTPUT_DIR / service['slug'] / f"{city['slug']}.html"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding='utf-8')

print(f"Generated {len(services) * len(cities)} pages")
```

### Data Files

**data/cities.csv**
```csv
name,slug,population,priority,delivery_days,pvz_addresses
Москва,moskva,13000000,Critical,1-2,"ПВЗ: Ленинский пр-т 50, Ховрино, Выхино"
Санкт-Петербург,ankt-peterburg,5600000,Critical,1-2,"ПВЗ: Невский пр-т 100, Московский пр-т 200"
Екатеринбург,ekaterinburg,1500000,Critical,2-3,"ПВЗ: ул. Ленина 50, ул. Малышева 30"
...
Ижевск,izhevsk,640000,Critical,1,"ПВЗ: ул. Пушкинская 50, ул. Карла Маркса 100"
```

**data/services.csv**
```csv
name,slug,base_price,priority
мерч с логотипом,merch-logo,1000,Critical
футболки с логотипом,tshirts-logo,850,Critical
кружки с логотипом,mugs-logo,550,Critical
толстовки с логотипом,hoodies-logo,2800,Critical
рюкзаки с логотипом,backpacks-logo,3500,High
сумки-тоты с логотипом,totes-logo,1200,Medium
блокноты с логотипом,notebooks-logo,650,Medium
ручки с логотипом,pens-logo,120,Low
```

---

## 📦 Content Generation Checklist

### Pre-Launch Checklist
- [ ] Cities CSV complete (20 cities)
- [ ] Services CSV complete (10 services)
- [ ] Template reviewed by SEO + Legal
- [ ] Schema.org validation passed
- [ ] Sitemap.xml generation script ready
- [ ] IndexNow API integration ready
- [ ] GSC / Яндекс.Вебмастер submission ready

### Generation Commands

```bash
# Generate all pages
python scripts/programmatic/generate_service_city.py

# Generate comparison pages
python scripts/programmatic/generate_comparisons.py

# Generate material pages
python scripts/programmatic/generate_materials.py

# Generate glossary
python scripts/programmatic/generate_glossary.py

# Generate FAQ pages
python scripts/programmatic/generate_faq.py

# Generate sitemap
python scripts/programmatic/generate_sitemap.py

# Submit to IndexNow
python scripts/utils/indexnow.py --all
```

---

## 📊 Quality Assurance

### Validation Rules
| Check | Tool | Threshold |
|---|---|---|
| **HTML Valid** | W3C Validator | 0 errors |
| **Schema.org Valid** | Google Rich Results Test | 0 errors |
| **Meta Title Length** | Custom script | 30-60 chars |
| **Meta Description Length** | Custom script | 120-160 chars |
| **H1 Present** | Custom script | 1 per page |
| **H1 Contains Keyword** | Custom script | Yes |
| **Canonical URL** | Custom script | Self-referencing |
| **Internal Links** | Custom script | ≥3 per page |
| **Images Have Alt** | Custom script | 100% |
| **Word Count** | Custom script | ≥800 words |
| **Schema.org Present** | Custom script | Yes |
| **Canonical Self-Ref** | Custom script | Yes |

### Automated QA Script
```python
# scripts/programmatic/qa_check.py
import requests
from bs4 import BeautifulSoup

def validate_page(url):
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    checks = {
        'status': resp.status_code == 200,
        'title_len': 30 <= len(soup.title.string) <= 60 if soup.title else False,
        'h1_count': len(soup.select('h1')) == 1,
        'h1_keyword': target_kw in soup.select_one('h1').text.lower(),
        'canonical': soup.select_one('link[rel="canonical"]')['href'] == url,
        'schema': len(soup.select('script[type="application/ld+json"]')) > 0,
        'images_alt': all(img.get('alt') for img in soup.select('img')),
        'internal_links': len(soup.select('a[href*="cifra18"]')) >= 3,
    }
    return checks
```

---

## 🚀 Deployment Pipeline

```yaml
# .github/workflows/programmatic.yml
name: Generate Programmatic Pages

on:
  schedule:
    - cron: '0 2 * * 1'  # Weekly Monday 2 AM
  workflow_dispatch:

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with: { python-version: '3.11' }
      - name: Install deps
        run: pip install -r requirements.txt
      - name: Generate pages
        run: |
          python scripts/programmatic/generate_service_city.py
          python scripts/programmatic/generate_comparisons.py
          python scripts/programmatic/generate_materials.py
      - name: QA Check
        run: python scripts/programmatic/qa_check.py
      - name: Deploy to staging
        run: rsync -av output/ staging.cifra18.ru/
      - name: IndexNow Ping
        run: python scripts/utils/indexnow.py --all
      - name: Submit sitemap to GSC
        run: python scripts/utils/gsc_submit.py
```

---

## 📊 Monitoring & Iteration

| Metric | Target | Review Cadence |
|---|---|---|
| **Pages Indexed** | 80% in 30 days | Weekly |
| **Organic Traffic** | +10% MoM | Weekly |
| **Top-10 Rankings** | 20% of pages | Monthly |
| **Conversion Rate** | >3% | Weekly |
| **Bounce Rate** | <60% | Weekly |
| **Avg Time on Page** | >2 min | Weekly |

### Iteration Loop
1. **Week 1-2:** Deploy first 100 pages (top 10 cities × 10 services)
2. **Week 3-4:** Analyze GSC data, fix indexing issues
3. **Month 2:** Deploy next 200 pages (remaining cities + comparisons)
4. **Month 3:** Deploy materials, glossary, FAQ
5. **Ongoing:** Monthly content refresh, quarterly full regeneration

---

*Generated: 2026-09-12*  
*Next Review: After Phase 0 deployment*