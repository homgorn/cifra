# Competitors Index: ЦИФРА18

**Last updated:** 2026-09-11

---

## 📁 Структура конкурентного анализа

```
competitors/
├── INDEX.md                      # Этот файл
├── deep_analysis.md              # Глубокий разбор (Tier 1 Local + Tier 2 Federal)
├── local_izhevsk/                # Профили локальных конкурентов
│   ├── INDEX.md
│   ├── print_express.md
│   ├── spektra.md
│   ├── document_center.md
│   ├── udmurt_print.md
│   └── maximum.md
├── federal/                      # Профили федеральных конкурентов
│   ├── INDEX.md
│   ├── printio.md
│   ├── ruprint.md
│   ├── printback.md
│   └── aggregators.md
├── gap_analysis.md               # Keyword gap, Content gap, Backlink gap
├── serp_analysis.md              # SERP features по топ-ключам
├── pricing_audit.md              # Ценовой аудит (mystery shopping)
└── review_sentiment.md           # Анализ отзывов (Яндекс.Карты, 2ГИС, Google)
```

---

## 🎯 Статус анализа

| Анализ | Статус | Файл |
|---|---|---|
| **Глубинный разбор (Tier 1 + Tier 2)** | ✅ Готово | `deep_analysis.md` |
| **Локальные конкуренты (Ижевск)** | 🔄 Планируется | `local_izhevsk/` |
| **Федеральные конкуренты** | 🔄 Планируется | `federal/` |
| **Keyword Gap Analysis** | ⏳ Ждет Topvisor | `gap_analysis.md` |
| **Content Gap Analysis** | ⏳ Ждет Topvisor + Screaming Frog | `gap_analysis.md` |
| **Backlink Gap** | ⏳ Ждет Ahrefs/Яндекс.Вебмастер | `gap_analysis.md` |
| **SERP Features Audit** | ⏳ Ждет Topvisor | `serp_analysis.md` |
| **Pricing Audit** | ⏳ Mystery shopping | `pricing_audit.md` |
| **Review Sentiment** | ⏳ API + ручной | `review_sentiment.md` |

---

## 🏆 Competitive Landscape Summary (from deep_analysis.md)

### Tier 1: Local (Ижевск/Удмуртия), 5 ключевых игроков
| Competitor | Strength | Weakness | ЦИФРА Advantage |
|---|---|---|---|
| Принт-Экспресс | Speed 1hr, location | No wide-format, no merch, no SDEK | Full catalog, merch, SDEK |
| Спектр | Design + outdoor | No in-house print | In-house = lower cost |
| Документ | Engineering print | No marketing/merch | Full-stack |
| Удмуртпечать | Gov contracts | Old equipment, no digital | Modern + calculator |
| Максимум | Wide-format | No small-run, no calculator | Calculator + full range |

### Tier 2: Federal (Russia-wide, SDEK-enabled), 3 ключевых игрока
| Competitor | Model | Threat | ЦИФРА Counter |
|---|---|---|---|
| **Printio** | POD Marketplace | 🔴 HIGH (merch) | Full-service: offset + wide + engineering + consulting |
| **Визитка.ру / Ruprint** | Online print shop | 🟠 HIGH (paper) | Paper + Merch + Outdoor under one roof |
| **Яндекс.Услуги / Авито** | Aggregator | 🟠 MEDIUM (local) | Build own organic + direct channels |

### Positioning Matrix
| Dimension | ЦИФРА | Printio | Ruprint | Local |
|---|---|---|---|---|
| **Product Range** | Paper + Merch + Outdoor + Engineering | Merch + Paper (POD) | Paper + Limited Wide | Niche |
| **Production** | In-house (all) | Outsourced | Partners | Limited |
| **Calculator** | Full (all categories) | Merch only | Paper only | Basic/None |
| **Delivery** | SDEK (Russia) | SDEK/CDEK | SDEK/Boxberry | Local only |
| **B2B Service** | Personal manager | API/Self-serve | Self-serve | Walk-in |
| **Speed** | 1hr + SDEK 1-3d | 3-5 days | 2-4 days | 1hr (digital only) |

---

## 🔍 Intelligence Gaps (What We Need)

| Intelligence | Source | Priority |
|---|---|---|
| **Topvisor competitor export** | Topvisor API (need access) | 🔥 Critical |
| **Ahrefs/Serpstat export** | Ahrefs/Serpstat subscription | 🟡 High |
| **SDEK tariff comparison** | SDEK API + competitor checkout | 🟡 High |
| **Competitor pricing audit** | Manual mystery shopping | 🟡 High |
| **Competitor content audit** | Screaming Frog + ручной | 🟡 High |
| **Review sentiment analysis** | Яндекс.Карты, 2ГИС, Google Maps | 🟡 High |
| **Backlink profile** | Ahrefs/Яндекс.Вебмастер | 🟡 High |

---

## 🛡 Defensive Moats to Build

| Moat | How to Build | Timeline |
|---|---|---|
| **Calculator as SEO asset** | Schema-rich, FAQ, comparison tables, SDEK integration | Phase 1 |
| **SDEK integration** | Real-time tariff, tracking widget, webhook → CRM | Phase 1-2 |
| **Corporate merch program** | Volume discounts, dedicated manager, design help, SDEK | Phase 2 |
| **Local dominance** | GBP/Yandex Maps: 100+ reviews, photos, posts, Q&A | Phase 0-1 |
| **Expert content** | Technologist blog, material guides, GOST explanations | Phase 2 |
| **SDEK-ready schema** | Product + Offer + shippingDetails on all PDPs | Phase 1 |
| **Referral program** | B2B partners (agencies, designers, event co's) commission | Phase 3 |

---

## 📊 Competitor Tracking Dashboard (To Build)

| Metric | Frequency | Tool |
|---|---|---|
| **Visibility % (Topvisor)** | Daily | Topvisor API |
| **Top-10 keywords count** | Weekly | Topvisor |
| **New content published** | Weekly | Screaming Frog + RSS |
| **Backlinks gained/lost** | Weekly | Ahrefs/Яндекс.Вебмастер |
| **Review count/sentiment** | Monthly | Яндекс.Карты API + 2ГИС |
| **SDEK delivery cities** | Quarterly | SDEK API |
| **Pricing changes** | Monthly | Mystery shopping |

---

## 🚀 Next Actions

1. **Get Topvisor access** → export competitor data
2. **Run competitive-analysis skill** with exported data
3. **Run competitor-profiling** for top 5 federal + top 5 local
4. **Build competitor keyword gap report** → feed into keyword research
5. **Mystery shop top 3 federal** → pricing, UX, delivery, support
6. **Build competitive positioning deck** for sales team

---

*This analysis feeds directly into: keyword research, content strategy, programmatic SEO (Service×City), offer packaging, and SDEK integration specs.*