# Стратегия поддомена WordPress: ЦИФРА18
## blog.cifra18.рф (или articles.cifra18.рф, media.cifra18.рф)

**Контекст:** Владелец знает WordPress, хочет вынести контентную часть (блог, статьи, программатик SEO, GEO-контент, портфолио) на отдельный поддомен на WP. Основной сайт (Bitrix): каталог, калькуляторы, заявки.

---

## 🎯 Зачем поддомен на WordPress

| Плюсы | Риски (и как митигировать) |
|---|---|
| **Скорость публикации**: Gutenberg, блоки, паттерны, ACF | **Разделение авторитета** → Жёсткая перелинковка, общий бренд, shared GA4/GSC |
| **Программатик SEO**: WP All Import, кастомные таксономии, ACF, генерация страниц | **Дубликаты контента** → Canonical на основной домен где нужно, уникальный контент на поддомене |
| **GEO-оптимизация**: плагины schema (Yoast/RankMath), llms.txt, AI-ready контент | **Тех. обслуживание 2 CMS** → Docker/WP Engine, автообновления, бэкапы |
| **Портфолио/Кейсы**: удобные CPT, галереи, фильтры | **SEO миграция статей** → 301 редиректы, сохранение URL структуры |
| **Видео/Дзен/Шортс**: встраивание, постинг через плагины | **Куки/Сессии** → Shared domain cookies для корзины/лида |

---

## 🏗 Архитектура поддомена

### Домен
```
blog.cifra18.рф  (или articles.cifra18.рф, media.cifra18.рф)
```
- SSL: wildcard `*.xn--18-6kc5a3bxam.xn--p1ai` или отдельный Let's Encrypt
- DNS: A-запись на WP сервер (отдельный от Bitrix)

### WordPress Stack
| Компонент | Рекомендация |
|---|---|
| **Хостинг** | WP Engine / Kinsta / Cloudways (Docker) / собственный VPS + Docker |
| **PHP** | 8.2+ |
| **MySQL** | 8.0 / MariaDB 10.6 |
| **Web Server** | Nginx + PHP-FPM |
| **Кеш** | Redis (object cache) + Nginx fastcgi_cache / WP Rocket |
| **CDN** | Cloudflare (Orange cloud): бесплатно, кеш, WAF, Polish, Mirage |

### Must-have плагины (минимальный набор)
| Плагин | Зачем |
|---|---|
| **Yoast SEO Premium / Rank Math Pro** | Schema, sitemap, breadcrumbs, AI content analysis, redirects |
| **ACF Pro** | Кастомные поля для сущностей, калькуляторов в статьях, FAQ |
| **Custom Post Type UI** | CPT: Кейсы, Услуги-статьи, Материалы, Оборудование, FAQ |
| **WP All Import Pro + ACF Addon** | Программатик импорт из CSV/XML (300+ страниц) |
| **Autoptimize / Perfmatters** | JS/CSS оптимизация, удаление неиспользуемого |
| **WP Rocket** (если бюджет позволяет) | Кеш, ленивая загрузка, предзагрузка |
| **IndexNow / Instant Indexing** | Мгновенная индексация в Яндекс/Бинг |
| **WebP Express / ShortPixel** | Авто WebP/AVIF |
| **LLMS.txt Generator** (кастом или плагин) | Генерация llms.txt |
| **WPGraphQL** (опционально) | Headless для интеграции с Bitrix |

---

## 📊 Контентная архитектура (CPT + Таксономии)

### Custom Post Types (CPT)
| CPT | Slug | Описание | Поля (ACF) |
|---|---|---|---|
| **Статьи (Posts)** | `/blog/` | Основной блог | author, category, tags, featured_image, seo_meta, faq, calculator_embed, related_cases |
| **Кейсы (Cases)** | `/cases/` | Портфолио как SEO-активы | client, industry, services (taxonomy), materials, equipment, gallery, results, testimonial, schema_type (CaseStudy) |
| **Услуги-статьи (Service Articles)** | `/services/` | Глубокие лендинги под ключи | service_category, calculator_shortcode, comparison_table, faq, price_range, schema (Service) |
| **Материалы (Materials)** | `/materials/` | Справочник: бумага, пленки, ткани, пластики | specs, gsm, colors, compatibility, price_range, application |
| **Оборудование (Equipment)** | `/equipment/` | Парк станков как trust-сигнал | model, capabilities, max_format, speed, materials, photos |
| **FAQ (FAQ Items)** | `/faq/` | Отдельные FAQ страницы для schema | question, answer, category, schema (FAQPage) |
| **Глоссарий (Glossary)** | `/glossary/` | Термины полиграфии для GEO | term, definition, related_terms, schema (DefinedTerm) |

### Таксономии (Taxonomies)
| Таксономия | Тип | Применение |
|---|---|---|
| **Категории услуг** | Иерархическая | Полиграфия → Визитки → Крафт/Дизайнерский; Широкоформат → Баннеры → Пленка/Бумага |
| **Индустрии/Ниши** | Плоская | HoReCa, Риелторы, Строительство, Медicina, Образование, Ивенты, Ритейл |
| **Типы продуктов** | Плоская | Роллап, Х-стенд, Визитки, Календари, Наклейки, Флаги, Мерч |
| **Материалы** | Иерархическая | Бумага → Офсетная/Крафт/Дизайнерская; Пленка → Мономер/Полимер/Ламинированная |
| **Теги (Tags)** | Плоская | Для cross-linking: "срочная печать", "дизайн макета", "доставка Ижевск" |

---

## 🔗 Интеграция с основным сайтом (Bitrix)

### 1. Перелинковка (Cross-linking)
| Направление | Реализация |
|---|---|
| **Bitrix → WP** | В карточках товаров/категорий: блок "Статьи по теме" (WP REST API / WPGraphQL) |
| **WP → Bitrix** | В статьях/кейсах: кнопки "Рассчитать стоимость", "Заказать", виджет калькулятора (iframe/JS widget) |
| **Общий футер/хедер** | Единый дизайн, лого, контакты, навигация (общий компонент или синхронизация меню) |

### 2. Единая аналитика
```
GA4: 1 Property → 2 Data Streams (Web: bitrix, Web: wp)
- cross-domain tracking: gtag('config', 'G-XXXX', { 'groups': 'default', 'cookie_flags': 'SameSite=None;Secure' })
- _ga cookie: domain: .xn--18-6kc5a3bxam.xn--p1ai
Яндекс.Метрика: 1 счётчик на оба поддомена (настройка "Поддомены")
```

### 3. Поиск (Search)
- **Bitrix поиск** → ищет только каталог/товары
- **WP поиск** (Relevanssi / SearchWP) → ищет статьи, кейсы, глоссарий
- **Общий поиск** (опционально): Algolia / Meilisearch индексирует оба источника

### 4. Авторизация/Лид-формы
- Формы заявки на WP → POST на Bitrix API (`/api/lead/`) или вебхук в Битрикс24
- Общие UTM-метки, передача `client_id` (GA), `yclid` (Яндекс)

### 5. Sitemap & Robots
**WP (Yoast/RankMath):**
```
sitemap_index.xml → включает: posts, cases, services, materials, equipment, faq, glossary
robots.txt:
User-agent: *
Allow: /
Disallow: /wp-admin/
Disallow: /wp-json/ (optional)
Sitemap: https://blog.cifra18.рф/sitemap_index.xml
```

**Bitrix robots.txt:**
```
User-agent: *
Allow: /
Disallow: /bitrix/
Disallow: /personal/
Disallow: /search/
Sitemap: https://xn--18-6kc5a3bxam.xn--p1ai/sitemap.xml
Sitemap: https://blog.cifra18.рф/sitemap_index.xml
```

---

## 🤖 Программатик SEO на WP (Programmatic SEO)

### Источники данных
1. **Экспорт каталога Битрикс** → CSV: 300+ услуг с категориями, ценами, характеристиками
2. **Глоссарий терминов** → CSV: 200+ терминов полиграфии
3. **Комбинации Город × Услуга** → Ижевск + 10 пригородов × 20 топ-услуг = 200 страниц
4. **Сравнения** → X vs Y матрица (20 услуг × 20 = 400 комбинаций, отбираем топ-50)
5. **FAQ база** → 300+ вопросов из поддержки/менеджеров

### Генерация страниц (WP All Import + ACF)
```php
// Пример шаблона для "Услуга в городе" (service-city)
/*
Template Name: Service City Programmatic
*/
$service = get_field('service_ref'); // Post Object → Service Article
$city = get_field('city_ref');       // Taxonomy Term → City

// Title: "Печать визиток в Ижевске - цены, сроки, заказать онлайн | Цифра18"
// H1: "Печать визиток в Ижевске"
// Контент: общий блок про услугу + локальный блок (адрес, доставка, кейсы в городе)
// Schema: Service + LocalBusiness + FAQ
// Canonical: на основную страницу услуги на Bitrix? ИЛИ self-canonical если уникальный контент
```

### Стратегия Canonical для программатика
| Тип страницы | Canonical |
|---|---|
| Услуга в городе (локальный лендинг) | **Self-canonical** (уникальный локальный контент) |
| Сравнение X vs Y | **Self-canonical** (уникальный контент) |
| Глоссарий термина | **Self-canonical** |
| Материал/Оборудование | **Self-canonical** |
| Автогенерированные тонкие страницы | **Canonical на родительскую** (категорию на Bitrix) |

---

## 🧠 GEO / AI Optimization на WP

### 1. llms.txt (автогенерация)
```php
// Плагин или му-плагин: генерирует llms.txt при публикации/обновлении
// Структура:
# Типография Цифра (Ижевск) - llms.txt
## Услуги
- [Печать визиток](https://blog.cifra18.рф/services/vizitki/) - цифровая и офсетная печать, от 1 часа
- [Широкоформатная печать](https://blog.cifra18.рф/services/wide-format/) - баннеры, плакаты, пленки
...
## Кейсы
- [Кубик-трансформер для Россельхозбанка](https://blog.cifra18.рф/cases/rosselhoz-bank/)
...
## Контакты
- Телефон: +7 (965) 842-32-41
- Email: izhcifra@yandex.ru
- Адрес: Ижевск, ул. 7-я Подлесная, 34
```

### 2. Passage-level оптимизация (для AI citations)
- Каждый H2 = ответ на вопрос (Question heading)
- Первый абзац после H2 = прямой ответ (40-60 слов)
- Таблицы сравнения, списки, цифры с источниками
- FAQ блоки с `FAQPage` schema

### 3. Entity consistency
- Единый JSON-LD `Organization` на обоих доменах (same `@id`)
- `sameAs` профили синхронизированы
- Брендовые сущности в контенте: `[Цифра]`, `[ИП Данилов]`, `[Ижевск]`

---

## 📦 Миграция 290 статей с Bitrix на WP

### План миграции
1. **Экспорт из Битрикса** → CSV/XML: URL, Title, Content, Date, Author, Category, Tags, Images, SEO meta
2. **Чистка контента** → скрипт: замена em-dash, чистка Битрикс-классов, нормализация изображений
3. **Импорт в WP** → WP All Import: Posts + ACF fields (original_url, bitrix_id, seo_meta)
3. **301 Редиректы** → на Bitrix: `/news/old-slug/` → `https://blog.cifra18.рф/blog/new-slug/`
4. **Проверка** → Screaming Frog / seo_audit.py на новом домене
5. **GSC/Яндекс** → Change of Address (если меняется домен) или просто добавление нового sitemap

### Сохранение URL структуры (желательно)
```
Было: https://xn--18-6kc5a3bxam.xn--p1ai/news/17-07-26-plotternaya-rezka-listov-sra3/
Стало: https://blog.cifra18.рф/blog/plotternaya-rezka-listov-sra3/  (без даты в URL)
Редирект: 301 на новй URL
```

---

## 📅 План запуска поддомена

| Неделя | Задачи |
|---|---|
| **1** | Настройка WP сервера, SSL, DNS, базовая тема (GeneratePress/Blocksy + Child) |
| **1** | Установка плагинов, настройка ACF, CPT, таксономий |
| **1** | Дизайн: хедер/футер как на Bitrix, цветовая схема, типографика |
| **2** | Импорт 290 статей (WP All Import), настройка редиректов на Bitrix |
| **2** | Создание программатик шаблонов: Service City, Comparisons, Materials |
| **2** | Настройка Schema (Yoast/RankMath), llms.txt генератор |
| **3** | Запуск программатик: 50 Service City страниц, 30 Comparisons, 50 Materials |
| **3** | Настройка GA4 cross-domain, Яндекс.Метрика, IndexNow |
| **3** | Перелинковка Bitrix ↔ WP (блоки "Статьи по теме", виджеты калькулятора) |
| **4** | QA: Rich Results Test, PageSpeed, Mobile Friendly, seo_audit.py |
| **4** | Запуск контент-плана: 2 статьи/неделю + 1 программатик батч/месяц |

---

## 💰 Оценка ресурсов

| Ресурс | Оценка |
|---|---|
| **Dev setup (WP + Docker + CI/CD)** | 16-24 часа |
| **Тема + ACF + CPT настройка** | 16-24 часа |
| **Импорт 290 статей + редиректы** | 8-16 часов |
| **Программатик шаблоны (5 типов)** | 24-40 часов |
| **Интеграция (API, виджеты, аналитика)** | 16-24 часа |
| **QA + запуск** | 8-16 часов |
| **Итого** | **~80-140 часов** (2-3 недели 1 fullstack dev) |

---

## ❓ Открытые вопросы (уточнить у владельца)

1. **Поддомен:** `blog.cifra18.рф` или `articles.cifra18.рф` или `media.cifra18.рф`?
2. **Хостинг:** свой VPS / Cloudways / WP Engine / Kinsta?
3. **Тема:** GeneratePress / Blocks / Astra / кастомная на ACF Blocks?
4. **Сохранять ли даты в URL статей?** (сейчас `/news/17-07-26-slug/`)
5. **Калькулятор в статьях:** iframe с Bitrix / JS виджет / шорткод WP?
6. **Кто будет публиковать контент?** (внутренний контент-менеджер / агентство)
7. **Бюджет на плагины:** Yoast/RankMath Pro, ACF Pro, WP All Import Pro, WP Rocket?
8. **Нужен ли мультиязык?** (только RU или будет EN/KZ?)

---

*Документ будет обновляться после получения ответов. Следующий шаг: техническое ТЗ для WP разработчика.*