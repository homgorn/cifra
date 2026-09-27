# Services Index — ЦИФРА18

**Last updated:** 2026-09-11  
**Source:** Site menu (homepage HTML) + search results + known products  
**Total:** 7 categories, 88 subcategories, 29 known product-level URLs  
**Status:** Structure complete, need Bitrix export for full product catalog (300+ SKUs)

---

## 📊 Overview

| Metric | Value |
|---|---|
| Root Categories | 7 |
| Subcategories (Level 2) | 88 |
| Known Product URLs (Level 3) | 29 |
| Estimated Total SKUs | ~300+ (need Bitrix export) |
| Geo Coverage | Ижевск + Удмуртия + РФ (delivery) |

---

## 🗂 Category Structure

| # | Category | Subcategories | Key Products |
|---|---|---|---|
| 1 | **Полиграфия** | 26 | Визитки (8 типов), Листовки, Календари, Пакеты, Блокноты, Бейджи, Ламинирование, УФ-печать, Фольгирование, Плоттерная резка, Коробки, Конверты, Бланки, Тейбл-тент |
| 2 | **Сувенирная продукция** | 28 | Кружки/термосы, Футболки/одежда, Ручки/карандаши, Шоколад, Брелоки/магниты, Попсокеты, Рюкзаки/сумки, Куб-трансформер, Награды/медали, USB-флешки, Лазерная гравировка |
| 3 | **Широкоформатная печать** | 10 | Баннеры (1.6м/3.2м), Пленки (самоклеящаяся, бэклайт, грейбек), Постеры, Ткани (флажная, полиэстер), Blue Back, Ламинированная бумага |
| 4 | **Мобильные стенды** | 11 | Roll-up (5 размеров), Х-banner, L-banner, Штендер, Пресс-волл, Аренда пресс-волла |
| 4 | **Инженерная печать** | 5 | Чертежи, Ксерокопия, Сканирование, Фальцовка, Брошюровка |
| 5 | **Стенды** | 5 | Стенды, Карманы ПЭТ, Оргстекло, Таблички |
| 6 | **Интерьер** | 6 | Картины на холсте, Постеры, Фотообои/фрески, Фотопостеры на пенокартоне |

---

## 🎯 Priority Money Pages (High Commercial Intent)

| Service | Search Intent | Target Keywords | Priority |
|---|---|---|---|
| **Визитки** | Commercial | "печать визиток Ижевск", "визитки на крафте", "визитки срочно" | 🔥 Critical |
| **Листовки/флаеры** | Commercial | "печать листовок Ижевск", "офсетная печать листовок", "цифровая печать листовок" | 🔥 Critical |
| **Баннеры/широкоформат** | Commercial | "печать баннеров Ижевск", "баннеры 3x6", "широкоформатная печать" | 🔥 Critical |
| **Роллапы/стеклы** | Commercial | "роллап купить Ижевск", "пресс-волл", "стеклы для выставок" | 🟡 High |
| **Сувенирка/мерч** | Commercial | "мерч с логотипом", "кружки с логотипом", "футболки с печатью" | 🟡 High |
| **Календари** | Seasonal | "печать календарей 2025", "календари корпоративные" | 🟡 High (Q4) |
| **Пакеты/упаковка** | Commercial | "брендированные пакеты", "крафт пакеты с логотипом" | 🟡 High |
| **Наружная реклама** | Commercial | "наружная реклама Ижевск", "стенды уличные", "таблички" | 🟢 Medium |

---

## 🌐 Scaling to Russia (SDEK Delivery)

### Current State
- **Local only:** Ижевск + пригороды Удмуртии
- **Pickup:** Ижевск, ул. 7-я Подлесная, 34
- **No online payment** — only request forms

### Required for Russia-Wide

| Component | Current | Needed for Russia |
|---|---|---|
| **Delivery** | Self-pickup only | SDEK integration (API), calculating widget, tracking |
| **Payment** | Invoice after order | Online payment (ЮKassa/Тинькофф/СБП), prepayment % |
| **Calculator** | Basic JS widget | Full-featured: material × size × quantity × delivery city |
| **Geo-pages** | None | Service × City landing pages (top-20 cities) |
| **SEO** | Local only | "печать визиток Москва", "баннеры СПб доставка", "мерч по РФ" |
| **Schema** | LocalBusiness | Product + Offer + shippingDetails (SDEK) |
| **Content** | Local cases | Cases from other cities, delivery testimonials |

### SDEK Integration Points

```javascript
// Calculator widget needs:
- SDEK API: calculate tariff (from 426069 to destination)
- Widget: city autocomplete (SDEK cities API)
- Tracking: post-order widget in customer cabinet
- Webhook: status updates → CRM/email/SMS
```

### Target Cities for Service×City Pages (Phase 1)

| Priority | Cities | Population | Rationale |
|---|---|---|---|
| 1 | Москва, СПб | 15M+ | Largest markets, high competition |
| 2 | Екатеринбург, Новосибирск, Казань, Нижний Новгород | 1-2M | Major industrial/commercial hubs |
| 3 | Челябинск, Омск, Самара, Ростов-на-Дону, Уфа | 1M+ | Regional capitals |
| 4 | Удмуртия cities: Ижевск, Воткинск, Глазов, Сарапул, Можега | 50-100K | Home region dominance |

---

## 📁 Files

| File | Description |
|---|---|
| `catalog_services_2026-09-11.md` | Full markdown catalog |
| `catalog_services_2026-09-11.csv` | Structured data for scripts |
| `services.md` | This index |

---

## 🔄 Next Steps

1. **Request Bitrix export** — full catalog with prices, properties, images
2. **Build calculator API** — integrate SDEK tariff calculator
3. **Create Service×City pages** — programmatic SEO for top 20 cities
4. **Add online payment** — ЮKassa/Тинькофф integration
5. **Schema update** — Product + Offer + shippingDetails for all SKUs