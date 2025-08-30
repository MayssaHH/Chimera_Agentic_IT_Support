.PHONY: help dev test run install clean format lint

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies using Poetry
	poetry install

dev:  ## Run development server with auto-reload
	poetry run uvicorn local_it_support.main:app --reload --host 0.0.0.0 --port 8000

test:  ## Run tests
	poetry run pytest

run:  ## Run production server
	poetry run uvicorn local_it_support.main:app --host 0.0.0.0 --port 8000

clean:  ## Clean up cache and temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

format:  ## Format code using black and isort
	poetry run black .
	poetry run isort .

lint:  ## Run linting checks
	poetry run flake8 .
	poetry run mypy .

ingest:  ## Run document ingestion pipeline
	@echo "Usage: make ingest DOCS_DIR=./company_docs"
	@if [ -z "$(DOCS_DIR)" ]; then \
		echo "Error: DOCS_DIR not specified. Use: make ingest DOCS_DIR=./company_docs"; \
		exit 1; \
	fi
	python3 -m src.ingest.pipeline $(DOCS_DIR)

ingest-test:  ## Test the ingestion pipeline
	python3 -m src.ingest.test_pipeline

ingest-example:  ## Run ingestion pipeline examples
	python3 -m src.ingest.example_usage

ingest-tickets:  ## Run historical tickets ingestion pipeline
	@echo "Usage: make ingest-tickets TICKET_DIR=./ticket_data"
	@if [ -z "$(TICKET_DIR)" ]; then \
		echo "Error: TICKET_DIR not specified. Use: make ingest-tickets TICKET_DIR=./ticket_data"; \
		exit 1; \
	fi
	python3 -m src.ingest.past_tickets $(TICKET_DIR)

ingest-tickets-test:  ## Test the tickets ingestion pipeline
	python3 -m src.ingest.test_past_tickets

setup:  ## Initial setup of the project
	poetry install
	poetry run pre-commit install
