import csv
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('webmaster/цифра18.рф_links_inside.tsv', 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f, delimiter='\t')
    rows = list(reader)

print('Total rows: ' + str(len(rows)))
print('Headers: ' + str(rows[0] if rows else 'none'))

# Analyze
from collections import Counter

status_counts = Counter()
source_domains = Counter()
target_domains = Counter()
anchors = Counter()

for r in rows[1:]:  # skip header
    if len(r) >= 6:
        source = r[0]
        target = r[1]
        anchor = r[2]
        status = r[3]
        status_counts[status] += 1
        anchors[anchor[:80]] += 1

print('\nStatus codes:')
for k, v in status_counts.most_common():
    print('  ' + str(k) + ': ' + str(v))

print('\nTop anchors:')
for k, v in anchors.most_common(20):
    print('  ' + str(v) + ': ' + str(k))

# Find 404/500 target URLs
print('\nBroken links (target 404/500/502):')
for r in rows[1:]:
    if len(r) >= 6:
        status = r[3]
        if status in ('404', '500', '502'):
            print('  ' + status + ' | ' + r[1] + ' | anchor: ' + r[2][:80])

# Find image hotlinks (source is image)
print('\nImage sources (upload/iblock):')
img_sources = [r for r in rows[1:] if '/upload/iblock/' in r[0] or '/wp-content/' in r[0]]
print('  Count: ' + str(len(img_sources)))
for r in img_sources[:10]:
    print('  ' + r[0] + ' -> ' + r[1])

# Product/ URLs
print('\n/product/ source URLs:')
prod_sources = [r for r in rows[1:] if '/product/' in r[0]]
print('  Count: ' + str(len(prod_sources)))
for r in prod_sources:
    print('  ' + r[0] + ' -> ' + r[1] + ' (' + r[3] + ')')

# Save parsed data
import json
parsed = []
for r in rows[1:]:
    if len(r) >= 6:
        parsed.append({
            'source': r[0],
            'target': r[1],
            'anchor': r[2],
            'status': r[3],
            'date1': r[4],
            'date2': r[5]
        })

with open('webmaster/links_inside_parsed.json', 'w', encoding='utf-8') as f:
    json.dump(parsed, f, ensure_ascii=False, indent=2)

print('\nParsed data saved to webmaster/links_inside_parsed.json')