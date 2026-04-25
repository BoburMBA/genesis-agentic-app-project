"""
GENESIS Platform — Pydantic Schemas
Request/response validation matching OpenAPI spec
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


# ── Agent DNA ─────────────────────────────────────────────────
class PromptGenes(BaseModel):
    system_prompt: str
    reasoning_pattern: Literal["chain-of-thought","tree-of-thought","react","plan-and-execute"] = "chain-of-thought"
    self_correction_enabled: bool = True
    verbosity: float = Field(default=0.5, ge=0.0, le=1.0)
    tone: str = "analytical"

class ParameterGenes(BaseModel):
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=64, le=8192)
    reasoning_effort: Literal["low","medium","high"] = "medium"

class ToolGenes(BaseModel):
    available_tools: List[str] = []
    max_tools_per_task: int = Field(default=5, ge=1, le=20)

class MemoryGenes(BaseModel):
    working_memory_size: int = Field(default=10, ge=1, le=50)
    episodic_retrieval_k: int = Field(default=5, ge=1, le=20)
    semantic_depth: int = Field(default=3, ge=1, le=10)
    consolidation_frequency: int = Field(default=100, ge=10)

class EvolutionGenes(BaseModel):
    mutation_rate: float = Field(default=0.1, ge=0.0, le=1.0)
    fitness_weights: Dict[str, float] = {}
    crossover_enabled: bool = True

class AgentDNA(BaseModel):
    dna_version: str = "1.0"
    prompt_genes: PromptGenes
    parameter_genes: ParameterGenes
    tool_genes: ToolGenes = ToolGenes()
    memory_genes: MemoryGenes = MemoryGenes()
    evolution_genes: EvolutionGenes = EvolutionGenes()


# ── Agent ─────────────────────────────────────────────────────
class AgentBase(BaseModel):
    type: Literal["research","code","analysis","creative","skill_builder","router","scheduler"]
    name: str
    dna: AgentDNA

class AgentCreate(AgentBase):
    generation: int = 1
    parent_ids: Optional[List[uuid.UUID]] = None

class AgentResponse(BaseModel):
    id: uuid.UUID
    type: str
    name: str
    generation: int
    dna: Dict[str, Any]
    fitness_score: float
    status: str
    execution_count: int
    tokens_used: int
    created_at: datetime
    updated_at: datetime
    last_executed_at: Optional[datetime] = None
    parent_ids: Optional[List[uuid.UUID]] = None

    model_config = {"from_attributes": True}

class AgentListResponse(BaseModel):
    agents: List[AgentResponse]
    total: int
    page: int
    page_size: int


# ── Task ──────────────────────────────────────────────────────
class TaskRequest(BaseModel):
    task: str = Field(..., min_length=1, max_length=10000)
    context: Optional[Dict[str, Any]] = None
    memory_scope: Literal["session","user","agent","global"] = "session"
    session_id: Optional[str] = None
    user_id: Optional[str] = None

class RoutingResult(BaseModel):
    selected_agent_type: str
    reasoning: str
    confidence: float
    router_agent_id: Optional[uuid.UUID] = None

class TaskResponse(BaseModel):
    task_id: uuid.UUID
    status: str
    output: str
    agent_name: str
    agent_type: str
    agent_id: uuid.UUID
    routing: Optional[RoutingResult] = None
    tokens_input: int
    tokens_output: int
    latency_ms: int
    memory_recalls: int
    created_at: datetime

    model_config = {"from_attributes": True}

class TaskListResponse(BaseModel):
    tasks: List[Dict[str, Any]]
    total: int


# ── Evolution ─────────────────────────────────────────────────
class EvolutionRequest(BaseModel):
    agent_types: Optional[List[str]] = None  # None = all types
    generations: int = Field(default=1, ge=1, le=10)
    selection_pressure: float = Field(default=0.7, ge=0.0, le=1.0)
    mutation_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    strategy: Literal["mutation_only","crossover","full"] = "full"

class MutationRequest(BaseModel):
    agent_id: uuid.UUID
    intensity: Literal["mild","medium","strong"] = "medium"
    target_genes: Optional[List[Literal["prompt","parameter","tool","memory","evolution"]]] = None

class EvolutionEventResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    old_fitness: Optional[float]
    new_fitness: Optional[float]
    changes: Optional[Dict[str, Any]]
    timestamp: datetime

    model_config = {"from_attributes": True}

class EvolutionGenerationResponse(BaseModel):
    id: uuid.UUID
    generation_number: int
    agent_type: str
    population_size: int
    avg_fitness: Optional[float]
    max_fitness: Optional[float]
    min_fitness: Optional[float]
    diversity_score: Optional[float]
    mutations_applied: int
    crossovers_applied: int
    new_agents_created: int
    agents_retired: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    events: List[EvolutionEventResponse] = []

    model_config = {"from_attributes": True}


# ── Memory ────────────────────────────────────────────────────
class MemoryScope(BaseModel):
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    session_id: Optional[str] = None

class MemoryStoreRequest(BaseModel):
    content: str = Field(..., min_length=1)
    memory_type: Literal["episodic","semantic","procedural"] = "episodic"
    scope: Optional[MemoryScope] = None
    importance: float = Field(default=0.6, ge=0.0, le=1.0)
    tags: List[str] = []

class MemoryEntry(BaseModel):
    id: str
    content: str
    memory_type: str
    importance: float
    score: Optional[float] = None
    agent_name: Optional[str] = None
    created_at: Optional[str] = None
    metadata: Dict[str, Any] = {}

class MemoryQueryResponse(BaseModel):
    memories: List[MemoryEntry]
    total: int
    query: str


# ── Skills ────────────────────────────────────────────────────
class SkillCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    definition: Optional[Dict[str, Any]] = None
    agent_type: Optional[str] = None
    tags: List[str] = []
    auto_generate: bool = False
    generation_prompt: Optional[str] = None

class SkillResponse(BaseModel):
    id: uuid.UUID
    name: str
    version: int
    description: Optional[str]
    definition: Dict[str, Any]
    fitness_score: float
    usage_count: int
    success_count: int
    agent_type: Optional[str]
    tags: Optional[List[str]]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

class SkillListResponse(BaseModel):
    skills: List[SkillResponse]
    total: int


# ── System ────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    services: Dict[str, str]
    agent_count: int
    task_count: int

class StatsResponse(BaseModel):
    agents: Dict[str, Any]
    tasks: Dict[str, Any]
    memory: Dict[str, Any]
    evolution: Dict[str, Any]
    skills: Dict[str, Any]


# ── A2A Protocol ──────────────────────────────────────────────
class A2AAgentCard(BaseModel):
    name: str = "GENESIS AI Platform"
    description: str = "Multi-agent genetic evolution system"
    version: str = "2.0.0"
    url: str
    capabilities: List[Dict[str, Any]] = []
    authentication: Dict[str, Any] = {"schemes": ["Bearer"]}

class A2ATaskRequest(BaseModel):
    id: str
    message: str
    context: Optional[Dict[str, Any]] = None
    callback_url: Optional[str] = None
