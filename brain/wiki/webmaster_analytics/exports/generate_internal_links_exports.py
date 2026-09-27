import csv
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('webmaster/links_inside_parsed.json', 'r', encoding='utf-8') as f:
    links = json.load(f)

# 1. broken links
with open('brain/wiki/webmaster_analytics/exports/internal_links_broken.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Source_URL', 'Target_URL', 'Anchor', 'Status', 'Date_Crawled', 'Date_Updated', 'Priority'])
    for l in links:
        if l['status'] in ('404', '500', '502'):
            priority = 'Critical' if l['target'].endswith('/') or 'catalog/' in l['target'] else 'High'
            writer.writerow([l['source'], l['target'], l['anchor'][:200], l['status'], l['date1'], l['date2'], priority])

# 2. by status
from collections import Counter
status_counts = Counter(l['status'] for l in links)
with open('brain/wiki/webmaster_analytics/exports/internal_links_by_status.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Status', 'Count', 'Percentage'])
    for status, count in status_counts.most_common():
        writer.writerow([status, count, round(count/len(links)*100, 1)])

# 3. image hotlinks
with open('brain/wiki/webmaster_analytics/exports/internal_links_image_hotlinks.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Image_Source', 'Target_URL', 'Anchor', 'Status', 'Issue'])
    for l in links:
        if '/upload/iblock/' in l['source'] or '/wp-content/' in l['source']:
            issue = ''
            if l['status'] in ('404', '500', '502'):
                issue = 'BROKEN_TARGET'
            elif 'vysechnaya' in l['target'] or 'suvenirnaya-produktsiya' in l['target'].replace('catalog/poligrafiya/', ''):
                issue = 'TYPO_IN_URL'
            writer.writerow([l['source'], l['target'], l['anchor'][:200], l['status'], issue])

# 4. typos
with open('brain/wiki/webmaster_analytics/exports/internal_links_typos.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Source_URL', 'Target_URL', 'Anchor', 'Typo_Type', 'Correct_URL'])
    typo_patterns = {
        'vysechnaya-produktsiya': 'suvenirnaya-produktsiya',
        'suvenirnaya-produktsiya': 'suvenirnaya-produktsiya',  # under /catalog/poligrafiya/
    }
    for l in links:
        for typo, correct in typo_patterns.items():
            if typo in l['target']:
                correct_url = l['target'].replace(typo, correct)
                writer.writerow([l['source'], l['target'], l['anchor'][:200], typo, correct_url])

# 5. target page summary (which pages receive most broken links)
target_broken = Counter()
for l in links:
    if l['status'] in ('404', '500', '502'):
        target_broken[l['target']] += 1

with open('brain/wiki/webmaster_analytics/exports/internal_links_target_summary.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Target_URL', 'Broken_Inbound_Count', 'Status', 'Action'])
    for target, count in target_broken.most_common():
        action = 'Fix page (200 OK)' if count > 3 else 'Redirect or restore'
        writer.writerow([target, count, links[0]['status'] if links else '', action])

print('Internal links exports generated!')