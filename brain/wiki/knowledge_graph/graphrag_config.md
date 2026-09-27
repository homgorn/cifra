# GraphRAG Configuration for ЦИФРА18 Customer Support Bot

## Overview
Build a Retrieval-Augmented Generation (RAG) system that leverages the knowledge graph for accurate, context-aware customer support responses about ЦИФРА18 services, pricing, materials, delivery, and capabilities.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      GraphRAG Pipeline                          │
├─────────────────────────────────────────────────────────────────┤
│  User Query → Intent Classification → Graph Retrieval          │
│                    ↓                      ↓                     │
│              SPARQL/Cypher         Subgraph Extraction         │
│                    ↓                      ↓                     │
│              Context Assembly → LLM Generation → Response      │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Vector Store (Embeddings)
```python
# vector_store.py
from sentence_transformers import SentenceTransformer
import chromadb
import json

model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
client = chromadb.PersistentClient(path="./vector_db")
collection = client.get_or_create_collection("cifra18_kg")

def embed_kg_entities(kg_file):
    with open(kg_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    documents = []
    metadatas = []
    ids = []
    
    for entity in data['@graph']:
        eid = entity.get('@id', '')
        label = entity.get('rdfs:label', '')
        comment = entity.get('rdfs:comment', '')
        desc = entity.get('schema:description', '')
        
        # Create rich text representation
        text_parts = [label]
        if comment: text_parts.append(comment)
        if desc: text_parts.append(desc)
        
        # Add key properties
        for key, value in entity.items():
            if key not in ['@id', '@type', 'rdfs:label', 'rdfs:comment', 'schema:description']:
                if isinstance(value, str):
                    text_parts.append(f"{key}: {value}")
                elif isinstance(value, list):
                    text_parts.append(f"{key}: {', '.join(str(v) for v in value)}")
        
        text = " | ".join(text_parts)
        documents.append(text)
        metadatas.append({"entity_id": eid, "label": label, "type": entity.get('@type', [''])[0] if entity.get('@type') else ''})
        ids.append(eid)
    
    # Batch embed and store
    embeddings = model.encode(documents, batch_size=32, show_progress_bar=True)
    collection.add(documents=documents, metadatas=metadatas, ids=ids, embeddings=embeddings.tolist())
    
    print(f"Embedded {len(documents)} entities")
```

### 2. Graph Retriever
```python
# graph_retriever.py
from rdflib import Graph, Namespace
from SPARQLWrapper import SPARQLWrapper, JSON
import re

CIFRA = Namespace("https://cifra18.ru/ontology#")
SCHEMA = Namespace("https://schema.org/")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")

class GraphRetriever:
    def __init__(self, kg_file, sparql_endpoint=None):
        self.kg = Graph()
        self.kg.parse(kg_file, format="turtle")
        self.sparql_endpoint = sparql_endpoint
        if sparql_endpoint:
            self.sparql = SPARQLWrapper(sparql_endpoint)
            self.sparql.setReturnFormat(JSON)
    
    def get_service_details(self, service_label):
        """Get complete service details by label"""
        query = f"""
        PREFIX cifra: <https://cifra18.ru/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?service ?desc ?printMethod ?material ?finishing ?minTirage ?maxTirage ?maxFormat ?productionTime WHERE {{
            ?service rdfs:label "{service_label}" .
            OPTIONAL {{ ?service rdfs:comment ?desc }}
            OPTIONAL {{ ?service cifra:hasPrintMethod ?printMethod }}
            OPTIONAL {{ ?service cifra:hasMaterial ?material }}
            OPTIONAL {{ ?service cifra:hasFinishing ?finishing }}
            OPTIONAL {{ ?service cifra:hasMinTirage ?minTirage }}
            OPTIONAL {{ ?service cifra:hasMaxTirage ?maxTirage }}
            OPTIONAL {{ ?service cifra:hasMaxFormat ?maxFormat }}
            OPTIONAL {{ ?service cifra:hasProductionTime ?productionTime }}
        }}
        """
        return self._execute_query(query)
    
    def get_materials_for_service(self, service_type):
        """Get all materials compatible with a service type"""
        query = f"""
        PREFIX cifra: <https://cifra18.ru/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT DISTINCT ?material ?label ?type ?price WHERE {{
            ?service a cifra:{service_type} .
            ?service cifra:hasMaterial ?material .
            ?material rdfs:label ?label .
            OPTIONAL {{ ?material cifra:materialType ?type }}
            OPTIONAL {{ ?material cifra:pricePerKg ?price }}
            OPTIONAL {{ ?material cifra:pricePerSqM ?price }}
        }}
        """
        return self._execute_query(query)
    
    def get_delivery_info(self, city):
        """Get SDEK delivery info for a city"""
        query = f"""
        PREFIX cifra: <https://cifra18.ru/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX schema: <https://schema.org/>
        SELECT ?city ?label ?population ?hasPVZ ?deliveryDays ?addresses WHERE {{
            ?city rdfs:label "{city}" .
            OPTIONAL {{ ?city schema:population ?population }}
            OPTIONAL {{ ?city cifra:hasSdekPVZ ?hasPVZ }}
            OPTIONAL {{ ?city cifra:deliveryDaysFromIzhevsk ?deliveryDays }}
            OPTIONAL {{ ?city cifra:sdekPVZAddresses ?addresses }}
        }}
        """
        return self._execute_query(query)
    
    def get_competitor_comparison(self):
        """Get competitor comparison data"""
        query = """
        PREFIX cifra: <https://cifra18.ru/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?comp ?label ?type ?strengths ?weaknesses ?threat ?hasAPI ?hasSDEK WHERE {
            cifra:company/cifra18 cifra:competesWith ?comp .
            ?comp rdfs:label ?label .
            ?comp cifra:competitorType ?type .
            OPTIONAL { ?comp cifra:strengths ?strengths }
            OPTIONAL { ?comp cifra:weaknesses ?weaknesses }
            OPTIONAL { ?comp cifra:threatLevel ?threat }
            OPTIONAL { ?comp cifra:hasAPI ?hasAPI }
            OPTIONAL { ?comp cifra:hasSDEKIntegration ?hasSDEK }
        }
        ORDER BY ?threat
        """
        return self._execute_query(query)
    
    def get_industry_needs(self, industry_label):
        """Get typical service needs for an industry"""
        query = f"""
        PREFIX cifra: <https://cifra18.ru/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?industry ?services ?avgCheck ?ltv ?decisionMaker ?keyNeeds WHERE {{
            ?industry rdfs:label "{industry_label}" .
            OPTIONAL {{ ?industry cifra:typicalServices ?services }}
            OPTIONAL {{ ?industry cifra:avgCheck ?avgCheck }}
            OPTIONAL {{ ?industry cifra:ltv ?ltv }}
            OPTIONAL {{ ?industry cifra:decisionMaker ?decisionMaker }}
            OPTIONAL {{ ?industry cifra:keyNeeds ?keyNeeds }}
        }}
        """
        return self._execute_query(query)
    
    def get_equipment_capabilities(self):
        """Get all equipment with capabilities"""
        query = """
        PREFIX cifra: <https://cifra18.ru/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?equip ?label ?type ?maxFormat ?maxSpeed ?colors ?inkType WHERE {
            cifra:company/cifra18 cifra:hasEquipment ?equip .
            ?equip rdfs:label ?label .
            ?equip cifra:equipmentType ?type .
            OPTIONAL { ?equip cifra:maxFormat ?maxFormat }
            OPTIONAL { ?equip cifra:maxSpeed ?maxSpeed }
            OPTIONAL { ?equip cifra:colorCount ?colors }
            OPTIONAL { ?equip cifra:inkType ?inkType }
        }
        """
        return self._execute_query(query)
    
    def _execute_query(self, query):
        if self.sparql_endpoint:
            self.sparql.setQuery(query)
            return self.sparql.query().convert()
        else:
            return self.kg.query(query)
```

### 3. Intent Classifier
```python
# intent_classifier.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import numpy as np

INTENTS = {
    "service_inquiry": [
        "что вы печатаете", "какие услуги", "что можете сделать",
        "печатаете ли вы", "есть ли у вас", "услуги типографии"
    ],
    "pricing_inquiry": [
        "сколько стоит", "цена", "стоимость", "прайс", "расчет",
        "калькулятор", "бюджет", "дорого ли"
    ],
    "material_inquiry": [
        "на чем печатаете", "материалы", "бумага", "пленка", "ткань",
        "крафт", "дизайнерский картон", "ПВХ"
    ],
    "delivery_inquiry": [
        "доставка", "сдэк", "как доставить", "привезете", "отправка",
        "пункт выдачи", "самовывоз", "дней доставка"
    ],
    "competitor_comparison": [
        "чем лучше", "в чем разница", "конкуренты", "другие типографии",
        "почему вы", "преимущества"
    ],
    "technical_specs": [
        "формат", "размер", "тираж", "сроки", "время печати",
        "минимальный заказ", "максимальный тираж"
    ],
    "order_process": [
        "как заказать", "оформить заказ", "макет", "файл", "препресс",
        "оплата", "надо ли приезжать"
    ],
    "equipment_inquiry": [
        "оборудование", "станки", "машины", "индиго", "хайдельберг",
        "латекс", "мимаки", "роланд"
    ]
}

class IntentClassifier:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=1000)
        self.classifier = LogisticRegression(max_iter=1000)
        self._train()
    
    def _train(self):
        texts = []
        labels = []
        for intent, examples in INTENTS.items():
            for ex in examples:
                texts.append(ex)
                labels.append(intent)
        
        X = self.vectorizer.fit_transform(texts)
        self.classifier.fit(X, labels)
    
    def predict(self, text):
        X = self.vectorizer.transform([text])
        proba = self.classifier.predict_proba(X)[0]
        intent = self.classifier.classes_[np.argmax(proba)]
        confidence = np.max(proba)
        return intent, confidence
```

### 4. GraphRAG Response Generator
```python
# graphrag_generator.py
from openai import OpenAI
import json

class GraphRAGGenerator:
    def __init__(self, retriever, vector_store, api_key=None):
        self.retriever = retriever
        self.vector_store = vector_store
        self.client = OpenAI(api_key=api_key) if api_key else None
    
    def generate_response(self, user_query, intent, confidence):
        # Retrieve relevant context from graph
        context = self._retrieve_context(user_query, intent)
        
        # Also get vector similarity results
        vector_results = self.vector_store.similarity_search(user_query, k=5)
        
        # Combine contexts
        full_context = self._format_context(context, vector_results)
        
        # Generate response
        system_prompt = self._get_system_prompt()
        user_prompt = f"""User Query: {user_query}
Intent: {intent} (confidence: {confidence:.2f})

Context from Knowledge Graph:
{full_context}

Generate a helpful, accurate response in Russian. Use specific data from the context. 
If information is missing, say so honestly. Include specific numbers, formats, and capabilities when relevant."""
        
        if self.client:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            return response.choices[0].message.content
        else:
            return self._fallback_response(user_query, intent, full_context)
    
    def _retrieve_context(self, query, intent):
        context = {}
        
        if intent == "service_inquiry":
            # Get all services grouped by category
            services = self.retriever.get_all_services()
            context['services'] = services
        
        elif intent == "pricing_inquiry":
            # Get pricing info for mentioned services
            context['pricing'] = self._extract_pricing(query)
        
        elif intent == "material_inquiry":
            materials = self.retriever.get_all_materials()
            context['materials'] = materials
        
        elif intent == "delivery_inquiry":
            # Extract city from query
            city = self._extract_city(query)
            if city:
                context['delivery'] = self.retriever.get_delivery_info(city)
        
        elif intent == "competitor_comparison":
            context['competitors'] = self.retriever.get_competitor_comparison()
        
        elif intent == "technical_specs":
            context['specs'] = self._extract_specs(query)
        
        elif intent == "equipment_inquiry":
            context['equipment'] = self.retriever.get_equipment_capabilities()
        
        return context
    
    def _get_system_prompt(self):
        return """Ты — эксперт по типографии «Цифра» (цифра18.рф, Ижевск). 
Твоя задача — отвечать на вопросы клиентов точно, конкретно, используя данные из базы знаний.

Правила:
1. Используй ТОЛЬКО предоставленный контекст. Не выдумывай.
2. Цитируй конкретные цифры: форматы, тиражи, сроки, цены материалов.
3. Указывай методы печати и материалы по имени.
4. Для доставки — назови город, дни доставки, есть ли ПВЗ СДЭК.
5. При сравнении с конкурентами — используй их сильные/слабые стороны из базы.
6. Если данных нет — честно скажи: "В базе нет точной информации по этому вопросу".
7. Тон: профессиональный, полезный, не шаблонный. Без "в современном мире".
8. Избегай тире (—), используй запятые и точки."""
    
    def _fallback_response(self, query, intent, context):
        # Simple template-based fallback when no LLM available
        templates = {
            "service_inquiry": "Мы предоставляем: {services_list}. Подробнее по каждому направлению — в разделе услуг на сайте.",
            "pricing_inquiry": "Цены зависят от тиража, материала и сложности. Для расчета нужен макет. Минимальный тираж цифровой печати — 1 экз., офсет — 500 экз.",
            "material_inquiry": "Печатаем на: {materials_list}. Выбираем материал под задачу и бюджет.",
            "delivery_inquiry": "Доставка СДЭК по всей России. Из Ижевска в Москву — 1 день, в СПб/Екб/Новосибирск — 2-3 дня. ПВЗ есть в 1000+ городов.",
            "competitor_comparison": "Наши преимущества: полный цикл (офсет+цифра+широкоформат+мерч+инженерка), свой калькулятор, СДЭК по РФ, консультации технологов. Конкуренты часто ограничены одной нишей.",
            "technical_specs": "Максимальные форматы: широкоформат до 3.2м (баннеры), цифровая до B2+, офсет до B1. Сроки: цифровая от 1 часа, офсет от 1 дня.",
            "order_process": "Пришлите макет (PDF, AI, CDR, PSD, TIFF 300dpi) — проверим, рассчитаем, согласуем. Оплата: карта, СБП, безнал. Самовывоз в Ижевске или СДЭК.",
            "equipment_inquiry": "У нас: HP Indigo (цифра), Heidelberg (офсет), HP Latex/Mimaki/Roland (широкоформат), плоттеры резки, лазерный гравер, UV-принтеры."
        }
        return templates.get(intent, "Уточните вопрос, пожалуйста.")
```

### 5. Main Bot Handler
```python
# bot_handler.py
import asyncio
from typing import Dict, Any

class Cifra18SupportBot:
    def __init__(self, kg_file, vector_db_path, sparql_endpoint=None):
        from graph_retriever import GraphRetriever
        from vector_store import embed_kg_entities
        from intent_classifier import IntentClassifier
        from graphrag_generator import GraphRAGGenerator
        
        self.retriever = GraphRetriever(kg_file, sparql_endpoint)
        self.intent_classifier = IntentClassifier()
        
        # Initialize vector store
        self.vector_client = chromadb.PersistentClient(path=vector_db_path)
        self.vector_collection = self.vector_client.get_collection("cifra18_kg")
        
        self.generator = GraphRAGGenerator(self.retriever, self.vector_collection)
    
    async def handle_message(self, user_id: str, message: str) -> Dict[str, Any]:
        # Classify intent
        intent, confidence = self.intent_classifier.predict(message)
        
        # Generate response
        response = self.generator.generate_response(message, intent, confidence)
        
        # Log for analytics
        self._log_interaction(user_id, message, intent, confidence, response)
        
        return {
            "response": response,
            "intent": intent,
            "confidence": confidence,
            "suggested_actions": self._get_suggested_actions(intent)
        }
    
    def _get_suggested_actions(self, intent):
        actions = {
            "service_inquiry": ["Рассчитать стоимость", "Посмотреть портфолио", "Связаться с технологом"],
            "pricing_inquiry": ["Отправить макет на расчет", "Скачать прайс", "Калькулятор на сайте"],
            "material_inquiry": ["Заказать образцы материалов", "Консультация технолога", "Сравнить материалы"],
            "delivery_inquiry": ["Рассчитать доставку", "Найти ПВЗ СДЭК", "Самовывоз в Ижевске"],
            "competitor_comparison": ["Сравнительная таблица", "Кейсы клиентов", "Тестовый заказ"],
            "technical_specs": ["Требования к макетам", "Шаблоны", "Препресс-чек-лист"],
            "order_process": ["Отправить макет", "Связаться с менеджером", "Демо-доступ к калькулятору"],
            "equipment_inquiry": ["Экскурсия по производству", "Тестовая печать", "Спецификация оборудования"]
        }
        return actions.get(intent, ["Связаться с менеджером", "Написать на izhcifra@yandex.ru"])
    
    def _log_interaction(self, user_id, message, intent, confidence, response):
        # Log to file or database for analytics
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "message": message,
            "intent": intent,
            "confidence": confidence,
            "response_length": len(response)
        }
        with open("bot_logs.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
```

## Deployment

### Docker Compose
```yaml
version: '3.8'
services:
  bot:
    build: .
    container_name: cifra18-bot
    ports:
      - "8000:8000"
    volumes:
      - ./cifra18_knowledge_graph.ttl:/app/kg.ttl
      - ./vector_db:/app/vector_db
      - ./bot_logs.jsonl:/app/bot_logs.jsonl
    environment:
      - SPARQL_ENDPOINT=http://fuseki:3030/cifra18/sparql
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - fuseki
    restart: unless-stopped

  fuseki:
    image: stain/jena-fuseki:4.10.0
    volumes:
      - ./fuseki-config.ttl:/fuseki/configuration/fuseki-config.ttl
      - ./cifra18_knowledge_graph.ttl:/fuseki/data/cifra18_knowledge_graph.ttl
    ports:
      - "3030:3030"
```

### API Endpoint (FastAPI)
```python
# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from bot_handler import Cifra18SupportBot

app = FastAPI(title="ЦИФРА18 Support Bot API")

bot = Cifra18SupportBot(
    kg_file="/app/kg.ttl",
    vector_db_path="/app/vector_db"
)

class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    intent: str
    confidence: float
    suggested_actions: list

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        result = await bot.handle_message(request.user_id, request.message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok", "service": "cifra18-support-bot"}
```

## Evaluation Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Intent Accuracy | >90% | Labeled test set |
| Response Relevance | >85% | Human evaluation |
| Factual Accuracy | 100% | KG-grounded facts only |
| Response Time | <2s | p95 latency |
| Coverage | >95% | Queries answered from KG |

## Test Queries for Validation

```python
TEST_QUERIES = [
    "Сколько стоит печать визиток на крафте 100 штук?",
    "Какие материалы есть для широкоформатной печати?",
    "Доставите ли в Москву и сколько дней?",
    "В чем разница между вами и Printio?",
    "Какой максимальный формат баннера?",
    "Есть ли у вас лазерная гравировка на металле?",
    "Как оформить заказ, если я в другом городе?",
    "Какие оборудование у вас стоит?",
    "Печатаете ли вы на холсте для картин?",
    "Есть ли срочная печать за 1 час?"
]
```

## Monitoring Dashboard (Grafana)
- Request volume by intent
- Average confidence scores
- Response time percentiles
- Error rates
- User satisfaction (thumbs up/down)
- Unanswered queries (for KG expansion)