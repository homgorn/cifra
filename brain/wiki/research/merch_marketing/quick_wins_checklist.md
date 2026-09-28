# Quick Wins Checklist: ЦИФРА18 Merch Marketing

**Date:** 2026-09-12  
**Purpose:** 30-day action plan for immediate impact  
**Status:** Ready to execute

---

## 🎯 Week 1 (Days 1-7): Foundation & Quick Wins

### Day 1-2: Technical Foundation
- [ ] **Fix sitemap generation** in Bitrix (all 19 sitemaps return 404, checked 2026-09-28)
  - Admin → Settings → SEO → Sitemap: enable generation, path `/sitemap.xml`
  - Verify `/sitemap.xml` returns 200 OK with valid XML
  - Update robots.txt with correct sitemap URLs
  - Submit to GSC + Яндекс.Вебмастер + Bing Webmaster Tools

- [ ] **Add canonical tags** to all pages
  - Edit `/local/templates/cifra_new/header.php`
  - Add: `<link rel="canonical" href="<?= $APPLICATION->GetCurPageParam('', ['PAGEN_1', 'SORT', 'ORDER', 'set_filter', 'clear_cache'], true) ?>">`
  - Verify on 10 random pages

- [ ] **Fix meta description placeholder**
  - Main page: replace "Description" with unique 150-char description
  - Blog pages: replace "Description" with unique descriptions
  - Catalog pages: auto-generate from first 160 chars of description

- [ ] **Fix H1 hierarchy on homepage**
 - Keep 1 H1: "Типография «Цифра», цифровая и широкоформатная печать в Ижевске"
  - Change other H1s to H2: "Сервис", "Качество и скорость", "Отзывы", "Новости", "Продукция"

### Day 3-4: Schema.org Deployment
- [ ] **Deploy JSON-LD templates** (5 types)
  - Organization + LocalBusiness (header/footer)
  - Product (PDP pages)
  - Article (blog posts)
  - BreadcrumbList (all pages)
  - FAQPage (FAQ sections)

- [ ] **Validate Schema.org**
  - Test 10 URLs in Google Rich Results Test
  - Fix all errors/warnings
  - Document in `/scripts/dev-fixes/schema_templates/`

### Day 5: Analytics & Tracking Setup
- [ ] **GA4 + GSC + Яндекс.Вебмастер + Bing + IndexNow**
  - GA4 property created, enhanced ecommerce enabled
  - GSC property verified (DNS/HTML tag)
  - Яндекс.Вебмастер verified (meta tag/file)
  - Bing Webmaster Tools verified
  - IndexNow API key configured

- [ ] **Baseline monitoring capture**
  ```bash
  python3 scripts/monitoring/drift_monitor.py --baseline
  python3 scripts/monitoring/tech_health.py
  ```

### Day 6-7: Quick Content Wins
- [ ] **Fix em-dash (—) → comma** across all pages
  - Find/replace in Bitrix templates and content
  - Check: 3 on homepage, 19 on news page, 2 on product page

- [ ] **Add lazy-loading** to images below fold
  - Template edit: `loading="lazy"` for images below fold
  - Keep hero images eager-loaded

- [ ] **Add width/height attributes** to all images
  - Prevent CLS (Cumulative Layout Shift)

---

## 🎯 Week 2 (Days 8-14): Merch Foundation

### Day 8-10: Merch Calculator + SDEK Integration
- [ ] **Integrate SDEK API** into calculator
  - Tariff calculator endpoint
  - City autocomplete (SDEK cities API)
  - Delivery time display
  - Free shipping threshold logic

- [ ] **Merch Calculator UI**
  - Product selector (category → product)
  - Material selector
  - Quantity with volume discounts
  - Real-time price + delivery calculation
  - "Add to cart" / "Get quote" buttons

- [ ] **Schema.org shippingDetails** on all PDP
  - Product + Offer + shippingDetails JSON-LD
  - SDEK tariff in structured data

### Day 11-12: Merch Landing Pages (Top 10)
- [ ] **Create 10 Service×City pages** (top 5 cities × top 2 services)
  - `/services/merch-futbolki-moskva/`
  - `/services/merch-kruzhki-sankt-peterburg/`
  - `/services/merch-xudi-ekaterinburg/`
  - `/services/merch-ryukzaki-novosibirsk/`
  - `/services/merch-sumki-toty-kazan/`
  - + 5 more

- [ ] **Each page includes:**
  - H1 with city + service
  - Calculator embed
  - Local SDEK PVZ addresses (top 3)
  - Delivery times for city
  - Local case study/testimonial
  - Schema.org Service + LocalBusiness + FAQPage

### Day 13-14: Merch Bundles & Cross-sell
- [ ] **Create 5 bundle pages**
  - Startup Welcome Kit
  - Remote Work Kit
  - Event Kit
  - Premium Gift Box
  - Corporate Welcome Kit

- [ ] **Cross-sell rules in calculator/cart**
  - Implement rules from `cross_sell_matrix.md`
  - "Frequently bought together" on PDP
  - Bundle discount auto-applied in cart

---

## 🎯 Week 3 (Days 15-21): Content & Programmatic Scale

### Day 15-17: Content Factory Launch
- [ ] **Publish 5 expert articles** (from content_plan.md)
  - "Чек-лист: подготовка макета для мерча"
  - "Полиэстер vs Хлопок: что выбрать для мерча"
 - "Кейс: мерч для кофейни: кружки на 30% чек"
  - "Service×City: Мерч с логотипом Москва"
  - "Сравнение: Футболка vs Худи vs Лонгслив"

- [ ] **Set up Content Factory**
  - Brief template in Notion
  - SME interview schedule (technologist, designer)
  - GEO QA checklist (5 pillars)
  - Schema validation pre-publish

### Day 18-19: Programmatic SEO Launch (First 50 pages)
- [ ] **Generate Service×City pages** (20 cities × 5 services = 100 pages)
  - Run `python scripts/programmatic/generate_service_city.py`
  - Validate schema on 10 sample pages
  - Submit sitemap to GSC + Яндекс.Вебмастер

- [ ] **Generate Material pages** (20 pages)
  - `/materials/kraft-265/`, `/materials/pvh-plenka/`, etc.
  - Schema: Product + Material specs

- [ ] **Generate Glossary pages** (20 terms)
  - `/glossary/dtg/`, `/glossary/sublimation/`, etc.
  - Schema: DefinedTerm

### Day 20-21: Comparison & FAQ Pages
- [ ] **10 comparison pages**
  - "Футболка vs Худи", "Кружка vs Термос", "Рюкзак vs Сумка-тота"
  - Schema: ComparisonPage + FAQPage

- [ ] **20 FAQ pages** from PAA
  - Auto-generated from People Also Ask
  - Schema: FAQPage

---

## 🎯 Week 4 (Days 22-30): Authority, SDEK, Email

### Day 22-24: SDEK Full Integration
- [ ] **SDEK tracking widget** in user cabinet
- [ ] **Email/SMS notifications** (webhook handlers)
- [ ] **Pickup point map** on checkout
- [ ] **Free shipping threshold** logic (configurable)

### Day 25-26: Email Sequences Launch
- [ ] **Set up ESP** (Customer.io / Resend / SendGrid)
  - Domain authentication (DKIM, SPF, DMARC)
  - Subdomain: `mail.cifra18.ru`
  - Suppression list import

- [ ] **Deploy 7 sequences** (from `email_sequences/`)
  - Welcome (5 emails)
  - Quote Nurture (5)
  - Post-Order (6)
  - Re-engagement (4)
  - Loyalty/Referral (4)
  - Abandoned Calculator (3)
  - Seasonal (4/quarter)

- [ ] **Set up segments & automation**
  - New leads → Welcome
  - Quote sent → Quote Nurture
  - Order placed → Post-Order
  - Delivered → Review Request (delay 3 days)
  - 30/60/90 days inactive → Re-engagement

### Day 27-28: Programmatic Scale (100+ pages)
- [ ] **Generate remaining Service×City** (150 pages)
- [ ] **Generate Materials** (30 pages)
- [ ] **Generate Glossary** (50 terms)
- [ ] **Generate FAQ** (50 pages)
- [ ] **Generate Comparisons** (20 pages)

### Day 29-30: SDEK API + Monitoring Go Live
- [ ] **SDEK webhook endpoint** live
- [ ] **Tracking widget** in user cabinet
- [ ] **Email/SMS notifications** via webhook
- [ ] **Monitoring stack live**
  - `tech_health.py` daily 03:00
  - `drift_monitor.py` daily 04:00
  - `rankings_pull.py` daily 05:00
  - `log_analyzer.py` daily 06:00
  - `geo_tracker.py` weekly Mon 07:00
  - `content_inventory.py` weekly Tue 07:00

- [ ] **Alerting live**
  - Telegram bot configured
  - Critical alerts → Telegram + PagerDuty
  - Warning alerts → Telegram

---

## ✅ 30-Day Success Criteria

| Metric | Target | Measurement |
|---|---|---|
| **Technical SEO** | 0 Blocking issues | seo-geo-audit re-run |
| **Schema Coverage** | 100% money pages | Rich Results Test |
| **Merch SKU** | 50+ | Catalog audit |
| **Service×City Pages** | 100+ indexed | GSC Index Coverage |
| **Merch Calculator** | Live + SDEK | Manual test 10 cities |
| **Email Sequences** | 7 live | ESP dashboard |
| **Email List** | 100+ subscribers | ESP dashboard |
| **Content Published** | 20+ articles | CMS + sitemap |
| **SDEK Integration** | Live + tracking | Test order → delivery |
| **Monitoring** | Live + alerting | Telegram test alert |

---

## 🚀 Post-30 Days (Month 2-3)

| Week | Focus |
|---|---|
| **Week 5-6** | Content factory at full speed (8 articles/mo), 200+ programmatic pages |
| **Week 7-8** | HR Merch Program launch, Corporate merch plans, Referral program |
| **Month 3** | SDEK marketplace partnership, Affiliate program, Corporate merch plans |
| **Month 4-6** | Scale to 200 SKU, 200+ programmatic pages, 35% merch revenue share |

---

## 📋 Daily Standup Template (for team)

```
Date: ____
✅ Yesterday: 
- [ ] Task 1
- [ ] Task 2

🎯 Today:
- [ ] Task 1
- [ ] Task 2

🚧 Blockers:
- [ ] Blocker 1 → Owner: ___ ETA: ___

📊 Metrics:
- Organic traffic: ___
- Calculator sessions: ___
- Leads: ___
- Orders: ___
```

---

*Checklist Version: 1.0*  
*Last Updated: 2026-09-12*  
*Owner: Marketing Lead*