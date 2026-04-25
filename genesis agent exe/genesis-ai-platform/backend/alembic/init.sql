-- GENESIS Platform — PostgreSQL Schema
-- Based on Technical Specification doc 03

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ── Agents ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type VARCHAR(50) NOT NULL CHECK (type IN (
        'research', 'code', 'analysis', 'creative',
        'skill_builder', 'router', 'scheduler'
    )),
    name VARCHAR(100) NOT NULL,
    generation INTEGER NOT NULL DEFAULT 1,
    dna JSONB NOT NULL DEFAULT '{}',
    fitness_score FLOAT CHECK (fitness_score >= 0 AND fitness_score <= 1) DEFAULT 0.5,
    parent_ids UUID[],
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (
        status IN ('active', 'evolving', 'sandbox', 'deprecated', 'retired')
    ),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_executed_at TIMESTAMPTZ,
    execution_count INTEGER DEFAULT 0,
    tokens_used BIGINT DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_agents_type       ON agents(type);
CREATE INDEX IF NOT EXISTS idx_agents_generation ON agents(generation);
CREATE INDEX IF NOT EXISTS idx_agents_status     ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_fitness    ON agents(fitness_score DESC);
CREATE INDEX IF NOT EXISTS idx_agents_dna        ON agents USING GIN(dna);

-- ── Task Executions ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS task_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    router_agent_id UUID REFERENCES agents(id),
    task_type VARCHAR(50) NOT NULL DEFAULT 'general',
    task_description TEXT NOT NULL,
    input_hash VARCHAR(64) NOT NULL,
    output JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'completed' CHECK (
        status IN ('completed', 'failed', 'timeout', 'cancelled', 'in_progress')
    ),
    fitness_contribution FLOAT,
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    latency_ms INTEGER,
    memory_recalls INTEGER DEFAULT 0,
    tools_used TEXT[],
    error_message TEXT,
    routing_confidence FLOAT,
    routing_reasoning TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tasks_agent   ON task_executions(agent_id);
CREATE INDEX IF NOT EXISTS idx_tasks_created ON task_executions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_status  ON task_executions(status);
CREATE INDEX IF NOT EXISTS idx_tasks_type    ON task_executions(task_type);

-- ── Skills ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    description TEXT,
    definition JSONB NOT NULL DEFAULT '{}',
    dna JSONB,
    fitness_score FLOAT DEFAULT 0.5 CHECK (fitness_score >= 0 AND fitness_score <= 1),
    usage_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    lineage UUID[],
    created_by UUID REFERENCES agents(id),
    agent_type VARCHAR(50),
    tags TEXT[],
    status VARCHAR(20) DEFAULT 'active' CHECK (
        status IN ('active', 'deprecated', 'sandbox', 'testing')
    ),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, version)
);

CREATE INDEX IF NOT EXISTS idx_skills_name       ON skills(name);
CREATE INDEX IF NOT EXISTS idx_skills_agent_type ON skills(agent_type);
CREATE INDEX IF NOT EXISTS idx_skills_fitness    ON skills(fitness_score DESC);
CREATE INDEX IF NOT EXISTS idx_skills_tags       ON skills USING GIN(tags);

-- ── Agent-Skill Associations ──────────────────────────────────
CREATE TABLE IF NOT EXISTS agent_skills (
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    skill_id UUID REFERENCES skills(id) ON DELETE CASCADE,
    proficiency FLOAT DEFAULT 0.5 CHECK (proficiency >= 0 AND proficiency <= 1),
    times_used INTEGER DEFAULT 0,
    avg_fitness FLOAT,
    PRIMARY KEY (agent_id, skill_id)
);

-- ── Evolution Generations ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS evolution_generations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    generation_number INTEGER NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    population_size INTEGER NOT NULL,
    avg_fitness FLOAT,
    max_fitness FLOAT,
    min_fitness FLOAT,
    std_fitness FLOAT,
    diversity_score FLOAT,
    mutations_applied INTEGER DEFAULT 0,
    crossovers_applied INTEGER DEFAULT 0,
    selections_performed INTEGER DEFAULT 0,
    new_agents_created INTEGER DEFAULT 0,
    agents_retired INTEGER DEFAULT 0,
    config JSONB,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'running' CHECK (
        status IN ('running', 'completed', 'failed')
    )
);

CREATE INDEX IF NOT EXISTS idx_evo_gen_type   ON evolution_generations(agent_type);
CREATE INDEX IF NOT EXISTS idx_evo_gen_number ON evolution_generations(generation_number);

-- ── Evolution Events ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS evolution_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    generation_id UUID REFERENCES evolution_generations(id),
    event_type VARCHAR(50) NOT NULL CHECK (
        event_type IN ('selection', 'mutation', 'crossover', 'evaluation', 'deployment', 'rollback')
    ),
    parent_ids UUID[],
    child_id UUID REFERENCES agents(id),
    old_fitness FLOAT,
    new_fitness FLOAT,
    changes JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evo_events_gen  ON evolution_events(generation_id);
CREATE INDEX IF NOT EXISTS idx_evo_events_type ON evolution_events(event_type);

-- ── Memory Metadata ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS memory_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    memory_type VARCHAR(20) NOT NULL CHECK (
        memory_type IN ('episodic', 'semantic', 'procedural')
    ),
    external_id VARCHAR(200) NOT NULL,
    storage_backend VARCHAR(20) NOT NULL CHECK (
        storage_backend IN ('qdrant', 'neo4j', 'redis')
    ),
    agent_id UUID REFERENCES agents(id),
    user_id VARCHAR(100),
    session_id VARCHAR(100),
    content_preview TEXT,
    importance_score FLOAT DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    UNIQUE(external_id, storage_backend)
);

CREATE INDEX IF NOT EXISTS idx_mem_type       ON memory_metadata(memory_type);
CREATE INDEX IF NOT EXISTS idx_mem_agent      ON memory_metadata(agent_id);
CREATE INDEX IF NOT EXISTS idx_mem_user       ON memory_metadata(user_id);
CREATE INDEX IF NOT EXISTS idx_mem_importance ON memory_metadata(importance_score DESC);
CREATE INDEX IF NOT EXISTS idx_mem_session    ON memory_metadata(session_id);

-- ── Consolidation Log ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS consolidation_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_memory_ids UUID[],
    target_memory_id UUID,
    consolidation_type VARCHAR(30) CHECK (
        consolidation_type IN ('episodic_to_semantic', 'semantic_to_procedural', 'memory_merge')
    ),
    facts_extracted INTEGER,
    facts_stored INTEGER,
    processing_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── System Config ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS system_config (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO system_config (key, value, description) VALUES
('evolution', '{
    "enabled": true,
    "auto_cycle": true,
    "cycle_interval_tasks": 100,
    "cycle_interval_hours": 24,
    "min_population_size": 5,
    "max_population_size": 20,
    "selection_pressure": 0.7,
    "default_mutation_rate": 0.1,
    "elitism_count": 2
}', 'Genetic evolution settings'),
('memory', '{
    "working_memory_size": 10,
    "episodic_retrieval_k": 5,
    "semantic_depth": 3,
    "consolidation_frequency": 100,
    "importance_threshold": 0.6,
    "default_ttl_days": 90
}', 'Memory system settings'),
('models', '{
    "primary": "claude-sonnet-4-20250514",
    "router": "claude-haiku-4-5-20251001",
    "embedding": "all-MiniLM-L6-v2"
}', 'LLM model configuration')
ON CONFLICT (key) DO NOTHING;
