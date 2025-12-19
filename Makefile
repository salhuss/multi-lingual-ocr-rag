.PHONY: help install install-backend install-frontend setup-db ingest run-backend run-frontend run test clean

help:
	@echo "Hajj RAG MVP - Available Commands"
	@echo "=================================="
	@echo "make install          - Install all dependencies"
	@echo "make setup-db         - Initialize database"
	@echo "make ingest           - Run OCR and ingestion pipeline"
	@echo "make run              - Run backend and frontend (separate terminals)"
	@echo "make run-backend      - Run backend only"
	@echo "make run-frontend     - Run frontend only"
	@echo "make test             - Run all tests"
	@echo "make clean            - Clean generated files"

install: install-backend install-frontend

install-backend:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt

install-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

setup-db:
	@echo "Setting up database..."
	@echo "Make sure PostgreSQL is running and DATABASE_URL is set in .env"
	cd backend && python -c "from app.database import init_db; init_db(); print('Database initialized!')"

ingest:
	@echo "Running OCR and ingestion pipeline..."
	@echo "Make sure PDFs are in data/raw/ directory"
	cd ingest && python scripts/ocr_pipeline.py

run-backend:
	@echo "Starting backend on port 8000..."
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-frontend:
	@echo "Starting frontend on port 3000..."
	cd frontend && npm run dev

test:
	@echo "Running tests..."
	cd backend && pytest tests/ -v
	cd ingest && pytest tests/ -v

clean:
	@echo "Cleaning generated files..."
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	rm -rf backend/.pytest_cache
	rm -rf ingest/.pytest_cache
	rm -rf frontend/.next
	rm -rf frontend/node_modules
	@echo "Clean complete!"
