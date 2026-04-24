# GENESIS AI PLATFORM — Memory System Design
## Deep Technical Design for 4-Tier Memory Architecture

**Version:** 1.0  
**Date:** April 2026  
**Classification:** Technical Deep Dive  
**Related Documents:** 01_MASTER_PROJECT_PLAN.md, 02_SYSTEM_ARCHITECTURE.md

---

## 1. MEMORY ARCHITECTURE OVERVIEW

### 1.1 The CoALA-Inspired 4-Tier Model

GENESIS implements a comprehensive memory architecture based on the **CoALA (Cognitive Architectures for Language Agents)** framework from Princeton (2023) and the latest 2025-2026 research in agent memory systems (arXiv:2512.13564).

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         MEMORY ARCHITECTURE                                     │
│                                                                                  │
│   TIER 1: WORKING MEMORY                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  Human Equivalent: Brain's scratch pad                                   │   │
│   │  Technology: Letta-style Virtual Context Management                      │   │
│   │  Duration: Session-only (TTL: 1 hour)                                   │   │
│   │  Capacity: ~30% of context window (active)                              │   │
│   │  Swap Strategy: Importance-based paging                                  │   │
│   │  Storage: Redis (hot) + Agent State (warm)                              │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                              │                                                   │
│                              │ Consolidation (every interaction)                 │
│                              ▼                                                   │
│   TIER 2: EPISODIC MEMORY                                                        │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  Human Equivalent: Autobiographical memory                              │   │
│   │  Technology: Mem0 with Qdrant backend                                    │   │
│   │  Duration: Persistent, long-term (TTL: 90 days default)                 │   │
│   │  Capacity: Unlimited (compressed)                                       │   │
│   │  Retrieval: Vector similarity + metadata filtering                       │   │
│   │  Storage: Qdrant (vectors) + PostgreSQL (metadata)                      │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                              │                                                   │
│                              │ Consolidation (every 50-200 episodes)             │
│                              ▼                                                   │
│   TIER 3: SEMANTIC MEMORY                                                        │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  Human Equivalent: General knowledge, facts                             │   │
│   │  Technology: Cognee Knowledge Graph with Neo4j                          │   │
│   │  Duration: Persistent, evolving                                         │   │
│   │  Capacity: Unlimited                                                    │   │
│   │  Retrieval: Graph traversal + vector search                             │   │
│   │  Storage: Neo4j (graph) + Qdrant (embeddings)                           │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                              │                                                   │
│                              │ Consolidation (every 200-500 episodes)            │
│                              ▼                                                   │
│   TIER 4: PROCEDURAL MEMORY                                                      │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  Human Equivalent: Muscle memory, skills                                │   │
│   │  Technology: Skill Registry with genetic encoding                       │   │
│   │  Duration: Persistent, versioned                                        │   │
│   │  Capacity: Unlimited                                                    │   │
│   │  Retrieval: Semantic matching + fitness ranking                         │   │
│   │  Storage: PostgreSQL + Qdrant (skill embeddings)                        │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Memory Tier Comparison

| Property | Working | Episodic | Semantic | Procedural |
|----------|---------|----------|----------|------------|
| **Speed** | <1ms | 50-100ms | 100-200ms | 20-50ms |
| **Capacity** | Context window | Millions | Unlimited | Thousands |
| **Persistence** | Session | Long-term | Permanent | Permanent |
| **Storage** | Redis | Qdrant + PG | Neo4j + Qdrant | PostgreSQL |
| **Key Operation** | Read/Write | Similarity search | Graph traversal | Exact match |
| **Consolidation** | → Episodic | → Semantic | → Procedural | N/A |
| **Technology** | Letta | Mem0 | Cognee | Custom |

---

## 2. TIER 1: WORKING MEMORY (LETTA-STYLE)

### 2.1 Design Philosophy

Working memory in GENESIS is inspired by **Letta's OS-style virtual context management**. The key insight: LLM context windows are like RAM — limited and expensive. External storage is like disk — abundant but slower. Smart swapping between them is the key to handling long-running tasks.

### 2.2 Architecture

```python
# genesis/memory/working.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import redis.asyncio as redis
from enum import Enum

class MemoryPriority(Enum):
    CRITICAL = 1    # System prompts, active task
    HIGH = 2        # Recent important context
    MEDIUM = 3      # Relevant historical context
    LOW = 4         # Background information
    ARCHIVE = 5     # Can be paged out immediately

@dataclass
class MemoryPage:
    """A single unit of working memory"""
    id: str
    content: str
    priority: MemoryPriority
    importance_score: float  # 0-1, calculated
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    ttl_seconds: int = 3600  # Default 1 hour
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_expired(self) -> bool:
        age = (datetime.now() - self.created_at).total_seconds()
        return age > self.ttl_seconds
    
    @property
    def lru_score(self) -> float:
        """Combined score for eviction decision"""
        recency = 1 / (1 + (datetime.now() - self.last_accessed).total_seconds())
        frequency = min(self.access_count / 10, 1.0)
        return (
            self.importance_score * 0.4 +
            recency * 0.3 +
            frequency * 0.2 +
            (1 / self.priority.value) * 0.1
        )

class VirtualContextManager:
    """
    OS-inspired virtual context management.
    
    Key concepts:
    - RAM = Active context window (30% of limit)
    - Disk = Archived context (70% of limit + external storage)
    - Page fault = Load from disk when accessed
    - Page out = Evict from RAM to disk
    """
    
    def __init__(
        self,
        context_window: int = 128000,
        ram_ratio: float = 0.3,
        redis_url: str = "redis://localhost:6379"
    ):
        self.context_window = context_window
        self.ram_size = int(context_window * ram_ratio)
        self.disk_size = context_window - self.ram_size
        
        self.ram: Dict[str, MemoryPage] = {}  # Active pages
        self.disk: redis.Redis = redis.from_url(redis_url)
        
        self.access_log: List[Dict] = []
        self.page_faults = 0
        self.page_hits = 0
    
    async def load(self, page: MemoryPage) -> None:
        """Load a page into RAM (context window)"""
        
        # Check if already in RAM (cache hit)
        if page.id in self.ram:
            self.ram[page.id].access_count += 1
            self.ram[page.id].last_accessed = datetime.now()
            self.page_hits += 1
            return
        
        # Page fault — need to load
        self.page_faults += 1
        
        # Evict pages if RAM is full
        while self._ram_usage() + len(page.content) > self.ram_size:
            await self._evict_lru_page()
        
        # Load into RAM
        self.ram[page.id] = page
        
        # Log access
        self.access_log.append({
            "type": "page_in",
            "page_id": page.id,
            "priority": page.priority.name,
            "timestamp": datetime.now().isoformat()
        })
    
    async def access(self, page_id: str) -> Optional[MemoryPage]:
        """Access a page — handles page faults automatically"""
        
        # Try RAM first
        if page_id in self.ram:
            self.ram[page_id].access_count += 1
            self.ram[page_id].last_accessed = datetime.now()
            self.page_hits += 1
            return self.ram[page_id]
        
        # Page fault — try to load from disk
        page_data = await self.disk.get(f"working_memory:{page_id}")
        if page_data:
            page = self._deserialize(page_data)
            await self.load(page)
            return page
        
        return None
    
    async def _evict_lru_page(self) -> None:
        """Evict least recently used page from RAM to disk"""
        
        if not self.ram:
            return
        
        # Find page with lowest LRU score
        lru_page = min(self.ram.values(), key=lambda p: p.lru_score)
        
        # Store to disk
        await self.disk.setex(
            f"working_memory:{lru_page.id}",
            lru_page.ttl_seconds,
            self._serialize(lru_page)
        )
        
        # Remove from RAM
        del self.ram[lru_page.id]
        
        self.access_log.append({
            "type": "page_out",
            "page_id": lru_page.id,
            "lru_score": lru_page.lru_score,
            "timestamp": datetime.now().isoformat()
        })
    
    def _ram_usage(self) -> int:
        """Calculate current RAM usage in tokens (approximate)"""
        return sum(len(p.content) for p in self.ram.values())
    
    def get_stats(self) -> Dict:
        """Get working memory statistics"""
        total_accesses = self.page_hits + self.page_faults
        hit_rate = self.page_hits / total_accesses if total_accesses > 0 else 0
        
        return {
            "ram_pages": len(self.ram),
            "ram_usage_tokens": self._ram_usage(),
            "ram_capacity": self.ram_size,
            "ram_utilization": self._ram_usage() / self.ram_size,
            "page_faults": self.page_faults,
            "page_hits": self.page_hits,
            "hit_rate": hit_rate,
            "eviction_count": len([l for l in self.access_log if l["type"] == "page_out"])
        }
    
    def _serialize(self, page: MemoryPage) -> bytes:
        import json
        return json.dumps({
            "id": page.id,
            "content": page.content,
            "priority": page.priority.value,
            "importance_score": page.importance_score,
            "access_count": page.access_count,
            "last_accessed": page.last_accessed.isoformat(),
            "created_at": page.created_at.isoformat(),
            "metadata": page.metadata
        }).encode()
    
    def _deserialize(self, data: bytes) -> MemoryPage:
        import json
        d = json.loads(data)
        return MemoryPage(
            id=d["id"],
            content=d["content"],
            priority=MemoryPriority(d["priority"]),
            importance_score=d["importance_score"],
            access_count=d["access_count"],
            last_accessed=datetime.fromisoformat(d["last_accessed"]),
            created_at=datetime.fromisoformat(d["created_at"]),
            metadata=d.get("metadata", {})
        )
```

### 2.3 Working Memory Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     WORKING MEMORY LIFECYCLE                                     │
│                                                                                  │
│  USER REQUEST                                                                    │
│       │                                                                          │
│       ▼                                                                          │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ 1. LOAD CRITICAL PAGES                                                   │   │
│  │    ├── System prompt → Priority: CRITICAL                                │   │
│  │    ├── Active task context → Priority: CRITICAL                          │   │
│  │    └── Tool definitions → Priority: HIGH                                 │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│       │                                                                          │
│       ▼                                                                          │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ 2. LOAD RELEVANT EPISODES (from Episodic Memory)                         │   │
│  │    ├── User preferences → Priority: HIGH                                 │   │
│  │    ├── Similar past tasks → Priority: MEDIUM                             │   │
│  │    └── Recent context → Priority: MEDIUM                                 │   │
│  │    (Evict LRU pages if RAM full)                                         │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│       │                                                                          │
│       ▼                                                                          │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ 3. LOAD SEMANTIC CONTEXT (from Semantic Memory)                          │   │
│  │    ├── Relevant facts → Priority: MEDIUM                                 │   │
│  │    └── Domain knowledge → Priority: LOW                                  │   │
│  │    (Evict LRU pages if RAM full)                                         │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│       │                                                                          │
│       ▼                                                                          │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ 4. EXECUTION                                                             │   │
│  │    ├── Agent processes with loaded context                               │   │
│  │    ├── Tool outputs dynamically loaded as new pages                      │   │
│  │    └── Observations stored with calculated importance                    │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│       │                                                                          │
│       ▼                                                                          │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ 5. UPDATE                                                                │   │
│  │    ├── Mark accessed pages (update LRU)                                  │   │
│  │    ├── Store new observations to Episodic Memory                         │   │
│  │    ├── Archive low-priority pages to disk                                │   │
│  │    └── Update importance scores based on utility                         │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│       │                                                                          │
│       ▼                                                                          │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ 6. SESSION END                                                           │   │
│  │    ├── Persist all RAM pages to disk                                     │   │
│  │    ├── Trigger Episodic Memory consolidation (async)                     │   │
│  │    └── Clear working memory                                              │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. TIER 2: EPISODIC MEMORY (MEM0-STYLE)

### 3.1 Design Philosophy

Episodic memory stores **personal interaction history** — what happened, when, and with whom. It's the memory that makes agents feel like they "remember" you. Based on **Mem0** (48K GitHub stars, YC-backed with $24M Series A), the most widely adopted agent memory framework.

### 3.2 Core Features

- **Atomic fact extraction:** Conversations are decomposed into atomic facts
- **Multi-level scoping:** User-level, session-level, and agent-level memory
- **Hybrid retrieval:** Vector similarity + metadata filtering
- **Memory compression:** Reduces prompt tokens by up to 80%
- **Framework agnostic:** Works with any agent framework

### 3.3 Implementation

```python
# genesis/memory/episodic.py
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance, Filter, FieldCondition, Range, MatchValue
import asyncpg
import hashlib
import json

@dataclass
class AtomicFact:
    """Extracted atomic fact from an interaction"""
    content: str
    source_interaction: str
    agent_id: str
    user_id: str
    session_id: str
    timestamp: datetime
    importance_score: float  # 0-1
    fact_type: str  # preference, fact, event, relationship
    entities: List[str]  # Named entities mentioned
    
    def to_payload(self) -> Dict:
        return {
            "content": self.content,
            "source": self.source_interaction,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "importance": self.importance_score,
            "type": self.fact_type,
            "entities": self.entities
        }

class MemoryExtractor:
    """
    LLM-powered atomic fact extraction.
    
    Inspired by Mem0's extraction pipeline:
    1. Chunk conversation
    2. Extract atomic facts
    3. Deduplicate
    4. Score importance
    """
    
    EXTRACTION_PROMPT = """
    Extract atomic facts from the following conversation.
    
    Rules:
    1. Each fact must be self-contained and independently meaningful
    2. Include temporal context (when applicable)
    3. Mark fact type: preference, fact, event, relationship
    4. Assign importance score (0.0-1.0)
    5. Extract named entities
    
    Conversation:
    {conversation}
    
    Return JSON array:
    [
      {{
        "content": "User is vegetarian and avoids dairy",
        "fact_type": "preference",
        "importance": 0.9,
        "entities": ["user", "vegetarian", "dairy"]
      }}
    ]
    """
    
    async def extract(self, interaction: Dict) -> List[AtomicFact]:
        """Extract atomic facts from an interaction"""
        
        from genesis.llm import get_fast_model
        llm = get_fast_model()
        
        # Format conversation
        conversation = self._format_conversation(interaction)
        
        # Extract facts
        prompt = self.EXTRACTION_PROMPT.format(conversation=conversation)
        response = await llm.complete(prompt, response_format={"type": "json_object"})
        
        facts_data = json.loads(response.content)
        
        # Create AtomicFact objects
        facts = []
        for f in facts_data:
            fact = AtomicFact(
                content=f["content"],
                source_interaction=interaction.get("id", ""),
                agent_id=interaction.get("agent_id", ""),
                user_id=interaction.get("user_id", ""),
                session_id=interaction.get("session_id", ""),
                timestamp=datetime.now(),
                importance_score=f.get("importance", 0.5),
                fact_type=f.get("fact_type", "fact"),
                entities=f.get("entities", [])
            )
            facts.append(fact)
        
        # Deduplicate
        facts = self._deduplicate(facts)
        
        return facts
    
    def _format_conversation(self, interaction: Dict) -> str:
        """Format interaction for LLM processing"""
        messages = interaction.get("messages", [])
        formatted = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted)
    
    def _deduplicate(self, facts: List[AtomicFact], similarity_threshold: float = 0.85) -> List[AtomicFact]:
        """Remove near-duplicate facts"""
        unique = []
        for fact in facts:
            is_duplicate = False
            for existing in unique:
                similarity = self._text_similarity(fact.content, existing.content)
                if similarity > similarity_threshold:
                    # Keep the more important one
                    if fact.importance_score > existing.importance_score:
                        existing.content = fact.content
                        existing.importance_score = fact.importance_score
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique.append(fact)
        return unique
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Simple Jaccard similarity for deduplication"""
        set1 = set(text1.lower().split())
        set2 = set(text2.lower().split())
        intersection = set1 & set2
        union = set1 | set2
        return len(intersection) / len(union) if union else 0

class EpisodicMemory:
    """
    Episodic memory with Mem0-inspired architecture.
    Dual-store: Qdrant (vectors) + PostgreSQL (metadata)
    """
    
    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        database_url: str = "postgresql://localhost:5432/genesis",
        collection_name: str = "episodic_memory"
    ):
        self.qdrant = QdrantClient(url=qdrant_url)
        self.db_url = database_url
        self.collection = collection_name
        self.extractor = MemoryExtractor()
        
        # Ensure collection exists
        self._init_collection()
    
    def _init_collection(self):
        """Initialize Qdrant collection if not exists"""
        try:
            self.qdrant.get_collection(self.collection)
        except Exception:
            self.qdrant.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=1536,
                    distance=Distance.COSINE,
                    quantization_scalar=ScalarQuantizationConfig(type="int8")
                )
            )
    
    async def store_interaction(self, interaction: Dict) -> List[str]:
        """
        Store an interaction in episodic memory.
        
        Pipeline:
        1. Extract atomic facts
        2. Generate embeddings
        3. Store in Qdrant with metadata
        4. Update PostgreSQL metadata
        """
        from genesis.embeddings import get_embeddings
        
        # Step 1: Extract facts
        facts = await self.extractor.extract(interaction)
        
        # Step 2: Generate embeddings
        texts = [f.content for f in facts]
        embeddings = await get_embeddings(texts)
        
        # Step 3: Store in Qdrant
        points = []
        for fact, embedding in zip(facts, embeddings):
            point_id = hashlib.md5(
                f"{fact.user_id}:{fact.content}:{fact.timestamp}".encode()
            ).hexdigest()
            
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload=fact.to_payload()
            ))
        
        self.qdrant.upsert(collection_name=self.collection, points=points)
        
        # Step 4: Store metadata in PostgreSQL
        conn = await asyncpg.connect(self.db_url)
        try:
            for fact, embedding in zip(facts, embeddings):
                await conn.execute("""
                    INSERT INTO memory_metadata 
                    (memory_type, external_id, storage_backend, agent_id, user_id, 
                     session_id, content_preview, importance_score, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (external_id, storage_backend) DO UPDATE SET
                        importance_score = EXCLUDED.importance_score,
                        access_count = memory_metadata.access_count + 1
                """, 
                    "episodic",
                    hashlib.md5(f"{fact.user_id}:{fact.content}:{fact.timestamp}".encode()).hexdigest(),
                    "qdrant",
                    fact.agent_id,
                    fact.user_id,
                    fact.session_id,
                    fact.content[:200],
                    fact.importance_score,
                    json.dumps({"entities": fact.entities, "fact_type": fact.fact_type})
                )
        finally:
            await conn.close()
        
        return [f"{fact.fact_type}:{fact.content[:50]}" for fact in facts]
    
    async def recall(
        self,
        query: str,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 10,
        min_importance: float = 0.3
    ) -> List[Dict]:
        """
        Recall memories relevant to the query.
        
        Uses hybrid retrieval:
        1. Vector similarity search
        2. Metadata filtering (agent_id, user_id)
        3. Importance threshold
        4. Reranking by combined score
        """
        from genesis.embeddings import get_embedding
        
        # Generate query embedding
        query_embedding = await get_embedding(query)
        
        # Build filter
        filter_conditions = [
            FieldCondition(key="importance", range=Range(gte=min_importance))
        ]
        if agent_id:
            filter_conditions.append(
                FieldCondition(key="agent_id", match=MatchValue(value=agent_id))
            )
        if user_id:
            filter_conditions.append(
                FieldCondition(key="user_id", match=MatchValue(value=user_id))
            )
        
        search_filter = Filter(must=filter_conditions)
        
        # Search
        results = self.qdrant.search(
            collection_name=self.collection,
            query_vector=query_embedding,
            query_filter=search_filter,
            limit=limit * 2,  # Get more for reranking
            with_payload=True
        )
        
        # Rerank: combine vector score with importance and recency
        scored_results = []
        for r in results:
            recency_score = self._calculate_recency(
                datetime.fromisoformat(r.payload.get("timestamp", "2024-01-01"))
            )
            combined_score = (
                r.score * 0.5 +                          # Vector similarity
                r.payload.get("importance", 0.5) * 0.3 +  # Importance
                recency_score * 0.2                       # Recency
            )
            scored_results.append((combined_score, r))
        
        # Sort by combined score and return top results
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        return [
            {
                "content": r.payload["content"],
                "type": r.payload.get("type", "fact"),
                "importance": r.payload.get("importance", 0.5),
                "timestamp": r.payload.get("timestamp"),
                "score": score,
                "entities": r.payload.get("entities", [])
            }
            for score, r in scored_results[:limit]
        ]
    
    def _calculate_recency(self, timestamp: datetime) -> float:
        """Calculate recency score (1.0 = now, 0.0 = 90 days ago)"""
        age_days = (datetime.now() - timestamp).total_seconds() / 86400
        return max(0, 1 - (age_days / 90))
```

---

## 4. TIER 3: SEMANTIC MEMORY (COGNEE-STYLE)

### 4.1 Design Philosophy

Semantic memory stores **general knowledge** — facts, concepts, and relationships. Based on **Cognee**, which builds knowledge graphs from unstructured data. The key innovation: agents can reason over relationships, not just retrieve similar text.

### 4.2 Core Features

- **Automatic knowledge graph construction:** From documents, conversations, external data
- **Multi-hop reasoning:** "Alice works at Company X, Company X is in Industry Y, therefore Alice is in Industry Y"
- **Graph + Vector hybrid:** Combine graph traversal with vector similarity
- **Continuous memory updates:** Knowledge evolves as new information arrives

### 4.3 Implementation

```python
# genesis/memory/semantic.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime
from neo4j import GraphDatabase, Driver
from qdrant_client import QdrantClient
import json

@dataclass
class Entity:
    """A node in the knowledge graph"""
    id: str
    name: str
    entity_type: str  # person, organization, concept, event, etc.
    description: str
    embedding: Optional[List[float]] = None
    properties: Dict = field(default_factory=dict)
    source: str = ""  # Where this entity was extracted from
    confidence: float = 0.8
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Relationship:
    """An edge in the knowledge graph"""
    source_id: str
    target_id: str
    relation_type: str  # works_at, part_of, causes, relates_to, etc.
    properties: Dict = field(default_factory=dict)
    confidence: float = 0.8
    source_evidence: str = ""

class GraphExtractor:
    """
    LLM-powered entity and relationship extraction.
    
    Inspired by Cognee's add-cognify-search pipeline.
    """
    
    EXTRACTION_PROMPT = """
    Extract entities and relationships from the following text.
    
    Entities to extract:
    - People, organizations, products, technologies
    - Concepts, events, locations
    
    Relationships to identify:
    - Professional: works_at, founded, leads, reports_to
    - Conceptual: part_of, type_of, instance_of
    - Causal: causes, enables, prevents
    - Generic: relates_to, mentioned_with
    
    Text:
    {text}
    
    Return JSON:
    {{
      "entities": [
        {{"name": "Alice", "type": "person", "description": "..."}}
      ],
      "relationships": [
        {{"source": "Alice", "target": "Company X", "type": "works_at"}}
      ]
    }}
    """
    
    async def extract(self, text: str) -> Tuple[List[Entity], List[Relationship]]:
        """Extract entities and relationships from text"""
        
        from genesis.llm import get_fast_model
        llm = get_fast_model()
        
        prompt = self.EXTRACTION_PROMPT.format(text=text[:8000])
        response = await llm.complete(prompt, response_format={"type": "json_object"})
        
        data = json.loads(response.content)
        
        entities = []
        entity_map = {}  # name -> id
        
        for e in data.get("entities", []):
            entity_id = f"{e['type']}:{e['name'].lower().replace(' ', '_')}"
            entity = Entity(
                id=entity_id,
                name=e["name"],
                entity_type=e["type"],
                description=e.get("description", ""),
                properties=e.get("properties", {}),
                confidence=e.get("confidence", 0.8)
            )
            entities.append(entity)
            entity_map[e["name"]] = entity_id
        
        relationships = []
        for r in data.get("relationships", []):
            if r["source"] in entity_map and r["target"] in entity_map:
                rel = Relationship(
                    source_id=entity_map[r["source"]],
                    target_id=entity_map[r["target"]],
                    relation_type=r["type"],
                    properties=r.get("properties", {}),
                    confidence=r.get("confidence", 0.8)
                )
                relationships.append(rel)
        
        return entities, relationships

class SemanticMemory:
    """
    Semantic memory with Cognee-inspired knowledge graph.
    
    Dual storage:
    - Neo4j: Graph structure (entities, relationships)
    - Qdrant: Vector embeddings for semantic search
    """
    
    def __init__(
        self,
        neo4j_url: str = "bolt://localhost:7687",
        neo4j_auth: Tuple[str, str] = ("neo4j", "genesis_password"),
        qdrant_url: str = "http://localhost:6333",
        collection_name: str = "semantic_memory"
    ):
        self.neo4j: Driver = GraphDatabase.driver(neo4j_url, auth=neo4j_auth)
        self.qdrant = QdrantClient(url=qdrant_url)
        self.collection = collection_name
        self.extractor = GraphExtractor()
        
        self._init_schema()
    
    def _init_schema(self):
        """Initialize Neo4j schema with constraints and indexes"""
        with self.neo4j.session() as session:
            # Constraints
            session.run("CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE")
            session.run("CREATE CONSTRAINT event_id IF NOT EXISTS FOR (ev:Event) REQUIRE ev.id IS UNIQUE")
            
            # Indexes
            session.run("CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)")
            session.run("CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)")
            session.run("CREATE INDEX rel_type IF NOT EXISTS FOR ()-[r:RELATES_TO]-() ON (r.relation_type)")
    
    async def ingest(self, documents: List[Dict]) -> Dict:
        """
        Ingest documents into semantic memory.
        
        Pipeline (Cognee-style):
        1. Add: Normalize and deduplicate
        2. Cognify: Extract entities and relationships
        3. Build graph: Merge into Neo4j
        4. Index: Store embeddings in Qdrant
        """
        
        from genesis.embeddings import get_embeddings
        
        all_entities = []
        all_relationships = []
        
        # Step 1 & 2: Extract from each document
        for doc in documents:
            text = doc.get("content", "")
            if not text:
                continue
            
            entities, relationships = await self.extractor.extract(text)
            all_entities.extend(entities)
            all_relationships.extend(relationships)
        
        # Deduplicate entities
        entity_map = {}
        for e in all_entities:
            if e.id not in entity_map:
                entity_map[e.id] = e
        
        # Step 3: Build graph in Neo4j
        with self.neo4j.session() as session:
            for entity in entity_map.values():
                session.run("""
                    MERGE (e:Entity {id: $id})
                    SET e.name = $name,
                        e.type = $type,
                        e.description = $description,
                        e.properties = $properties,
                        e.confidence = $confidence,
                        e.updated_at = datetime()
                    RETURN e
                """, {
                    "id": entity.id,
                    "name": entity.name,
                    "type": entity.entity_type,
                    "description": entity.description,
                    "properties": json.dumps(entity.properties),
                    "confidence": entity.confidence
                })
            
            for rel in all_relationships:
                session.run("""
                    MATCH (a:Entity {id: $source_id})
                    MATCH (b:Entity {id: $target_id})
                    MERGE (a)-[r:RELATES_TO {
                        relation_type: $rel_type
                    }]->(b)
                    SET r.properties = $properties,
                        r.confidence = $confidence,
                        r.updated_at = datetime()
                """, {
                    "source_id": rel.source_id,
                    "target_id": rel.target_id,
                    "rel_type": rel.relation_type,
                    "properties": json.dumps(rel.properties),
                    "confidence": rel.confidence
                })
        
        # Step 4: Generate embeddings and store in Qdrant
        if entity_map:
            embeddings = await get_embeddings([
                f"{e.name}: {e.description}" 
                for e in entity_map.values()
            ])
            
            from qdrant_client.models import PointStruct
            points = [
                PointStruct(
                    id=e.id,
                    vector=emb,
                    payload={
                        "entity_id": e.id,
                        "name": e.name,
                        "type": e.entity_type,
                        "description": e.description
                    }
                )
                for e, emb in zip(entity_map.values(), embeddings)
            ]
            
            self.qdrant.upsert(collection_name=self.collection, points=points)
        
        return {
            "entities_created": len(entity_map),
            "relationships_created": len(all_relationships),
            "documents_processed": len(documents)
        }
    
    async def reason(self, query: str, max_depth: int = 3) -> List[Dict]:
        """
        Multi-hop reasoning over the knowledge graph.
        
        Strategy:
        1. Find entry points via vector search
        2. Traverse graph from entry points
        3. Rank paths by relevance to query
        """
        from genesis.embeddings import get_embedding
        
        # Step 1: Find entry points
        query_embedding = await get_embedding(query)
        
        entry_points = self.qdrant.search(
            collection_name=self.collection,
            query_vector=query_embedding,
            limit=3,
            with_payload=True
        )
        
        # Step 2: Graph traversal
        all_paths = []
        
        with self.neo4j.session() as session:
            for ep in entry_points:
                entity_id = ep.payload["entity_id"]
                
                # Cypher query for multi-hop traversal
                result = session.run("""
                    MATCH path = (start:Entity {id: $start_id})-[:RELATES_TO*1..""" + str(max_depth) + """]-(end:Entity)
                    WHERE start <> end
                    WITH path, 
                         [node in nodes(path) | node.name] as node_names,
                         [rel in relationships(path) | rel.relation_type] as rel_types,
                         reduce(conf = 1.0, rel in relationships(path) | conf * rel.confidence) as path_confidence
                    RETURN node_names, rel_types, path_confidence, length(path) as depth
                    ORDER BY path_confidence DESC
                    LIMIT 10
                """, {"start_id": entity_id})
                
                for record in result:
                    all_paths.append({
                        "nodes": record["node_names"],
                        "relationships": record["rel_types"],
                        "confidence": record["path_confidence"],
                        "depth": record["depth"]
                    })
        
        # Step 3: Rank and deduplicate paths
        all_paths.sort(key=lambda p: p["confidence"], reverse=True)
        
        # Deduplicate similar paths
        unique_paths = []
        seen = set()
        for path in all_paths:
            path_key = "->".join(path["nodes"])
            if path_key not in seen:
                seen.add(path_key)
                unique_paths.append(path)
        
        return unique_paths[:10]
    
    def get_entity(self, entity_id: str) -> Optional[Dict]:
        """Get full entity information with relationships"""
        
        with self.neo4j.session() as session:
            # Get entity
            entity_result = session.run(
                "MATCH (e:Entity {id: $id}) RETURN e",
                {"id": entity_id}
            )
            entity_record = entity_result.single()
            
            if not entity_record:
                return None
            
            entity = dict(entity_record["e"])
            
            # Get relationships
            rels_result = session.run("""
                MATCH (e:Entity {id: $id})-[r:RELATES_TO]-(other:Entity)
                RETURN other.name as related_entity, 
                       other.type as related_type,
                       r.relation_type as relation,
                       CASE WHEN startNode(r) = e THEN 'outgoing' ELSE 'incoming' END as direction
            """, {"id": entity_id})
            
            entity["relationships"] = [dict(r) for r in rels_result]
            
            return entity
```

---

## 5. TIER 4: PROCEDURAL MEMORY (SKILL SYSTEM)

### 5.1 Design Philosophy

Procedural memory stores **executable skills** — how to do things. Unlike other memory tiers, procedural memory is directly executable. Skills are versioned, fitness-tracked, and genetically encoded, enabling evolution over time.

### 5.2 Skill Structure

```python
# genesis/memory/procedural.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import hashlib
import json

@dataclass
class SkillDNA:
    """
    Genetic encoding of a skill.
    
    This is the genotype that can be:
    - Mutated (prompt changes, parameter tuning)
    - Crossed over (blending two skills)
    - Evaluated for fitness
    """
    # Identification
    skill_name: str
    version: int = 1
    
    # The skill definition
    description: str = ""
    prompt_template: str = ""  # Primary instruction
    
    # Tool requirements
    required_tools: List[str] = field(default_factory=list)
    optional_tools: List[str] = field(default_factory=list)
    
    # Parameters (tunable genes)
    parameters: Dict[str, Any] = field(default_factory=lambda: {
        "temperature": 0.3,
        "max_tokens": 2048,
        "reasoning_effort": "medium",
        "max_iterations": 5,
        "timeout_seconds": 30
    })
    
    # Validation rules
    input_schema: Dict = field(default_factory=dict)
    output_schema: Dict = field(default_factory=dict)
    validation_rules: List[str] = field(default_factory=list)
    
    # Execution pattern
    execution_pattern: str = "sequential"  # sequential, parallel, conditional
    error_handling: str = "retry"  # retry, fallback, abort
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    complexity_level: str = "medium"  # simple, medium, complex
    estimated_duration_seconds: int = 60
    
    # Genetic metadata
    lineage: List[str] = field(default_factory=list)  # Ancestor skill IDs
    mutation_history: List[Dict] = field(default_factory=list)
    
    def to_json(self) -> str:
        return json.dumps({
            "skill_name": self.skill_name,
            "version": self.version,
            "description": self.description,
            "prompt_template": self.prompt_template,
            "required_tools": self.required_tools,
            "optional_tools": self.optional_tools,
            "parameters": self.parameters,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "validation_rules": self.validation_rules,
            "execution_pattern": self.execution_pattern,
            "error_handling": self.error_handling,
            "tags": self.tags,
            "complexity_level": self.complexity_level,
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "lineage": self.lineage,
            "mutation_history": self.mutation_history
        }, indent=2)
    
    @property
    def dna_hash(self) -> str:
        """Unique hash for this DNA configuration"""
        return hashlib.sha256(self.to_json().encode()).hexdigest()[:16]

@dataclass
class Skill:
    """A registered skill with runtime metadata"""
    id: str
    dna: SkillDNA
    
    # Runtime metadata
    fitness_score: float = 0.5
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_execution_time_ms: float = 0
    
    # Status
    status: str = "active"  # active, deprecated, experimental
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.5
    
    @property
    def composite_fitness(self) -> float:
        """
        Composite fitness score considering multiple factors:
        - Explicit fitness score (0.4)
        - Success rate (0.3)
        - Usage popularity (0.2)
        - Efficiency (0.1)
        """
        usage_score = min(self.usage_count / 100, 1.0)
        
        # Assume lower execution time is better
        efficiency = max(0, 1 - (self.avg_execution_time_ms / 60000))
        
        return (
            self.fitness_score * 0.4 +
            self.success_rate * 0.3 +
            usage_score * 0.2 +
            efficiency * 0.1
        )
```

### 5.3 Skill Registry

```python
class ProceduralMemory:
    """
    Registry for executable skills.
    
    Features:
    - Semantic skill matching (find best skill for task)
    - Version management
    - Fitness tracking
    - Hot-swapping (load new versions without restart)
    """
    
    def __init__(
        self,
        db_url: str = "postgresql://localhost:5432/genesis",
        qdrant_url: str = "http://localhost:6333",
        collection_name: str = "procedural_memory"
    ):
        self.db_url = db_url
        self.qdrant = QdrantClient(url=qdrant_url)
        self.collection = collection_name
        
        # In-memory cache of active skills
        self.active_skills: Dict[str, Skill] = {}
        
        # Load active skills
        asyncio.create_task(self._load_active_skills())
    
    async def find_skill(self, task_description: str, agent_type: Optional[str] = None) -> Optional[Skill]:
        """
        Find the best skill for a given task description.
        
        Uses semantic matching:
        1. Embed task description
        2. Search skill embeddings
        3. Filter by fitness threshold
        4. Return best match
        """
        from genesis.embeddings import get_embedding
        
        # Embed task
        task_embedding = await get_embedding(task_description)
        
        # Search
        filter_conditions = []
        if agent_type:
            filter_conditions.append(
                FieldCondition(key="agent_type", match=MatchValue(value=agent_type))
            )
        
        results = self.qdrant.search(
            collection_name=self.collection,
            query_vector=task_embedding,
            query_filter=Filter(must=filter_conditions) if filter_conditions else None,
            limit=5,
            with_payload=True
        )
        
        # Filter by fitness and return best
        viable = [
            r for r in results 
            if r.payload.get("fitness_score", 0) > 0.5
            and r.payload.get("status") == "active"
        ]
        
        if not viable:
            return None
        
        best = max(viable, key=lambda r: r.score * r.payload.get("fitness_score", 0.5))
        
        # Load full skill from database
        skill_id = best.payload["skill_id"]
        return await self.get_skill(skill_id)
    
    async def register_skill(self, dna: SkillDNA, created_by: Optional[str] = None) -> Skill:
        """
        Register a new skill or new version of existing skill.
        """
        import asyncpg
        
        # Check if skill with same name exists
        conn = await asyncpg.connect(self.db_url)
        try:
            existing = await conn.fetchrow(
                "SELECT id, version FROM skills WHERE name = $1 ORDER BY version DESC LIMIT 1",
                dna.skill_name
            )
            
            if existing:
                # New version
                dna.version = existing["version"] + 1
                skill_id = existing["id"]
            else:
                # New skill
                skill_id = str(uuid.uuid4())
            
            # Store in database
            await conn.execute("""
                INSERT INTO skills (id, name, version, description, definition, dna, 
                                  fitness_score, created_by, agent_type, tags)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """, 
                skill_id,
                dna.skill_name,
                dna.version,
                dna.description,
                dna.to_json(),
                json.dumps(dna.__dict__, default=str),
                0.5,  # Initial fitness
                created_by,
                dna.tags[0] if dna.tags else None,
                dna.tags
            )
        finally:
            await conn.close()
        
        # Index in Qdrant
        from genesis.embeddings import get_embedding
        skill_text = f"{dna.skill_name}: {dna.description}. Tools: {', '.join(dna.required_tools)}. Tags: {', '.join(dna.tags)}"
        embedding = await get_embedding(skill_text)
        
        from qdrant_client.models import PointStruct
        self.qdrant.upsert(
            collection_name=self.collection,
            points=[PointStruct(
                id=skill_id,
                vector=embedding,
                payload={
                    "skill_id": skill_id,
                    "name": dna.skill_name,
                    "version": dna.version,
                    "fitness_score": 0.5,
                    "status": "active",
                    "tags": dna.tags
                }
            )]
        )
        
        skill = Skill(id=skill_id, dna=dna)
        self.active_skills[skill_id] = skill
        
        return skill
    
    async def update_fitness(self, skill_id: str, task_result: Dict):
        """
        Update skill fitness based on execution result.
        
        Called after every skill execution to continuously
        improve fitness estimates.
        """
        skill = self.active_skills.get(skill_id)
        if not skill:
            skill = await self.get_skill(skill_id)
        
        if not skill:
            return
        
        # Update counters
        skill.usage_count += 1
        if task_result.get("success"):
            skill.success_count += 1
        else:
            skill.failure_count += 1
        
        # Update average execution time
        exec_time = task_result.get("latency_ms", 0)
        skill.avg_execution_time_ms = (
            (skill.avg_execution_time_ms * (skill.usage_count - 1) + exec_time)
            / skill.usage_count
        )
        
        # Update fitness score using exponential moving average
        task_fitness = task_result.get("fitness_score", 0.5)
        alpha = 0.3  # Learning rate
        skill.fitness_score = (1 - alpha) * skill.fitness_score + alpha * task_fitness
        
        # Persist updates
        import asyncpg
        conn = await asyncpg.connect(self.db_url)
        try:
            await conn.execute("""
                UPDATE skills 
                SET fitness_score = $1, 
                    usage_count = $2, 
                    success_count = $3,
                    failure_count = $4
                WHERE id = $5
            """, skill.fitness_score, skill.usage_count, 
                skill.success_count, skill.failure_count, skill_id)
        finally:
            await conn.close()
```

---

## 6. MEMORY CONSOLIDATION PIPELINE

### 6.1 Consolidation Triggers

| Trigger Type | Condition | Action |
|-------------|-----------|--------|
| **Count-based** | Every 50-200 episodic memories | Consolidate to semantic |
| **Time-based** | Every 24 hours | Full consolidation sweep |
| **Manual** | Admin trigger | Immediate consolidation |
| **Threshold** | Episodic storage > 80% capacity | Emergency consolidation |
| **Agent request** | Agent detects pattern | On-demand consolidation |

### 6.2 Consolidation: Episodic → Semantic

```python
class ConsolidationPipeline:
    """
    Memory consolidation inspired by the Generative Agents paper (Park et al. 2023).
    
    Key insight from the paper:
    "When the reflection mechanism was removed from the 25-agent simulation,
    emergent coordination behaviors disappeared entirely."
    
    Consolidation is THE most impactful component for believable agent behavior.
    """
    
    CONSOLIDATION_PROMPT = """
    Analyze the following episodic memories and extract higher-level semantic knowledge.
    
    Instructions:
    1. Identify recurring themes, patterns, and concepts
    2. Extract general facts and preferences (not specific events)
    3. Build entity relationships
    4. Create durable knowledge that doesn't reference specific timestamps
    
    Episodic Memories:
    {memories}
    
    Return:
    {{
      "semantic_facts": [
        {{
          "fact": "User prefers concise answers over detailed explanations",
          "confidence": 0.9,
          "supporting_episodes": ["episode_id_1", "episode_id_2"]
        }}
      ],
      "entities": [
        {{
          "name": "User",
          "type": "person",
          "attributes": {{"communication_style": "concise"}}
        }}
      ],
      "relationships": [
        {{
          "source": "User",
          "target": "concise_answers",
          "type": "prefers"
        }}
      ]
    }}
    """
    
    async def consolidate_episodic_to_semantic(
        self,
        agent_id: Optional[str] = None,
        batch_size: int = 100
    ) -> ConsolidationResult:
        """
        Consolidate episodic memories into semantic knowledge.
        
        Process:
        1. Gather unconsolidated episodes
        2. Group by relevance
        3. Extract semantic facts via LLM
        4. Store in semantic memory (Cognee/Neo4j)
        5. Mark episodes as consolidated
        """
        
        # Step 1: Gather unconsolidated episodes
        episodes = await self._get_unconsolidated_episodes(agent_id, batch_size)
        
        if not episodes:
            return ConsolidationResult(sources_processed=0, targets_created=0)
        
        # Step 2: Group by similarity
        groups = self._group_by_similarity(episodes)
        
        total_facts = 0
        
        # Step 3: Process each group
        for group in groups:
            # Extract semantic knowledge
            facts = await self._extract_semantic_facts(group)
            
            # Step 4: Store in semantic memory
            for fact in facts:
                await self.semantic_memory.store_fact(fact)
                total_facts += 1
        
        # Step 5: Mark episodes as consolidated
        await self._mark_consolidated([e.id for e in episodes])
        
        return ConsolidationResult(
            sources_processed=len(episodes),
            targets_created=total_facts,
            facts_extracted=total_facts
        )
    
    async def _extract_semantic_facts(self, episodes: List[EpisodicMemory]) -> List[Dict]:
        """Use LLM to extract semantic facts from episodes"""
        
        from genesis.llm import get_powerful_model
        llm = get_powerful_model()
        
        # Format episodes
        memories_text = "\n\n".join([
            f"[{e.timestamp}] {e.content} (Importance: {e.importance})"
            for e in episodes
        ])
        
        prompt = self.CONSOLIDATION_PROMPT.format(memories=memories_text)
        
        response = await llm.complete(prompt, response_format={"type": "json_object"})
        data = json.loads(response.content)
        
        return data.get("semantic_facts", [])
```

### 6.3 Consolidation: Semantic → Procedural

```python
    async def consolidate_semantic_to_procedural(
        self,
        agent_id: Optional[str] = None
    ) -> ConsolidationResult:
        """
        Convert repeated semantic patterns into procedural skills.
        
        Trigger: When an agent repeatedly performs similar tasks successfully,
        extract the pattern as a skill.
        """
        
        # Find frequently executed task patterns
        patterns = await self._find_repeated_patterns(agent_id)
        
        skills_created = 0
        
        for pattern in patterns:
            if pattern.frequency > 3 and pattern.avg_fitness > 0.7:
                # Generate skill from pattern
                skill_dna = await self._pattern_to_skill(pattern)
                
                # Register skill
                await self.procedural_memory.register_skill(
                    dna=skill_dna,
                    created_by=agent_id
                )
                
                skills_created += 1
        
        return ConsolidationResult(
            sources_processed=len(patterns),
            targets_created=skills_created
        )
    
    async def _pattern_to_skill(self, pattern: TaskPattern) -> SkillDNA:
        """Convert a task pattern into a skill definition"""
        
        from genesis.llm import get_powerful_model
        llm = get_powerful_model()
        
        prompt = f"""
        Create a skill definition based on the following task execution pattern.
        
        Pattern:
        - Task type: {pattern.task_type}
        - Description: {pattern.description}
        - Tools used: {', '.join(pattern.tools_used)}
        - Average steps: {pattern.avg_steps}
        - Success rate: {pattern.success_rate}
        - Common inputs: {pattern.input_examples}
        
        Create a skill with:
        1. Clear description
        2. System prompt template
        3. Required tools
        4. Input/output schemas
        5. Validation rules
        
        Return JSON matching SkillDNA schema.
        """
        
        response = await llm.complete(prompt, response_format={"type": "json_object"})
        skill_data = json.loads(response.content)
        
        return SkillDNA(
            skill_name=skill_data.get("skill_name", pattern.task_type),
            description=skill_data.get("description", ""),
            prompt_template=skill_data.get("prompt_template", ""),
            required_tools=skill_data.get("required_tools", []),
            parameters=skill_data.get("parameters", {}),
            input_schema=skill_data.get("input_schema", {}),
            output_schema=skill_data.get("output_schema", {}),
            tags=[pattern.task_type, "auto-generated"]
        )
```

---

## 7. PERFORMANCE OPTIMIZATION

### 7.1 Caching Strategy

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         MEMORY CACHE HIERARCHY                                   │
│                                                                                  │
│   L1: In-Memory (Agent Instance)                                                │
│   ├── Working Memory pages (LRU eviction)                                       │
│   ├── Recently used skills                                                      │
│   └── Active agent configurations                                               │
│   Hit: <1ms | Capacity: ~100MB per agent                                        │
│                                                                                  │
│   L2: Redis (Shared)                                                            │
│   ├── Working memory archive (paged out)                                        │
│   ├── Agent state snapshots                                                     │
│   └── Pub/sub messages                                                          │
│   Hit: 1-5ms | Capacity: Configurable (default 1GB)                            │
│                                                                                  │
│   L3: Qdrant (Vector Search)                                                    │
│   ├── Episodic memory embeddings                                                │
│   ├── Semantic entity embeddings                                                │
│   └── Skill embeddings                                                          │
│   Hit: 20-50ms | Capacity: Billions of vectors                                 │
│                                                                                  │
│   L4: Neo4j (Graph Traversal)                                                   │
│   ├── Knowledge graph nodes                                                     │
│   ├── Relationships                                                             │
│   └── Path indexes                                                              │
│   Hit: 50-100ms | Capacity: Unlimited                                           │
│                                                                                  │
│   L5: PostgreSQL (Metadata)                                                     │
│   ├── Agent registry                                                            │
│   ├── Execution logs                                                            │
│   └── System configuration                                                      │
│   Hit: 5-20ms | Capacity: TB scale                                              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Benchmarks

| Operation | Target Latency | Optimization |
|-----------|---------------|--------------|
| Working memory access | <1ms | In-memory LRU cache |
| Working memory page fault | 5-10ms | Redis with pipelining |
| Episodic store | 50ms | Qdrant batch upsert |
| Episodic recall (single) | 50-100ms | Qdrant HNSW index |
| Semantic ingestion (10 docs) | 2-5s | Parallel extraction |
| Semantic reasoning (3 hops) | 100-200ms | Neo4j path indexing |
| Skill matching | 20-50ms | Qdrant ANN + metadata filter |
| Full consolidation cycle | 30-60s | Batch processing |

---

*Document Status: MEMORY SYSTEM DESIGN COMPLETE*  
*Next Review: After Phase 2 Implementation*  
*Document Owner: Genesis AI Platform Memory Engineering Team*
