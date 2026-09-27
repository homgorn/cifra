# SPARQL Endpoint Configuration for ЦИФРА18 Knowledge Graph

## Fuseki Configuration (Apache Jena)

### fuseki-config.ttl
```turtle
@prefix :        <#> .
@prefix fuseki:  <http://jena.apache.org/fuseki#> .
@prefix rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs:    <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ja:      <http://jena.hpl.hp.com/2005/11/Assembler#> .

# Main dataset
<#cifra18> rdf:type fuseki:Dataset ;
    fuseki:name "cifra18" ;
    fuseki:dataset <#dataset> ;
    fuseki:service <#sparql> , <#update> , <#query> , <#data> , <#sparql-http> ;
    .

# In-memory dataset with TTL file
<#dataset> rdf:type ja:RDFDataset ;
    ja:defaultGraph <#graph> ;
    .

<#graph> rdf:type ja:MemoryDataset ;
    ja:content [ ja:externalContent <file:cifra18_knowledge_graph.ttl> ] ;
    .

# SPARQL Query endpoint
<#sparql> rdf:type fuseki:Service ;
    fuseki:name "sparql" ;
    fuseki:service fuseki:query ;
    fuseki:dataset <#dataset> ;
    .

# SPARQL Update endpoint
<#update> rdf:type fuseki:Service ;
    fuseki:name "update" ;
    fuseki:service fuseki:update ;
    fuseki:dataset <#dataset> ;
    .

# SPARQL Query (alternative)
<#query> rdf:type fuseki:Service ;
    fuseki:name "query" ;
    fuseki:service fuseki:query ;
    fuseki:dataset <#dataset> ;
    .

# Data upload endpoint
<#data> rdf:type fuseki:Service ;
    fuseki:name "data" ;
    fuseki:service fuseki:data ;
    fuseki:dataset <#dataset> ;
    .

# HTTP SPARQL endpoint
<#sparql-http> rdf:type fuseki:Service ;
    fuseki:name "sparql" ;
    fuseki:service fuseki:query ;
    fuseki:dataset <#dataset> ;
    fuseki:endpoint "sparql" ;
    .
```

## Docker Compose for Fuseki
```yaml
version: '3.8'
services:
  fuseki:
    image: stain/jena-fuseki:4.10.0
    container_name: cifra18-fuseki
    ports:
      - "3030:3030"
    volumes:
      - ./fuseki-config.ttl:/fuseki/configuration/fuseki-config.ttl
      - ./cifra18_knowledge_graph.ttl:/fuseki/data/cifra18_knowledge_graph.ttl
      - fuseki-data:/fuseki/databases
    environment:
      - JVM_ARGS=-Xmx2g
    restart: unless-stopped

volumes:
  fuseki-data:
```

## Useful SPARQL Queries

### 1. All services provided by ЦИФРА18
```sparql
PREFIX cifra: <https://cifra18.ru/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?service ?label ?description ?printMethod ?minTirage ?maxFormat WHERE {
    cifra:company/cifra18 cifra:hasService ?service .
    ?service rdfs:label ?label .
    OPTIONAL { ?service rdfs:comment ?description }
    OPTIONAL { ?service cifra:hasPrintMethod ?printMethod }
    OPTIONAL { ?service cifra:hasMinTirage ?minTirage }
    OPTIONAL { ?service cifra:hasMaxFormat ?maxFormat }
}
ORDER BY ?label
```

### 2. All materials with their properties
```sparql
PREFIX cifra: <https://cifra18.ru/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?material ?label ?type ?grammage ?price WHERE {
    ?material a cifra:Material .
    ?material rdfs:label ?label .
    OPTIONAL { ?material cifra:materialType ?type }
    OPTIONAL { ?material cifra:grammage ?grammage }
    OPTIONAL { ?material cifra:pricePerKg ?price }
    OPTIONAL { ?material cifra:pricePerSqM ?price }
}
ORDER BY ?label
```

### 3. Equipment capabilities
```sparql
PREFIX cifra: <https://cifra18.ru/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?equipment ?label ?type ?maxFormat ?maxSpeed ?colors WHERE {
    cifra:company/cifra18 cifra:hasEquipment ?equipment .
    ?equipment rdfs:label ?label .
    ?equipment cifra:equipmentType ?type .
    OPTIONAL { ?equipment cifra:maxFormat ?maxFormat }
    OPTIONAL { ?equipment cifra:maxSpeed ?maxSpeed }
    OPTIONAL { ?equipment cifra:colorCount ?colors }
}
```

### 4. Competitor analysis
```sparql
PREFIX cifra: <https://cifra18.ru/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?competitor ?label ?type ?strengths ?weaknesses ?threat WHERE {
    cifra:company/cifra18 cifra:competesWith ?competitor .
    ?competitor rdfs:label ?label .
    ?competitor cifra:competitorType ?type .
    OPTIONAL { ?competitor cifra:strengths ?strengths }
    OPTIONAL { ?competitor cifra:weaknesses ?weaknesses }
    OPTIONAL { ?competitor cifra:threatLevel ?threat }
}
```

### 5. Target cities with SDEK coverage
```sparql
PREFIX cifra: <https://cifra18.ru/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <https://schema.org/>

SELECT ?city ?label ?population ?hasPVZ ?deliveryDays WHERE {
    ?city a cifra:Location .
    ?city rdfs:label ?label .
    ?city schema:population ?population .
    OPTIONAL { ?city cifra:hasSdekPVZ ?hasPVZ }
    OPTIONAL { ?city cifra:deliveryDaysFromIzhevsk ?deliveryDays }
    FILTER (?city != cifra:location/russia && ?city != cifra:location/world)
}
ORDER BY ?deliveryDays ?label
```

### 6. Industry-specific service needs
```sparql
PREFIX cifra: <https://cifra18.ru/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?industry ?label ?services ?avgCheck ?ltv WHERE {
    ?industry a cifra:Industry .
    ?industry rdfs:label ?label .
    OPTIONAL { ?industry cifra:typicalServices ?services }
    OPTIONAL { ?industry cifra:avgCheck ?avgCheck }
    OPTIONAL { ?industry cifra:ltv ?ltv }
}
ORDER BY ?label
```

### 7. Service-Material compatibility
```sparql
PREFIX cifra: <https://cifra18.ru/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?service ?serviceLabel ?material ?materialLabel ?printMethod WHERE {
    ?service cifra:hasMaterial ?material .
    ?service rdfs:label ?serviceLabel .
    ?material rdfs:label ?materialLabel .
    OPTIONAL { ?service cifra:hasPrintMethod ?printMethod }
}
ORDER BY ?serviceLabel
```

### 8. Products with prices and specs
```sparql
PREFIX cifra: <https://cifra18.ru/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <https://schema.org/>

SELECT ?product ?label ?price ?currency ?weight ?dimensions WHERE {
    ?product a cifra:Product .
    ?product rdfs:label ?label .
    OPTIONAL { ?product cifra:hasPrice ?price }
    OPTIONAL { ?product cifra:hasCurrency ?currency }
    OPTIONAL { ?product cifra:hasWeight ?weight }
    OPTIONAL { ?product cifra:hasDimensions ?dimensions }
}
```

### 9. Intent classification for pages
```sparql
PREFIX cifra: <https://cifra18.ru/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?intent ?label ?comment WHERE {
    ?intent a cifra:Intent .
    ?intent rdfs:label ?label .
    OPTIONAL { ?intent rdfs:comment ?comment }
}
```

### 10. Complete service details with all properties
```sparql
PREFIX cifra: <https://cifra18.ru/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?service ?label ?description ?printMethod ?material ?finishing ?minTirage ?maxTirage ?maxFormat ?productionTime WHERE {
    ?service a ?type .
    FILTER (?type IN (cifra:PrintService, cifra:WideFormatService, cifra:DigitalPrintService, cifra:OffsetPrintService, cifra:MerchService, cifra:EngineeringPrintService, cifra:PostPressService, cifra:MobileStandService))
    ?service rdfs:label ?label .
    OPTIONAL { ?service rdfs:comment ?description }
    OPTIONAL { ?service cifra:hasPrintMethod ?printMethod }
    OPTIONAL { ?service cifra:hasMaterial ?material }
    OPTIONAL { ?service cifra:hasFinishing ?finishing }
    OPTIONAL { ?service cifra:hasMinTirage ?minTirage }
    OPTIONAL { ?service cifra:hasMaxTirage ?maxTirage }
    OPTIONAL { ?service cifra:hasMaxFormat ?maxFormat }
    OPTIONAL { ?service cifra:hasProductionTime ?productionTime }
}
ORDER BY ?type ?label
```

## API Usage Examples

### Python (rdflib)
```python
from rdflib import Graph, Namespace
from rdflib.plugins.sparql import prepareQuery

CIFRA = Namespace("https://cifra18.ru/ontology#")
g = Graph()
g.parse("cifra18_knowledge_graph.ttl", format="turtle")

# Query all services
q = prepareQuery("""
    SELECT ?service ?label WHERE {
        cifra:company/cifra18 cifra:hasService ?service .
        ?service rdfs:label ?label .
    }
""", initNs={"cifra": CIFRA, "rdfs": RDFS})

for row in g.query(q):
    print(f"{row.service} - {row.label}")
```

### HTTP API
```bash
# Query endpoint
curl -X POST http://localhost:3030/cifra18/sparql \
  -H "Content-Type: application/sparql-query" \
  -d 'SELECT * WHERE { ?s ?p ?o } LIMIT 10'

# Update endpoint
curl -X POST http://localhost:3030/cifra18/update \
  -H "Content-Type: application/sparql-update" \
  -d 'INSERT DATA { <cifra:newEntity> <rdfs:label> "New Entity" }'
```

## Health Check
```bash
curl http://localhost:3030/\$/ping
```

## Monitoring
- Metrics available at: `http://localhost:3030/\$/metrics`
- Logs: `docker logs cifra18-fuseki`