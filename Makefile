# Makefile for Flask API

.PHONY: help install install-dev run test coverage clean docker-build docker-up docker-down lint format

help:
	@echo "Available commands:"
	@echo "  make install       - Install production dependencies"
	@echo "  make install-dev   - Install development dependencies"
	@echo "  make run          - Run development server"
	@echo "  make test         - Run tests"
	@echo "  make coverage     - Run tests with coverage"
	@echo "  make clean        - Remove cache and build files"
	@echo "  make docker-build - Build Docker images"
	@echo "  make docker-up    - Start Docker services"
	@echo "  make docker-down  - Stop Docker services"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

run:
	python run.py

test:
	pytest

coverage:
	pytest --cov=app --cov-report=term-missing --cov-report=html

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov build dist

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

lint:
	flake8 . --exclude=venv,env,.venv,.env,venv*,env*
	ruff check .

fix:
	ruff check --fix .
	black . --exclude '/(venv|env|\.venv|\.env|venv.*|env.*|.*venv|.*env)/'

format:
	black . --exclude '/(venv|env|\.venv|\.env|venv.*|env.*|.*venv|.*env)/'


.DEFAULT_GOAL := help
