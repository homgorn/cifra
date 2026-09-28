# Entities Index: ЦИФРА18

**Last updated:** 2026-09-10  
**Status:** Начальное заполнение (после экспорта каталога и ключей)

---

## 📋 Сущности проекта

| Сущность | Файл | Статус | Описание |
|---|---|---|---|
| **Brand** | `brand.md` | ⏳ Planned | Типография «Цифра», ИП Данилов К.Л., НПП, миссия, ценности |
| **Services** | `services.md` | ⏳ Planned | 300+ услуг: каталог, категории, цены, характеристики |
| **Locations** | `locations.md` | ⏳ Planned | Ижевск, Удмуртия, пригороды (Воткинск, Глазов, Сарапул, Можега...) |
| **Competitors** | `competitors.md` | ⏳ Planned | Локальные (Ижевск) + федералы (Printio, Визитка.ру, Рупечат, Яндекс.Услуги) |
| **Keywords** | `keywords.md` | ⏳ Planned | Семантическое ядро по кластерам (после seo-keyword-research) |
| **Intent Map** | `intent_map.md` | ⏳ Planned | Интент-карта: Informational / Commercial / Transactional / Navigational |
| **Materials** | `materials.md` | ⏳ Planned | Бумаги, пленки, ткани, пластики: справочник для программатика |
| **Equipment** | `equipment.md` | ⏳ Planned | Парк станков: модель, возможности, макс. формат, скорость |
| **Standards** | `standards.md` | ⏳ Planned | ГОСТ, ISO, технические требования к макетам |
| **Industries** | `industries.md` | ⏳ Planned | HoReCa, Риелторы, Строительство, Медицина, Образование, Ивенты, Ритейл |

---

## 🔗 Связи сущностей (Entity Graph)

```
Brand (Organization/LocalBusiness)
├── hasLocation → Locations (Ижевск, Удмуртия)
├── offers → Services (300+ услуг в 7 категориях)
│   ├── Полиграфия (28 подкатегорий)
│   ├── Сувенирная продукция (28+)
│   ├── Широкоформатная печать (10)
│   ├── Инженерная печать (5)
│   ├── Стенды (5)
│   ├── Интерьер (6)
│   └── Мобильные стенды (11)
├── uses → Materials (бумага, пленка, ткань, пластик)
├── uses → Equipment (станки: цифровые, офсетные, широкоформатные, постпечатные)
├── serves → Industries (HoReCa, Риелторы, Строительство, Медицина, Образование, Ивенты, Ритейл)
├── follows → Standards (ГОСТ полиграфии, ISO 12647, технические требования)
├── hasContent → Articles (290 статей на WP поддомене)
├── hasContent → Cases (портфолио: кейсы клиентов)
├── hasContent → Glossary (термины полиграфии)
├── hasContent → FAQ (частые вопросы)
└── competesWith → Competitors (локальные + федералы)
```

---

## 📊 Атрибуты ключевых сущностей (для JSON-LD / программатика)

### Service (Услуга)
```json
{
  "@type": "Service",
  "name": "Печать визиток на крафте",
  "category": "Полиграфия > Визитки",
  "provider": {"@id": "#organization"},
  "areaServed": ["Ижевск", "Воткинск", "Глазов", "Сарапул", "Можега"],
  "priceRange": "от 4.5 ₽/шт",
  "description": "Визитки на крафте...",
  "offers": {"@type": "Offer", "price": 4.5, "priceCurrency": "RUB", "availability": "InStock"},
  "hasFAQ": ["Сколько стоит?", "Какие сроки?", "Как подготовить макет?"],
  "relatedMaterials": ["Крафт 265гр", "Крафт 350гр"],
  "relatedEquipment": ["Цифровая печать HP Indigo", "Плоттерная резка"]
}
```

### Material (Материал)
```json
{
  "@type": "Product",
  "name": "Картон Natural Kraft 265гр",
  "category": "Материалы > Бумага > Крафт",
  "description": "Натуральный крафтовый картон...",
  "specifications": {"weight": "265 g/m²", "color": "brown", "finish": "uncoated"},
  "suitableFor": ["Визитки", "Пакеты", "Таблички", "Мерч"],
  "priceRange": "от X руб/лист"
}
```

### Location (Локация)
```json
{
  "@type": "City",
  "name": "Ижевск",
  "containedIn": "Удмуртская Республика",
  "population": 640000,
  "coordinates": {"lat": 56.8519, "lng": 53.2033},
  "servicesOffered": ["Все категории"],
  "deliveryAvailable": true,
  "pickupAvailable": true
}
```

### Competitor (Конкурент)
```json
{
  "@type": "Organization",
  "name": "Типография [Название]",
  "url": "https://...",
  "location": "Ижевск / Россия",
  "categories": ["Полиграфия", "Широкоформат", "Сувенирка"],
  "strengths": ["Цена", "Скорость", "Ассортимент"],
  "weaknesses": ["Нет калькулятора", "Старый сайт", "Нет кейсов"],
  "keywordsOverlap": ["печать визиток ижевск", "баннеры ижевск"],
  "backlinkGap": ["2gis.ru", "zoon.ru", "avito.ru"]
}
```

---

## 🎯 Использование сущностей

| Use Case | Сущности | Где применяется |
|---|---|---|
| **JSON-LD Schema** | Brand, Service, Product, Location, FAQ | Все страницы |
| **Programmatic SEO** | Service × Location, Material, Comparison | WP поддомен |
| **Content Briefs** | Service, Material, Industry, FAQ | Статьи, товарки |
| **Internal Linking** | Service, Material, Case, Article | Перелинковка |
| **GEO / AI Citability** | Brand, Service, Material, Standard, FAQ | Ответы в ИИ |
| **SMM / PR** | Brand, Case, Industry, Equipment | Посты, пресс-релизы |
| **Sales Enablement** | Service, Material, Equipment, Case | КП, презентации, калькуляторы |

---

## 📝 План наполнения (после экспортов)

1. **Экспорт каталога Битрикс** → `scripts/export/bitrix_catalog_export.py` → `entities/services.md`
2. **Экспорт 290 статей** → `scripts/audit/articles_audit.py` → анализ → `entities/keywords.md`, `entities/intent_map.md`
3. **Keyword Research (Топвизор + PAA)** → `entities/keywords.md`, `entities/intent_map.md`
4. **Competitor Profiling (Топвизор + ручной)** → `entities/competitors.md`
5. **Materials/Equipment справочник** → ручное заполнение от технологов → `entities/materials.md`, `entities/equipment.md`
6. **Industries/Standards** → из кейсов и FAQ менеджеров → `entities/industries.md`, `entities/standards.md`

---

*Сущности: это семантическое ядро проекта. Поддерживать в актуальном состоянии постоянно.*