"""
GENESIS Platform — FastAPI Routers
All REST endpoints matching the OpenAPI specification.
"""
import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import select, func, desc, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import (
    Agent, TaskExecution, Skill, AgentSkill,
    EvolutionGeneration, EvolutionEvent, MemoryMetadata, SystemConfig
)
from app.schemas import (
    AgentCreate, AgentResponse, AgentListResponse,
    TaskRequest, TaskResponse,
    EvolutionRequest, EvolutionGenerationResponse,
    MutationRequest,
    MemoryStoreRequest, MemoryQueryResponse, MemoryEntry,
    SkillCreate, SkillResponse, SkillListResponse,
    HealthResponse, StatsResponse,
    A2AAgentCard, A2ATaskRequest,
)
from app.agents.engine import AGENT_DNA_DEFAULTS, AGENT_NAMES
from app.dependencies import get_agent_engine, get_memory_manager, get_evolution_engine, get_episodic_memory

log = structlog.get_logger(__name__)

# ═══════════════════════════════════════════════════════════════
# AGENTS ROUTER
# ═══════════════════════════════════════════════════════════════
agents_router = APIRouter(prefix="/agents", tags=["agents"])


@agents_router.get("", response_model=AgentListResponse)
async def list_agents(
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    min_fitness: Optional[float] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Agent)
    if type:
        stmt = stmt.where(Agent.type == type)
    if status:
        stmt = stmt.where(Agent.status == status)
    if min_fitness is not None:
        stmt = stmt.where(Agent.fitness_score >= min_fitness)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(desc(Agent.fitness_score))
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    agents = (await db.execute(stmt)).scalars().all()

    return AgentListResponse(
        agents=[AgentResponse.model_validate(a) for a in agents],
        total=total,
        page=page,
        page_size=page_size,
    )


@agents_router.post("", response_model=AgentResponse, status_code=201)
async def create_agent(payload: AgentCreate, db: AsyncSession = Depends(get_db)):
    dna = payload.dna.model_dump()
    agent = Agent(
        type=payload.type,
        name=payload.name,
        generation=payload.generation,
        dna=dna,
        parent_ids=payload.parent_ids,
        fitness_score=0.5,
        status="active",
    )
    db.add(agent)
    await db.flush()
    log.info("agent.created", id=str(agent.id), type=agent.type)
    return AgentResponse.model_validate(agent)


@agents_router.get("/seed", response_model=AgentListResponse)
async def seed_agents(db: AsyncSession = Depends(get_db)):
    """Seed the database with the 6 default GENESIS agents if empty."""
    count = (await db.execute(select(func.count()).select_from(Agent))).scalar() or 0
    if count > 0:
        stmt = select(Agent).order_by(desc(Agent.fitness_score))
        agents = (await db.execute(stmt)).scalars().all()
        return AgentListResponse(
            agents=[AgentResponse.model_validate(a) for a in agents],
            total=count, page=1, page_size=20,
        )

    seed_configs = [
        ("router",        "NEXUS",     4, 0.87),
        ("research",      "ORACLE",    5, 0.91),
        ("code",          "FORGE",     3, 0.83),
        ("analysis",      "SIGMA",     6, 0.88),
        ("creative",      "MUSE",      2, 0.76),
        ("skill_builder", "ARCHITECT", 1, 0.71),
    ]

    new_agents = []
    for agent_type, name, gen, fitness in seed_configs:
        dna = AGENT_DNA_DEFAULTS.get(agent_type, {})
        agent = Agent(
            type=agent_type,
            name=name,
            generation=gen,
            dna=dna,
            fitness_score=fitness,
            execution_count=max(0, (gen - 1) * 40),
            tokens_used=max(0, (gen - 1) * 100000),
            status="active",
        )
        db.add(agent)
        new_agents.append(agent)

    await db.flush()
    log.info("agents.seeded", count=len(new_agents))
    return AgentListResponse(
        agents=[AgentResponse.model_validate(a) for a in new_agents],
        total=len(new_agents), page=1, page_size=20,
    )


@agents_router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(404, detail="Agent not found")
    return AgentResponse.model_validate(agent)


@agents_router.delete("/{agent_id}")
async def retire_agent(agent_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(404, detail="Agent not found")
    agent.status = "retired"
    return {"status": "retired", "agent_id": str(agent_id)}


@agents_router.put("/{agent_id}/dna")
async def update_dna(
    agent_id: uuid.UUID,
    dna: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(404, detail="Agent not found")
    agent.dna = dna
    return {"status": "updated", "agent_id": str(agent_id)}


# ═══════════════════════════════════════════════════════════════
# TASKS ROUTER
# ═══════════════════════════════════════════════════════════════
tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])


@tasks_router.post("", response_model=TaskResponse)
async def execute_task(
    payload: TaskRequest,
    db: AsyncSession = Depends(get_db),
    engine=Depends(get_agent_engine),
):
    start = time.time()
    session_id = payload.session_id or "default"

    # 1. Load active agents
    stmt = select(Agent).where(Agent.status == "active").order_by(desc(Agent.fitness_score))
    agents = (await db.execute(stmt)).scalars().all()
    if not agents:
        raise HTTPException(503, detail="No active agents available. Run /api/v1/agents/seed first.")

    agents_dicts = [
        {
            "id": a.id, "type": a.type, "name": a.name,
            "dna": a.dna, "fitness_score": a.fitness_score,
            "generation": a.generation,
        }
        for a in agents
    ]

    # 2. Route the task
    routing = await engine.route_task(payload.task, agents_dicts)
    selected_type = routing.get("selected_agent_type", "research")

    # Find router agent
    router_agent = next((a for a in agents if a.type == "router"), None)

    # Find execution agent
    exec_agent_model = next(
        (a for a in agents if a.type == selected_type),
        next((a for a in agents if a.type == "research"), agents[0])
    )
    exec_agent = {
        "id": exec_agent_model.id,
        "type": exec_agent_model.type,
        "name": exec_agent_model.name,
        "dna": exec_agent_model.dna,
        "fitness_score": exec_agent_model.fitness_score,
    }

    # 3. Execute task via LangGraph
    result = await engine.execute(
        task=payload.task,
        agent=exec_agent,
        session_id=session_id,
        user_id=payload.user_id,
    )

    # 4. Persist task execution
    input_hash = hashlib.sha256(payload.task.encode()).hexdigest()[:64]
    task_exec = TaskExecution(
        agent_id=exec_agent_model.id,
        router_agent_id=router_agent.id if router_agent else None,
        task_type=selected_type,
        task_description=payload.task,
        input_hash=input_hash,
        output={"response": result.get("response", ""), "metadata": {}},
        status="completed" if not result.get("error") else "failed",
        fitness_contribution=result.get("fitness_score", 0.5),
        tokens_input=result.get("tokens_input", 0),
        tokens_output=result.get("tokens_output", 0),
        latency_ms=result.get("latency_ms", 0),
        memory_recalls=result.get("memory_recalls", 0),
        routing_confidence=routing.get("confidence", 0.7),
        routing_reasoning=routing.get("reasoning", ""),
        error_message=result.get("error"),
    )
    db.add(task_exec)

    # 5. Update agent stats
    exec_agent_model.execution_count += 1
    exec_agent_model.tokens_used += result.get("tokens_input", 0) + result.get("tokens_output", 0)
    exec_agent_model.last_executed_at = datetime.now(timezone.utc)
    exec_agent_model.fitness_score = min(0.99, exec_agent_model.fitness_score + 0.001)

    if router_agent:
        router_agent.execution_count += 1

    await db.flush()

    from app.schemas import RoutingResult
    return TaskResponse(
        task_id=task_exec.id,
        status=task_exec.status,
        output=result.get("response", ""),
        agent_name=exec_agent_model.name,
        agent_type=exec_agent_model.type,
        agent_id=exec_agent_model.id,
        routing=RoutingResult(
            selected_agent_type=selected_type,
            reasoning=routing.get("reasoning", ""),
            confidence=routing.get("confidence", 0.7),
            router_agent_id=router_agent.id if router_agent else None,
        ),
        tokens_input=result.get("tokens_input", 0),
        tokens_output=result.get("tokens_output", 0),
        latency_ms=result.get("latency_ms", 0),
        memory_recalls=result.get("memory_recalls", 0),
        created_at=task_exec.created_at,
    )


@tasks_router.get("")
async def list_tasks(
    agent_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(TaskExecution)
    if agent_id:
        stmt = stmt.where(TaskExecution.agent_id == agent_id)
    if status:
        stmt = stmt.where(TaskExecution.status == status)

    count = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0
    stmt = stmt.order_by(desc(TaskExecution.created_at)).offset((page - 1) * page_size).limit(page_size)
    tasks = (await db.execute(stmt)).scalars().all()

    return {
        "tasks": [
            {
                "id": str(t.id),
                "agent_id": str(t.agent_id),
                "task_type": t.task_type,
                "task_description": t.task_description,
                "status": t.status,
                "tokens_input": t.tokens_input,
                "tokens_output": t.tokens_output,
                "latency_ms": t.latency_ms,
                "memory_recalls": t.memory_recalls,
                "routing_confidence": t.routing_confidence,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in tasks
        ],
        "total": count,
    }


# ═══════════════════════════════════════════════════════════════
# EVOLUTION ROUTER
# ═══════════════════════════════════════════════════════════════
evolution_router = APIRouter(prefix="/evolution", tags=["evolution"])


@evolution_router.post("/run")
async def run_evolution(
    payload: EvolutionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    evo_engine=Depends(get_evolution_engine),
):
    """Run evolution cycle across the agent population."""
    # Load active agents
    stmt = select(Agent).where(Agent.status == "active")
    if payload.agent_types:
        stmt = stmt.where(Agent.type.in_(payload.agent_types))
    agents = (await db.execute(stmt)).scalars().all()

    if not agents:
        raise HTTPException(404, detail="No eligible agents found")

    agents_dicts = [
        {"id": a.id, "type": a.type, "name": a.name, "dna": a.dna,
         "fitness_score": a.fitness_score, "generation": a.generation}
        for a in agents
    ]

    # Load recent task history per agent
    task_history: Dict[str, List] = {}
    for agent in agents:
        stmt2 = (
            select(TaskExecution)
            .where(TaskExecution.agent_id == agent.id)
            .order_by(desc(TaskExecution.created_at))
            .limit(10)
        )
        tasks = (await db.execute(stmt2)).scalars().all()
        task_history[str(agent.id)] = [
            {"task_description": t.task_description, "output": t.output,
             "latency_ms": t.latency_ms, "tokens_output": t.tokens_output,
             "status": t.status}
            for t in tasks
        ]

    # Get current generation number
    gen_stmt = select(func.max(EvolutionGeneration.generation_number))
    max_gen = (await db.execute(gen_stmt)).scalar() or 0
    new_gen_num = max_gen + 1

    config = {
        "elitism_count": 2,
        "selection_pressure": payload.selection_pressure,
        "strategy": payload.strategy,
    }

    # Run the evolution
    evo_result = await evo_engine.run_generation(
        agents=agents_dicts,
        task_history_by_agent=task_history,
        config=config,
    )

    stats = evo_result["stats"]
    events_data = evo_result["events"]

    # Create generation record
    gen_record = EvolutionGeneration(
        generation_number=new_gen_num,
        agent_type="mixed",
        population_size=stats["population_size"],
        avg_fitness=stats["avg_fitness"],
        max_fitness=stats["max_fitness"],
        min_fitness=stats["min_fitness"],
        std_fitness=stats["std_fitness"],
        diversity_score=stats["diversity_score"],
        mutations_applied=stats["mutations_applied"],
        crossovers_applied=stats["crossovers_applied"],
        selections_performed=stats["selections_performed"],
        new_agents_created=stats["new_agents_created"],
        agents_retired=stats.get("agents_retired", 0),
        config=config,
        status="running",
    )
    db.add(gen_record)
    await db.flush()

    # Apply evolved DNA back to existing agents & create new agents
    new_agents_data = evo_result["new_agents"]
    retired_ids = set()

    # Map original agents by ID
    orig_map = {str(a.id): a for a in agents}

    for new_agent_data in new_agents_data:
        orig_id = str(new_agent_data.get("id", ""))
        if orig_id in orig_map:
            # Update existing agent's DNA and generation
            orig = orig_map[orig_id]
            orig.dna = new_agent_data["dna"]
            orig.generation = new_agent_data.get("generation", orig.generation)
            orig.fitness_score = new_agent_data.get("fitness_score", orig.fitness_score)
        else:
            # New offspring from crossover/mutation
            parent_ids = new_agent_data.get("parent_ids", [])
            parent_type = next(
                (orig_map[str(p)].type for p in parent_ids if str(p) in orig_map),
                "research"
            )
            parent_name = next(
                (orig_map[str(p)].name for p in parent_ids if str(p) in orig_map),
                "AGENT"
            )
            new_agent = Agent(
                type=parent_type,
                name=parent_name,
                generation=new_agent_data.get("generation", 1),
                dna=new_agent_data["dna"],
                fitness_score=new_agent_data.get("fitness_score", 0.5),
                parent_ids=[p for p in parent_ids if p],
                status="active",
            )
            db.add(new_agent)

    # Record evolution events
    for ev in events_data:
        evo_event = EvolutionEvent(
            generation_id=gen_record.id,
            event_type=ev["event_type"],
            parent_ids=ev.get("parent_ids"),
            old_fitness=ev.get("old_fitness"),
            new_fitness=ev.get("new_fitness"),
            changes=ev.get("changes"),
        )
        db.add(evo_event)

    gen_record.status = "completed"
    gen_record.completed_at = datetime.now(timezone.utc)
    await db.flush()

    return {
        "generation": new_gen_num,
        "status": "completed",
        "stats": stats,
        "events_count": len(events_data),
    }


@evolution_router.post("/mutate/{agent_id}")
async def mutate_agent(
    agent_id: uuid.UUID,
    payload: MutationRequest,
    db: AsyncSession = Depends(get_db),
    evo_engine=Depends(get_evolution_engine),
):
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(404, detail="Agent not found")

    agent_dict = {"id": agent.id, "type": agent.type, "dna": agent.dna, "fitness_score": agent.fitness_score}
    result = await evo_engine.mutate_agent(agent_dict, intensity=payload.intensity, target_genes=payload.target_genes)

    agent.dna = result.new_dna
    agent.generation += 1

    return {
        "agent_id": str(agent_id),
        "intensity": payload.intensity,
        "changes": result.changes,
        "new_generation": agent.generation,
    }


@evolution_router.get("/history")
async def get_evolution_history(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(EvolutionGeneration)
        .order_by(desc(EvolutionGeneration.generation_number))
        .limit(limit)
    )
    gens = (await db.execute(stmt)).scalars().all()
    return {
        "generations": [
            {
                "id": str(g.id),
                "generation_number": g.generation_number,
                "avg_fitness": g.avg_fitness,
                "max_fitness": g.max_fitness,
                "diversity_score": g.diversity_score,
                "mutations_applied": g.mutations_applied,
                "crossovers_applied": g.crossovers_applied,
                "status": g.status,
                "started_at": g.started_at.isoformat() if g.started_at else None,
            }
            for g in reversed(gens)
        ]
    }


@evolution_router.get("/events")
async def get_evolution_events(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(EvolutionEvent).order_by(desc(EvolutionEvent.timestamp)).limit(limit)
    events = (await db.execute(stmt)).scalars().all()
    return {
        "events": [
            {
                "id": str(e.id),
                "event_type": e.event_type,
                "old_fitness": e.old_fitness,
                "new_fitness": e.new_fitness,
                "changes": e.changes,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            }
            for e in events
        ]
    }


# ═══════════════════════════════════════════════════════════════
# MEMORY ROUTER
# ═══════════════════════════════════════════════════════════════
memory_router = APIRouter(prefix="/memory", tags=["memory"])


@memory_router.post("", status_code=201)
async def store_memory(
    payload: MemoryStoreRequest,
    db: AsyncSession = Depends(get_db),
    episodic=Depends(get_episodic_memory),
):
    scope = payload.scope or {}
    agent_id = scope.agent_id if hasattr(scope, 'agent_id') else None
    user_id = scope.user_id if hasattr(scope, 'user_id') else None
    session_id = scope.session_id if hasattr(scope, 'session_id') else None

    mem_id = await episodic.store(
        content=payload.content,
        agent_id=agent_id,
        user_id=user_id,
        session_id=session_id,
        importance=payload.importance,
        memory_type=payload.memory_type,
    )

    # Record in PostgreSQL for querying
    meta = MemoryMetadata(
        memory_type=payload.memory_type,
        external_id=mem_id,
        storage_backend="qdrant",
        agent_id=uuid.UUID(agent_id) if agent_id else None,
        user_id=user_id,
        session_id=session_id,
        content_preview=payload.content[:200],
        importance_score=payload.importance,
    )
    db.add(meta)

    return {"memory_id": mem_id, "status": "stored"}


@memory_router.get("", response_model=MemoryQueryResponse)
async def query_memory(
    query: str = Query(..., min_length=1),
    memory_type: str = Query("all"),
    k: int = Query(5, ge=1, le=20),
    agent_id: Optional[str] = Query(None),
    session_id: Optional[str] = Query(None),
    episodic=Depends(get_episodic_memory),
):
    results = await episodic.search(
        query=query,
        k=k,
        agent_id=agent_id,
        session_id=session_id,
    )

    entries = [
        MemoryEntry(
            id=r["id"],
            content=r["content"],
            memory_type=r.get("memory_type", "episodic"),
            importance=r.get("importance", 0.5),
            score=r.get("score"),
            created_at=r.get("created_at"),
        )
        for r in results
    ]

    return MemoryQueryResponse(memories=entries, total=len(entries), query=query)


@memory_router.get("/stats")
async def get_memory_stats(
    db: AsyncSession = Depends(get_db),
    episodic=Depends(get_episodic_memory),
):
    qdrant_stats = await episodic.get_stats()
    pg_count = (await db.execute(select(func.count()).select_from(MemoryMetadata))).scalar() or 0

    return {
        "episodic": qdrant_stats,
        "metadata_records": pg_count,
        "working": {"status": "redis-backed", "ttl_hours": 24},
        "semantic": {"status": "neo4j-backed"},
        "procedural": {"status": "postgresql-backed"},
    }


# ═══════════════════════════════════════════════════════════════
# SKILLS ROUTER
# ═══════════════════════════════════════════════════════════════
skills_router = APIRouter(prefix="/skills", tags=["skills"])


@skills_router.get("", response_model=SkillListResponse)
async def list_skills(
    agent_type: Optional[str] = Query(None),
    min_fitness: Optional[float] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Skill)
    if agent_type:
        stmt = stmt.where(Skill.agent_type == agent_type)
    if min_fitness is not None:
        stmt = stmt.where(Skill.fitness_score >= min_fitness)
    if status:
        stmt = stmt.where(Skill.status == status)

    stmt = stmt.order_by(desc(Skill.fitness_score))
    skills = (await db.execute(stmt)).scalars().all()
    return SkillListResponse(
        skills=[SkillResponse.model_validate(s) for s in skills],
        total=len(skills),
    )


@skills_router.post("", response_model=SkillResponse, status_code=201)
async def create_skill(
    payload: SkillCreate,
    db: AsyncSession = Depends(get_db),
    engine=Depends(get_agent_engine),
):
    definition = payload.definition or {}

    if payload.auto_generate:
        # Use ARCHITECT agent to auto-generate the skill
        stmt = select(Agent).where(Agent.type == "skill_builder", Agent.status == "active")
        builder = (await db.execute(stmt)).scalars().first()

        if builder:
            prompt = (
                payload.generation_prompt or
                f"Design a complete skill specification for: {payload.name}. "
                f"Description: {payload.description or 'A useful agent skill'}. "
                "Return JSON with: {\"steps\": [...], \"inputs\": {...}, \"outputs\": {...}, "
                "\"success_criteria\": [...], \"example_usage\": \"...\"}"
            )
            agent_dict = {
                "id": builder.id, "type": builder.type,
                "name": builder.name, "dna": builder.dna,
            }
            result = await engine.execute(task=prompt, agent=agent_dict)
            try:
                import re
                json_match = re.search(r'\{[\s\S]+\}', result.get("response", "{}"))
                if json_match:
                    definition = json.loads(json_match.group())
            except Exception:
                definition = {"generated": True, "prompt": prompt, "response": result.get("response", "")[:500]}

    # Check for existing version
    stmt = select(Skill).where(Skill.name == payload.name).order_by(desc(Skill.version))
    existing = (await db.execute(stmt)).scalars().first()
    version = (existing.version + 1) if existing else 1

    skill = Skill(
        name=payload.name,
        version=version,
        description=payload.description,
        definition=definition,
        fitness_score=0.55,
        agent_type=payload.agent_type,
        tags=payload.tags or [],
        status="active",
    )
    db.add(skill)
    await db.flush()

    return SkillResponse.model_validate(skill)


@skills_router.get("/seed")
async def seed_skills(db: AsyncSession = Depends(get_db)):
    """Seed the database with default skills."""
    count = (await db.execute(select(func.count()).select_from(Skill))).scalar() or 0
    if count > 0:
        return {"status": "already_seeded", "count": count}

    defaults = [
        ("Web Research Synthesis", "research", ["research","web","synthesis"], 0.89,
         "Search the web and synthesize findings into structured reports with citations."),
        ("Code Generation & Testing", "code", ["code","testing","generation"], 0.84,
         "Generate production-quality code with comprehensive tests and documentation."),
        ("Statistical Pattern Detection", "analysis", ["statistics","patterns","data"], 0.92,
         "Identify statistical patterns, anomalies, and trends in datasets."),
        ("Multi-Source Verification", "research", ["verification","sources","accuracy"], 0.88,
         "Cross-reference multiple sources to verify factual claims."),
        ("Creative Content Brainstorm", "creative", ["brainstorm","creative","ideation"], 0.71,
         "Generate diverse ideas and creative concepts for any domain."),
        ("Skill Gap Analysis", "skill_builder", ["meta","analysis","skills"], 0.68,
         "Detect missing capabilities and generate skill specifications to fill gaps."),
    ]

    created = []
    for name, agent_type, tags, fitness, desc in defaults:
        skill = Skill(
            name=name, version=1, description=desc,
            definition={"auto_seeded": True, "tags": tags},
            fitness_score=fitness, agent_type=agent_type, tags=tags, status="active",
        )
        db.add(skill)
        created.append(name)

    await db.flush()
    return {"status": "seeded", "count": len(created), "skills": created}


# ═══════════════════════════════════════════════════════════════
# SYSTEM ROUTER
# ═══════════════════════════════════════════════════════════════
system_router = APIRouter(prefix="/system", tags=["system"])


@system_router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    services = {}
    try:
        await db.execute(select(func.now()))
        services["postgres"] = "healthy"
    except Exception as e:
        services["postgres"] = f"unhealthy: {str(e)[:50]}"

    agent_count = (await db.execute(select(func.count()).select_from(Agent))).scalar() or 0
    task_count = (await db.execute(select(func.count()).select_from(TaskExecution))).scalar() or 0

    return HealthResponse(
        status="operational",
        version="2.0.0",
        environment="development",
        services=services,
        agent_count=agent_count,
        task_count=task_count,
    )


@system_router.get("/stats", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    # Agent stats
    agent_count = (await db.execute(select(func.count()).select_from(Agent).where(Agent.status == "active"))).scalar() or 0
    avg_fitness = (await db.execute(select(func.avg(Agent.fitness_score)).where(Agent.status == "active"))).scalar() or 0
    max_gen = (await db.execute(select(func.max(Agent.generation)))).scalar() or 0

    # Task stats
    task_count = (await db.execute(select(func.count()).select_from(TaskExecution))).scalar() or 0
    avg_latency = (await db.execute(select(func.avg(TaskExecution.latency_ms)))).scalar() or 0
    total_tokens = (await db.execute(select(func.sum(Agent.tokens_used)))).scalar() or 0

    # Evolution stats
    gen_count = (await db.execute(select(func.count()).select_from(EvolutionGeneration))).scalar() or 0
    max_gen_num = (await db.execute(select(func.max(EvolutionGeneration.generation_number)))).scalar() or 0

    # Skills
    skill_count = (await db.execute(select(func.count()).select_from(Skill).where(Skill.status == "active"))).scalar() or 0

    # Memory
    mem_count = (await db.execute(select(func.count()).select_from(MemoryMetadata))).scalar() or 0

    return StatsResponse(
        agents={"active": agent_count, "avg_fitness": round(float(avg_fitness), 4), "max_generation": max_gen},
        tasks={"total": task_count, "avg_latency_ms": round(float(avg_latency), 1), "total_tokens": total_tokens},
        evolution={"generations_run": gen_count, "current_generation": max_gen_num},
        memory={"total_memories": mem_count},
        skills={"active": skill_count},
    )


# ═══════════════════════════════════════════════════════════════
# A2A PROTOCOL ROUTER
# ═══════════════════════════════════════════════════════════════
a2a_router = APIRouter(prefix="/a2a", tags=["a2a"])


@a2a_router.get("/agent.json", response_model=A2AAgentCard)
async def agent_card():
    return A2AAgentCard(
        name="GENESIS AI Platform",
        description="Multi-agent system with genetic evolution, 4-tier memory, and autonomous skill building",
        version="2.0.0",
        url="http://localhost:8000/api/v1",
        capabilities=[
            {"name": "research", "description": "Web research and synthesis"},
            {"name": "code", "description": "Code generation and review"},
            {"name": "analysis", "description": "Data analysis and insights"},
            {"name": "creative", "description": "Creative content generation"},
            {"name": "skill_building", "description": "Autonomous skill creation"},
        ],
        authentication={"schemes": ["Bearer"]},
    )


@a2a_router.post("/tasks", status_code=202)
async def a2a_submit_task(payload: A2ATaskRequest):
    """A2A-compatible task submission endpoint."""
    return {
        "task_id": payload.id,
        "status": "accepted",
        "message": "Task queued for processing. Use /api/v1/tasks/{id} to poll status.",
    }
