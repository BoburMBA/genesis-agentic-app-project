# GENESIS AI PLATFORM — Workspace Workflow & Operations Guide
## Complete Development and Operational Workflows

**Version:** 1.0  
**Date:** April 2026  
**Classification:** Operations Guide  
**Related Documents:** 01_MASTER_PROJECT_PLAN.md, 02_SYSTEM_ARCHITECTURE.md

---

## 1. DEVELOPMENT WORKFLOW

### 1.1 Git Branching Strategy

```
main (production)
  │
  ├── release/v0.1.0 (release branch)
  │     │
  │     └── hotfix/memory-leak (emergency fixes)
  │
  ├── develop (integration branch)
  │     │
  │     ├── feature/GEN-123-memory-consolidation
  │     ├── feature/GEN-124-evolution-controller
  │     ├── feature/GEN-125-skill-builder-agent
  │     └── feature/GEN-126-a2a-protocol
  │
  └── spike/GEN-200-neo4j-performance (research branches)
```

**Branch Rules:**
| Branch | Protection | CI/CD | Description |
|--------|-----------|-------|-------------|
| `main` | Required reviews: 2 | Full pipeline | Production deployments |
| `develop` | Required reviews: 1 | Build + test | Integration branch |
| `feature/*` | Required reviews: 1 | Build + test | Feature development |
| `hotfix/*` | Required reviews: 2 | Full pipeline | Emergency fixes |
| `spike/*` | None | Build only | Research/experiments |

### 1.2 Development Lifecycle

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   DESIGN     │────▶│  IMPLEMENT   │────▶│    TEST      │────▶│    MERGE     │
│              │     │              │     │              │     │              │
│ Architecture │     │ Feature code │     │ Unit + Int.  │     │ PR Review    │
│ Doc update   │     │ Tests        │     │ Benchmarks   │     │ Merge to dev │
│ DNA schema   │     │ API spec     │     │ Evolution    │     │              │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### 1.3 Pull Request Template

```markdown
## GENESIS-XXX: Feature Title

### Description
Brief description of the change

### DNA Changes (if applicable)
- [ ] New gene added
- [ ] Gene modified
- [ ] Schema version bumped

### Memory Impact
- [ ] New memory type: ___
- [ ] Memory schema changed
- [ ] Consolidation pipeline updated

### Evolution Impact
- [ ] New operator: ___
- [ ] Fitness function changed
- [ ] Selection strategy updated

### Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Benchmarks run: baseline=___, new=___
- [ ] Evolution cycle validated (if applicable)

### Checklist
- [ ] Code follows style guide
- [ ] Documentation updated
- [ ] API spec updated
- [ ] Migrations added (if schema changed)
```

---

## 2. DAILY OPERATIONS WORKFLOW

### 2.1 System Startup Sequence

```bash
#!/bin/bash
# scripts/startup.sh

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           GENESIS AI PLATFORM - STARTUP                    ║"
echo "╚════════════════════════════════════════════════════════════╝"

# 1. Infrastructure
echo "[1/6] Starting infrastructure services..."
docker-compose up -d qdrant neo4j redis postgres

# Wait for services
echo "Waiting for Qdrant..."
until curl -s http://localhost:6333/healthz > /dev/null; do sleep 1; done
echo "Qdrant ✓"

echo "Waiting for Neo4j..."
until cypher-shell -u neo4j -p genesis_password "RETURN 1;" > /dev/null 2>&1; do sleep 1; done
echo "Neo4j ✓"

echo "Waiting for PostgreSQL..."
until pg_isready -h localhost -p 5432 > /dev/null; do sleep 1; done
echo "PostgreSQL ✓"

echo "Redis ✓"

# 2. Database migrations
echo "[2/6] Running database migrations..."
alembic upgrade head

# 3. Initialize Qdrant collections
echo "[3/6] Initializing vector collections..."
python -m genesis.infra.init_qdrant

# 4. Initialize Neo4j schema
echo "[4/6] Initializing graph schema..."
python -m genesis.infra.init_neo4j

# 5. Load system configuration
echo "[5/6] Loading system configuration..."
python -m genesis.infra.load_config

# 6. Start application
echo "[6/6] Starting GENESIS API..."
docker-compose up -d genesis

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║           GENESIS IS ONLINE                                ║"
echo "║  API: http://localhost:8000                                ║"
echo "║  Docs: http://localhost:8000/docs                          ║"
echo "║  Metrics: http://localhost:8000/metrics                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
```

### 2.2 Daily Health Check

```python
# scripts/health_check.py
"""
Comprehensive health check for GENESIS platform
Run: python -m scripts.health_check
"""

import asyncio
import httpx
from datetime import datetime, timedelta
from genesis.config import get_config

async def health_check():
    config = get_config()
    checks = []
    
    # Check 1: API responds
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:8000/health")
            checks.append(("API", resp.status_code == 200, resp.elapsed.total_seconds()))
    except Exception as e:
        checks.append(("API", False, str(e)))
    
    # Check 2: Qdrant reachable
    try:
        from qdrant_client import QdrantClient
        qc = QdrantClient(url=config.qdrant_url)
        collections = qc.get_collections()
        checks.append(("Qdrant", True, f"{len(collections.collections)} collections"))
    except Exception as e:
        checks.append(("Qdrant", False, str(e)))
    
    # Check 3: Neo4j reachable
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(config.neo4j_url, auth=(config.neo4j_user, config.neo4j_password))
        with driver.session() as session:
            result = session.run("RETURN 1 as n")
            record = result.single()
            checks.append(("Neo4j", record["n"] == 1, "connected"))
        driver.close()
    except Exception as e:
        checks.append(("Neo4j", False, str(e)))
    
    # Check 4: PostgreSQL reachable
    try:
        import asyncpg
        conn = await asyncpg.connect(config.database_url)
        result = await conn.fetchval("SELECT 1")
        await conn.close()
        checks.append(("PostgreSQL", result == 1, "connected"))
    except Exception as e:
        checks.append(("PostgreSQL", False, str(e)))
    
    # Check 5: Redis reachable
    try:
        import redis.asyncio as redis
        r = redis.from_url(config.redis_url)
        pong = await r.ping()
        await r.close()
        checks.append(("Redis", pong, "connected"))
    except Exception as e:
        checks.append(("Redis", False, str(e)))
    
    # Check 6: Active agents count
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:8000/api/v1/agents?status=active")
            data = resp.json()
            agent_count = len(data["agents"])
            checks.append(("Active Agents", agent_count > 0, f"{agent_count} agents"))
    except Exception as e:
        checks.append(("Active Agents", False, str(e)))
    
    # Check 7: Evolution status
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:8000/api/v1/evolution/status")
            data = resp.json()
            checks.append(("Evolution", data["enabled"], f"gen {data.get('current_generation', 'N/A')}"))
    except Exception as e:
        checks.append(("Evolution", False, str(e)))
    
    # Print report
    print(f"\n{'='*60}")
    print(f"  GENESIS HEALTH CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    all_pass = True
    for name, status, detail in checks:
        icon = "✓" if status else "✗"
        status_str = "PASS" if status else "FAIL"
        print(f"  {icon} {name:<20} [{status_str}] {detail}")
        if not status:
            all_pass = False
    
    print(f"{'='*60}")
    print(f"  Overall: {'ALL CHECKS PASSED' if all_pass else 'SOME CHECKS FAILED'}")
    print(f"{'='*60}\n")
    
    return all_pass

if __name__ == "__main__":
    asyncio.run(health_check())
```

### 2.3 Evolution Monitoring Dashboard

```python
# scripts/evolution_dashboard.py
"""
Real-time evolution monitoring
Run: python -m scripts.evolution_dashboard
"""

import asyncio
import curses
from datetime import datetime
from genesis.db import get_db_pool

async def render_dashboard(stdscr):
    """Render real-time evolution dashboard using curses"""
    
    curses.curs_set(0)  # Hide cursor
    stdscr.nodelay(1)   # Non-blocking input
    
    pool = await get_db_pool()
    
    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        # Header
        stdscr.addstr(0, 0, "╔" + "═" * (w-2) + "╗")
        stdscr.addstr(1, 0, "║" + "GENESIS EVOLUTION DASHBOARD".center(w-2) + "║")
        stdscr.addstr(2, 0, "╠" + "═" * (w-2) + "╣")
        
        # Get latest data
        async with pool.acquire() as conn:
            # Agent stats by type
            agent_stats = await conn.fetch("""
                SELECT type, COUNT(*) as count, AVG(fitness_score) as avg_fitness, MAX(generation) as max_gen
                FROM agents WHERE status = 'active' GROUP BY type ORDER BY type
            """)
            
            # Latest evolution generation
            latest_gen = await conn.fetchrow("""
                SELECT * FROM evolution_generations ORDER BY generation_number DESC LIMIT 1
            """)
            
            # Top performers
            top_agents = await conn.fetch("""
                SELECT id, type, generation, fitness_score, execution_count
                FROM agents WHERE status = 'active' ORDER BY fitness_score DESC LIMIT 5
            """)
            
            # Memory stats
            memory_stats = await conn.fetch("""
                SELECT memory_type, COUNT(*) as count, AVG(importance_score) as avg_importance
                FROM memory_metadata GROUP BY memory_type
            """)
        
        # Render agent stats
        row = 3
        stdscr.addstr(row, 0, "║ AGENT POPULATION" + " " * (w-19) + "║")
        row += 1
        stdscr.addstr(row, 0, "╠" + "─" * (w-2) + "╣")
        row += 1
        
        for stat in agent_stats:
            line = f"║  {stat['type']:<15} Count: {stat['count']:>3}  Avg Fitness: {stat['avg_fitness']:.3f}  Max Gen: {stat['max_gen']:>3}"
            stdscr.addstr(row, 0, line + " " * (w-len(line)-1) + "║")
            row += 1
        
        # Render evolution status
        row += 1
        stdscr.addstr(row, 0, "╠" + "─" * (w-2) + "╣")
        row += 1
        stdscr.addstr(row, 0, "║ EVOLUTION STATUS" + " " * (w-19) + "║")
        row += 1
        stdscr.addstr(row, 0, "╠" + "─" * (w-2) + "╣")
        row += 1
        
        if latest_gen:
            line = f"║  Generation: {latest_gen['generation_number']}  Status: {latest_gen['status']}  Avg Fitness: {latest_gen['avg_fitness']:.3f}"
            stdscr.addstr(row, 0, line + " " * (w-len(line)-1) + "║")
            row += 1
            line = f"║  Population: {latest_gen['population_size']}  Mutations: {latest_gen['mutations_applied']}  Crossovers: {latest_gen['crossovers_applied']}"
            stdscr.addstr(row, 0, line + " " * (w-len(line)-1) + "║")
            row += 1
        
        # Render top performers
        row += 1
        stdscr.addstr(row, 0, "╠" + "─" * (w-2) + "╣")
        row += 1
        stdscr.addstr(row, 0, "║ TOP PERFORMERS" + " " * (w-17) + "║")
        row += 1
        stdscr.addstr(row, 0, "╠" + "─" * (w-2) + "╣")
        row += 1
        
        for agent in top_agents:
            line = f"║  {agent['id'][:8]}  {agent['type']:<12} Gen:{agent['generation']:>3}  Fitness:{agent[' fitness_score']:.3f}  Runs:{agent['execution_count']}"
            stdscr.addstr(row, 0, line + " " * (w-len(line)-1) + "║")
            row += 1
        
        # Footer
        stdscr.addstr(h-2, 0, "╠" + "─" * (w-2) + "╣")
        time_str = datetime.now().strftime("%H:%M:%S")
        footer = f"║ Last update: {time_str} | Press 'q' to quit"
        stdscr.addstr(h-1, 0, footer + " " * (w-len(footer)-1) + "║")
        
        stdscr.refresh()
        
        # Check for quit
        key = stdscr.getch()
        if key == ord('q'):
            break
        
        await asyncio.sleep(2)

if __name__ == "__main__":
    curses.wrapper(lambda stdscr: asyncio.run(render_dashboard(stdscr)))
```

---

## 3. TASK EXECUTION WORKFLOW

### 3.1 Standard Task Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         TASK EXECUTION WORKFLOW                                  │
│                                                                                  │
│  STEP 1: TASK INTAKE                                                             │
│  ┌──────────────┐                                                                │
│  │ User Request │───▶ Parse intent ──▶ Classify task type                        │
│  └──────────────┘                                                                │
│       │                                                                          │
│       ▼                                                                          │
│  STEP 2: CONTEXT GATHERING                                                       │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ 1. Load user profile from Episodic Memory (Mem0)                         │   │
│  │ 2. Query Semantic Memory for relevant knowledge (Cognee/Neo4j)           │   │
│  │ 3. Check Procedural Memory for applicable skills                         │   │
│  │ 4. Build working context (Letta-style RAM loading)                       │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│       │                                                                          │
│       ▼                                                                          │
│  STEP 3: AGENT SELECTION                                                         │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ Router Agent analyzes:                                                    │   │
│  │ - Task type match                                                         │   │
│  │ - Agent availability                                                      │   │
│  │ - Fitness scores                                                          │   │
│  │ - Memory overlap (genetic diversity consideration)                        │   │
│  │ Result: Primary agent selected + Backup agents identified                 │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│       │                                                                          │
│       ▼                                                                          │
│  STEP 4: EXECUTION                                                               │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ Agent executes through LangGraph state machine:                           │   │
│  │ ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐            │   │
│  │ │ Retrieve │───▶│  Reason  │───▶│  Execute │───▶│ Reflect  │            │   │
│  │ │  Memory  │    │          │    │  Tools   │    │          │            │   │
│  │ └──────────┘    └──────────┘    └──────────┘    └──────────┘            │   │
│  │                                                         │                │   │
│  │                                                         ▼                │   │
│  │                                                   ┌──────────┐           │   │
│  │                                                   │ Consolidate│         │   │
│  │                                                   │  Memory    │         │   │
│  │                                                   └──────────┘           │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│       │                                                                          │
│       ▼                                                                          │
│  STEP 5: MEMORY UPDATE (async)                                                   │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ 1. Store interaction in Episodic Memory (Mem0/Qdrant)                    │   │
│  │ 2. Extract facts for Semantic Memory (Cognee/Neo4j)                      │   │
│  │ 3. Update agent execution stats (PostgreSQL)                             │   │
│  │ 4. Calculate fitness contribution                                          │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│       │                                                                          │
│       ▼                                                                          │
│  STEP 6: RESPONSE                                                                │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ 1. Format response                                                         │   │
│  │ 2. Include source citations (from memory)                                  │   │
│  │ 3. Return to user + metadata (tokens used, latency, memory recalls)       │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Multi-Agent Collaboration Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    MULTI-AGENT COLLABORATION FLOW                                │
│                                                                                  │
│  COMPLEX TASK: "Research the latest AI safety papers, summarize findings,        │
│                 and create a presentation outline"                               │
│                                                                                  │
│  ┌──────────┐                                                                    │
│  │  Router  │───▶ Decomposes into subtasks:                                      │
│  │  Agent   │     [Research] → [Analyze] → [Create]                              │
│  └────┬─────┘                                                                    │
│       │                                                                          │
│       ▼                                                                          │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ PHASE 1: RESEARCH (Research Agent)                                       │   │
│  │ ┌──────────────┐                                                        │   │
│  │ │ Search web   │───▶ Mem0: "User prefers academic sources"              │   │
│  │ │ for papers   │───▶ Cognee: "AI safety is related to alignment,        │   │
│  │ │              │        interpretability, red-teaming"                    │   │
│  │ └──────┬───────┘                                                        │   │
│  │        │                                                                 │   │
│  │        ▼                                                                 │   │
│  │ ┌──────────────┐                                                        │   │
│  │ │ Download &   │───▶ PDF Reader tool                                     │   │
│  │ │ extract PDFs │───▶ Data extraction                                     │   │
│  │ └──────┬───────┘                                                        │   │
│  │        │                                                                 │   │
│  │        ▼                                                                 │   │
│  │ ┌──────────────┐                                                        │   │
│  │ │ Store in     │───▶ Episodic: "Found 5 papers on AI safety"            │   │
│  │ │ memory       │───▶ Semantic: Extract entities (authors, topics,        │   │
│  │ │              │        methods) → Cognee/Neo4j                          │   │
│  │ └──────────────┘                                                        │   │
│  │ Result: Structured research data + memory updates                        │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│       │                                                                          │
│       ▼ (via Internal Bus)                                                       │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ PHASE 2: ANALYSIS (Analysis Agent)                                       │   │
│  │ ┌──────────────┐                                                        │   │
│  │ │ Read research│───▶ Episodic: "Previous research data available"       │   │
│  │ │ data         │───▶ Semantic: Query graph for related concepts         │   │
│  │ └──────┬───────┘                                                        │   │
│  │        │                                                                 │   │
│  │        ▼                                                                 │   │
│  │ ┌──────────────┐                                                        │   │
│  │ │ Identify     │───> "Key themes: Constitutional AI, RLHF,             │   │
│  │ │ patterns &   │     Mechanistic Interpretability"                       │   │
│  │ │ themes       │                                                        │   │
│  │ └──────┬───────┘                                                        │   │
│  │        │                                                                 │   │
│  │        ▼                                                                 │   │
│  │ ┌──────────────┐                                                        │   │
│  │ │ Generate     │───▶ Analysis report with cited sources                  │   │
│  │ │ insights     │───▶ Episodic: "Analysis completed, 3 themes found"     │   │
│  │ └──────────────┘                                                        │   │
│  │ Result: Analysis report + memory updates                                 │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│       │                                                                          │
│       ▼ (via Internal Bus)                                                       │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ PHASE 3: CREATION (Creative Agent)                                       │   │
│  │ ┌──────────────┐                                                        │   │
│  │ │ Read analysis│───▶ Episodic: "Previous analysis context loaded"       │   │
│  │ │ report       │                                                        │   │
│  │ └──────┬───────┘                                                        │   │
│  │        │                                                                 │   │
│  │        ▼                                                                 │   │
│  │ ┌──────────────┐                                                        │   │
│  │ │ Create       │───▶ "Presentation outline with 5 sections"              │   │
│  │ │ presentation │───▶ Episodic: "Created outline per user preference"    │   │
│  │ │ outline      │     (Semantic: "User prefers bullet-point format")      │   │
│  │ └──────────────┘                                                        │   │
│  │ Result: Final deliverable                                                │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│       │                                                                          │
│       ▼                                                                          │
│  ┌──────────┐                                                                    │
│  │  Router  │───▶ Aggregate results, format final response                     │
│  │  Agent   │───▶ Memory: "Completed multi-agent task successfully"           │
│  └──────────┘                                                                    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. EVOLUTION WORKFLOW

### 4.1 Automated Evolution Cycle

```python
# scripts/trigger_evolution.py
"""
Trigger and monitor evolution cycles
Usage: python -m scripts.trigger_evolution --type research --generations 3
"""

import asyncio
import argparse
import httpx
from datetime import datetime

async def trigger_evolution(agent_type: str, generations: int, population: int):
    """Trigger an evolution cycle and monitor progress"""
    
    print(f"\n{'='*60}")
    print(f"  TRIGGERING EVOLUTION")
    print(f"  Agent Type: {agent_type}")
    print(f"  Generations: {generations}")
    print(f"  Population: {population}")
    print(f"{'='*60}\n")
    
    # Trigger evolution
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "http://localhost:8000/api/v1/evolution/run",
            json={
                "agent_types": [agent_type],
                "population_size": population,
                "generations": generations,
                "selection_pressure": 0.7
            }
        )
        
        if resp.status_code != 202:
            print(f"Failed to start evolution: {resp.text}")
            return
        
        job = resp.json()
        job_id = job["job_id"]
        print(f"Evolution job started: {job_id}\n")
        
        # Monitor progress
        print("Generation | Avg Fitness | Max Fitness | Diversity | Status")
        print("-" * 60)
        
        completed = False
        while not completed:
            await asyncio.sleep(5)
            
            status_resp = await client.get(
                f"http://localhost:8000/api/v1/evolution/status/{job_id}"
            )
            status = status_resp.json()
            
            for gen in status.get("generations", []):
                print(f"{gen['generation_number']:>10} | "
                      f"{gen['avg_fitness']:>11.3f} | "
                      f"{gen['max_fitness']:>11.3f} | "
                      f"{gen['diversity_score']:>9.3f} | "
                      f"{gen['status']}")
            
            if status.get("status") in ["completed", "failed"]:
                completed = True
                print("-" * 60)
                print(f"Final Status: {status['status']}")
                print(f"Total Generations: {status.get('total_generations', 'N/A')}")
                print(f"Best Fitness: {status.get('best_fitness', 'N/A')}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trigger GENESIS evolution")
    parser.add_argument("--type", default="research", help="Agent type to evolve")
    parser.add_argument("--generations", type=int, default=1, help="Number of generations")
    parser.add_argument("--population", type=int, default=10, help="Population size")
    
    args = parser.parse_args()
    asyncio.run(trigger_evolution(args.type, args.generations, args.population))
```

### 4.2 Manual DNA Editing (Admin)

```python
# scripts/edit_agent_dna.py
"""
Admin tool for manual DNA editing
Usage: python -m scripts.edit_agent_dna --agent <uuid> --prompt "new prompt"
"""

import asyncio
import argparse
import json
import httpx

async def edit_dna(agent_id: str, prompt: str = None, temperature: float = None):
    """Edit an agent's DNA with safety checks"""
    
    async with httpx.AsyncClient() as client:
        # Get current DNA
        resp = await client.get(f"http://localhost:8000/api/v1/agents/{agent_id}/dna")
        if resp.status_code != 200:
            print(f"Agent not found: {agent_id}")
            return
        
        dna = resp.json()
        print("Current DNA:")
        print(json.dumps(dna, indent=2))
        
        # Apply changes
        new_dna = dna.copy()
        if prompt:
            new_dna["prompt_genes"]["system_prompt"] = prompt
        if temperature is not None:
            new_dna["parameter_genes"]["temperature"] = temperature
        
        # Update (requires admin auth)
        update_resp = await client.put(
            f"http://localhost:8000/api/v1/agents/{agent_id}/dna",
            json=new_dna,
            headers={"X-Admin-Key": "admin-secret"}
        )
        
        if update_resp.status_code == 200:
            print("\n✓ DNA updated successfully")
            print("Agent will be validated in sandbox before deployment")
        else:
            print(f"\n✗ Update failed: {update_resp.text}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Edit agent DNA")
    parser.add_argument("--agent", required=True, help="Agent ID")
    parser.add_argument("--prompt", help="New system prompt")
    parser.add_argument("--temperature", type=float, help="New temperature")
    
    args = parser.parse_args()
    asyncio.run(edit_dna(args.agent, args.prompt, args.temperature))
```

---

## 5. MEMORY OPERATIONS WORKFLOW

### 5.1 Memory Inspection

```python
# scripts/inspect_memory.py
"""
Inspect an agent's memory across all tiers
Usage: python -m scripts.inspect_memory --agent <uuid> [--query "search term"]
"""

import asyncio
import argparse
from genesis.memory import EpisodicMemory, SemanticMemory, WorkingMemoryManager

async def inspect_memory(agent_id: str, query: str = None):
    """Comprehensive memory inspection"""
    
    print(f"\n{'='*70}")
    print(f"  MEMORY INSPECTION FOR AGENT: {agent_id}")
    print(f"{'='*70}\n")
    
    # Working Memory
    print("┌─────────────────────────────────────────────────────────────────────┐")
    print("│ WORKING MEMORY (Letta-style)                                        │")
    print("└─────────────────────────────────────────────────────────────────────┘")
    wm = WorkingMemoryManager()
    active = await wm.get_active_context(agent_id)
    print(f"Active Context Size: {len(active)} items")
    for item in active[:5]:  # Show top 5
        print(f"  • [{item.importance:.2f}] {item.content[:80]}...")
    if len(active) > 5:
        print(f"  ... and {len(active) - 5} more")
    
    # Episodic Memory
    print("\n┌─────────────────────────────────────────────────────────────────────┐")
    print("│ EPISODIC MEMORY (Mem0)                                              │")
    print("└─────────────────────────────────────────────────────────────────────┘")
    em = EpisodicMemory()
    if query:
        episodes = await em.recall(query, agent_id=agent_id)
    else:
        episodes = await em.get_recent(agent_id, limit=10)
    
    print(f"Retrieved: {len(episodes)} episodes")
    for ep in episodes[:5]:
        print(f"  • [{ep.timestamp}] {ep.content[:80]}...")
        print(f"    Importance: {ep.importance:.2f} | Type: {ep.memory_type}")
    
    # Semantic Memory
    print("\n┌─────────────────────────────────────────────────────────────────────┐")
    print("│ SEMANTIC MEMORY (Cognee/Neo4j)                                      │")
    print("└─────────────────────────────────────────────────────────────────────┘")
    sm = SemanticMemory()
    if query:
        facts = await sm.reason(query, agent_id=agent_id)
    else:
        facts = await sm.get_entities(agent_id, limit=10)
    
    print(f"Retrieved: {len(facts)} facts/entities")
    for fact in facts[:5]:
        print(f"  • {fact.name}: {fact.description[:80]}...")
        if fact.relationships:
            print(f"    Related: {', '.join(r.type for r in fact.relationships[:3])}")
    
    # Procedural Memory
    print("\n┌─────────────────────────────────────────────────────────────────────┐")
    print("│ PROCEDURAL MEMORY (Skills)                                          │")
    print("└─────────────────────────────────────────────────────────────────────┘")
    from genesis.skills import ProceduralMemory
    pm = ProceduralMemory()
    skills = await pm.get_agent_skills(agent_id)
    
    print(f"Skills: {len(skills)}")
    for skill in skills:
        print(f"  • {skill.name} v{skill.version} "
              f"(Fitness: {skill.fitness_score:.2f}, "
              f"Used: {skill.usage_count}x)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect agent memory")
    parser.add_argument("--agent", required=True, help="Agent ID")
    parser.add_argument("--query", help="Search query")
    
    args = parser.parse_args()
    asyncio.run(inspect_memory(args.agent, args.query))
```

### 5.2 Memory Consolidation Trigger

```python
# scripts/trigger_consolidation.py
"""
Manually trigger memory consolidation
Usage: python -m scripts.trigger_consolidation [--agent <uuid>] [--type episodic_to_semantic]
"""

import asyncio
import argparse
from genesis.memory.consolidation import ConsolidationPipeline

async def trigger_consolidation(agent_id: str = None, consolidation_type: str = "all"):
    """Trigger memory consolidation manually"""
    
    pipeline = ConsolidationPipeline()
    
    print(f"Starting consolidation: {consolidation_type}")
    if agent_id:
        print(f"Agent filter: {agent_id}")
    
    result = await pipeline.run(
        agent_id=agent_id,
        consolidation_type=consolidation_type,
        dry_run=False
    )
    
    print(f"\nConsolidation Complete:")
    print(f"  Source memories processed: {result.sources_processed}")
    print(f"  New memories created: {result.targets_created}")
    print(f"  Facts extracted: {result.facts_extracted}")
    print(f"  Processing time: {result.duration_ms}ms")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trigger memory consolidation")
    parser.add_argument("--agent", help="Specific agent ID")
    parser.add_argument("--type", default="all", 
                       choices=["all", "episodic_to_semantic", "semantic_to_procedural"])
    
    args = parser.parse_args()
    asyncio.run(trigger_consolidation(args.agent, args.type))
```

---

## 6. DEPLOYMENT WORKFLOW

### 6.1 Release Process

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         RELEASE WORKFLOW                                         │
│                                                                                  │
│  1. FEATURE FREEZE                                                               │
│     ├── All features merged to develop                                           │
│     ├── Run full test suite                                                      │
│     └── Update version in pyproject.toml                                         │
│                                                                                  │
│  2. RELEASE BRANCH                                                               │
│     ├── git checkout -b release/v0.1.0                                           │
│     ├── Run integration tests                                                    │
│     ├── Run evolution benchmarks                                                 │
│     └── Update CHANGELOG.md                                                      │
│                                                                                  │
│  3. SANDBOX VALIDATION                                                           │
│     ├── Deploy to staging environment                                            │
│     ├── Run 24-hour evolution cycle                                              │
│     ├── Verify memory consolidation                                              │
│     └── Load test with synthetic traffic                                         │
│                                                                                  │
│  4. PRODUCTION DEPLOYMENT                                                        │
│     ├── Merge release branch to main                                             │
│     ├── Tag release: git tag v0.1.0                                              │
│     ├── Build Docker image: genesis-ai-platform:v0.1.0                           │
│     ├── Blue-green deployment                                                    │
│     └── Verify health checks                                                     │
│                                                                                  │
│  5. POST-DEPLOYMENT                                                              │
│     ├── Monitor metrics for 2 hours                                              │
│     ├── Verify agent fitness scores stable                                       │
│     ├── Check memory operations normal                                           │
│     └── Announce release                                                         │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

*Document Status: OPERATIONS GUIDE COMPLETE*  
*Next Review: After Phase 1 Implementation*  
*Document Owner: Genesis AI Platform DevOps Team*
