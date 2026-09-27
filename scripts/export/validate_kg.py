#!/usr/bin/env python3
"""
Validate the ЦИФРА18 Knowledge Graph for completeness and correctness.
"""
import json
import sys
from collections import Counter

KG_FILE = "/Users/user/Projects/цифра 2025/2026/brain/wiki/knowledge_graph/cifra18_knowledge_graph.ttl"
TRIPLETS_FILE = "/Users/user/Projects/цифра 2025/2026/brain/wiki/knowledge_graph/cifra18_triplets.ttl"

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_kg():
    data = load_json(KG_FILE)
    entities = data.get('@graph', [])
    
    print("=" * 60)
    print("ЦИФРА18 Knowledge Graph Validation Report")
    print("=" * 60)
    
    # 1. Basic counts
    print(f"\n📊 Entity Count: {len(entities)}")
    
    # 2. Check for required fields
    missing_id = []
    missing_type = []
    missing_label = []
    type_counts = Counter()
    
    for e in entities:
        eid = e.get('@id')
        etype = e.get('@type')
        label = e.get('rdfs:label')
        
        if not eid:
            missing_id.append(e)
        if not etype:
            missing_type.append(eid)
        if not label:
            missing_label.append(eid)
        
        if isinstance(etype, list):
            for t in etype:
                type_counts[t.split('#')[-1]] += 1
        elif etype:
            type_counts[etype.split('#')[-1]] += 1
    
    print(f"\n✅ Required Fields Check:")
    print(f"   @id present: {len(entities) - len(missing_id)}/{len(entities)}")
    print(f"   @type present: {len(entities) - len(missing_type)}/{len(entities)}")
    print(f"   rdfs:label present: {len(entities) - len(missing_label)}/{len(entities)}")
    
    if missing_id:
        print(f"   ⚠️  Missing @id: {len(missing_id)} entities")
    if missing_type:
        print(f"   ⚠️  Missing @type: {missing_type[:5]}")
    if missing_label:
        print(f"   ⚠️  Missing rdfs:label: {missing_label[:5]}")
    
    # 3. Type distribution
    print(f"\n📦 Entity Types:")
    for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"   {t}: {count}")
    
    # 4. Check for duplicate IDs
    ids = [e.get('@id') for e in entities if e.get('@id')]
    duplicates = [id for id, count in Counter(ids).items() if count > 1]
    print(f"\n🔍 Duplicate IDs: {len(duplicates)}")
    if duplicates:
        for d in duplicates:
            print(f"   ⚠️  {d}")
    
    # 5. Service coverage
    service_types = ['PrintService', 'WideFormatService', 'DigitalPrintService', 
                     'OffsetPrintService', 'MerchService', 'EngineeringPrintService',
                     'PostPressService', 'MobileStandService']
    service_entities = [e for e in entities if any(st in str(e.get('@type', [])) for st in service_types)]
    print(f"\n🖨️  Services: {len(service_entities)}")
    
    services_with_method = 0
    services_with_material = 0
    services_with_min_tirage = 0
    services_with_max_format = 0
    
    for s in service_entities:
        if s.get('cifra:hasPrintMethod'):
            services_with_method += 1
        if s.get('cifra:hasMaterial'):
            services_with_material += 1
        if s.get('cifra:hasMinTirage'):
            services_with_min_tirage += 1
        if s.get('cifra:hasMaxFormat'):
            services_with_max_format += 1
    
    print(f"   Has print method: {services_with_method}/{len(service_entities)} ({100*services_with_method/len(service_entities):.0f}%)")
    print(f"   Has material: {services_with_material}/{len(service_entities)} ({100*services_with_material/len(service_entities):.0f}%)")
    print(f"   Has min tirage: {services_with_min_tirage}/{len(service_entities)} ({100*services_with_min_tirage/len(service_entities):.0f}%)")
    print(f"   Has max format: {services_with_max_format}/{len(service_entities)} ({100*services_with_max_format/len(service_entities):.0f}%)")
    
    # 6. Location coverage
    locations = [e for e in entities if e.get('@type') == 'cifra:Location' or 'Location' in str(e.get('@type', []))]
    print(f"\n📍 Locations: {len(locations)}")
    locs_with_pvz = sum(1 for l in locations if l.get('cifra:hasSdekPVZ'))
    locs_with_days = sum(1 for l in locations if l.get('cifra:deliveryDaysFromIzhevsk'))
    print(f"   Has SDEK PVZ: {locs_with_pvz}/{len(locations)}")
    print(f"   Has delivery days: {locs_with_days}/{len(locations)}")
    
    # 7. Competitor coverage
    competitors = [e for e in entities if 'Competitor' in str(e.get('@type', []))]
    print(f"\n🏆 Competitors: {len(competitors)}")
    comps_with_threat = sum(1 for c in competitors if c.get('cifra:threatLevel'))
    comps_with_type = sum(1 for c in competitors if c.get('cifra:competitorType'))
    print(f"   Has threat level: {comps_with_threat}/{len(competitors)}")
    print(f"   Has competitor type: {comps_with_type}/{len(competitors)}")
    
    # 8. Industry coverage
    industries = [e for e in entities if 'Industry' in str(e.get('@type', []))]
    print(f"\n🏭 Industries: {len(industries)}")
    inds_with_services = sum(1 for i in industries if i.get('cifra:typicalServices'))
    inds_with_avg_check = sum(1 for i in industries if i.get('cifra:avgCheck'))
    print(f"   Has typical services: {inds_with_services}/{len(industries)}")
    print(f"   Has avg check: {inds_with_avg_check}/{len(industries)}")
    
    # 9. Validate triplets
    print(f"\n🔗 Triplet Validation:")
    try:
        triplet_data = load_json(TRIPLETS_FILE)
        triplets = triplet_data.get('@graph', [])
        print(f"   Total triplets: {len(triplets)}")
        
        # Count by predicate
        pred_counts = Counter()
        for t in triplets:
            pred = t.get('cifra:predicate', '')
            pred_counts[pred.split('#')[-1]] += 1
        
        print(f"   Predicate distribution:")
        for p, c in sorted(pred_counts.items(), key=lambda x: -x[1])[:15]:
            print(f"      {p}: {c}")
    except Exception as e:
        print(f"   ⚠️  Could not load triplets: {e}")
    
    # 10. Summary
    print(f"\n{'=' * 60}")
    print("VALIDATION SUMMARY")
    print(f"{'=' * 60}")
    
    issues = []
    if missing_id: issues.append(f"Missing @id: {len(missing_id)}")
    if missing_type: issues.append(f"Missing @type: {len(missing_type)}")
    if missing_label: issues.append(f"Missing rdfs:label: {len(missing_label)}")
    if duplicates: issues.append(f"Duplicate IDs: {len(duplicates)}")
    if services_with_method < len(service_entities): issues.append(f"Services missing print method: {len(service_entities) - services_with_method}")
    if services_with_material < len(service_entities): issues.append(f"Services missing material: {len(service_entities) - services_with_material}")
    if locs_with_pvz < len(locations): issues.append(f"Locations missing SDEK PVZ: {len(locations) - locs_with_pvz}")
    if comps_with_threat < len(competitors): issues.append(f"Competitors missing threat level: {len(competitors) - comps_with_threat}")
    
    if issues:
        print("⚠️  ISSUES FOUND:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ ALL CHECKS PASSED")
        return True

if __name__ == "__main__":
    success = validate_kg()
    sys.exit(0 if success else 1)