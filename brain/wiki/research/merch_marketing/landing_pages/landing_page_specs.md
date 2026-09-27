# Landing Pages Specs — ЦИФРА18 Merch

**Date:** 2026-09-12  
**Purpose:** Technical specifications for merch landing pages (Service×City, Category, Bundle, Comparison)

---

## 🎯 Landing Page Types

| Page Type | Count | Template | Priority |
|---|---|---|---|
| **Service×City (Merch)** | 200 | ServiceCityMerch | 🔴 Critical |
| **Service×City (Print)** | 200 | ServiceCityPrint | 🔴 Critical |
| **Category Pages** | 7 | CategoryMerch | 🟠 High |
| **Comparison Pages** | 50 | Comparison | 🟠 High |
| **Bundle Pages** | 20 | BundlePage | 🟡 Medium |
| **Category Pages** | 7 | CategoryMerch | 🟠 High |
| **Industry Pages** | 10 | IndustryMerch | 🟡 Medium |
| **Bundle Pages** | 20 | BundlePage | 🟡 Medium |

---

## 🏗️ Page Template Architecture

### Base Template Structure

```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{H1} | Цифра18</title>
  <meta name="description" content="{Meta Description 120-160 chars}">
  <link rel="canonical" href="{Canonical URL}">
  
  <!-- JSON-LD Schema -->
  <script type="application/ld+json">
  {Schema.org JSON-LD}
  </script>
  
  <!-- Critical CSS (inline) -->
  <style>{Critical CSS}</style>
  
  <!-- Preload key resources -->
  <link rel="preload" as="image" href="{Hero Image}">
  <link rel="preload" as="style" href="/css/main.css">
  <link rel="preload" as="script" href="/js/calculator.js">
</head>
<body>
  <!-- Header (shared) -->
  <header class="header" role="banner">
    <!-- Logo, Nav, Phone, Calculator Link, Cart -->
  </header>
  
  <!-- Hero Section -->
  <section class="hero" aria-labelledby="hero-heading">
    <div class="container">
      <h1 id="hero-heading">{H1}</h1>
      <p class="lead">{Subheadline}</p>
      <div class="hero-cta-group">
        <a href="#calculator" class="btn btn-primary">Рассчитать стоимость</a>
        <a href="#catalog" class="btn btn-secondary">Посмотреть каталог</a>
      </div>
    </div>
  </section>
  
  <!-- Calculator Widget (above fold) -->
  <section id="calculator" class="calculator-section" aria-labelledby="calc-heading">
    <div class="container">
      <h2 id="calc-heading" class="visually-hidden">Калькулятор стоимости</h2>
      <div id="calculator-widget" data-service="{service}" data-city="{city}"></div>
    </section>
  
  <!-- Benefits/Trust Signals -->
  <section class="benefits" aria-labelledby="benefits-heading">
    <h2 id="benefits-heading" class="visually-hidden">Почему Цифра18</h2>
    <ul class="benefits-grid">
      <li><svg>...</svg><h3>Своё производство</li>
      <li><svg>...</svg><h3>Сроки от 1 часа</li>
      <li><svg>...</svg><h3>Доставка СДЭК по РФ</li>
      <li><svg>...</svg><h3>Помощь с макетом бесплатно</li>
    </ul>
  </section>
  
  <!-- Product Grid / Catalog -->
  <section id="catalog" class="catalog-section" aria-labelledby="catalog-heading">
    <h2 id="catalog-heading">{Category Title}</h2>
    <div class="product-grid" role="list">
      {Product Cards}
    </div>
    <a href="/catalog/{category}/" class="btn btn-outline">Все товары категории</a>
  </section>
  
  <!-- Comparison Table (if comparison page) -->
  <section class="comparison" aria-labelledby="comp-heading">
    <h2 id="comp-heading">Сравнение: {Product A} vs {Product B}</h2>
    <table class="comparison-table">
      <thead><tr><th>Характеристика</th><th>{Product A}</th><th>{Product B}</th></tr></thead>
      <tbody>{Comparison Rows}</tbody>
    </table>
  </section>
  
  <!-- FAQ Section (Schema.org FAQPage) -->
  <section class="faq" aria-labelledby="faq-heading">
    <h2 id="faq-heading">Частые вопросы</h2>
    <div class="faq-list" itemscope itemtype="https://schema.org/FAQPage">
      {FAQ Items with Schema.org markup}
    </ul>
  </section>
  
  <!-- Trust Signals / Social Proof -->
  <section class="social-proof" aria-labelledby="proof-heading">
    <h2 id="proof-heading">Что говорят клиенты</h2>
    <div class="reviews-carousel">
      {Review Cards with Schema.org Review markup}
    </div>
    <a href="/reviews/" class="btn btn-outline">Все отзывы</a>
  </section>
  
  <!-- Cross-sell / Bundle Section -->
  <section class="bundles" aria-labelledby="bundle-heading">
    <h2 id="bundle-heading">Популярные наборы</h2>
    <div class="bundles-grid">
      {Bundle Cards with Schema.org Product markup}
    </ul>
  </section>
  
  <!-- CTA Section -->
  <section class="cta-section" aria-labelledby="cta-heading">
    <h2 id="cta-heading">Готовы заказать?</h2>
    <p>Рассчитайте стоимость за 30 секунд</p>
    <a href="#calculator" class="btn btn-primary btn-lg">Рассчитать стоимость</a>
  </section>
  
  <!-- Footer (shared) -->
  <footer class="footer" role="contentinfo">
    <!-- Contact, Links, Social, Schema.org Organization -->
  </footer>
  
  <!-- JS Modules -->
  <script type="module" src="/js/calculator.js"></script>
  <script type="module" src="/js/bundle-builder.js"></script>
  <script type="module" src="/js/cross-sell.js"></script>
</body>
```

---

## 📋 Page Specifications by Type

### 1. Service×City Page (Merch) — `ServiceCityMerch`

| Element | Specification |
|---|---|
| **URL Pattern** | `/services/merch-{service}-{city}/` |
| **H1** | `{Service} в {City} — цены, сроки, доставка СДЭК | Цифра18` |
| **Title Tag** | `{Service} в {City} — цены, сроки, доставка СДЭК | Цифра18` (≤60 chars) |
| **Meta Description** | `{Service} в {City} от Цифра18: цены от {price}₽, сроки от 1 часа, доставка СДЭК по России. Калькулятор онлайн.` (120-160 chars) |
| **H1** | `{Service} в {City} — цены, сроки, доставка СДЭК` |
| **Schema.org** | `Service` + `LocalBusiness` + `FAQPage` + `Product` (for featured products) |
| **Calculator** | Embedded widget (service={service}, city={city}) |
| **Featured Products** | 3-5 top products for this service |
| **FAQ** | 3-5 questions (Schema.org FAQPage) |
| **Local Content** | SDEK PVZ addresses in city, delivery times, local cases |
| **Internal Links** | Calculator, Main service page, Category page, Comparison pages |
| **Schema.org** | `Service`, `LocalBusiness`, `FAQPage`, `Product` (featured), `BreadcrumbList` |

### 2. Category Page (Merch) — `CategoryMerch`

| Element | Specification |
|---|---|
| **URL** | `/services/merch-{category}/` |
| **H1** | `{Category Name} с логотипом — цены, каталог, доставка СДЭК` |
| **Schema** | `CollectionPage` + `ItemList` (Product) |
| **Content** | Category description, subcategories grid, featured products, buying guide |
| **Filters** | Price range, material, production time, delivery |
| **Sort** | Popularity, Price (asc/desc), Newest |
| **Schema** | `CollectionPage`, `ItemList` (Product), `BreadcrumbList` |

### 3. Comparison Page — `Comparison`

| Element | Specification |
|---|---|
| **URL** | `/compare/{product-a}-vs-{product-b}/` |
| **H1** | `{Product A} vs {Product B}: сравнение, цены, что выбрать` |
| **Schema** | `ComparisonPage` (custom) + `ItemList` (Product) |
| **Content** | Comparison table, decision framework, use cases, verdict |
| **Table Columns** | Parameter | Product A | Product B |
| **Schema** | Custom `ComparisonPage` + `ItemList` (Product) + `FAQPage` |

### 4. Bundle Page — `BundlePage`

| Element | Specification |
|---|---|
| **URL** | `/bundles/{bundle-slug}/` |
| **H1** | `{Bundle Name} — состав, цена, скидка {X}%` |
| **Schema** | `Product` (bundle as Product) + `Offer` (bundle offer) |
| **Content** | Bundle contents list, individual prices vs bundle price, savings calculator, use cases |
| **Bundle Builder** | Interactive "Build your own" widget |
| **Schema** | `Product` (bundle), `Offer` (bundle price), `ItemList` (components) |

---

## 🎨 Design System Specs

### Color Palette
| Role | Hex | Usage |
|---|---|---|
| **Primary** | `#1A1A2E` | Primary buttons, headers, links |
| **Primary Light** | `#2D2D4A` | Hover states |
| **Accent** | `#E8A838` | CTAs, highlights, accents |
| **Accent Light** | `#F5E6A0` | Hover on accent |
| **Background** | `#FFFFFF` | Page background |
| **Surface** | `#F8F9FA` | Cards, sections |
| **Text Primary** | `#1A1A2E` | Body text |
| **Text Secondary** | `#6B7280` | Secondary text, meta |
| **Border** | `#E5E7EB` | Borders, dividers |
| **Success** | `#10B981` | Success messages, in stock |
| **Warning** | `#F59E0B` | Low stock, warnings |
| **Error** | `#EF4444` | Errors, out of stock |

### Typography
| Element | Font | Size | Weight | Line Height |
|---|---|---|---|---|
| **H1** | Inter | 48px / 32px (mobile) | 700 | 1.1 |
| **H2** | Inter | 36px / 28px | 700 | 1.2 |
| **H3** | Inter | 24px / 20px | 600 | 1.3 |
| **H4** | Inter | 20px / 18px | 600 | 1.4 |
| **Body Large** | Inter | 20px / 18px | 400 | 1.6 |
| **Body** | Inter | 16px / 16px | 400 | 1.6 |
| **Body Small** | Inter | 14px / 14px | 400 | 1.5 |
| **Caption** | Inter | 12px / 12px | 400 | 1.4 |
| **Button** | Inter | 16px | 600 | 1.4 |

### Spacing Scale
| Token | Value | Usage |
|---|---|---|
| `space-xs` | 4px | Icon gaps |
| `space-sm` | 8px | Form fields, button padding |
| `space-md` | 16px | Card padding, form gaps |
| `space-lg` | 24px | Section gaps, card margins |
| `space-xl` | 32px | Section padding |
| `space-2xl` | 48px | Hero padding, section separation |
| `space-3xl` | 64px | Page-level separation |

### Breakpoints
| Breakpoint | Min Width | Columns |
|---|---|---|
| **Mobile** | 320px | 1 |
| **Tablet** | 768px | 2 |
| **Desktop** | 1024px | 3-4 |
| **Wide** | 1440px | 4-5 |

---

## ⚡ Performance Budget

| Metric | Budget | Measurement |
|---|---|---|
| **LCP** | < 2.5s | Lighthouse |
| **INP** | < 200ms | Lighthouse |
| **CLS** | < 0.1 | Lighthouse |
| **TTFB** | < 600ms | Lighthouse |
| **Total JS** | < 170 KB gzipped | Bundle analyzer |
| **Total CSS** | < 50 KB gzipped | Bundle analyzer |
| **Images** | WebP/AVIF, lazy-loaded | Lighthouse |
| **Fonts** | WOFF2, subset, preload | Lighthouse |

---

## ♿ Accessibility (WCAG 2.1 AA)

| Requirement | Implementation |
|---|---|
| **Color Contrast** | 4.5:1 normal text, 3:1 large text |
| **Keyboard Navigation** | All interactive elements focusable, visible focus |
| **Alt Text** | All images have descriptive alt |
| **Form Labels** | Every input has associated label |
| **ARIA Labels** | Icon buttons, complex widgets |
| **Focus Order** | Logical tab order |
| **Skip Link** | "Skip to main content" link |
| **Language** | `lang="ru"` on html |
| **Zoom** | Content readable at 200% zoom |
| **Motion** | Respects `prefers-reduced-motion` |

---

## 🔧 Component Library

### Calculator Widget
```jsx
// Props
interface CalculatorProps {
  service: string;        // service slug
  city?: string;          // city slug (optional)
  defaultParams?: {       // pre-fill from URL
    material?: string;
    quantity?: number;
    size?: string;
    printMethod?: string;
  };
  onCalculate: (result: CalculationResult) => void;
  onAddToCart: (items: CartItem[]) => void;
}

// Features:
// - Real-time price calculation
// - SDEK delivery cost (AJAX to API)
// - Material/print method selectors
// - Quantity with volume discounts
// - Add to cart / Get quote buttons
// - Save calculation (localStorage)
// - Share calculation (URL with params)
```

### Product Card
```jsx
interface ProductCardProps {
  product: Product;
  variant?: 'default' | 'compact' | 'featured';
  showAddToCart?: boolean;
  showQuickView?: boolean;
  crossSell?: CrossSellItem[];
}
```

### Bundle Card
```jsx
interface BundleCardProps {
  bundle: Bundle;
  showSavings?: boolean;
  showAddToCart?: boolean;
  variant?: 'default' | 'featured';
}
```

### Comparison Table
```jsx
interface ComparisonTableProps {
  products: Product[];
  attributes: ComparisonAttribute[];
  highlightBest?: boolean;
  stickyHeader?: boolean;
}
```

---

## 🧪 Testing Checklist

### Pre-Launch QA
- [ ] All pages return 200
- [ ] Canonical URLs correct
- [ ] Schema.org validates (Google Rich Results Test)
- [ ] Lighthouse score > 90 (Performance, Accessibility, Best Practices, SEO)
- [ ] Core Web Vitals pass (LCP < 2.5s, INP < 200ms, CLS < 0.1)
- [ ] Mobile usability (Google Mobile-Friendly Test)
- [ ] Schema.org validates (Schema Markup Validator)
- [ ] Sitemap.xml includes all new pages
- [ ] Robots.txt allows crawling
- [ ] IndexNow API ping successful
- [ ] GSC / Яндекс.Вебмастер sitemap submitted

### Cross-Browser Testing
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Chrome Mobile (iOS/Android)
- [ ] Safari Mobile (iOS)

---

## 📁 File Structure

```
/src
  /components
    /calculator
    /product-card
    /bundle-card
    /comparison-table
    /faq-accordion
    /review-carousel
    /bundle-builder
    /cross-sell
  /pages
    /service-city-merch
    /service-city-print
    /category-merch
    /comparison
    /bundle
    /category-merch
    /industry-merch
  /templates
    /service-city-merch.html
    /service-city-print.html
    /category-merch.html
    /comparison.html
    /bundle.html
    /category-merch.html
  /data
    /cities.csv
    /services.csv
    /materials.csv
    /bundles.json
    /cross-sell-rules.json
  /scripts
    /generate-service-city.py
    /generate-comparisons.py
    /generate-materials.py
    /generate-bundles.py
    /generate-glossary.py
    /generate-faq.py
    /generate-sitemap.py
    /qa-check.py
```

---

*Spec Version: 1.0*  
*Last Updated: 2026-09-12*  
*Next Review: After Phase 0 deployment*