.PHONY: help install dev test lint format migrate run shell docker-up docker-down docker-build clean

# Variables
PYTHON := python
PIP := pip
DOCKER_COMPOSE := docker compose
MANAGE := $(PYTHON) manage.py

# Colors
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help: ## Show this help
	@echo "ABSERVICE - Makefile commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# ==================== Development ====================

install: ## Install Python dependencies
	$(PIP) install -r requirements/development.txt

dev: ## Start development server
	$(MANAGE) runserver

run: dev ## Alias for dev

shell: ## Open Django shell
	$(MANAGE) shell_plus

dbshell: ## Open database shell
	$(MANAGE) dbshell

# ==================== Database ====================

migrate: ## Run database migrations
	$(MANAGE) migrate

makemigrations: ## Create new migrations
	$(MANAGE) makemigrations

migrations: makemigrations migrate ## Create and apply migrations

resetdb: ## Reset database (development only!)
	$(MANAGE) reset_db --noinput
	$(MAKE) migrate
	$(MANAGE) setup_permissions
	$(MANAGE) createsuperuser

# ==================== Testing ====================

test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=apps --cov-report=html --cov-report=term

test-fast: ## Run tests in parallel
	pytest -n auto

# ==================== Code Quality ====================

lint: ## Run linting
	ruff check .

lint-fix: ## Fix linting issues
	ruff check . --fix

format: ## Format code
	ruff format .

format-check: ## Check code formatting
	ruff format . --check

typecheck: ## Run type checking
	mypy apps/

quality: lint format-check typecheck ## Run all code quality checks

# ==================== Docker ====================

docker-up: ## Start Docker containers
	$(DOCKER_COMPOSE) up -d

docker-down: ## Stop Docker containers
	$(DOCKER_COMPOSE) down

docker-build: ## Build Docker images
	$(DOCKER_COMPOSE) build

docker-logs: ## View Docker logs
	$(DOCKER_COMPOSE) logs -f

docker-shell: ## Open shell in web container
	$(DOCKER_COMPOSE) exec web bash

docker-test: ## Run tests in Docker
	$(DOCKER_COMPOSE) exec web pytest

docker-migrate: ## Run migrations in Docker
	$(DOCKER_COMPOSE) exec web python manage.py migrate

# ==================== Production ====================

docker-prod-up: ## Start production containers
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml up -d

docker-prod-down: ## Stop production containers
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml down

docker-prod-logs: ## View production logs
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml logs -f

# ==================== Utilities ====================

collectstatic: ## Collect static files
	$(MANAGE) collectstatic --noinput

setup-permissions: ## Setup default permissions and roles
	$(MANAGE) setup_permissions

createsuperuser: ## Create superuser
	$(MANAGE) createsuperuser

clean: ## Clean Python cache files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true

# ==================== Initial Setup ====================

init: ## Initialize project (first time setup)
	@echo "$(YELLOW)Installing dependencies...$(NC)"
	$(MAKE) install
	@echo "$(YELLOW)Running migrations...$(NC)"
	$(MAKE) migrate
	@echo "$(YELLOW)Setting up permissions...$(NC)"
	$(MAKE) setup-permissions
	@echo "$(GREEN)Project initialized successfully!$(NC)"
	@echo "Run 'make createsuperuser' to create an admin account"
	@echo "Run 'make dev' to start the development server"

init-docker: ## Initialize project with Docker
	@echo "$(YELLOW)Building Docker images...$(NC)"
	$(MAKE) docker-build
	@echo "$(YELLOW)Starting containers...$(NC)"
	$(MAKE) docker-up
	@echo "$(YELLOW)Running migrations...$(NC)"
	$(MAKE) docker-migrate
	@echo "$(YELLOW)Setting up permissions...$(NC)"
	$(DOCKER_COMPOSE) exec web python manage.py setup_permissions
	@echo "$(GREEN)Project initialized successfully!$(NC)"
	@echo "Run 'docker compose exec web python manage.py createsuperuser' to create an admin"
	@echo "Access the app at http://localhost:8000"
