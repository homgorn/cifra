# Граф знаний: Запросы ↔ Страницы ↔ Энтити

**Цель:** Построить семантическую сеть для GEO-оптимизации, внутренней перелинковки и контент-планирования  
**Методология:** Извлечение триплетов (Subject-Predicate-Object) из запросов, URL, заголовков, анкоров  
**Инструменты:** `extract_triplets.py`, `combine_knowledge_graph.py`, NetworkX/Neo4j для визуализации  

---

## 🧠 Энтити (Сущности): Ядро графа

### Тип 1: ОРГАНИЗАЦИЯ (Organization)
```
Entity: Типография «Цифра» (Цифра18)
├── @id: https://xn--18-6kc5a3bxam.xn--p1ai/#organization
├── name: "Типография «Цифра»"
├── alternateName: ["Цифра18", "Цифра 18", "ИП Данилов К.Л."]
├── url: https://xn--18-6kc5a3bxam.xn--p1ai
├── logo: https://xn--18-6kc5a3bxam.xn--p1ai/logo.svg
├── address: "ул. 7-я Подлесная, 34, Ижевск, Удмуртская Республика, 426069"
├── geo: {latitude: 56.8519, longitude: 53.2033}
├── telephone: ["+7-965-842-32-41", "+7-3412-32-32-41"]
├── email: izhcifra@yandex.ru
├── openingHours: Mo-Fr 09:00-18:00
├── priceRange: "₽₽"
├── sameAs: [VK, Telegram, YouTube, Дзен - уточнить]
└── knowsAbout: [Полиграфия, Широкоформат, Мерч, Инженерная печать, Сувенирка]
```

### Тип 2: УСЛУГИ (Services/Products), Коммерческие энтити
```
Service: Печать визиток
├── category: Полиграфия
├── areaServed: Ижевск, Удмуртия
├── hasOffer: {price: от 350₽/100шт, availability: InStock}
├── material: [Крафт, Дизайнерский картон, Пластик, Дерево, Металл]
├── technology: [Цифровая, Офсетная, Белый тонер, УФ]
├── turnaround: "от 1 часа"
├── relatedQueries: ["визитки ижевск", "печать визиток ижевск", "визитки на крафте"...]
├── targetPage: /catalog/poligrafiya/vizitki/
├── subServices: [Срочная печать, Дизайнерские, На крафте, Белым тонером]
└── competitors: [Контур Фото, ПринтЭкспро, ВАСТОН]

Service: Изготовление календарей
├── category: Полиграфия
├── seasonal: Q3-Q4 (авг-дек)
├── types: [Квартальные, Настенные, Перекидные, Карманные, Домик, Премиум]
├── materials: [Бумага, Прозрачный пластик, Картон]
├── options: [1 рекламное поле, 3 поля, Светодиод, Фигурная резка]
├── targetPage: /catalog/poligrafiya/kalendari/
└── relatedQueries: ["печать календарей ижевск", "календари на 2027", "квартальный календарь"...]

Service: Широкоформатная печать
├── category: Реклама/Широкоформат
├── materials: [Баннерная ткань, Пленка (Grey/Blue/Black Back), Постерная бумага, Холст, Фотообои]
├── formats: [А0, А1, А2, 2х3м, Рулон до 1.6м]
├── technologies: [УФ, Латекс, Экосольвент]
├── finishing: [Ламинация, Плоттерная резка, Люверсы, Карманы]
├── targetPage: /catalog/shirokoformatnaya-pechat/
└── subServices: [Баннеры, Пленка, Постеры, Фотообои, Картины на холсте]

Service: Мобильные стенды
├── category: Выставочное оборудование
├── types: [Ролл-ап, Х-баннер, L-баннер, Пресс-волл, Штендер]
├── rental: true (аренда доступна)
├── materials: [Алюминий, Баннерная ткань, Пластик, Углепластик]
├── targetPage: /catalog/mobilnye-stendy/
└── relatedQueries: ["ролл ап ижевск", "пресс волл ижевск", "аренда стендов ижевск"...]

Service: Инженерная печать
├── category: Техническая документация
├── formats: [А0, А1, А2, А3, А4]
├── services: [Печать чертежей, Ксерокопия, Сканирование, Фальцовка, Брошюровка]
├── software: [AutoCAD, KOMPAS, Revit, PDF]
├── standards: [ГОСТ 2.301-68, ГОСТ 2.305-68]
├── targetPage: /catalog/inzhenernaya-pechat/
└── relatedQueries: ["печать чертежей ижевск", "ксерокопия а1", "сканирование а0"...]

Service: Сувенирная продукция / Мерч
├── category: B2C + Корпоративные подарки
├── subcategories:
│   ├── Одежда: [Футболки DTF, Сублимация, Термотрансфер, Худи, Поло]
│   ├── Посуда: [Кружки (обычные, хамелеон, термо), Термокружки, Стаканы]
│   ├── Магниты: [Виниловые 5x7, 7x10, 15x21, Фигурные, Зеркальные]
│   ├── Сумки: [Шопперы, Экосумки, Рюкзаки, Баффы]
│   ├── Еда: [Шоколад с логотипом, Конфеты, Коробки-открытки]
│   └── Мелочь: [Попсокеты, Брелоки, Флешки, Пауэрбанки, Часы]
├── targetPage: /catalog/suvenirnaya-produktsiya/
└── b2bAngle: ["Корпоративный мерч", "Новогодние подарки", "Онбординг наборы"]
```

### Тип 3: ЛОКАЦИИ (Places), Local SEO
```
Place: Ижевск
├── @type: City
├── containedIn: Удмуртская Республика
├── geo: {lat: 56.85, lon: 53.20}
├── population: ~620k
├── servedBy: Типография «Цифра»
└── queries: ["ижевск", "в ижевске", "г ижевск", "ижевск центр", "улица пушкинская ижевск"]

Place: Удмуртская Республика
├── @type: AdministrativeArea
├── queries: ["удмуртия", "удмуртская республика", "изhevsk udmurtia"]
```

### Тип 4: ТЕХНОЛОГИИ / МАТЕРИАЛЫ (Technologies/Materials), Информационные
```
Technology: Цифровая печать
├── pros: ["Срочно", "От 1 шт.", "Переменные данные", "Цветопробы"]
├── cons: ["Дороже на тиражах 500+", "Меньше формат"]
├── bestFor: ["Визитки", "Листовки", "Буклеты", "Календари мелкие тиражи"]
└── relatedQueries: ["цифровая печать ижевск", "цифровая печать визиток"]

Technology: Офсетная печать
├── pros: ["Дешево на тиражах 500+", "Качество", "Пантоны", "Большие форматы"]
├── cons: ["Долгая подготовка", "Мин. тираж 300-500", "Нет переменных данных"]
├── bestFor: ["Листовки а5/а6", "Календари", "Журналы", "Коробки"]
└── relatedQueries: ["офсетная печать ижевск", "офсетная печать визиток"]

Material: Крафт-картон
├── properties: ["Эко", "Текстура", "Коричневый", "Переработка"]
├── usedIn: ["Визитки", "Пакеты", "Конверты", "Ярлыки"]
└── queries: ["визитки на крафте", "крафт пакеты", "крафт конверты"]

Material: Дизайнерский картон
├── brands: ["Curious", "Splendor", "Majestic", "Sirio", "Мулен", "Тактильные"]
├── properties: ["Текстура", "Цвет в массе", "Премиум", "Тиснение/фольга"]
└── queries: ["визитки на дизайнерском картоне", "дизайнерская бумага для визиток"]
```

### Тип 5: СРАВНЕНИЯ / ВЫБОР (Comparisons), High CTR энтити
```
Comparison: Ролл-ап vs Х-баннер
├── entities: [Ролл-ап, Х-баннер]
├── criteria: [Цена, Переносимость, Размер, Сборка, Стабильность, Аренда]
├── verdict: "Ролл-ап - для постоянного использования, Х-баннер - для разовых/бюджет"
├── targetPage: /comparison/roll-up-vs-h-banner/
└── queries: ["ролл ап или х баннер", "чем отличается ролл ап от х баннера"]

Comparison: Цифровая vs Офсетная печать
├── entities: [Цифровая печать, Офсетная печать]
├── criteria: [Тираж, Срок, Цена, Качество, Формат, Переменные данные]
├── verdict: "До 300 экз - цифра, от 500 - офсет"
├── targetPage: /comparison/cifrovaya-vs-ofsetnaya/
└── queries: ["цифровая или офсетная печать", "в чем разница цифра и офсет"]

Comparison: Крафт vs Дизайнерский картон для визиток
├── entities: [Крафт, Дизайнерский картон]
├── criteria: [Стиль, Цена, Тираж, Фольга/тиснение, Эко]
├── targetPage: /comparison/kraft-vs-dizaynerskiy/
└── queries: ["визитки крафт или дизайнерский", "что лучше крафт или дизайнерский"]
```

---

## 🔗 Отношения (Predicates): Ребра графа

| Предикат | Domain | Range | Пример |
|---|---|---|---|
| `offers` | Organization | Service | Цифра offers Печать визиток |
| `hasCategory` | Service | Category | Визитки hasCategory Полиграфия |
| `hasSubService` | Service | Service | Визитки hasSubService Срочная печать |
| `usesTechnology` | Service | Technology | Визитки usesTechnology Цифровая печать |
| `usesMaterial` | Service | Material | Визитки usesMaterial Крафт |
| `hasOffer` | Service | Offer | Визитки hasOffer {price: 350₽} |
| `targetPage` | Service | WebPage | Визитки targetPage /catalog/poligrafiya/vizitki/ |
| `servesArea` | Service | Place | Визитки servesArea Ижевск |
| `competesWith` | Service | Organization | Визитки competesWith Контур Фото |
| `hasComparison` | Service | Comparison | Визитки hasComparison Крафт vs Дизайнерский |
| `relatedQuery` | Service | Query | Визитки relatedQuery "визитки ижевск" |
| `hasQueryPosition` | Query | Position | "визитки ижевск" hasQueryPosition 1.97 |
| `hasIntent` | Query | Intent | "визитки ижевск" hasIntent Commercial |
| `targetsPage` | Query | WebPage | "визитки ижевск" targetsPage /catalog/poligrafiya/vizitki/ |
| `mentionsEntity` | WebPage | Entity | /catalog/poligrafiya/vizitki/ mentionsEntity Визитки |
| `linksTo` | WebPage | WebPage | /catalog/poligrafiya/vizitki/ linksTo /blog/tekhnicheskie-trebovaniya/ |
| `hasSchema` | WebPage | SchemaType | /catalog/poligrafiya/vizitki/ hasSchema Product |

---

## 📊 Граф в цифрах (оценка)

| Метрика | Значение |
|---|---|
| **Энтити (узлы)** | ~85 (1 Org + 7 Services + 2 Places + 15 Tech/Mat + 10 Comparisons + 50 Product variants) |
| **Отношения (ребра)** | ~320 |
| **Запросы, мапнутые на энтити** | 420/535 (78%) |
| **Страницы с энтити** | 142 SEARCHABLE → 60 с явными энтити |
| **Кластеры (communities)** | 8 основных (L1 из семантических кластеров) |

---

## 🎯 Применение графа для SEO/GEO

### 1. Schema.org разметка (JSON-LD)
Каждая энтити → свой JSON-LD на целевой странице:
```json
// На /catalog/poligrafiya/vizitki/
{
  "@context": "https://schema.org",
  "@type": "Service",
  "name": "Печать визиток в Ижевске",
  "provider": {"@id": "https://xn--18-6kc5a3bxam.xn--p1ai/#organization"},
  "areaServed": "Ижевск, Удмуртия",
  "hasOfferCatalog": {...},
  "knowsAbout": ["Крафт", "Дизайнерский картон", "Белый тонер", "Срочная печать"]
}
```

### 2. Внутренняя перелинковка (Entity-based)
```
Страница визиток → ссылки на:
  - Материалы: /blog/materialy-dlya-vizitek/ (mentionsEntity: Крафт, Дизайнерский)
  - Технологии: /blog/cifrovaya-vs-ofsetnaya/ (hasComparison)
  - Требования: /blog/tekhnicheskie-trebovaniya/ (relatedQuery: "требования к макету")
  - Сравнения: /comparison/kraft-vs-dizaynerskiy/ (hasComparison)
  - Кейсы: /portfolio/vizitki-dlya-yurista/ (mentionsEntity: Визитки)
```

### 3. Контент-план из графа (Entity Coverage)
```
Для каждого Service энтити нужны:
✅ Целевая страница (targetPage)
✅ JSON-LD Service + Offer + FAQ
❌ Страница сравнений (hasComparison) - 0/10
❌ Информационные статьи (relatedQuery: informational) - 0/50
❌ Локальные лендинги (servesArea) - 0/6
❌ Кейсы/портфолио (mentionsEntity) - 3/20
```

### 4. llms.txt генерация
```
# Типография «Цифра» - ключевые страницы для ИИ
## Организация
https://xn--18-6kc5a3bxam.xn--p1ai/#organization - Типография «Цифра», Ижевск, ул. 7-я Подлесная 34

## Услуги
https://xn--18-6kc5a3bxam.xn--p1ai/catalog/poligrafiya/vizitki/ - Печать визиток (крафт, дизайнерский, срочно)
https://xn--18-6kc5a3bxam.xn--p1ai/catalog/poligrafiya/kalendari/ - Календари на 2027 (квартальные, настенные, премиум)
https://xn--18-6kc5a3bxam.xn--p1ai/catalog/shirokoformatnaya-pechat/ - Широкоформатная печать (баннеры, постеры, фотообои)
https://xn--18-6kc5a3bxam.xn--p1ai/catalog/mobilnye-stendy/ - Мобильные стенды (ролл-ап, пресс-волл, х-баннер, аренда)
https://xn--18-6kc5a3bxam.xn--p1ai/catalog/inzhenernaya-pechat/ - Инженерная печать (чертежи А0-А4, сканирование, фальцовка)
https://xn--18-6kc5a3bxam.xn--p1ai/catalog/suvenirnaya-produktsiya/ - Мерч и сувенирка (кружки, футболки, магниты, шоколад)

## Экспертиза
https://xn--18-6kc5a3bxam.xn--p1ai/blog/tekhnicheskie-trebovaniya/ - Требования к макетам для печати
https://xn--18-6kc5a3bxam.xn--p1ai/comparison/roll-up-vs-h-banner/ - Выбор стенда для выставки
https://xn--18-6kc5a3bxam.xn--p1ai/comparison/cifrovaya-vs-ofsetnaya/ - Цифровая или офсетная печать
```

---

## 🛠 Скрипты для работы с графом

```python
# extract_triplets.py - извлечение из запросов/страниц
# combine_knowledge_graph.py - объединение в NetworkX/Neo4j
# validate_kg.py - проверка полноты (entity coverage)
# export_llms_txt.py - генерация llms.txt
# export_schema_jsonld.py - генерация JSON-LD для всех страниц
```

### Пример triplet extraction из запроса:
```
Query: "визитки на крафте ижевск заказать дешево"
→ Triplets:
  (Визитки, usesMaterial, Крафт)
  (Визитки, servesArea, Ижевск)
  (Визитки, hasIntent, Transactional)
  (Визитки, hasPriceModifier, Дешево)
  (Визитки, hasAction, Заказать)
```

---

## 📋 Экспорты

- `exports/entities.json`, все энтити с атрибутами
- `exports/triplets.csv`, все ребра (subject, predicate, object)
- `exports/entity_coverage.csv`, покрытие энтити страницами/контентом
- `exports/llms.txt`, готовый файл для ИИ
- `exports/schema_templates/`, JSON-LD шаблоны по типам страниц

---

## 🔄 Обновление графа

1. **Еженедельно:** новые запросы из Вебмастера → новые relatedQuery edges
2. **Ежемесячно:** новые страницы → новые mentionsEntity edges
3. **Квартально:** аудит entity coverage → контент-план на следующий квартал
4. **При запуске новых услуг:** добавить Service энтити + все связи

---

*Граф является живой структурой. Актуальная версия в `exports/knowledge_graph.graphml` для Gephi/Neo4j.*