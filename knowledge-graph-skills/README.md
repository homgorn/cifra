# Knowledge Graph Skills — Reusable Components

## Folder Structure
```
knowledge-graph-skills/
├── ontology/
│   ├── classes.ttl          # Классы сущностей (OWL/RDF)
│   ├── properties.ttl       # Свойства/предикаты
│   └── axioms.ttl           # Аксиомы/ограничения
├── entities/
│   ├── organization.ttl     # Организации
│   ├── services.ttl         # Услуги
│   ├── products.ttl         # Товары
│   ├── materials.ttl        # Материалы
│   ├── locations.ttl        # Локации
│   ├── industries.ttl       # Индустрии
│   └── competitors.ttl      # Конкуренты
├── triplets/
│   ├── offers.ttl           # Organization → Service
│   ├── hasMaterial.ttl      # Product → Material
│   ├── suitableFor.ttl      # Material/Service → Industry
│   └── deliversVia.ttl      # Org → DeliveryService
├── extraction/
│   ├── entity_extractor.py  # NER + rules
│   ├── intent_classifier.py # Intent classification
│   └── kg_builder.py        # Graph construction
├── programmatic/
│   ├── templates/           # Jinja2 templates
│   ├── generators/          # Page generators
│   └── validators/          # Schema validation
├── geo/
│   ├── llms_txt_generator.py
│   ├── citability_scorer.py
│   └── entity_consistency.py
└── tools/
    ├── sparql_queries.sparql
    ├── kg_validator.py
    └── kg_visualizer.py
```

## Quick Start

### 1. Install Dependencies
```bash
pip install rdflib spacy networkx pandas jsonld
python -m spacy download ru_core_news_lg
```

### 2. Load Ontology
```python
from rdflib import Graph
g = Graph()
g.parse("ontology/classes.ttl", format="ttl")
```

### 3. Extract Entities
```python
from extraction.entity_extractor import extract_entities
entities = extract_entities(text, domain="printing")
```

### 4. Build Knowledge Graph
```python
from extraction.kg_builder import build_kg
kg = build_kg(entities, triplets)
```

### 5. Query with SPARQL
```sparql
PREFIX cifra: <https://cifra18.ru/ontology/>
SELECT ?service ?material WHERE {
    ?service cifra:hasMaterial ?material .
    ?service cifra:offers cifra:Цифра18 .
}
```

### 6. Generate Programmatic Pages
```python
from programmatic.generators import generate_service_city_pages
pages = generate_service_city_pages(kg, services, cities)
```

### 7. GEO Optimization
```python
from geo.llms_txt_generator import generate_llms_txt
from geo.citability_scorer import score_page
llms_txt = generate_llms_txt(kg)
score = score_page(html_content)
```

## Key Files for Reuse

| File | Purpose | Reusable |
|------|---------|----------|
| `ontology/classes.ttl` | Domain ontology (classes, properties) | ✅ Full |
| `extraction/entity_extractor.py` | NER + domain rules | ✅ Full |
| `extraction/intent_classifier.py` | 4 intent types + modifiers | ✅ Full |
| `extraction/kg_builder.py` | Graph construction | ✅ Full |
| `programmatic/generators/` | Page generators | ✅ Adaptable |
| `geo/llms_txt_generator.py` | Auto llms.txt from KG | ✅ Full |
| `geo/citability_scorer.py` | 5-pillar GEO score | ✅ Full |
| `tools/sparql_queries.sparql` | Common queries | ✅ Full |

## Domain Adaptation

Для нового домена (например, недвижмость, авто, медицина):
1. Скопируйте `ontology/classes.ttl`
2. Замените `cifra:` namespace на свой
3. Добавьте/удалите классы под домен
4. Обновите domain dictionaries в `entity_extractor.py`
5. Переобучите intent classifier на своих данных

## Validation

```bash
# Validate ontology
python -m rdflib.validate ontology/classes.ttl

# Validate triplets
python tools/kg_validator.py --graph entities/ --shapes ontology/

# Test extraction
python -m extraction.entity_extractor --test "Визитки на крафте в Ижевске от 4.5 руб"
```

---

*Эта папка — портативный навык для построения knowledge graph в любых SEO/GEO проектах.*