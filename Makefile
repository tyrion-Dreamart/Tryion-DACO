.PHONY: up down build logs shell migrate revision seed

# ── Docker ────────────────────────────────────────────────────────────────────
up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build --no-cache

logs:
	docker compose logs -f api

shell:
	docker compose exec api bash

# ── Database ──────────────────────────────────────────────────────────────────
migrate:
	docker compose exec api alembic upgrade head

revision:
	docker compose exec api alembic revision --autogenerate -m "$(msg)"

downgrade:
	docker compose exec api alembic downgrade -1

# ── Dev helpers ───────────────────────────────────────────────────────────────
seed:
	docker compose exec api python -m app.utils.seed

test:
	docker compose exec api pytest tests/ -v

lint:
	docker compose exec api ruff check app/

format:
	docker compose exec api ruff format app/
