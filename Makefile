.PHONY: help install sync frontend backend dev test test-frontend test-backend lint

FRONTEND_DIR := frontend
BACKEND_DIR := backend

# Default: list available targets
help:
	@echo "Family Kanban — common targets"
	@echo ""
	@echo "  make install        Install frontend + backend dependencies"
	@echo "  make frontend       Start Vite dev server (http://localhost:5173)"
	@echo "  make backend        Start API with reload (http://localhost:8000)"
	@echo "  make dev            Start backend and frontend together"
	@echo "  make test           Run frontend + backend tests"
	@echo "  make test-frontend  Run frontend tests (vitest)"
	@echo "  make test-backend   Run backend tests (pytest)"
	@echo "  make lint           Lint frontend (eslint)"
	@echo ""

install sync:
	cd $(FRONTEND_DIR) && npm install
	cd $(BACKEND_DIR) && uv sync --group dev

frontend:
	cd $(FRONTEND_DIR) && npm run dev

backend:
	cd $(BACKEND_DIR) && uv run uvicorn app.main:app --reload --port 8000

# Run API + Vite together (Ctrl+C stops both).
dev:
	$(MAKE) -j2 backend frontend

test: test-frontend test-backend

test-frontend:
	cd $(FRONTEND_DIR) && npm test

test-backend:
	cd $(BACKEND_DIR) && uv run pytest

lint:
	cd $(FRONTEND_DIR) && npm run lint
