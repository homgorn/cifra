import csv
import os
import json
import sys
from collections import Counter, defaultdict

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

files = [
    'webmaster/цифра18.рф_d4614eeeb7cd1a4c18473d6d.csv',
    'webmaster/цифра18.рф_900a1ba465bf8692167043b9.csv',
    'webmaster/цифра18.рф_66ca0f04c5a5028b3cc120e9.csv',
    'webmaster/цифра18.рф_33851bbe4da16518d0877b78.csv',
    'webmaster/цифра18.рф_2644f2f73b3615228c8ce777.csv',
    'webmaster/webmaste_structure_cifra.csv'
]

def safe_float(v):
    """Safely convert value to float"""
    if isinstance(v, list):
        return None
    if not v or not v.strip():
        return None
    try:
        return float(v)
    except:
        return None

print("=" * 80)
print("DETAILED ANALYSIS")
print("=" * 80)

# 1. Pages index status
print("\n1. PAGES INDEX STATUS (цифра18.рф_d4614eeeb7cd1a4c18473d6d.csv)")
with open(files[0], 'r', encoding='utf-8-sig') as fp:
    reader = csv.DictReader(fp)
    pages = list(reader)

status_counts = Counter(p['status'] for p in pages)
http_counts = Counter(p['httpCode'] for p in pages)
print("Status distribution:")
for k, v in status_counts.most_common():
    print('  {}: {}'.format(k, v))
print("\nHTTP codes:")
for k, v in http_counts.most_common():
    print('  {}: {}'.format(k, v))

searchable = [p for p in pages if p['status'] == 'SEARCHABLE']
print('\nSEARCHABLE pages: {}'.format(len(searchable)))
for p in searchable[:30]:
    print('  {} | {}'.format(p['url'], p['title'][:80]))

duplicates = [p for p in pages if p['status'] == 'DUPLICATE']
print('\nDUPLICATE pages: {}'.format(len(duplicates)))
for p in duplicates[:20]:
    print('  {} | {}'.format(p['url'], p['title'][:80] if p['title'] else '(no title)'))

parse_errors = [p for p in pages if p['status'] == 'PARSE_ERROR']
print('\nPARSE_ERROR pages: {}'.format(len(parse_errors)))
for p in parse_errors[:20]:
    print('  {} | {}'.format(p['url'], p['title'][:80] if p['title'] else '(no title)'))

other = [p for p in pages if p['status'] == 'OTHER']
print('\nOTHER pages: {}'.format(len(other)))

http_errors = [p for p in pages if p['status'] == 'HTTP_ERROR']
print('HTTP_ERROR pages: {}'.format(len(http_errors)))
for p in http_errors:
    print('  {} | {}'.format(p['url'], p['title'][:80] if p['title'] else '(no title)'))

redirect_ns = [p for p in pages if p['status'] == 'REDIRECT_NOTSEARCHABLE']
print('REDIRECT_NOTSEARCHABLE pages: {}'.format(len(redirect_ns)))

bad_quality = [p for p in pages if p['status'] == 'BAD_QUALITY']
print('BAD_QUALITY pages: {}'.format(len(bad_quality)))

# 2. Indexing events
print("\n\n2. INDEXING EVENTS (цифра18.рф_900a1ba465bf8692167043b9.csv)")
with open(files[1], 'r', encoding='utf-8-sig') as fp:
    reader = csv.DictReader(fp)
    events = list(reader)

event_counts = Counter(e['event'] for e in events)
status_counts2 = Counter(e['status'] for e in events)
print("Event types:")
for k, v in event_counts.most_common():
    print('  {}: {}'.format(k, v))
print("\nStatus in events:")
for k, v in status_counts2.most_common():
    print('  {}: {}'.format(k, v))

# Show recent events
recent_adds = [e for e in events if e['event'] == 'ADD'][:20]
print("\nRecent ADD events:")
for e in recent_adds:
    print('  {} | {} | {}'.format(e['updateDate'], e['url'], e['title'][:60]))

recent_dels = [e for e in events if e['event'] == 'DELETE'][:20]
print("\nRecent DELETE events:")
for e in recent_dels:
    print('  {} | {} | {} -> {}'.format(e['updateDate'], e['url'], e['status'], e['target'][:60] if e['target'] else ''))

# 3. Query positions (66ca - daily positions)
print("\n\n3. QUERY POSITIONS - 66ca (daily positions)")
with open(files[2], 'r', encoding='utf-8-sig') as fp:
    reader = csv.DictReader(fp)
    queries_pos = list(reader)

print('Total queries: {}'.format(len(queries_pos)))
date_cols = [c for c in queries_pos[0].keys() if c != 'Query']
print('Date columns: {}'.format(date_cols))

queries_with_pos = []
for q in queries_pos:
    positions = []
    for k, v in q.items():
        if k != 'Query':
            val = safe_float(v)
            if val is not None:
                positions.append(val)
    if positions:
        queries_with_pos.append((q['Query'], positions))

print('Queries with positions: {}'.format(len(queries_with_pos)))

avg_positions = []
for query, positions in queries_with_pos:
    avg = sum(positions) / len(positions)
    avg_positions.append((query, avg, len(positions), min(positions), max(positions)))

avg_positions.sort(key=lambda x: x[1])
print("\nTop 50 queries by average position:")
for q, avg, cnt, mn, mx in avg_positions[:50]:
    print('  {:.2f} (n={}, min={:.0f}, max={:.0f}) - {}'.format(avg, cnt, mn, mx, q))

# Queries in top 10
top10 = [x for x in avg_positions if x[1] <= 10]
print("\nQueries in TOP 10 (avg pos <= 10): {}".format(len(top10)))
for q, avg, cnt, mn, mx in top10:
    print('  {:.2f} - {}'.format(avg, q))

# 4. Query positions (3385 - average positions)
print("\n\n4. QUERY POSITIONS - 3385 (average positions)")
with open(files[3], 'r', encoding='utf-8-sig') as fp:
    reader = csv.DictReader(fp)
    queries_avg = list(reader)

queries_with_avg = []
for q in queries_avg:
    positions = []
    for k, v in q.items():
        if k != 'Query':
            val = safe_float(v)
            if val is not None:
                positions.append(val)
    if positions:
        queries_with_avg.append((q['Query'], positions))

print('Queries with avg positions: {}'.format(len(queries_with_avg)))

avg_positions2 = []
for query, positions in queries_with_avg:
    avg = sum(positions) / len(positions)
    avg_positions2.append((query, avg, len(positions), min(positions), max(positions)))

avg_positions2.sort(key=lambda x: x[1])
print("\nTop 50 queries by average position (3385):")
for q, avg, cnt, mn, mx in avg_positions2[:50]:
    print('  {:.2f} (n={}, min={:.0f}, max={:.0f}) - {}'.format(avg, cnt, mn, mx, q))

top10_2 = [x for x in avg_positions2 if x[1] <= 10]
print("\nQueries in TOP 10 (avg pos <= 10): {}".format(len(top10_2)))
for q, avg, cnt, mn, mx in top10_2:
    print('  {:.2f} - {}'.format(avg, q))

# 5. Site structure
print("\n\n5. SITE STRUCTURE (webmaste_structure_cifra.csv)")
with open(files[5], 'r', encoding='utf-8-sig') as fp:
    reader = csv.DictReader(fp)
    structure = list(reader)

print('Sections: {}'.format(len(structure)))
total_indexed = 0
total_downloaded = 0
total_searchable = 0
for s in structure:
    idx = int(s['g-link 2']) if s['g-link 2'].isdigit() else 0
    dl = int(s['g-link 3']) if s['g-link 3'].isdigit() else 0
    sch = int(s['StarTable-Cell']) if s['StarTable-Cell'].isdigit() else 0
    total_indexed += idx
    total_downloaded += dl
    total_searchable += sch
    print('  {}: indexed={}, downloaded={}, searchable={}'.format(
        s['g-link'], idx, dl, sch))
print('  TOTAL: indexed={}, downloaded={}, searchable={}'.format(
    total_indexed, total_downloaded, total_searchable))

# Save parsed data for later use
output = {
    'pages': pages,
    'events': events,
    'queries_pos': queries_pos,
    'queries_avg': queries_avg,
    'structure': structure,
    'stats': {
        'status_counts': dict(status_counts),
        'http_counts': dict(http_counts),
        'event_counts': dict(event_counts),
        'searchable_count': len(searchable),
        'duplicate_count': len(duplicates),
        'parse_error_count': len(parse_errors),
        'other_count': len(other),
        'http_error_count': len(http_errors),
        'redirect_ns_count': len(redirect_ns),
        'bad_quality_count': len(bad_quality),
        'queries_with_pos_count': len(queries_with_pos),
        'queries_with_avg_count': len(queries_with_avg),
    }
}

with open('webmaster/parsed_data.json', 'w', encoding='utf-8') as fp:
    json.dump(output, fp, ensure_ascii=False, indent=2)

print("\n\nParsed data saved to webmaster/parsed_data.json")