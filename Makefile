# FirstReply task runner. Every target works from the repo root.
UV ?= uv
export PYTHONPATH := $(CURDIR)

.PHONY: help install dev dev-stub lint format test test-llm check smoke ownership fixtures schema eval report docs train guardian-train label loadtest csp-check docker spike models

help: ## list targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' Makefile | awk 'BEGIN{FS=":.*?## "}{printf "  %-15s %s\n", $$1, $$2}'

install: ## install Python dependencies
	$(UV) sync

dev: ## API + built frontend on :8000 (real components where implemented)
	$(UV) run uvicorn backend.app.main:app --reload --port $${PORT:-8000}

dev-stub: ## API on :8000 with every component stubbed (frontend development)
	FR_STUB=1 FR_EMBED=hash $(UV) run uvicorn backend.app.main:app --reload --port $${PORT:-8000}

lint: ## ruff lint + format check
	$(UV) run ruff check .
	$(UV) run ruff format --check .

format: ## auto-format Python
	$(UV) run ruff format .
	$(UV) run ruff check --fix .

test: ## all Python tests (offline, hash embeddings)
	FR_EMBED=hash $(UV) run pytest -q

test-llm: ## tests that call the real OpenAI API (needs OPENAI_API_KEY; costs cents)
	FR_FAKE_LLM=0 FR_EMBED=hash $(UV) run pytest -q -m llm

check: lint test ## lint + tests (must pass before every merge)

smoke: ## end-to-end API smoke test
	FR_EMBED=hash $(UV) run pytest -q tests/e2e

ownership: ## check this lane only changed files it owns
	$(UV) run python scripts/check_ownership.py

fixtures: ## regenerate example API payloads (stub mode)
	$(UV) run python scripts/make_fixtures.py

schema: ## regenerate JSON schemas for content files
	$(UV) run python scripts/export_schema.py

eval: ## run every lane evaluation -> eval/reports/
	$(UV) run python scripts/run_evals.py

report: ## rebuild README metrics tables (RED-TEAM lane)
	@if [ -f scripts/report.py ]; then $(UV) run python scripts/report.py; else echo "report: not implemented yet (lane: redteam)"; fi

docs: ## build HOW_IT_WORKS.md from docs/how/*
	$(UV) run python scripts/build_docs.py

train: ## train the skill detector (ML lane)
	$(UV) run python -m backend.app.ml.train

guardian-train: ## train the Guardian classifier (SAFETY lane)
	$(UV) run python -m backend.app.safety.train_guardian

label: ## open the labeling tool (DATA lane)
	@if [ -f tools/labeler/index.html ]; then echo "Open tools/labeler/index.html in your browser"; else echo "label: not implemented yet (lane: data)"; fi

loadtest: ## load test a local prod-mode server (FR_LLM=0, no API cost)
	FR_LLM=0 $(UV) run python deploy/loadtest.py

csp-check: ## check the security policy in headless Chromium (FR_URL, default http://127.0.0.1:7860)
	node deploy/csp_check.mjs $${FR_URL:-http://127.0.0.1:7860}

docker: ## build the container (DEPLOY lane)
	@if [ -f Dockerfile ]; then docker build -t firstreply .; else echo "docker: not implemented yet (lane: deploy)"; fi

spike: ## refusal/quality test of the OpenAI friend voice (needs OPENAI_API_KEY)
	$(UV) run python scripts/spike_actor.py

models: ## list OpenAI models your key can use
	$(UV) run python scripts/list_models.py
