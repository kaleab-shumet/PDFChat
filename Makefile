.PHONY: help check test dev coverage ci install clean

# Colors for output
GREEN=\033[0;32m
YELLOW=\033[0;33m
RED=\033[0;31m
NC=\033[0m # No Color

help: ## Show this help message
	@echo "PDFChat Development Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  ${GREEN}%-20s${NC} %s\n", $$1, $$2}'

# === CORE WORKFLOW COMMANDS ===

install: ## Install dependencies and build containers
	@echo "${YELLOW}📦 Installing dependencies...${NC}"
	docker compose build

check: ## Run code quality checks (formatting, linting)
	@echo "${YELLOW}🔍 Running code quality checks...${NC}"
	uv run black --check . && uv run ruff check .
	@echo "${GREEN}✅ All quality checks passed!${NC}"

check-strict: ## Run strict quality checks (including type checking)
	@echo "${YELLOW}🔍 Running strict code quality checks...${NC}"
	uv run black --check . && uv run ruff check . && uv run mypy .
	@echo "${GREEN}✅ All strict quality checks passed!${NC}"


test: check ## Run full test suite (check -> unit -> integration)
	@echo "${YELLOW}🧪 Running test suite...${NC}"
	$(MAKE) test-unit
	$(MAKE) test-integration
	@echo "${GREEN}🎉 All tests passed!${NC}"

ci: ## Complete CI workflow (install -> check-strict -> test -> e2e)
	@echo "${YELLOW}🚀 Running CI workflow...${NC}"
	$(MAKE) install
	@echo "${YELLOW}🔍 Running all checks and tests in single container...${NC}"
	docker compose --profile test run --rm test /bin/bash -c "\
		echo '📝 Checking code formatting...' && \
		uv run black --check . && \
		echo '🔧 Running linter...' && \
		uv run ruff check . && \
		echo '🔍 Running type checker...' && \
		uv run mypy . && \
		echo '🧪 Running unit tests...' && \
		uv run pytest tests/unit/ && \
		echo '🧪 Running integration tests...' && \
		uv run pytest tests/integration/"
	@echo "${YELLOW}🚀 Starting services for e2e tests...${NC}"
	docker compose up -d
	@echo "${YELLOW}⏳ Waiting for services to be ready...${NC}"
	sleep 15
	@echo "${YELLOW}🔍 Checking API health...${NC}"
	timeout 30 bash -c 'until curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; do sleep 2; done' || (echo "API failed to start" && docker compose logs api && docker compose down && exit 1)
	@echo "${YELLOW}🧪 Running end-to-end tests...${NC}"
	$(MAKE) test-e2e || (docker compose down && exit 1)
	docker compose down
	@echo "${GREEN}🎊 CI workflow completed successfully!${NC}"

# === DEVELOPMENT COMMANDS ===

dev: ## Start development environment
	@echo "${YELLOW}🚀 Starting development environment...${NC}"
	docker compose up 2>&1 | tee server.log
	@echo "${GREEN}📍 API available at: http://localhost:8000${NC}"

dev-bg: ## Start development environment in background
	@echo "${YELLOW}🚀 Starting development environment (background)...${NC}"
	docker compose up -d
	@echo "${GREEN}📍 API available at: http://localhost:8000${NC}"

stop: ## Stop all services
	@echo "${YELLOW}🛑 Stopping all services...${NC}"
	docker compose down

restart: ## Restart all services
	@echo "${YELLOW}🔄 Restarting services...${NC}"
	docker compose restart

# === DATABASE COMMANDS ===

db-setup: ## Set up database with migrations
	@echo "${YELLOW}🗄️  Setting up database...${NC}"
	docker compose up -d postgres
	sleep 3
	$(MAKE) migrate

migrate: ## Run database migrations
	@echo "${YELLOW}⬆️  Running database migrations...${NC}"
	docker compose exec api uv run alembic upgrade head

db-reset: ## Reset database (WARNING: destroys all data)
	@echo "${RED}⚠️  Resetting database (this will destroy all data)...${NC}"
	@read -p "Are you sure? (y/N) " -n 1 -r; echo; if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker compose down -v; \
		docker compose up -d postgres; \
		sleep 5; \
		$(MAKE) migrate; \
	else \
		echo "Database reset cancelled."; \
	fi

# === TESTING COMMANDS ===

test-unit: ## Run unit tests only
	@echo "${YELLOW}🧪 Running unit tests...${NC}"
	docker compose --profile test run --rm test uv run pytest tests/unit/

test-integration: ## Run integration tests only  
	@echo "${YELLOW}🧪 Running integration tests...${NC}"
	docker compose --profile test run --rm test uv run pytest tests/integration/

test-e2e: ## Run end-to-end tests only
	@echo "${YELLOW}🧪 Running end-to-end tests...${NC}"
	PYTHONPATH=. uv run pytest tests/e2e/ -v --no-cov

test-watch: ## Run tests in watch mode
	@echo "${YELLOW}👀 Running tests in watch mode...${NC}"
	docker compose --profile test run --rm test uv run pytest -f tests/

coverage: ## Generate test coverage report
	@echo "${YELLOW}📊 Generating coverage report...${NC}"
	docker compose --profile test run --rm test uv run pytest --cov=api --cov-report=html --cov-report=term-missing tests/
	@echo "${GREEN}📁 Coverage report: htmlcov/index.html${NC}"

# === UTILITY COMMANDS ===

logs: ## Show logs from all services
	docker compose logs -f

logs-api: ## Show API logs only
	docker compose logs -f api

logs-db: ## Show database logs only
	docker compose logs -f postgres

shell: ## Open shell in API container
	docker compose exec api /bin/bash

db-shell: ## Open PostgreSQL shell
	docker compose exec postgres psql -U postgres -d pdfchat

health: ## Check service health
	@echo "${YELLOW}🔍 Checking service health...${NC}"
	@curl -s http://localhost:8000/api/v1/health | jq . || echo "${RED}❌ API not responding${NC}"
	@docker compose exec postgres pg_isready -U postgres || echo "${RED}❌ Database not ready${NC}"

# === CLEANUP COMMANDS ===

clean: ## Remove all containers, images and volumes
	@echo "${RED}🗑️  Cleaning up Docker resources...${NC}"
	docker compose down -v --rmi all --remove-orphans

clean-cache: ## Clean Python cache files
	@echo "${YELLOW}🧹 Cleaning Python cache...${NC}"
	docker compose exec api find . -name "*.pyc" -delete
	docker compose exec api find . -name "__pycache__" -delete

# === QUICK COMMANDS ===

format: ## Format code with black and ruff
	@echo "${YELLOW}✨ Formatting code...${NC}"
	uv run black . && uv run ruff check --fix .

lint: ## Run only linting checks
	@echo "${YELLOW}🔧 Running linter...${NC}"
	uv run ruff check .

type-check: ## Run only type checking
	@echo "${YELLOW}🔍 Running type checker...${NC}"
	uv run mypy .