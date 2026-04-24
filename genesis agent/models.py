"""
GENESIS Platform — SQLAlchemy ORM Models
Exact mapping of the Technical Specification database schema
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, DateTime, Float, ForeignKey,
    Integer, String, Text, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ── Agent ─────────────────────────────────────────────────────
class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    generation: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    dna: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    fitness_score: Mapped[Optional[float]] = mapped_column(Float, default=0.5)
    parent_ids: Mapped[Optional[List[uuid.UUID]]] = mapped_column(ARRAY(UUID(as_uuid=True)))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    execution_count: Mapped[int] = mapped_column(Integer, default=0)
    tokens_used: Mapped[int] = mapped_column(BigInteger, default=0)

    # Relationships
    task_executions: Mapped[List["TaskExecution"]] = relationship(
        "TaskExecution", back_populates="agent", foreign_keys="TaskExecution.agent_id",
        cascade="all, delete-orphan"
    )
    agent_skills: Mapped[List["AgentSkill"]] = relationship(
        "AgentSkill", back_populates="agent", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "type IN ('research','code','analysis','creative','skill_builder','router','scheduler')",
            name="valid_agent_type"
        ),
        CheckConstraint(
            "status IN ('active','evolving','sandbox','deprecated','retired')",
            name="valid_agent_status"
        ),
        CheckConstraint(
            "fitness_score >= 0 AND fitness_score <= 1",
            name="valid_fitness"
        ),
    )

    def __repr__(self) -> str:
        return f"<Agent id={self.id} type={self.type} name={self.name} gen={self.generation}>"


# ── Task Execution ────────────────────────────────────────────
class TaskExecution(Base):
    __tablename__ = "task_executions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    router_agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    task_type: Mapped[str] = mapped_column(String(50), nullable=False, default="general")
    task_description: Mapped[str] = mapped_column(Text, nullable=False)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    output: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    fitness_contribution: Mapped[Optional[float]] = mapped_column(Float)
    tokens_input: Mapped[int] = mapped_column(Integer, default=0)
    tokens_output: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    memory_recalls: Mapped[int] = mapped_column(Integer, default=0)
    tools_used: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    routing_confidence: Mapped[Optional[float]] = mapped_column(Float)
    routing_reasoning: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    agent: Mapped["Agent"] = relationship("Agent", back_populates="task_executions", foreign_keys=[agent_id])


# ── Skill ─────────────────────────────────────────────────────
class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    description: Mapped[Optional[str]] = mapped_column(Text)
    definition: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    dna: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    fitness_score: Mapped[float] = mapped_column(Float, default=0.5)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    lineage: Mapped[Optional[List[uuid.UUID]]] = mapped_column(ARRAY(UUID(as_uuid=True)))
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    agent_type: Mapped[Optional[str]] = mapped_column(String(50))
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    agent_skills: Mapped[List["AgentSkill"]] = relationship("AgentSkill", back_populates="skill")

    __table_args__ = (UniqueConstraint("name", "version", name="uq_skill_name_version"),)


# ── Agent-Skill Association ───────────────────────────────────
class AgentSkill(Base):
    __tablename__ = "agent_skills"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    proficiency: Mapped[float] = mapped_column(Float, default=0.5)
    times_used: Mapped[int] = mapped_column(Integer, default=0)
    avg_fitness: Mapped[Optional[float]] = mapped_column(Float)

    agent: Mapped["Agent"] = relationship("Agent", back_populates="agent_skills")
    skill: Mapped["Skill"] = relationship("Skill", back_populates="agent_skills")


# ── Evolution Generation ──────────────────────────────────────
class EvolutionGeneration(Base):
    __tablename__ = "evolution_generations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    generation_number: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    population_size: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_fitness: Mapped[Optional[float]] = mapped_column(Float)
    max_fitness: Mapped[Optional[float]] = mapped_column(Float)
    min_fitness: Mapped[Optional[float]] = mapped_column(Float)
    std_fitness: Mapped[Optional[float]] = mapped_column(Float)
    diversity_score: Mapped[Optional[float]] = mapped_column(Float)
    mutations_applied: Mapped[int] = mapped_column(Integer, default=0)
    crossovers_applied: Mapped[int] = mapped_column(Integer, default=0)
    selections_performed: Mapped[int] = mapped_column(Integer, default=0)
    new_agents_created: Mapped[int] = mapped_column(Integer, default=0)
    agents_retired: Mapped[int] = mapped_column(Integer, default=0)
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="running")

    events: Mapped[List["EvolutionEvent"]] = relationship("EvolutionEvent", back_populates="generation")


# ── Evolution Event ───────────────────────────────────────────
class EvolutionEvent(Base):
    __tablename__ = "evolution_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    generation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evolution_generations.id")
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    parent_ids: Mapped[Optional[List[uuid.UUID]]] = mapped_column(ARRAY(UUID(as_uuid=True)))
    child_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"))
    old_fitness: Mapped[Optional[float]] = mapped_column(Float)
    new_fitness: Mapped[Optional[float]] = mapped_column(Float)
    changes: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    generation: Mapped[Optional["EvolutionGeneration"]] = relationship(
        "EvolutionGeneration", back_populates="events"
    )


# ── Memory Metadata ───────────────────────────────────────────
class MemoryMetadata(Base):
    __tablename__ = "memory_metadata"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    memory_type: Mapped[str] = mapped_column(String(20), nullable=False)
    external_id: Mapped[str] = mapped_column(String(200), nullable=False)
    storage_backend: Mapped[str] = mapped_column(String(20), nullable=False)
    agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"))
    user_id: Mapped[Optional[str]] = mapped_column(String(100))
    session_id: Mapped[Optional[str]] = mapped_column(String(100))
    content_preview: Mapped[Optional[str]] = mapped_column(Text)
    importance_score: Mapped[float] = mapped_column(Float, default=0.5)
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)

    __table_args__ = (UniqueConstraint("external_id", "storage_backend", name="uq_memory_external"),)


# ── System Config ─────────────────────────────────────────────
class SystemConfig(Base):
    __tablename__ = "system_config"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
