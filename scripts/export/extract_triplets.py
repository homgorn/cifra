#!/usr/bin/env python3
"""
Generate triplets/relationships file for the knowledge graph.
Extracts all relationships from entity properties and creates explicit triplet statements.
"""
import json
import os

KG_FILE = "/Users/user/Projects/цифра 2025/2026/brain/wiki/knowledge_graph/cifra18_knowledge_graph.ttl"
OUTPUT_FILE = "/Users/user/Projects/цифра 2025/2026/brain/wiki/knowledge_graph/cifra18_triplets.ttl"

def load_kg():
    with open(KG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_triplets(data):
    """Extract all triplets from the knowledge graph entities."""
    triplets = []
    entities_by_id = {}
    
    # Build entity index
    for entity in data.get('@graph', []):
        eid = entity.get('@id')
        if eid:
            entities_by_id[eid] = entity
    
    # Known relationship properties
    rel_props = [
        'cifra:hasService',
        'cifra:produces',
        'cifra:locatedIn',
        'cifra:deliversVia',
        'cifra:hasEquipment',
        'cifra:hasMaterial',
        'cifra:hasPrintMethod',
        'cifra:hasFinishing',
        'cifra:competesWith',
        'cifra:suitableFor',
        'cifra:materialType',
        'schema:containedInPlace',
        'cifra:hasCertification',
        'cifra:hasProductionCapability',
        'cifra:duplicateOf',
        'cifra:hasAPI',
        'cifra:hasIntegrations',
        'cifra:hasSDEKIntegration',
        'cifra:hasShopifyPlugin',
        'cifra:hasWooCommercePlugin',
        'cifra:hasSDEKDelivery',
        'cifra:hasOnlineCalculator',
        'cifra:hasOnlineEditor',
        'cifra:hasPartnerNetwork',
        'cifra:hasDesignTool',
        'cifra:hasPrintPartners',
        'cifra:hasDesign',
        'cifra:hasProduction',
        'cifra:hasWideFormat',
        'cifra:hasMerch',
        'cifra:hasCalculator',
        'cifra:hasOnlinePayment',
        'cifra:hasSDEK',
        'cifra:hasDigitalPrint',
        'cifra:hasOffsetPrint',
        'cifra:hasEngineeringPrint',
        'cifra:hasDigitalTools',
        'cifra:hasSDEKRussia',
        'cifra:hasSDEKOffice',
        'cifra:isHQ',
        'cifra:isMajorHub',
        'cifra:isTargetCity',
        'cifra:hasSdekPVZ',
        'cifra:covers',
        'cifra:requires',
        'cifra:producedBy',
        'cifra:hasReview',
        'cifra:hasFAQ',
        'cifra:hasCaseStudy',
        'cifra:hasSpecification',
        'cifra:hasColorProfile',
        'cifra:hasDeliveryTime',
        'cifra:hasTracking',
        'cifra:hasPickupPoints',
        'cifra:hasCalculator',
        'cifra:hasIntent',
    ]
    
    for entity in data.get('@graph', []):
        subject = entity.get('@id')
        if not subject:
            continue
        
        # Process each property
        for prop, value in entity.items():
            if prop in ['@id', '@type', 'rdfs:label', 'rdfs:comment', 'schema:description', 
                       'schema:name', 'schema:legalName', 'schema:url', 'schema:email',
                       'schema:telephone', 'schema:address', 'schema:geo', 'schema:foundingDate',
                       'schema:numberOfEmployees', 'schema:currenciesAccepted', 'schema:paymentAccepted',
                       'schema:areaServed', 'cifra:cms', 'cifra:domain', 'cifra:deliveryPartner',
                       'cifra:targetCities', 'cifra:targetIndustries', 'cifra:seoGoals',
                       'cifra:equipmentType', 'cifra:manufacturer', 'cifra:model', 'cifra:maxFormat',
                       'cifra:maxSpeed', 'cifra:colorCount', 'cifra:printResolution', 'cifra:mediaWeightRange',
                       'cifra:mediaTypes', 'cifra:vdp', 'cifra:priceRange', 'cifra:maintenanceCostPerYear',
                       'cifra:supplier', 'cifra:installationDate', 'cifra:status',
                       'cifra:competitorType', 'cifra:merchSKU', 'cifra:catalogSize', 'cifra:trafficEstimate',
                       'cifra:topKeywords', 'cifra:threatLevel', 'cifra:locations', 'cifra:rating2GIS',
                       'cifra:reviewCount2GIS', 'cifra:agencyMarkup', 'cifra:speed',
                       'cifra:typicalServices', 'cifra:typicalTirage', 'cifra:seasonality', 'cifra:avgCheck',
                       'cifra:ltv', 'cifra:decisionMaker', 'cifra:keyNeeds', 'cifra:grammage', 'cifra:unit',
                       'cifra:color', 'cifra:finish', 'cifra:ecoFriendly', 'cifra:recyclable', 'cifra:fscCertified',
                       'cifra:pricePerKg', 'cifra:supplier', 'cifra:grammageRange', 'cifra:textures', 'cifra:colors',
                       'cifra:brands', 'cifra:durability', 'cifra:widthMax', 'cifra:inkCompatibility',
                       'cifra:applications', 'cifra:pricePerSqM', 'cifra:hasLamination', 'cifra:laminationType',
                       'cifra:weightRange', 'cifra:printMethod', 'cifra:transmission', 'cifra:opacity',
                       'cifra:materialType', 'cifra:certification', 'cifra:recycledContent', 'cifra:grade',
                       'cifra:maxTemp', 'cifra:coating', 'cifra:species', 'cifra:grades', 'cifra:thicknessRange',
                       'cifra:whiteness', 'cifra:population', 'cifra:latitude', 'cifra:longitude',
                       'cifra:timezone', 'cifra:sdekPVZAddresses', 'cifra:majorCities', 'cifra:hasSdekCoverage',
                       'cifra:distanceFromIzhevskKm', 'cifra:priority', 'cifra:deliveryDaysFromIzhevsk',
                       'cifra:timezones', 'cifra:cuttingCapability', 'cifra:cuttingTypes',
                       'cifra:inkType', 'cifra:precision', 'cifra:tonerType', 'cifra:automation',
                       'cifra:vcTechnology', 'cifra:vcColors', 'cifra:specialToner', 'cifra:automationLevel',
                       'cifra:maxTirage', 'cifra:model', 'cifra:warehouses',
                       'cifra:hasMinTirage', 'cifra:hasMaxTirage', 'cifra:hasMaxFormat', 'cifra:hasProductionTime']:
                continue
            
            if prop in rel_props:
                if isinstance(value, list):
                    for obj in value:
                        triplets.append({
                            "subject": subject,
                            "predicate": prop,
                            "object": obj
                        })
                else:
                    triplets.append({
                        "subject": subject,
                        "predicate": prop,
                        "object": value
                    })
            
            # Also handle array values that might be relationships
            elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], str) and value[0].startswith('cifra:'):
                for obj in value:
                    triplets.append({
                        "subject": subject,
                        "predicate": prop,
                        "object": obj
                    })
    
    return triplets

def main():
    data = load_kg()
    triplets = extract_triplets(data)
    
    # Create triplet graph
    triplet_graph = {
        "@context": data.get('@context', {}),
        "@graph": []
    }
    
    for t in triplets:
        triplet_graph["@graph"].append({
            "@id": f"cifra:triplet/{len(triplet_graph['@graph'])}",
            "@type": "cifra:Triplet",
            "cifra:subject": t["subject"],
            "cifra:predicate": t["predicate"],
            "cifra:object": t["object"]
        })
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(triplet_graph, f, ensure_ascii=False, indent=2)
    
    print(f"Generated {len(triplets)} triplets")
    print(f"Output written to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()