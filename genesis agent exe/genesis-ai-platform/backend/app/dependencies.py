"""
GENESIS Platform — FastAPI Dependency Injection
Shared singleton clients: Anthropic, Qdrant, Redis, Neo4j, engines.
"""
from functools import lru_cache
from typing import Optional

import redis.asyncio as aioredis
import structlog
from anthropic import AsyncAnthropic
from fastapi import Depends
from qdrant_client import AsyncQdrantClient

from app.config import get_settings

log = structlog.get_logger(__name__)
settings = get_settings()

# ── Singleton clients (module-level, initialized on startup) ──
_anthropic: Optional[AsyncAnthropic] = None
_qdrant: Optional[AsyncQdrantClient] = None
_redis: Optional[aioredis.Redis] = None
_neo4j_driver = None


def get_anthropic() -> AsyncAnthropic:
    global _anthropic
    if _anthropic is None:
        _anthropic = AsyncAnthropic(
            api_key=settings.anthropic_api_key,
            base_url=settings.anthropic_base_url,
        )
    return _anthropic


def get_qdrant() -> AsyncQdrantClient:
    global _qdrant
    if _qdrant is None:
        _qdrant = AsyncQdrantClient(url=settings.qdrant_url)
    return _qdrant


def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


def get_neo4j_driver():
    global _neo4j_driver
    if _neo4j_driver is None:
        try:
            from neo4j import AsyncGraphDatabase
            _neo4j_driver = AsyncGraphDatabase.driver(
                settings.neo4j_url,
                auth=(settings.neo4j_user, settings.neo4j_password),
            )
        except Exception as e:
            log.warning("neo4j.connection.failed", error=str(e))
            return None
    return _neo4j_driver


# ── Memory System ─────────────────────────────────────────────
def get_episodic_memory(qdrant: AsyncQdrantClient = Depends(get_qdrant)):
    from app.memory.memory_system import EpisodicMemory
    return EpisodicMemory(qdrant)


def get_working_memory(redis: aioredis.Redis = Depends(get_redis)):
    from app.memory.memory_system import WorkingMemory
    return WorkingMemory(redis)


def get_semantic_memory():
    driver = get_neo4j_driver()
    if driver is None:
        return None
    from app.memory.memory_system import SemanticMemory
    return SemanticMemory(driver)


def get_memory_manager(
    episodic=Depends(get_episodic_memory),
    working=Depends(get_working_memory),
):
    from app.memory.memory_system import MemoryManager
    semantic = get_semantic_memory()
    return MemoryManager(working=working, episodic=episodic, semantic=semantic)


# ── Agent Engine ──────────────────────────────────────────────
def get_agent_engine(
    llm: AsyncAnthropic = Depends(get_anthropic),
    memory_manager=Depends(get_memory_manager),
):
    from app.agents.engine import AgentEngine
    return AgentEngine(memory_manager=memory_manager, llm=llm)


# ── Evolution Engine ──────────────────────────────────────────
def get_evolution_engine(llm: AsyncAnthropic = Depends(get_anthropic)):
    from app.genetic.evolution_engine import GeneticEvolutionEngine
    return GeneticEvolutionEngine(llm=llm)


# ── Lifecycle ─────────────────────────────────────────────────
async def startup():
    """Initialize all connections and ensure Qdrant collections exist."""
    log.info("genesis.startup.begin")
    llm = get_anthropic()
    qdrant = get_qdrant()
    redis = get_redis()

    # Ensure Qdrant collections
    from app.memory.memory_system import EpisodicMemory
    episodic = EpisodicMemory(qdrant)
    try:
        await episodic.ensure_collection()
        log.info("qdrant.collection.ready")
    except Exception as e:
        log.warning("qdrant.collection.failed", error=str(e))

    # Ping Redis
    try:
        await redis.ping()
        log.info("redis.connection.ready")
    except Exception as e:
        log.warning("redis.connection.failed", error=str(e))

    log.info("genesis.startup.complete")


async def shutdown():
    """Gracefully close all connections."""
    global _redis, _qdrant, _neo4j_driver
    if _redis:
        await _redis.aclose()
    if _qdrant:
        await _qdrant.close()
    if _neo4j_driver:
        await _neo4j_driver.close()
    log.info("genesis.shutdown.complete")
