# GENESIS AI Platform — Backend

**Genetic Evolution Network with Episodic & Semantic Intelligence System**

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     GENESIS v2.0 Backend                     │
├──────────────┬──────────────┬───────────────┬───────────────┤
│  FastAPI      │  LangGraph   │  Genetic Evo  │  Memory Sys   │
│  REST API     │  Agent State │  Engine       │  4-Tier       │
│  + A2A + MCP  │  Machines    │  LLM-Powered  │               │
├──────────────┴──────────────┴───────────────┴───────────────┤
│  PostgreSQL  │  Qdrant VDB  │  Redis Cache  │  Neo4j Graph  │
│  Metadata    │  Episodic    │  Working Mem  │  Semantic Mem  │
└─────────────────────────────────────────────────────────────┘
```

### Layer Breakdown

| Layer | Purpose | Technology |
|-------|---------|------------|
| **API** | REST endpoints + A2A protocol | FastAPI + Pydantic |
| **Agent Engine** | LangGraph state machines | LangGraph + Anthropic |
| **Genetic Evolution** | LLM-powered mutation/crossover | Custom Engine |
| **Memory — Working** | Context window paging | Redis LRU |
| **Memory — Episodic** | Atomic fact storage + retrieval | Qdrant + SentenceTransformers |
| **Memory — Semantic** | Knowledge graph | Neo4j + Cypher |
| **Memory — Procedural** | Skill registry | PostgreSQL |
| **Metadata** | Agent/task/skill/evolution records | PostgreSQL + SQLAlchemy |

---

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Docker + Docker Compose
- Anthropic API key

### 2. Environment Setup

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 3. Start Infrastructure

```bash
docker-compose up -d postgres qdrant redis neo4j
# Wait for services to be healthy (~15 seconds)
docker-compose ps
```

### 4. Install Python Dependencies

```bash
pip install -e ".[dev]"
```

### 5. Start the API

```bash
uvicorn app.main:app --reload --port 8000
```

### 6. Seed Initial Data

```bash
# Seed 6 default agents
curl http://localhost:8000/api/v1/agents/seed

# Seed default skills
curl http://localhost:8000/api/v1/skills/seed
```

### 7. Verify

```bash
curl http://localhost:8000/api/v1/system/health
# Open http://localhost:8000/docs for Swagger UI
```

---

## API Endpoints

### Agents
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/agents` | List all agents |
| GET | `/api/v1/agents/seed` | Seed default 6 agents |
| POST | `/api/v1/agents` | Create agent |
| GET | `/api/v1/agents/{id}` | Get agent details + DNA |
| PUT | `/api/v1/agents/{id}/dna` | Update agent DNA |
| DELETE | `/api/v1/agents/{id}` | Retire agent |

### Tasks
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/tasks` | Execute task (routes via NEXUS) |
| GET | `/api/v1/tasks` | List task history |

### Evolution
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/evolution/run` | Run evolution cycle |
| POST | `/api/v1/evolution/mutate/{id}` | Mutate single agent |
| GET | `/api/v1/evolution/history` | Generation history |
| GET | `/api/v1/evolution/events` | All evolution events |

### Memory
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/memory` | Store memory entry |
| GET | `/api/v1/memory` | Semantic search memories |
| GET | `/api/v1/memory/stats` | Memory system stats |

### Skills
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/skills` | List skills |
| GET | `/api/v1/skills/seed` | Seed default skills |
| POST | `/api/v1/skills` | Create skill (manual or auto-generate) |

### System
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/system/health` | Health check all services |
| GET | `/api/v1/system/stats` | Platform statistics |
| GET | `/api/v1/a2a/agent.json` | A2A Agent Card |

---

## Key Design Decisions

### LangGraph State Machines
Each agent runs as a LangGraph graph with nodes:
1. `retrieve_memory` → fetch relevant episodic + working memories
2. `execute_task` → run LLM with DNA-encoded system prompt
3. (implicit) post-task memory extraction

### LLM-Powered Genetic Operations
- **Mutation**: Claude rewrites the agent's system prompt at mild/medium/strong intensity
- **Crossover**: Claude semantically blends two parent prompts weighted by their fitness scores
- **Fitness evaluation Stage 1**: LLM judge scores recent task history
- **Fitness evaluation Stage 2**: Sandbox benchmark tasks with criteria checking

### 4-Tier Memory
- **Tier 1 (Working)**: Redis LPUSH/LTRIM, session-scoped, 10-item LRU window
- **Tier 2 (Episodic)**: Qdrant cosine similarity search over SentenceTransformer embeddings
- **Tier 3 (Semantic)**: Neo4j knowledge graph (entity + relationship extraction)
- **Tier 4 (Procedural)**: PostgreSQL skill registry with fitness tracking

---

## Running Tests

```bash
pytest tests/ -v --tb=short
```

---

## Frontend Integration

The React frontend (genesis-platform.jsx) calls the backend via the API client in `frontend-api-client.js`.

To wire the frontend to the backend, set:
```
VITE_API_URL=http://localhost:8000/api/v1
```

The frontend falls back to direct Anthropic API calls if the backend is unavailable (for demo mode).

---

## What's Next (Phase 2+)

- [ ] Real A2A + MCP protocol implementation
- [ ] LangSmith tracing integration
- [ ] Prometheus metrics endpoint
- [ ] Memory consolidation pipeline (episodic → semantic auto-consolidation)
- [ ] Skill sandbox execution (Docker-isolated code execution)
- [ ] Blue-green agent deployment automation
- [ ] Rate limiting + authentication middleware
- [ ] WebSocket endpoint for real-time evolution streaming
