# Seed data - cifra18 (cifra18 / xn--18-6kc5a3bxam.xn--p1ai)

## Site identity
- Domain: cifra18.рф (punycode xn--18-6kc5a3bxam.xn--p1ai)
- Business: Tipografiya "Cifra", g. Izhhevsk, Udmurtiya
- Legal: IP Danilov Konstantin Leonidovich, INN 182501416864
- Phones: +7 (965) 842-32-41, +7 (3412) 32-32-41
- Email: izhcifra@yandex.ru
- Address: 426069, Udmurtskaya Resp, g. Izhevsk, ul. 7-ya Podlesnaya, d. 34
- CMS: Bitrix CMS 23.300 (1C-Bitrix), UTF_MODE=Y, SITE_ID=s1
- Analytics: Yandex.Metrika 50863157 (ecommerce=dataLayer), bitrix.info ba.js
- Template: /local/templates/cifra_new (custom Bitrix template)

## Site map (from live fetch)
- / - homepage
- /news/ - blog (H1 "Blog"), 22+ articles, last dated 17.07.26
- /portfolio/ - cases
- /video/ - video
- /about/ - company page (rekvizit, advantages, photo/video of production)
- /catalog/ - catalog root
  - /catalog/poligrafiya/ - printing (28 subcategories)
  - /catalog/suvenirnaya-produktsiya/ - souvenirs (28+)
  - /catalog/inzhenernaya-pechat/ - engineering print (5)
  - /catalog/shirokoformatnaya-pechat/ - wide-format (10)
  - /catalog/stendy/ - stands (5)
  - /catalog/interer/ - interior (6)
  - /catalog/mobilnye-stendy/ - mobile stands (11)
- /search/ - search form
- Product pages: /catalog/poligrafiya/vizitki/vizitki-na-krafte/ etc.

## robots.txt (measured)
```
User-agent: *
Allow: /
Crawl-delay:3
sitemap: https://xn--18-6kc5a3bxam.xn--p1ai/shop/sitemap.xml
sitemap: https://xn--18-6kc5a3bxam.xn--p1ai/shop/sitemapindex.xml
sitemap: https://xn--18-6kc5a3bxam.xn--p1ai/shop/sitemapmobileindex.xml
Sitemap: https://xn--18-6kc5a3bxam.xn--p1ai/shop/sitemap-hot-4040969.xml ... 4010969.xml (20 files)
```
- AI bots: NOT blocked (Allow: /) - good for GEO
- BUT: all 23 declared sitemaps return HTTP 404 (measured). Hard blocker - GSC will show "Sitemap not found".

## Collector results (seo_audit.py, 3 pages)
| Page | Title len | Meta desc | H1 | Headings | Images | Empty alt | Over 200KB | Words | Canonical | Schema |
|---|---|---|---|---|---|---|---|---|---|---|
| / | 62 OK | 11 "Description" BAD | 5 | 13, seq H2 H1 H2 H1x5 H2 H2 H3x4 | 83 | 13 | 11/15 | 1433 | NONE | none |
| /catalog/poligrafiya/vizitki/ | 68 OK | 206 TOO LONG | 2 | 21 | 34 | 5 | 9/15 | 1385 | NONE | none |
| /news/ | 7 "Novosti" BAD | 11 "Description" BAD | 1 (Blog) | 27 | 36 | 5 | 5/15 | 1445 | NONE | none |

Common: canonical absent on all pages; no JSON-LD schema anywhere; meta description = literal "Description" on / and /news/; no lazyload; em-dashes present (3 on /, 2 on vizitki, 19 on /news/).

## Known gaps (to verify)
- [ ] GSC indexation ratio - NOT MEASURED (need access)
- [ ] GA4 / Yandex.Metrika real traffic - NOT MEASURED
- [ ] PageSpeed scores - NOT MEASURED
- [ ] Backlink profile - NOT MEASURED
- [ ] Competitor keyword data - NOT MEASURED (Google search blocked from this env)
- [ ] GBP (Yandex.Karty) listing health - NOT MEASURED
- [ ] Real sitemap URLs - all 23 404, needs CMS fix
- [ ] News article URLs - /news/17-07-26-* returns 404, slug pattern unknown