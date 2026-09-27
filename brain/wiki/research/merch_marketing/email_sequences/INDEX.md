# Email Sequences — ЦИФРА18 Merch Marketing

**Date:** 2026-09-12  
**Location:** `brain/wiki/research/merch_marketing/email_sequences/`

---

## 📧 Email Sequences Overview

| Sequence | Emails | Duration | Trigger | Goal |
|---|---|---|---|---|
| **Welcome** | 5 | 14 days | Form submit / Lead magnet download | Activate, educate, convert |
| **Quote Nurture** | 5 | 10 days | Quote sent, no order | Overcome objections, close |
| **Post-Order** | 6 | 21 days | Order placed | Transparency, loyalty, review |
| **Re-engagement** | 4 | 30 days | 30/60/90 days inactive | Win back |
| **Loyalty & Referral** | 4 | Ongoing | Post-purchase / Milestone | LTV increase, referrals |
| **Seasonal** | 4/quarter | Seasonal | Calendar events | Seasonal revenue |
| **Abandoned Calculator** | 3 | 7 days | Calculator used, no quote | Recover abandoned |

---

## 📁 Files in This Directory

| File | Description |
|---|---|
| `welcome_sequence.md` | 5-email welcome sequence with templates |
| `quote_nurture.md` | 5-email quote nurture sequence |
| `post_order.md` | 6-email post-order sequence |
| `reengagement.md` | 4-email re-engagement sequence |
| `loyalty_referral.md` | Loyalty & referral emails |
| `abandoned_calculator.md` | 3-email abandoned calculator recovery |
| `seasonal.md` | Quarterly seasonal campaigns |

---

## 📋 Quick Reference: All Sequences

### 1. Welcome Sequence (5 emails / 14 days)
| Email | Day | Subject | CTA |
|---|---|---|---|
| 1 | 0 | Welcome + Price Guide PDF | Download price guide |
| 2 | 1 | Behind the scenes: Production tour | Virtual tour |
| 3 | 3 | 3 mistakes in layouts + Checklist PDF | Download checklist |
| 4 | 5 | Case study: 5000 cards in 3 hours | View case study |
| 5 | 7 | Promo code WELCOME5 (5% off) | Order with discount |

### 2. Quote Nurture (5 emails / 10 days)
| Email | Day | Subject | CTA |
|---|---|---|---|
| 1 | 0 | Your quote is ready | Order now |
| 2 | 2 | Why kraft is best for you | Learn more |
| 3 | 4 | Case study: Realtor +20% calls | View case |
| 4 | 6 | FAQ: 5 questions before ordering | Order now |
| 5 | 8 | Promo WELCOME5 expires Friday | Order with discount |

### 3. Post-Order (6 emails / 21 days)
| Email | Trigger | Subject | CTA |
|---|---|---|---|
| 1 | Order placed | Order confirmed + tracking link | Track order |
| 2 | Production start | Order in production | View progress |
| 3 | Shipped | Ready! SDEK tracking | Track SDEK |
| 4 | Delivered | Delivered! Rate us → 5% off | Leave review |
| 5 | Day 7 | How's it working? | Share results |
| 6 | Day 21 | Reorder discount 10% | Reorder |

### 4. Re-engagement (4 emails / 30 days)
| Email | Day | Subject | CTA |
|---|---|---|---|
| 1 | 30 | We miss you! Everything OK? | "All good" / Unsubscribe |
| 2 | 45 | What's new this month | View updates |
| 3 | 60 | 10% comeback discount | Use RETURN10 |
| 4 | 90 | Last chance - we'll remove you | Keep me / Goodbye |

### 5. Loyalty & Referral (Ongoing)
| Email | Trigger | Subject | CTA |
|---|---|---|---|
| Review Request | Day 3 post-delivery | How was quality? Rate us → 5% off | Leave review |
| Referral | Day 14 | Invite colleague → 500₽ credit | Refer friend |
| Reorder Reminder | Day 60/90/180 | Running low? Reorder 10% off | Reorder |
| Seasonal | Calendar | Holiday campaigns | Shop seasonal |

### 6. Abandoned Calculator (3 emails / 7 days)
| Email | Day | Subject | CTA |
|---|---|---|---|
| 1 | 1 | You calculated merch cost - don't forget to order! | Complete order |
| 2 | 3 | Your calc saved: 100 kraft cards = 450₽ | Complete order |
| 3 | 7 | Last chance: 5% off this calc expires tomorrow | Use SAVE5 |

---

## 📊 Performance Targets

| Sequence | Open Rate | CTR | Conversion | Revenue/Email |
|---|---|---|---|---|
| Welcome | 35% | 5% | 8% | 500₽ |
| Quote Nurture | 30% | 8% | 15% | 1,200₽ |
| Post-Order | 50% | 15% | 20% (review) | 300₽ |
| Re-engagement | 20% | 5% | 10% | 800₽ |
| Loyalty/Referral | 40% | 10% | 15% | 2,000₽ |
| Abandoned Calc | 25% | 10% | 12% | 600₽ |

---

## 🛠 Implementation Checklist

- [ ] ESP Setup (Customer.io / Resend / SendGrid)
- [ ] Domain auth (DKIM, SPF, DMARC)
- [ ] Subdomain: `mail.cifra18.ru`
- [ ] Segments created in ESP
- [ ] Sequences built in ESP
- [ ] Webhooks configured (quote.sent, order.placed, order.delivered)
- [ ] A/B tests configured (Welcome subject lines)
- [ ] Tracking UTM parameters
- [ ] Suppression list imported
- [ ] Test sends to internal team
- [ ] Launch 🚀

---

*Location: `brain/wiki/research/merch_marketing/email_sequences/`*  
*Updated: 2026-09-12*