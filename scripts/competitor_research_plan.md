# Competitor Research Plan — 50+ Competitors in Izhevsk

## Phase 1: Discover All Competitors (Week 1)

### Chunk 1: Direct Competitors in Izhevsk (Typeography/Print) — Target: 20-25
- Search 2GIS / Yandex Maps for "типография Ижевск"
- Search Google for "типография Ижевск печать визиток"
- Search Yandex for "широкоформатная печать Ижевск"
- Search for "печатная продукция Ижевск"
- Search "мерч Ижевск", "сувенирка Ижевск"
- Search "баннеры Ижевск", "роллапы Ижевск"

### Chunk 2: Regional/National Competitors with Delivery to Izhevsk — Target: 15-20
- Printio, RuPrint, Printful, Canva Print
- Regional print shops with delivery
- Marketplace sellers (WB, Ozon) for merch

### Chunk 3: Niche/Specialized Competitors — Target: 10
- Engineering print (drawings, scanning)
- Packaging specialists
- Promo merchandise specialists
- Corporate gift companies

---

## Phase 2: Deep Profiling (Using competitor-profiling skill)

For each competitor, create profile with:
1. **Website analysis** (homepage, pricing, services, about)
2. **SEO data** (keywords, traffic, backlinks via Topvisor/Topvisor API)
3. **Pricing audit** (mystery shopping for key products)
4. **Review sentiment** (2GIS, Yandex Maps, Google Maps)
5. **Content strategy** (blog, social media, SEO content)

---

## Phase 3: Email Marketing Setup

### Incoming Email Analysis
- Export all incoming emails (IMAP/IMAP)
- Categorize by: leads, support, spam, newsletters, orders
- Identify patterns: FAQ topics, objections, buying signals
- Build knowledge base from real customer questions

### Email Marketing Strategy
1. **Welcome sequence** for new leads (5 emails)
2. **Lead nurture** for quote requests (5 emails)
3. **Post-order** sequence (confirmation → production → delivery → review)
5. **Re-engagement** for old leads (30/60/90 days)
6. **Post-purchase** review request + referral
6. **Educational newsletter** (monthly) — expert tips, materials, cases
7. **Seasonal campaigns** (New Year calendars, March 8 gifts, September school print)

### Automation Setup
- Welcome → Lead Nurture → Quote → Order → Delivery → Review → Referral
- Segments: New leads, Quoted no order, Ordered once, Repeat customers, Lost deals
- Triggers: Quote sent, Order placed, Delivered, 30 days no activity

---

## Execution Order (This Week)

### Today (Chunk 1): Discover Izhevsk Competitors
- [ ] 2GIS scraping: "типография Ижевск" → 50+ results
- [ ] Yandex Maps: "типография Ижевск" 
- [ ] Google: "типография Ижевск цены", "печать визиток Ижевск"
- [ ] Compile master list with URLs

### Tomorrow (Chunk 2): Federal/Regional Competitors
- [ ] Printio, RuPrint, Printful, Canva Print, Printback
- [ ] Regional print shops with SDEK delivery
- [ ] Marketplace analysis (WB/Ozon merch)

### Day 3-4: Deep Profiling (10-15 per day)
- Use competitor-profiling skill template
- Save raw data to `competitor-profiles/raw/`
- Build profiles with SEO, pricing, content, reviews

### Day 5-6: Email Marketing Setup
- Analyze incoming email base (export from mail server)
- Build welcome/nurture sequences using newsletter-writer skill
- Design email templates for each sequence
- Set up automation in available tool (Customer.io / Resend / SendGrid)

---

## Email Marketing from Incoming Emails

### Step 1: Export & Categorize
```bash
# Export from mail server (IMAP)
# Categories:
# 1. New inquiries (quote requests)
# 2. Existing orders (status updates)
# 3. Support/complaints
# 4. Spam/newsletters
# 5. Partner/vendor emails
```

### Step 2: Analyze & Build Knowledge Base
- Top 50 questions from incoming emails → FAQ content
- Top 20 objections → Email sequence content
- Common pricing questions → Calculator improvements
- Seasonal patterns → Campaign calendar

### Step 3: Build Sequences
1. **Welcome** (5 emails): Welcome → Story → Best Content → Social Proof → Soft Offer
2. **Quote Nurture** (5 emails): Thanks → Value → Case Study → FAQ → Direct CTA
3. **Post-Order** (5 emails): Confirmation → Production → Shipping → Delivered → Review
4. **Re-engagement** (30/60/90 days): Check-in → Value → Last Chance
5. **Post-Purchase**: Delivery confirmation → Review request → Referral

### Quick Wins from Email Base
- Top 20 FAQ → Blog posts + FAQ schema
- Top 10 objections → Email sequence + landing page copy
- Seasonal peaks → Campaign calendar
- Partner/vendor emails → Partnership outreach list