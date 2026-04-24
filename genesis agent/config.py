"""
GENESIS Platform — Application Configuration
Pydantic Settings with environment variable support
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ────────────────────────────────────────────────────
    app_env: str = "development"
    app_secret_key: str = "change-me-in-production"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    # ── LLM Providers ─────────────────────────────────────────
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # ── Models ────────────────────────────────────────────────
    primary_model: str = "claude-sonnet-4-20250514"
    router_model: str = "claude-haiku-4-5-20251001"
    embedding_model: str = "all-MiniLM-L6-v2"

    # ── Infrastructure ────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://genesis:genesis_password@localhost:5432/genesis"
    qdrant_url: str = "http://localhost:6333"
    neo4j_url: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "genesis_password"
    redis_url: str = "redis://localhost:6379"

    # ── Evolution ─────────────────────────────────────────────
    evolution_auto_cycle: bool = True
    evolution_cycle_interval_tasks: int = 100
    evolution_min_population: int = 5
    evolution_max_population: int = 20
    evolution_selection_pressure: float = 0.7
    evolution_default_mutation_rate: float = 0.1
    evolution_elitism_count: int = 2

    # ── Memory ────────────────────────────────────────────────
    memory_working_size: int = 10
    memory_episodic_k: int = 5
    memory_semantic_depth: int = 3
    memory_consolidation_frequency: int = 100
    memory_importance_threshold: float = 0.6
    memory_default_ttl_days: int = 90

    # ── Qdrant Collection Names ───────────────────────────────
    qdrant_episodic_collection: str = "genesis_episodic"
    qdrant_semantic_collection: str = "genesis_semantic"
    qdrant_skills_collection: str = "genesis_skills"
    qdrant_vector_size: int = 384  # all-MiniLM-L6-v2 output dim


@lru_cache
def get_settings() -> Settings:
    return Settings()
