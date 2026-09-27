import json
import csv
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Metric semantics (verified 2026-09-23 by cross-checking same query/day):
# - *_66ca0f04...csv  = SHOWS (impressions) per day, integers
# - *_33851bbe...csv  = AVG POSITION per day, decimals
# - *_2644f2f7...csv  = CLICKS per day, sparse small ints
# parsed_data.json keys: queries_pos = shows (66ca), queries_avg = positions (3385)

DAYS = ['2026-09-14', '2026-09-15', '2026-09-16', '2026-09-17',
        '2026-09-18', '2026-09-19', '2026-09-20']


def safe_val(v):
    if isinstance(v, list):
        return None
    if not v or not v.strip():
        return None
    try:
        return float(v)
    except:
        return None


def daily_vals(row):
    vals = {}
    for d in DAYS:
        v = safe_val(row.get(d))
        if v is not None:
            vals[d] = v
    return vals


with open('webmaster/parsed_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

pages = data['pages']
shows_rows = data['queries_pos']
pos_rows = data['queries_avg']
structure = data['structure']
events = data['events']

with open('webmaster/цифра18.рф_2644f2f73b3615228c8ce777.csv', 'r', encoding='utf-8-sig') as f:
    clicks_rows = list(csv.DictReader(f))

shows_by_q = {r['Query']: daily_vals(r) for r in shows_rows}
pos_by_q = {r['Query']: daily_vals(r) for r in pos_rows}
clicks_by_q = {r['Query']: daily_vals(r) for r in clicks_rows}

queries = sorted(set(shows_by_q) | set(pos_by_q) | set(clicks_by_q))


def summarize(q):
    pv = list(pos_by_q.get(q, {}).values())
    sv = list(shows_by_q.get(q, {}).values())
    cv = list(clicks_by_q.get(q, {}).values())
    pos_avg = round(sum(pv) / len(pv), 2) if pv else None
    return {
        'pos_avg': pos_avg,
        'pos_min': min(pv) if pv else None,
        'pos_max': max(pv) if pv else None,
        'pos_days': len(pv),
        'shows': int(sum(sv)) if sv else 0,
        'clicks': int(sum(cv)) if cv else 0,
        'ctr': round(sum(cv) / sum(sv) * 100, 1) if sv and sum(sv) else 0.0,
    }


# 1. all_queries_positions.csv (positions + shows + clicks + CTR)
with open('brain/wiki/webmaster_analytics/exports/all_queries_positions.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Query', 'Avg_Position', 'Min_Position', 'Max_Position', 'Days_With_Data',
                     'Shows_Total', 'Clicks_Total', 'CTR_%', 'Positions_Detail'])
    for q in queries:
        s = summarize(q)
        if s['pos_avg'] is None:
            continue
        detail = '; '.join('%s:%s' % (d, v) for d, v in pos_by_q[q].items())
        writer.writerow([q, s['pos_avg'], s['pos_min'], s['pos_max'], s['pos_days'],
                         s['shows'], s['clicks'], s['ctr'], detail])

# 2. searchable_pages.csv
with open('brain/wiki/webmaster_analytics/exports/searchable_pages.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['URL', 'HTTP_Code', 'Status', 'Last_Access', 'Title', 'Meta_Description'])
    for p in pages:
        if p['status'] == 'SEARCHABLE':
            writer.writerow([p['url'], p['httpCode'], p['status'], p['lastAccess'], p['title'], p['metaDescription']])

# 3. duplicate_pages.csv
with open('brain/wiki/webmaster_analytics/exports/duplicate_pages.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['URL', 'HTTP_Code', 'Status', 'Last_Access', 'Title', 'Meta_Description'])
    for p in pages:
        if p['status'] == 'DUPLICATE':
            writer.writerow([p['url'], p['httpCode'], p['status'], p['lastAccess'], p['title'], p['metaDescription']])

# 4. parse_error_pages.csv
with open('brain/wiki/webmaster_analytics/exports/parse_error_pages.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['URL', 'HTTP_Code', 'Status', 'Last_Access', 'Title', 'Meta_Description'])
    for p in pages:
        if p['status'] == 'PARSE_ERROR':
            writer.writerow([p['url'], p['httpCode'], p['status'], p['lastAccess'], p['title'], p['metaDescription']])

# 5. redirect_pages.csv
with open('brain/wiki/webmaster_analytics/exports/redirect_pages.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['URL', 'HTTP_Code', 'Status', 'Last_Access', 'Title', 'Meta_Description'])
    for p in pages:
        if p['status'] == 'REDIRECT_NOTSEARCHABLE':
            writer.writerow([p['url'], p['httpCode'], p['status'], p['lastAccess'], p['title'], p['metaDescription']])

# 6. bad_quality_pages.csv
with open('brain/wiki/webmaster_analytics/exports/bad_quality_pages.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['URL', 'HTTP_Code', 'Status', 'Last_Access', 'Title', 'Meta_Description'])
    for p in pages:
        if p['status'] == 'BAD_QUALITY':
            writer.writerow([p['url'], p['httpCode'], p['status'], p['lastAccess'], p['title'], p['metaDescription']])

# 7. http_error_pages.csv
with open('brain/wiki/webmaster_analytics/exports/http_error_pages.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['URL', 'HTTP_Code', 'Status', 'Last_Access', 'Title', 'Meta_Description'])
    for p in pages:
        if p['status'] == 'HTTP_ERROR':
            writer.writerow([p['url'], p['httpCode'], p['status'], p['lastAccess'], p['title'], p['metaDescription']])

# 8. other_pages.csv
with open('brain/wiki/webmaster_analytics/exports/other_pages.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['URL', 'HTTP_Code', 'Status', 'Last_Access', 'Title', 'Meta_Description'])
    for p in pages:
        if p['status'] == 'OTHER':
            writer.writerow([p['url'], p['httpCode'], p['status'], p['lastAccess'], p['title'], p['metaDescription']])

# 9. top_queries_by_cluster.csv
with open('brain/wiki/webmaster_analytics/exports/top_queries_by_cluster.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Query', 'Avg_Position', 'Shows_Total', 'Clicks_Total', 'CTR_%',
                     'Cluster_L1', 'Cluster_L2', 'Intent', 'Target_Page', 'Status'])
    for q in queries:
        s = summarize(q)
        if s['pos_avg'] is None:
            continue
        writer.writerow([q, s['pos_avg'], s['shows'], s['clicks'], s['ctr'],
                         'TODO', 'TODO', 'TODO', 'TODO', 'TODO'])

# 10. content_gaps_prioritized.csv
with open('brain/wiki/webmaster_analytics/exports/content_gaps_prioritized.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Priority', 'Query', 'Avg_Position', 'Cluster', 'Missing_Page_Type', 'Suggested_URL', 'Effort', 'Impact'])
    gaps = [
        ('Critical', 'идеи календарей для производства на 2027 год', 13, 'Календари', 'Статья', '/blog/idei-kalendarey-2027/', 'Medium', 'High'),
        ('Critical', 'визитки на дизайнерском картоне', 2.7, 'Визитки', 'Подкатегория', '/catalog/poligrafiya/vizitki/dizaynerskie/', 'Low', 'High'),
        ('Critical', 'срочная печать визиток в ижевске', 7, 'Визитки', 'Подкатегория', '/catalog/poligrafiya/vizitki/srochnaya/', 'Low', 'High'),
        ('High', 'кружка хамелеон на заказ', 6, 'Мерч', 'Товар', '/catalog/suvenirnaya-produktsiya/pechat-na-kruzhkakh/chameleon/', 'Low', 'Medium'),
        ('High', 'аренда ролл апа ижевск', 10, 'Стенды', 'Лендинг аренды', '/catalog/mobilnye-stendy/arenda/roll-up/', 'Medium', 'Medium'),
        ('Critical', 'печать на баннере ижевск', 5, 'Широкоформат', 'Подкатегория', '/catalog/shirokoformatnaya-pechat/bannery/', 'Low', 'High'),
        ('Critical', 'печать на пленке ижевск', 5, 'Широкоформат', 'Подкатегория', '/catalog/shirokoformatnaya-pechat/plenka/', 'Low', 'High'),
        ('Critical', 'печать постеров ижевск', 6, 'Широкоформат', 'Подкатегория', '/catalog/shirokoformatnaya-pechat/postery/', 'Low', 'High'),
        ('High', 'сравнение ролл ап и х-баннер', 0, 'Сравнения', 'Сравнение', '/comparison/roll-up-vs-h-banner/', 'Low', 'High'),
        ('Critical', 'технические требования к макетам', 0, 'Инфо', 'Статья (Pillar)', '/blog/tekhnicheskie-trebovaniya-maketov/', 'Medium', 'High'),
    ]
    for row in gaps:
        writer.writerow(row)

# 11. site_structure.csv
with open('brain/wiki/webmaster_analytics/exports/site_structure.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Section', 'Indexed', 'Downloaded', 'Searchable', 'Indexation_Rate_%'])
    for s in structure:
        idx = int(s['g-link 2']) if s['g-link 2'].isdigit() else 0
        dl = int(s['g-link 3']) if s['g-link 3'].isdigit() else 0
        sch = int(s['StarTable-Cell']) if s['StarTable-Cell'].isdigit() else 0
        rate = round(sch / idx * 100, 1) if idx > 0 else 0
        writer.writerow([s['g-link'], idx, dl, sch, rate])

# 12. indexing_events.csv
with open('brain/wiki/webmaster_analytics/exports/indexing_events.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Update_Date', 'URL', 'HTTP_Code', 'Status', 'Target', 'Last_Access', 'Title', 'Event'])
    for e in events:
        writer.writerow([e['updateDate'], e['url'], e['httpCode'], e['status'], e['target'], e['lastAccess'], e['title'], e['event']])

commercial_keywords = ['визитк', 'печать', 'заказать', 'купить', 'цена', 'стоимость', 'изготовлени', 'кружк', 'магнит', 'календар', 'листовк', 'флаер', 'баннер', 'стенд', 'ролл', 'пресс', 'штендер', 'сувенир', 'мерч', 'одежд', 'футболк', 'худи', 'шоколад', 'бейдж', 'брелок', 'попсокет', 'сумк', 'рюкзак', 'термокружк', 'термос', 'наклейк', 'стикер', 'пакет', 'конверт', 'папк', 'блокнот', 'ежедневник', 'чертеж', 'ксерокоп', 'сканирован', 'фальцовк', 'брошюр', 'ламинирован', 'уф печат', 'плоттер', 'резк', 'фотообо', 'фреск', 'холст', 'картин', 'постер', 'дизайнерск', 'крафт', 'белым тонер', 'сублимац', 'дтф', 'термотрансф', 'аренд']
info_keywords = ['где', 'как', 'сколько', 'можно ли', 'что такое', 'чем отличается', 'или', 'выбрать', 'требован', 'макет', 'размер', 'формат', 'технолог', 'гост', 'стандарт', 'идеи', 'тренд', 'обзор', 'сравнен', 'vs', 'против', 'лучше', 'худше', 'плюсы', 'минусы', 'преимуществ', 'недостатк']
brand_keywords = ['цифра', 'типография цифра', 'ооо цифра', 'ип данилов', 'цифра 18', 'цифра18', 'цифра ижевск', 'типография ижевск официальный', '7 подлесная', 'цифра режим', 'цифра сайт', 'цифра пакет', 'цифра полиграфия', 'цифра типография', 'цифра сервис']


def matches(q, keywords):
    ql = q.lower()
    return any(kw in ql for kw in keywords)


# 13. commercial_queries.csv
with open('brain/wiki/webmaster_analytics/exports/commercial_queries.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Query', 'Avg_Position', 'Shows_Total', 'Clicks_Total', 'CTR_%', 'Cluster'])
    for q in queries:
        if matches(q, commercial_keywords):
            s = summarize(q)
            if s['pos_avg'] is None:
                continue
            writer.writerow([q, s['pos_avg'], s['shows'], s['clicks'], s['ctr'], 'TODO'])

# 14. informational_queries.csv
with open('brain/wiki/webmaster_analytics/exports/informational_queries.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Query', 'Avg_Position', 'Shows_Total', 'Clicks_Total', 'CTR_%', 'Cluster'])
    for q in queries:
        if matches(q, info_keywords):
            s = summarize(q)
            if s['pos_avg'] is None:
                continue
            writer.writerow([q, s['pos_avg'], s['shows'], s['clicks'], s['ctr'], 'TODO'])

# 15. brand_queries.csv
with open('brain/wiki/webmaster_analytics/exports/brand_queries.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Query', 'Avg_Position', 'Shows_Total', 'Clicks_Total', 'CTR_%'])
    for q in queries:
        if matches(q, brand_keywords):
            s = summarize(q)
            if s['pos_avg'] is None:
                continue
            writer.writerow([q, s['pos_avg'], s['shows'], s['clicks'], s['ctr']])

# 16. query_shows_daily.csv (raw shows matrix)
with open('brain/wiki/webmaster_analytics/exports/query_shows_daily.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Query'] + DAYS + ['Shows_Total'])
    for q in queries:
        d = shows_by_q.get(q, {})
        writer.writerow([q] + [int(d.get(day, 0)) for day in DAYS] + [int(sum(d.values()))])

# 17. query_clicks_daily.csv (raw clicks matrix)
with open('brain/wiki/webmaster_analytics/exports/query_clicks_daily.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Query'] + DAYS + ['Clicks_Total'])
    for q in queries:
        d = clicks_by_q.get(q, {})
        writer.writerow([q] + [int(d.get(day, 0)) for day in DAYS] + [int(sum(d.values()))])

# sanity check vs wiki numbers
pos_vals = [(q, summarize(q)['pos_avg']) for q in queries if summarize(q)['pos_avg'] is not None]
t1 = sum(1 for _, a in pos_vals if a <= 1.0)
t3 = sum(1 for _, a in pos_vals if a <= 3.0)
t10 = sum(1 for _, a in pos_vals if a <= 10.0)
print("queries=%d top1=%d top3=%d top10=%d" % (len(pos_vals), t1, t3, t10))
print("All exports generated successfully!")
