.PHONY: help install test run docker-up docker-down clean

help:
	@echo "Available commands:"
	@echo "  make install     - Install dependencies"
	@echo "  make test        - Run tests"
	@echo "  make run         - Run development server"
	@echo "  make docker-up   - Start Docker containers"
	@echo "  make docker-down - Stop Docker containers"
	@echo "  make clean       - Clean cache and temp files"

install:
	cd backend && pip install -r requirements.txt
	python -m nltk.downloader punkt stopwords
	python -m spacy download en_core_web_sm
	cd frontend && npm install

test:
	cd backend && pytest tests/ -v --cov=src

run:
	cd backend && uvicorn src.main:app --reload --port 8000

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov

format:
	cd backend && black src/ tests/
	cd backend && isort src/ tests/

lint:
	cd backend && flake8 src/ tests/
	cd backend && mypy src/