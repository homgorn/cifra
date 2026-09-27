# ЦИФРА18 Knowledge Graph — Main Index

## Overview
Complete knowledge graph for Типография «Цифра» (цифра18.рф, Ижевск) covering all services, products, materials, equipment, locations, competitors, industries, intents, and relationships across the Russian market.

**Version:** 1.0  
**Last Updated:** 2026-09-13  
**Entities:** 239 unique entities  
**Triplets:** 387 relationships  
**Format:** JSON-LD (Turtle-compatible)

---

## File Structure

```
brain/wiki/knowledge_graph/
├── cifra18_knowledge_graph.ttl      # Main combined KG (239 entities)
├── cifra18_triplets.ttl             # Explicit triplet relationships (387)
├── entities/
│   ├── company.ttl                  # Company entity (1)
│   ├── materials.ttl                # Materials (18)
│   ├── equipment.ttl                # Equipment (11)
│   ├── locations.ttl                # Locations (22)
│   ├── industries.ttl               # Industries (14)
│   ├── competitors.ttl              # Competitors (20)
│   ├── poligrafiya_services.ttl     # Print services (26)
│   ├── shirokoformatnaya_services.ttl # Wide-format services (10)
│   ├── suvenirnaya_services.ttl     # Merch/souvenir services (26)
│   ├── inzhenernaya_services.ttl    # Engineering print (5)
│   ├── interer_services.ttl         # Interior print (6)
│   ├── mobilnye_stendy_services.ttl # Mobile stands (10)
│   ├── stendy_services.ttl          # Stands/displays (5)
│   └── interer_stendy_mobilnye.ttl  # Combined (16, deduped)
├── ontologies/
│   └── printing_ontology.ttl        # Core ontology (65 classes/properties)
├── intents/
│   └── intents.ttl                  # Search intents (9)
├── sparql_endpoint_config.md        # Fuseki/SPARQL setup
├── graph_visualization_config.md    # Neo4j/Gephi/Graphistry setup
└── graphrag_config.md               # GraphRAG for support bot
```

---

## Entity Summary

| Category | Count | Key Entities |
|----------|-------|--------------|
| **Company** | 1 | ЦИФРА18 (ИП Данилов К.Л.) |
| **Services** | 83 | Digital/Offset/Wide-format/Merch/Engineering/Interior/Mobile |
| **Materials** | 18 | Kraft, Designer cardboard, PVC films, Banner fabric, Polyester, Canvas, Organic cotton, rPET, Stainless steel, Ceramic, Wood, Offset paper |
| **Equipment** | 11 | HP Indigo, Heidelberg, HP Latex, Mimaki, Roland, Epson, Canon, Konica Minolta, Ricoh, Xerox |
| **Locations** | 22 | Izhevsk (HQ), Udmurtia cities (4), Top-15 Russian cities (Moscow, SPb, Ekb, etc.) |
| **Industries** | 14 | HoReCa, Real Estate, Construction, Medical, Education, Industrial, Retail, Automotive, Finance, Beauty, Events, Pharma |
| **Competitors** | 17 | Printio, RuPrint, Printful, Printback, Canva Print, Яндекс.Услуги, Авито, 2ГИС, Профи.ру, Контур-Фото, Vaston, SMART, КанцПарк, Максимум, Удмуртпечать, Принт-Экспресс, Копи-центр Документ |
| **Intents** | 9 | Informational, Commercial, Transactional, Navigational, Local, Seasonal, B2B, Urgent |

---

## Core Ontology Classes

```
cifra:PrintShop
├── cifra:hasService → cifra:Service
│   ├── cifra:PrintService
│   │   ├── cifra:DigitalPrintService
│   │   ├── cifra:OffsetPrintService
│   │   └── cifra:WideFormatService
│   ├── cifra:MerchService
│   ├── cifra:EngineeringPrintService
│   ├── cifra:PostPressService
│   └── cifra:MobileStandService
├── cifra:produces → cifra:Product
├── cifra:hasEquipment → cifra:Equipment
├── cifra:locatedIn → cifra:Location
├── cifra:deliversVia → cifra:Delivery
└── cifra:competesWith → cifra:Competitor
```

### Key Properties
- `cifra:hasPrintMethod` → DigitalPrint, OffsetPrint, EcoSolventPrint, LatexPrint, UVPrint, SublimationPrint, DTG, WhiteTonerPrint, LaserEngraving
- `cifra:hasMaterial` → 18 material entities
- `cifra:hasFinishing` → Lamination, Foiling, Embossing, DieCutting, UVVarnish, Folding, Binding
- `cifra:hasMinTirage` / `cifra:hasMaxTirage` → Integer
- `cifra:hasMaxFormat` → String (e.g., "3.2м", "B2+", "A0")
- `cifra:hasProductionTime` → ISO Duration (e.g., "PT1H", "P1D")

---

## Relationship Summary (387 Triplets)

| Predicate | Count | Description |
|-----------|-------|-------------|
| `cifra:hasService` | 83 | Company → Services |
| `cifra:produces` | 7 | Company → Products |
| `cifra:hasEquipment` | 11 | Company → Equipment |
| `cifra:locatedIn` | 1 | Company → Izhevsk |
| `cifra:deliversVia` | 1 | Company → SDEK |
| `cifra:competesWith` | 17 | Company → Competitors |
| `cifra:hasMaterial` | 89 | Service → Materials |
| `cifra:hasPrintMethod` | 78 | Service → Print Methods |
| `cifra:hasFinishing` | 23 | Service/Product → Finishing |
| `cifra:hasMinTirage` | 67 | Service → Min Tirage |
| `cifra:hasMaxTirage` | 12 | Service → Max Tirage |
| `cifra:hasMaxFormat` | 45 | Service → Max Format |
| `cifra:hasProductionTime` | 18 | Service → Production Time |
| `cifra:materialType` | 18 | Material → Type |
| `cifra:hasSdekPVZ` | 21 | Location → SDEK Coverage |
| `cifra:deliveryDaysFromIzhevsk` | 19 | Location → Delivery Days |
| `cifra:typicalServices` | 14 | Industry → Services |
| `cifra:strengths` / `cifra:weaknesses` | 34 | Competitor → SWOT |
| `cifra:hasAPI` / `cifra:hasSDEKIntegration` | 12 | Competitor → Capabilities |

---

## Key Business Insights from Graph

### Service Coverage Matrix
| Service Category | Methods | Materials | Min Tirage | Max Format | Production Time |
|-----------------|---------|-----------|------------|------------|-----------------|
| Digital Print | HP Indigo (ElectroInk) | Coated, Uncoated, Textured, Synthetic, Self-adhesive, Metallic | 1 | B2+ | 1 hour |
| Offset Print | Heidelberg | Offset paper, Designer cardboard | 500 | B1 | 1 day |
| Wide-format | Eco-solvent, Latex, UV | PVC films, Banner fabric, Polyester, Backlit, Grey Back | 1 | 3.2m | Same day |
| Merch (Sublimation) | Sublimation | Polyester, Ceramic, Metal, rPET | 1 | Various | 1-2 days |
| Merch (DTG) | DTG | Cotton, Organic Cotton | 1 | A3 | 1 day |
| Engineering | Large Format Inkjet, LED | Offset paper, Tracing paper | 1 | A0+ | 1 hour |
| Mobile Stands | Wide-format Inkjet, UV | Banner fabric, PET film | 1 | 2x3m | 1-2 days |

### Competitive Positioning
```
Critical Threats:  Printio (POD marketplace), RuPrint (Full-cycle online), Контур-Фото (Local network)
High Threats:      Printful (Global POD), Printback (B2B platform), Canva Print (Design-first)
Medium Threats:    Яндекс.Услуги, Авито, 2ГИС, Профи.ру, Vaston, SMART
Low Threats:       КанцПарк, Максимум, Удмуртпечать, Принт-Экспресс, Копи-центр Документ
```

### Target Cities Priority
| Priority | Cities | Delivery Days | SDEK PVZ |
|----------|--------|---------------|----------|
| Critical | Moscow, SPb, Ekaterinburg, Novosibirsk | 1-3 | Yes |
| High | Kazan, Nizhny Novgorod, Chelyabinsk, Omsk, Samara, Rostov, Ufa, Krasnoyarsk, Voronezh, Perm, Volgograd | 2-4 | Yes |

---

## Quick SPARQL Queries

### Get all services with details
```sparql
PREFIX cifra: <https://cifra18.ru/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?s ?label ?method ?material ?minTirage ?maxFormat ?time WHERE {
    cifra:company/cifra18 cifra:hasService ?s .
    ?s rdfs:label ?label .
    OPTIONAL { ?s cifra:hasPrintMethod ?method }
    OPTIONAL { ?s cifra:hasMaterial ?material }
    OPTIONAL { ?s cifra:hasMinTirage ?minTirage }
    OPTIONAL { ?s cifra:hasMaxFormat ?maxFormat }
    OPTIONAL { ?s cifra:hasProductionTime ?time }
}
```

### Get materials for specific service
```sparql
PREFIX cifra: <https://cifra18.ru/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?m ?label ?type ?price WHERE {
    cifra:service_poligrafiya_vizitki cifra:hasMaterial ?m .
    ?m rdfs:label ?label .
    OPTIONAL { ?m cifra:materialType ?type }
    OPTIONAL { ?m cifra:pricePerKg ?price }
}
```

### Get delivery info for city
```sparql
PREFIX cifra: <https://cifra18.ru/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?city ?label ?days ?hasPVZ ?addresses WHERE {
    ?city rdfs:label "Москва" .
    OPTIONAL { ?city cifra:deliveryDaysFromIzhevsk ?days }
    OPTIONAL { ?city cifra:hasSdekPVZ ?hasPVZ }
    OPTIONAL { ?city cifra:sdekPVZAddresses ?addresses }
}
```

---

## Integration Points

### 1. Bitrix CMS (cifra18.рф)
- **JSON-LD schemas** → `/scripts/dev-fixes/*.jsonld` (Organization, Product, Article, BreadcrumbList, FAQ)
- **Sitemap** → Auto-generated from KG service entities
- **Meta tags** → From service labels, descriptions, intents

### 2. SDEK API
- **Delivery zones** → From Location entities with `cifra:hasSdekPVZ`
- **PVZ addresses** → From `cifra:sdekPVZAddresses`
- **Delivery times** → From `cifra:deliveryDaysFromIzhevsk`

### 3. Topvisor/SEO Tools
- **Keywords** → From service labels + intent classification
- **Competitor tracking** → From Competitor entities + threat levels
- **Local SEO** → From Location entities (Udmurtia + Top-15 cities)

### 4. CRM/Битрикс24
- **Lead qualification** → Industry entities with `cifra:avgCheck`, `cifra:ltv`, `cifra:decisionMaker`
- **Service matching** → `cifra:suitableFor` links Industry → Service
- **ROI attribution** → Order → Service → Equipment → Cost tracking

### 5. Customer Support Bot (GraphRAG)
- **Intent classification** → 9 intent types from KG
- **Context retrieval** → SPARQL + Vector similarity
- **Response generation** → LLM grounded in KG facts

---

## Maintenance Scripts

```bash
# Rebuild combined KG from entity files
python3 scripts/export/combine_knowledge_graph.py

# Extract triplets
python3 scripts/export/extract_triplets.py

# Embed for vector search
python3 scripts/export/embed_kg_entities.py

# Import to Neo4j
cypher-shell -f brain/wiki/knowledge_graph/neo4j_init.cypher

# Start Fuseki
docker-compose -f brain/wiki/knowledge_graph/fuseki-docker-compose.yml up -d

# Validate KG
python3 scripts/export/validate_kg.py
```

---

## Quality Gates

- [ ] All 239 entities have `@id`, `@type`, `rdfs:label`
- [ ] No duplicate `@id` values
- [ ] All service entities have `cifra:hasPrintMethod` and `cifra:hasMaterial`
- [ ] All location entities have `cifra:hasSdekPVZ` and `cifra:deliveryDaysFromIzhevsk`
- [ ] All competitor entities have `cifra:threatLevel` and `cifra:competitorType`
- [ ] All industry entities have `cifra:typicalServices` and `cifra:avgCheck`
- [ ] Triplet count matches entity relationships (387)
- [ ] SPARQL queries return expected results
- [ ] Vector embeddings generated for all entities
- [ ] GraphRAG bot answers test queries correctly

---

## Next Steps

1. **Owner Access Required:**
   - Яндекс.Метрика counter ID
   - Яндекс.Вебмастер verification
   - Топвизор API key
   - Битрикс админка access
   - CRM/Битрикс24 API
   - IMAP access to izhcifra@yandex.ru
   - SDEK API credentials

2. **Phase 0 Fixes (Blocking):**
   - Fix sitemap.xml (all URLs return 404)
   - Add canonical tags
   - Fix meta descriptions (currently "Description" placeholder)
   - Fix H1 hierarchy (5 H1s on homepage)
   - Add JSON-LD schemas to templates

3. **Phase 1 Content:**
   - Generate service pages from KG entities
   - Create city/service-area pages for top 15 cities
   - Build comparison pages vs top 5 competitors
   - Implement FAQ from `cifra:hasFAQ` relationships

4. **Phase 2 GEO/AI:**
   - Generate llms.txt from KG
   - Optimize for AI citations (answer-first structure)
   - Submit to AI directories
   - Set up brand mention monitoring

---

## Contact
- **Project:** ЦИФРА18 SEO+GEO Promotion
- **Domain:** xn--18-6kc5a3bxam.xn--p1ai (цифра18.рф)
- **Location:** Ижевск, Удмуртия
- **CMS:** 1С-Битрикс 23.300
- **Delivery:** СДЭК по всей России