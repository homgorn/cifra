#!/usr/bin/env python3
"""
Combine all TTL entity files into a single unified knowledge graph.
"""
import json
import os
import sys

ENTITY_DIR = "/Users/user/Projects/цифра 2025/2026/brain/wiki/knowledge_graph/entities"
ONTOLOGY_FILE = "/Users/user/Projects/цифра 2025/2026/brain/wiki/knowledge_graph/ontologies/printing_ontology.ttl"
INTENTS_FILE = "/Users/user/Projects/цифра 2025/2026/brain/wiki/knowledge_graph/intents/intents.ttl"
OUTPUT_FILE = "/Users/user/Projects/цифра 2025/2026/brain/wiki/knowledge_graph/cifra18_knowledge_graph.ttl"

def load_jsonld(filepath):
    """Load a JSON-LD file and return the @graph array."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('@graph', []), data.get('@context', {})

def main():
    all_entities = []
    combined_context = {
        "cifra": "https://cifra18.ru/ontology#",
        "schema": "https://schema.org/",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "owl": "http://www.w3.org/2002/07/owl#",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "skos": "http://www.w3.org/2004/02/skos/core#",
        "dcterms": "http://purl.org/dc/terms/"
    }
    
    # Process entity files
    entity_files = [
        "company.ttl",
        "materials.ttl",
        "equipment.ttl",
        "locations.ttl",
        "industries.ttl",
        "competitors.ttl",
        "poligrafiya_services.ttl",
        "shirokoformatnaya_services.ttl",
        "suvenirnaya_services.ttl",
        "inzhenernaya_services.ttl",
        "interer_services.ttl",
        "mobilnye_stendy_services.ttl",
        "stendy_services.ttl",
        "interer_stendy_mobilnye.ttl",
        "inzhenernaya_stendy_services.ttl"
    ]
    
    seen_ids = set()
    duplicate_count = 0
    
    for filename in entity_files:
        filepath = os.path.join(ENTITY_DIR, filename)
        if os.path.exists(filepath):
            try:
                entities, context = load_jsonld(filepath)
                for entity in entities:
                    entity_id = entity.get('@id')
                    if entity_id in seen_ids:
                        duplicate_count += 1
                        print(f"  Duplicate skipped: {entity_id} from {filename}")
                        continue
                    seen_ids.add(entity_id)
                    all_entities.append(entity)
                print(f"Loaded {len(entities)} entities from {filename}")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
        else:
            print(f"File not found: {filepath}")
    
    # Load ontology
    try:
        ontology_entities, _ = load_jsonld(ONTOLOGY_FILE)
        for entity in ontology_entities:
            entity_id = entity.get('@id')
            if entity_id not in seen_ids:
                seen_ids.add(entity_id)
                all_entities.append(entity)
        print(f"Loaded {len(ontology_entities)} entities from ontology")
    except Exception as e:
        print(f"Error loading ontology: {e}")
    
    # Load intents
    try:
        intent_entities, _ = load_jsonld(INTENTS_FILE)
        for entity in intent_entities:
            entity_id = entity.get('@id')
            if entity_id not in seen_ids:
                seen_ids.add(entity_id)
                all_entities.append(entity)
        print(f"Loaded {len(intent_entities)} entities from intents")
    except Exception as e:
        print(f"Error loading intents: {e}")
    
    # Write combined graph
    combined = {
        "@context": combined_context,
        "@graph": all_entities
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== Summary ===")
    print(f"Total unique entities: {len(all_entities)}")
    print(f"Duplicates skipped: {duplicate_count}")
    print(f"Output written to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()