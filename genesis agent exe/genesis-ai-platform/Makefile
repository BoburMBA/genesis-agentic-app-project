.PHONY: help setup start stop restart logs seed test clean reset status

# ── Colors ────────────────────────────────────────────────────
GREEN  := \033[0;32m
YELLOW := \033[1;33m
CYAN   := \033[0;36m
RESET  := \033[0m

help:
	@echo ""
	@echo "$(CYAN)GENESIS AI Platform — Commands$(RESET)"
	@echo "────────────────────────────────────────"
	@echo "  $(GREEN)make setup$(RESET)    First-time setup (copy .env, pull images)"
	@echo "  $(GREEN)make start$(RESET)    Build and start all services"
	@echo "  $(GREEN)make stop$(RESET)     Stop all services"
	@echo "  $(GREEN)make restart$(RESET)  Restart all services"
	@echo "  $(GREEN)make seed$(RESET)     Seed agents and skills into database"
	@echo "  $(GREEN)make logs$(RESET)     Follow all service logs"
	@echo "  $(GREEN)make status$(RESET)   Check health of all services"
	@echo "  $(GREEN)make test$(RESET)     Run backend tests"
	@echo "  $(GREEN)make clean$(RESET)    Remove containers (keep data volumes)"
	@echo "  $(GREEN)make reset$(RESET)    Remove containers AND all data (full wipe)"
	@echo ""

# ── First-time setup ──────────────────────────────────────────
setup:
	@echo "$(YELLOW)Setting up GENESIS AI Platform...$(RESET)"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)✓ Created .env from .env.example$(RESET)"; \
		echo "$(YELLOW)⚠ Edit .env and add your ANTHROPIC_API_KEY before starting!$(RESET)"; \
	else \
		echo "$(GREEN)✓ .env already exists$(RESET)"; \
	fi
	@docker-compose pull postgres redis qdrant 2>/dev/null || true
	@echo "$(GREEN)✓ Setup complete. Run 'make start' when ready.$(RESET)"

# ── Start stack ───────────────────────────────────────────────
start:
	@echo "$(CYAN)Building and starting GENESIS AI Platform...$(RESET)"
	@docker-compose up --build -d
	@echo ""
	@echo "$(CYAN)Waiting for services to be healthy...$(RESET)"
	@sleep 5
	@$(MAKE) _wait_healthy
	@echo ""
	@echo "$(GREEN)✓ GENESIS AI Platform is running!$(RESET)"
	@echo ""
	@echo "  Frontend:  http://localhost:3000"
	@echo "  Backend:   http://localhost:8000"
	@echo "  API Docs:  http://localhost:8000/docs"
	@echo "  Qdrant UI: http://localhost:6333/dashboard"
	@echo ""
	@echo "Run '$(YELLOW)make seed$(RESET)' to load initial agents and skills."

# ── Wait for healthy ──────────────────────────────────────────
_wait_healthy:
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		STATUS=$$(curl -s http://localhost:8000/api/v1/system/health 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null); \
		if [ "$$STATUS" = "operational" ]; then \
			echo "$(GREEN)✓ Backend is healthy$(RESET)"; \
			break; \
		fi; \
		echo "  Waiting for backend... ($$i/10)"; \
		sleep 5; \
	done

# ── Seed data ─────────────────────────────────────────────────
seed:
	@echo "$(CYAN)Seeding agents and skills...$(RESET)"
	@curl -s http://localhost:8000/api/v1/agents/seed | python3 -c \
		"import sys,json; d=json.load(sys.stdin); print('✓ Seeded', d.get('total', len(d.get('agents',[]))), 'agents')"
	@curl -s http://localhost:8000/api/v1/skills/seed | python3 -c \
		"import sys,json; d=json.load(sys.stdin); print('✓ Seeded', d.get('count', 0), 'skills')"
	@echo "$(GREEN)✓ Done. Open http://localhost:3000 to start using GENESIS.$(RESET)"

# ── Status ────────────────────────────────────────────────────
status:
	@echo "$(CYAN)Service Status:$(RESET)"
	@docker-compose ps
	@echo ""
	@echo "$(CYAN)API Health:$(RESET)"
	@curl -s http://localhost:8000/api/v1/system/health | python3 -m json.tool 2>/dev/null || echo "Backend not responding"
	@echo ""
	@echo "$(CYAN)Platform Stats:$(RESET)"
	@curl -s http://localhost:8000/api/v1/system/stats | python3 -m json.tool 2>/dev/null || echo "Backend not responding"

# ── Logs ──────────────────────────────────────────────────────
logs:
	@docker-compose logs -f --tail=50

logs-backend:
	@docker-compose logs -f backend --tail=100

logs-frontend:
	@docker-compose logs -f frontend --tail=50

# ── Stop/restart ──────────────────────────────────────────────
stop:
	@docker-compose stop
	@echo "$(GREEN)✓ All services stopped$(RESET)"

restart:
	@docker-compose restart
	@echo "$(GREEN)✓ All services restarted$(RESET)"

restart-backend:
	@docker-compose restart backend
	@echo "$(GREEN)✓ Backend restarted$(RESET)"

# ── Tests ─────────────────────────────────────────────────────
test:
	@echo "$(CYAN)Running backend tests...$(RESET)"
	@docker-compose exec backend pytest tests/ -v --tb=short

test-local:
	@cd backend && pytest tests/ -v --tb=short

# ── Cleanup ───────────────────────────────────────────────────
clean:
	@docker-compose down
	@echo "$(GREEN)✓ Containers removed (data volumes preserved)$(RESET)"

reset:
	@echo "$(YELLOW)WARNING: This will delete ALL data including the database!$(RESET)"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	@docker-compose down -v
	@echo "$(GREEN)✓ Full reset complete$(RESET)"

# ── Quick task test ───────────────────────────────────────────
test-task:
	@echo "$(CYAN)Running a test task...$(RESET)"
	@curl -s -X POST http://localhost:8000/api/v1/tasks \
		-H "Content-Type: application/json" \
		-d '{"task": "Explain what the GENESIS AI platform does in 2 sentences.", "session_id": "test-session"}' \
		| python3 -c "import sys,json; d=json.load(sys.stdin); print('Agent:', d.get('agent_name')); print('Output:', d.get('output','')[:300])"

# ── Neo4j (optional, for full semantic memory) ────────────────
start-full:
	@docker-compose --profile full up --build -d
	@echo "$(GREEN)✓ Started with Neo4j (full semantic memory mode)$(RESET)"
	@echo "  Neo4j UI: http://localhost:7474"
