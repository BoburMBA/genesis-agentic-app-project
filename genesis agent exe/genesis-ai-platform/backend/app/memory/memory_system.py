"""
GENESIS Platform — Memory System
4-tier memory: Working (Redis) + Episodic (Qdrant) + Semantic (Neo4j) + Procedural (PostgreSQL)
"""
import json
import uuid
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import redis.asyncio as aioredis
import structlog
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance, PointStruct, Filter, FieldCondition, MatchValue,
    VectorParams, UpdateStatus, SearchRequest,
)
from sentence_transformers import SentenceTransformer

from app.config import get_settings

log = structlog.get_logger(__name__)
settings = get_settings()

# ── Embedding model (singleton) ───────────────────────────────
_embed_model: Optional[SentenceTransformer] = None

def get_embed_model() -> SentenceTransformer:
    global _embed_model
    if _embed_model is None:
        _embed_model = SentenceTransformer(settings.embedding_model)
    return _embed_model

def embed(text: str) -> List[float]:
    model = get_embed_model()
    return model.encode(text, normalize_embeddings=True).tolist()


# ── Tier 1: Working Memory (Redis) ────────────────────────────
class WorkingMemory:
    """
    Letta-style OS virtual memory for context window management.
    Session-scoped, LRU-evicted, Redis-backed.
    """

    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.ttl = 3600 * 24  # 24h session TTL
        self.max_items = settings.memory_working_size

    def _key(self, session_id: str) -> str:
        return f"genesis:wm:{session_id}"

    async def push(self, session_id: str, item: Dict[str, Any]) -> None:
        key = self._key(session_id)
        item["ts"] = datetime.now(timezone.utc).isoformat()
        await self.redis.lpush(key, json.dumps(item))
        await self.redis.ltrim(key, 0, self.max_items - 1)
        await self.redis.expire(key, self.ttl)

    async def get_context(self, session_id: str, k: int = 10) -> List[Dict[str, Any]]:
        key = self._key(session_id)
        items = await self.redis.lrange(key, 0, k - 1)
        return [json.loads(i) for i in reversed(items)]

    async def clear(self, session_id: str) -> None:
        await self.redis.delete(self._key(session_id))

    async def stats(self, session_id: str) -> Dict[str, Any]:
        key = self._key(session_id)
        length = await self.redis.llen(key)
        ttl = await self.redis.ttl(key)
        return {"items": length, "max_items": self.max_items, "ttl_seconds": ttl}


# ── Tier 2: Episodic Memory (Qdrant) ─────────────────────────
class EpisodicMemory:
    """
    Mem0-inspired episodic memory. Stores atomic facts as vectors in Qdrant.
    Supports multi-level scoping: user / session / agent / global.
    """

    def __init__(self, qdrant: AsyncQdrantClient):
        self.qdrant = qdrant
        self.collection = settings.qdrant_episodic_collection

    async def ensure_collection(self) -> None:
        try:
            await self.qdrant.get_collection(self.collection)
        except Exception:
            await self.qdrant.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=settings.qdrant_vector_size,
                    distance=Distance.COSINE
                )
            )
            log.info("qdrant.collection_created", collection=self.collection)

    async def store(
        self,
        content: str,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        importance: float = 0.6,
        memory_type: str = "fact",
        extra_meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        mem_id = str(uuid.uuid4())
        vector = embed(content)
        payload = {
            "content": content,
            "agent_id": agent_id,
            "user_id": user_id,
            "session_id": session_id,
            "importance": importance,
            "memory_type": memory_type,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **(extra_meta or {}),
        }
        await self.qdrant.upsert(
            collection_name=self.collection,
            points=[PointStruct(id=mem_id, vector=vector, payload=payload)]
        )
        log.info("memory.episodic.stored", id=mem_id, agent=agent_id)
        return mem_id

    async def search(
        self,
        query: str,
        k: int = 5,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        min_score: float = 0.4,
    ) -> List[Dict[str, Any]]:
        vector = embed(query)

        # Build filter from scope
        conditions = []
        if agent_id:
            conditions.append(FieldCondition(key="agent_id", match=MatchValue(value=agent_id)))
        if user_id:
            conditions.append(FieldCondition(key="user_id", match=MatchValue(value=user_id)))
        if session_id:
            conditions.append(FieldCondition(key="session_id", match=MatchValue(value=session_id)))

        search_filter = Filter(must=conditions) if conditions else None

        results = await self.qdrant.search(
            collection_name=self.collection,
            query_vector=vector,
            limit=k,
            query_filter=search_filter,
            with_payload=True,
            score_threshold=min_score,
        )

        return [
            {
                "id": str(r.id),
                "content": r.payload.get("content", ""),
                "score": r.score,
                "importance": r.payload.get("importance", 0.5),
                "memory_type": r.payload.get("memory_type", "fact"),
                "agent_id": r.payload.get("agent_id"),
                "created_at": r.payload.get("created_at"),
            }
            for r in results
        ]

    async def extract_and_store_facts(
        self,
        task: str,
        response: str,
        agent_id: str,
        session_id: str,
        llm_client: Any,
    ) -> List[str]:
        """
        Mem0-style: call LLM to extract atomic facts, store each one.
        Returns list of stored memory IDs.
        """
        prompt = f"""Extract 1-3 key atomic facts from this AI interaction.
Each fact should be self-contained and reusable.
Return ONLY a JSON array: [{{"content":"...", "type":"fact|preference|event", "importance":0.0-1.0}}]

Task: {task[:500]}
Response: {response[:800]}"""

        try:
            msg = await llm_client.messages.create(
                model=settings.router_model,
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}]
            )
            text = msg.content[0].text if msg.content else "[]"
            # Strip markdown fences
            text = text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            facts = json.loads(text)
        except Exception as e:
            log.warning("memory.extract_facts.failed", error=str(e))
            facts = [{"content": f"Completed task: {task[:100]}", "type": "event", "importance": 0.5}]

        stored_ids = []
        for fact in facts[:3]:
            if isinstance(fact, dict) and fact.get("content"):
                mem_id = await self.store(
                    content=fact["content"],
                    agent_id=agent_id,
                    session_id=session_id,
                    importance=fact.get("importance", 0.6),
                    memory_type=fact.get("type", "fact"),
                )
                stored_ids.append(mem_id)

        return stored_ids

    async def get_stats(self) -> Dict[str, Any]:
        try:
            info = await self.qdrant.get_collection(self.collection)
            return {
                "total_vectors": info.points_count,
                "status": info.status,
                "collection": self.collection,
            }
        except Exception:
            return {"total_vectors": 0, "status": "unavailable"}


# ── Tier 3: Semantic Memory (Neo4j knowledge graph) ───────────
class SemanticMemory:
    """
    Cognee-inspired knowledge graph stored in Neo4j.
    Extracts entities and relationships, enables multi-hop reasoning.
    """

    def __init__(self, driver: Any):
        self.driver = driver  # neo4j.AsyncDriver

    async def store_entity(self, name: str, entity_type: str, properties: Dict[str, Any]) -> str:
        entity_id = hashlib.md5(f"{entity_type}:{name}".encode()).hexdigest()
        async with self.driver.session() as session:
            await session.run(
                """
                MERGE (e:Entity {id: $id})
                SET e.name = $name, e.type = $type, e.updated_at = $updated_at
                SET e += $props
                """,
                id=entity_id, name=name, type=entity_type,
                updated_at=datetime.now(timezone.utc).isoformat(),
                props=properties
            )
        return entity_id

    async def store_relationship(
        self, source_id: str, target_id: str, rel_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        async with self.driver.session() as session:
            await session.run(
                """
                MATCH (s:Entity {id: $src})
                MATCH (t:Entity {id: $tgt})
                MERGE (s)-[r:RELATES {type: $type}]->(t)
                SET r.created_at = $ts
                """,
                src=source_id, tgt=target_id, type=rel_type,
                ts=datetime.now(timezone.utc).isoformat()
            )

    async def query_neighborhood(self, entity_name: str, depth: int = 2) -> List[Dict[str, Any]]:
        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (e:Entity {name: $name})
                CALL apoc.path.subgraphAll(e, {maxLevel: $depth})
                YIELD nodes, relationships
                RETURN nodes, relationships
                """,
                name=entity_name, depth=depth
            )
            records = await result.data()
            return records

    async def get_stats(self) -> Dict[str, Any]:
        try:
            async with self.driver.session() as session:
                result = await session.run("MATCH (n:Entity) RETURN count(n) AS entities")
                data = await result.data()
                entity_count = data[0]["entities"] if data else 0

                result2 = await session.run("MATCH ()-[r]->() RETURN count(r) AS rels")
                data2 = await result2.data()
                rel_count = data2[0]["rels"] if data2 else 0

            return {"entities": entity_count, "relationships": rel_count, "status": "connected"}
        except Exception as e:
            return {"entities": 0, "relationships": 0, "status": "unavailable", "error": str(e)}


# ── Memory Manager (orchestrates all tiers) ───────────────────
class MemoryManager:
    """
    Unified interface for all 4 memory tiers.
    Used by agents during task execution.
    """

    def __init__(
        self,
        working: WorkingMemory,
        episodic: EpisodicMemory,
        semantic: Optional[SemanticMemory] = None,
    ):
        self.working = working
        self.episodic = episodic
        self.semantic = semantic

    async def retrieve_context(
        self,
        query: str,
        session_id: str,
        agent_id: Optional[str] = None,
        k: int = 5,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Retrieve both working memory (recent turns) and relevant episodic memories.
        Returns (working_context, episodic_memories)
        """
        working = await self.working.get_context(session_id, k=k)
        episodic = await self.episodic.search(
            query=query,
            k=k,
            agent_id=agent_id,
            session_id=session_id,
        )
        return working, episodic

    async def store_interaction(
        self,
        task: str,
        response: str,
        agent_id: str,
        session_id: str,
        llm_client: Any,
    ) -> Dict[str, Any]:
        """Full post-task memory storage pipeline."""
        # Push to working memory
        await self.working.push(session_id, {
            "role": "assistant",
            "content": response[:500],
            "agent_id": agent_id,
            "task": task[:200],
        })

        # Extract and store episodic facts
        stored_ids = await self.episodic.extract_and_store_facts(
            task=task,
            response=response,
            agent_id=agent_id,
            session_id=session_id,
            llm_client=llm_client,
        )

        return {
            "working_memory_updated": True,
            "episodic_memories_stored": len(stored_ids),
            "memory_ids": stored_ids,
        }

    async def build_memory_context_string(
        self,
        query: str,
        session_id: str,
        agent_id: Optional[str] = None,
    ) -> str:
        """Format retrieved memories as a string to inject into agent context."""
        working, episodic = await self.retrieve_context(
            query=query, session_id=session_id, agent_id=agent_id
        )

        parts = []

        if working:
            parts.append("## Recent Context")
            for item in working[-3:]:
                parts.append(f"- {item.get('task','')}: {item.get('content','')[:150]}")

        if episodic:
            parts.append("\n## Relevant Memory")
            for mem in episodic[:3]:
                score_pct = f"{mem['score']*100:.0f}%"
                parts.append(f"- [{score_pct}] {mem['content']}")

        return "\n".join(parts) if parts else ""
