# Landing Pages — ЦИФРА18 Merch Marketing

**Date:** 2026-09-12  
**Location:** `brain/wiki/research/merch_marketing/landing_pages/`

---

## 📁 Files in This Directory

| File | Description |
|---|---|
| `landing_page_specs.md` | Technical specifications for all landing page types |

---

## 🎯 Landing Page Types & Specs

### 1. Service×City Pages (Merch) — 200 pages
| Spec | Detail |
|---|---|
| **URL Pattern** | `/services/merch-{service}-{city}/` |
| **H1** | `{Service} в {City} — цены, сроки, доставка СДЭК` |
| **Schema** | Service + LocalBusiness + FAQPage + Product |
| **Calculator** | Embedded (service + city pre-filled) |
| **Local Content** | SDEK PVZ addresses, delivery times, local cases |

### 2. Service×City Pages (Print) — 200 pages
| Spec | Detail |
|---|---|
| **URL Pattern** | `/services/print-{service}-{city}/` |
| **H1** | `Печать {service} в {City} — цены, сроки, доставка СДЭК` |
| **Schema** | Service + LocalBusiness + FAQPage + Product |

### 3. Category Pages (Merch) — 7 pages
| Category | URL |
|---|---|
| Одежда | `/services/merch-apparel/` |
| Посуда | `/services/merch-drinkware/` |
| Аксессуары | `/services/merch-accessories/` |
| Канцелярия | `/services/merch-office/` |
| Сумки и упаковка | `/services/merch-bags/` |
| Премиальные подарки | `/services/merch-premium/` |
| Корп. программы | `/services/merch-corporate/` |

### 4. Comparison Pages — 50 pages
| Format | Example URLs |
|---|---|
| X vs Y | `/compare/futbolka-vs-xudi/`, `/compare/kruzhka-vs-termokruzhka/` |
| Alternatives | `/alternatives/to-printio/`, `/alternatives/to-ruprint/` |
| Best for | `/best-merch-for-hr/`, `/best-merch-for-events/` |

### 5. Bundle Pages — 20 pages
| Bundle | URL |
|---|---|
| Startup Welcome Kit | `/bundles/startup-welcome-kit/` |
| Remote Work Kit | `/bundles/remote-work-kit/` |
| Event Kit | `/bundles/event-kit/` |
| Premium Gift Box | `/bundles/premium-gift-box/` |
| Corporate Welcome Kit | `/bundles/corporate-welcome-kit/` |
| VIP Gift Box | `/bundles/vip-gift-box/` |
| Event Kit | `/bundles/event-kit/` |
| Remote Work Kit | `/bundles/remote-work-kit/` |
| Merch Subscription | `/bundles/merch-subscription/` |

### 5. Industry Pages — 10 pages
| Industry | URL |
|---|---|
| HoReCa | `/industries/horeca/` |
| Real Estate | `/industries/real-estate/` |
| Construction | `/industries/construction/` |
| Medical | `/industries/medical/` |
| Education | `/industries/education/` |
| Events | `/industries/events/` |
| Tech/IT | `/industries/tech/` |
| Finance | `/industries/finance/` |
| Retail | `/industries/retail/` |
| Corporate | `/industries/corporate/` |

---

## 🎯 Page Template Specifications

### Service×City Page (Merch)
```
H1: {Service} в {City} — цены, сроки, доставка СДЭК
Meta: {Service} в {City} от Цифра18: цены от {price}₽, сроки от 1 часа, доставка СДЭК по России.

Sections:
1. Hero + Calculator embed
2. Benefits (4 icons)
3. Featured Products (3-5 cards)
3. Calculator embed (pre-filled)
4. Local content (SDEK PVZ, delivery times)
5. FAQ (3-5 questions, Schema FAQPage)
6. Social proof (reviews, cases)
7. Cross-sell bundles
8. CTA section
8. Footer
```

### Schema.org (Required)
- Service
- LocalBusiness  
- FAQPage
- Product (for featured products)
- BreadcrumbList
- Organization (global)

---

## 🎯 Quick Reference: Page Counts

| Type | Count | Priority |
|---|---|---|
| Service×City Merch | 200 | 🔴 Critical |
| Service×City Print | 200 | 🔴 Critical |
| Category Merch | 7 | 🟠 High |
| Comparison | 50 | 🟠 High |
| Bundle Pages | 20 | 🟡 Medium |
| Industry | 10 | 🟡 Medium |
| **Total** | **~487** | |

---

*Location: `brain/wiki/research/merch_marketing/landing_pages/`*  
*Updated: 2026-09-12*