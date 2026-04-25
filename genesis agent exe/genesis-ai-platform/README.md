# 🧬 GENESIS AI Platform

**Genetic Evolution Network with Episodic & Semantic Intelligence System**

A production-grade multi-agent AI platform where agents evolve genetically, build persistent memory, and autonomously create new skills.

---

## What's Inside

```
genesis-ai-platform/
├── docker-compose.yml          ← Start everything with one command
├── docker-compose.dev.yml      ← Dev override (hot reload)
├── .env.example                ← Copy to .env and add your API key
├── Makefile                    ← make setup / make start / make seed
├── scripts/
│   └── seed.py                 ← Initialize agents and skills
│
├── backend/                    ← FastAPI Python backend
│   ├── Dockerfile
│   ├── pyproject.toml          ← All Python dependencies
│   ├── alembic/
│   │   └── init.sql            ← PostgreSQL schema (auto-run on startup)
│   ├── app/
│   │   ├── main.py             ← FastAPI app entry point
│   │   ├── config.py           ← Settings (reads from .env)
│   │   ├── database.py         ← Async SQLAlchemy
│   │   ├── models.py           ← ORM models (agents, tasks, skills, evolution)
│   │   ├── dependencies.py     ← DI: Anthropic, Qdrant, Redis, engines
│   │   ├── schemas/            ← Pydantic request/response models
│   │   ├── agents/
│   │   │   └── engine.py       ← LangGraph state machines
│   │   ├── genetic/
│   │   │   └── evolution_engine.py  ← LLM-powered mutation/crossover/fitness
│   │   ├── memory/
│   │   │   └── memory_system.py     ← 4-tier memory (Redis+Qdrant+Neo4j+PG)
│   │   └── routers/
│   │       └── __init__.py     ← All REST endpoints
│   └── tests/
│       └── test_api.py
│
└── frontend/                   ← React + Vite frontend
    ├── Dockerfile              ← Multi-stage: build → nginx serve
    ├── nginx.conf              ← Proxies /api/* to backend
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.jsx            ← React entry point
        ├── App.jsx             ← Full 9-view application (1500+ lines)
        └── api.js              ← Backend API client
```

---

## Quick Start (5 minutes)

### Prerequisites
- Docker Desktop (Mac/Windows) or Docker + Docker Compose (Linux)
- An Anthropic API key — get one at [console.anthropic.com](https://console.anthropic.com)

### 1. Configure environment

```bash
cp .env.example .env
```

Open `.env` and set your API key:
```
ANTHROPIC_API_KEY=sk-ant-...your-key-here...
```

### 2. Start the platform

**Option A — Make (easiest):**
```bash
make setup
make start
make seed
```

**Option B — Docker Compose directly:**
```bash
docker-compose up --build -d
# Wait ~60 seconds for all services to start, then:
python3 scripts/seed.py
```

### 3. Open the app

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:3000 |
| **Backend API** | http://localhost:8000 |
| **API Docs (Swagger)** | http://localhost:8000/docs |
| **Qdrant Dashboard** | http://localhost:6333/dashboard |
| **Neo4j Browser** | http://localhost:7474 (if started with `--profile full`) |

---

## What Happens at Startup

1. **PostgreSQL** starts and runs `alembic/init.sql` — creates all tables, indexes, and seeds system config
2. **Qdrant** starts — will receive vector embeddings from the sentence transformer
3. **Redis** starts — used for working memory (session context)
4. **Backend** builds (including downloading the `all-MiniLM-L6-v2` embedding model), starts FastAPI
5. **Frontend** builds React app, serves via Nginx — proxies `/api/*` to backend
6. **Seed** (`make seed` or `python3 scripts/seed.py`) creates 6 default agents and 6 default skills

---

## Using the Platform

### 9 Views in the UI

| View | What to do |
|------|-----------|
| **Command Center** | See overall fitness, evolution history charts, agent population |
| **Agent Matrix** | Browse all 6 agents, click any to inspect full DNA |
| **Agent Chat** | Chat directly with any agent or use AUTO routing via NEXUS |
| **Task Terminal** | Execute tasks — watch routing, execution, and memory storage live |
| **Evolution Chamber** | Click "Run Evolution Cycle" to mutate and crossover agents |
| **Memory Core** | Browse episodic memories stored from past interactions |
| **Skills Lab** | Generate new skills via ARCHITECT (the meta-agent) |
| **Architecture** | Full 5-layer system diagram and execution flow |
| **DNA Editor** | Live-edit any agent's temperature, tokens, memory genes |

### Quick API Test

```bash
# Execute a task
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"task": "Explain quantum entanglement simply", "session_id": "my-session"}'

# Run an evolution cycle
curl -X POST http://localhost:8000/api/v1/evolution/run \
  -H "Content-Type: application/json" \
  -d '{"generations": 1, "strategy": "full"}'

# Search memory
curl "http://localhost:8000/api/v1/memory?query=quantum+physics&k=5"

# Get platform stats
curl http://localhost:8000/api/v1/system/stats
```

---

## Architecture

```
Browser (port 3000)
    │
    ▼
Nginx  ─── /api/* ──────────────────────────────┐
    │                                             │
    │ (static files)                              ▼
React App (9 views)                    FastAPI Backend (port 8000)
    │                                             │
    └── api.js ───── fetch /api/v1/* ────────────┤
                                                  │
                    ┌─────────────────────────────┤
                    │                             │
                    ▼                             ▼
              LangGraph Agents          Genetic Evolution Engine
                    │                             │
                    ▼                             ▼
            ┌───────────────────────────────────────────────┐
            │              Memory System (4 tiers)          │
            │  Redis (working) │ Qdrant (episodic)          │
            │  Neo4j (semantic)│ PostgreSQL (procedural)    │
            └───────────────────────────────────────────────┘
```

---

## The 6 Agents

| Agent | Name | Role | Model |
|-------|------|------|-------|
| Router | NEXUS | Routes tasks to the best agent | claude-haiku (fast) |
| Research | ORACLE | Web research, synthesis | claude-sonnet |
| Code | FORGE | Code generation and review | claude-sonnet |
| Analysis | SIGMA | Data analysis, pattern detection | claude-sonnet |
| Creative | MUSE | Content creation, ideation | claude-sonnet |
| Skill Builder | ARCHITECT | Generates new agent skills | claude-sonnet |

---

## Development Mode (Hot Reload)

```bash
# Backend + frontend both with live code reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Frontend hot reload at port 5173
# Backend hot reload — edit files in backend/app/
```

---

## Commands Reference

```bash
make help           # Show all commands
make setup          # First-time setup
make start          # Build and start all services
make seed           # Load initial agents and skills
make status         # Health check + stats
make logs           # Follow all logs
make logs-backend   # Follow backend logs only
make test           # Run backend tests
make test-task      # Execute a test task via API
make stop           # Stop all services
make restart        # Restart all services
make clean          # Remove containers (keep data)
make reset          # Full wipe including database
make start-full     # Start with Neo4j (semantic memory)
```

---

## Troubleshooting

**Backend fails to start:**
```bash
make logs-backend
# Most common cause: missing ANTHROPIC_API_KEY in .env
```

**"No active agents" error on tasks:**
```bash
make seed    # or: python3 scripts/seed.py
```

**Qdrant connection error:**
```bash
docker-compose ps qdrant   # Check if it's running
curl http://localhost:6333/healthz
```

**Port conflicts:**
Change ports in `docker-compose.yml`:
- Frontend: `"3001:80"` (from 3000)
- Backend: `"8001:8000"` (from 8000)

**Slow first build:**
Normal — Docker is downloading Python packages and the 90MB sentence transformer model. Subsequent builds are fast (cached layers).

---

## What's Implemented

### ✅ Phase 1 (Foundation) — Complete
- PostgreSQL schema: agents, tasks, skills, evolution_generations, memory_metadata
- 4-tier memory system: Redis (working) + Qdrant (episodic) + Neo4j (semantic, optional) + PostgreSQL (procedural)
- LangGraph agent state machines with memory retrieval
- LLM-powered genetic mutation (mild/medium/strong prompt rewriting)
- Semantic crossover (fitness-weighted LLM blending)
- 3-stage fitness evaluation
- Full REST API + A2A protocol endpoint
- React frontend: 9 views, 1500+ lines

### 🔄 Phase 2 (Genetic Engine) — Next
- WebSocket for real-time evolution streaming
- Automated evolution controller (auto-triggers after N tasks)
- Blue-green agent deployment with rollback
- Diversity maintenance (prevents premature convergence)
- Full benchmark suite per agent type

### 📋 Phases 3–5
- Neo4j semantic memory with entity extraction
- Memory consolidation pipeline (episodic → semantic)
- Skill sandbox execution (Docker-isolated)
- LangSmith tracing + Prometheus metrics
- Auth + rate limiting
- Production Kubernetes deployment
