#!/bin/bash

# Setup script for Hajj RAG MVP

set -e

echo "=================================="
echo "Hajj RAG MVP Setup Script"
echo "=================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi
echo "✅ Python 3 found: $(python3 --version)"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi
echo "✅ Node.js found: $(node --version)"

# Check PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "⚠️  PostgreSQL client not found. Make sure PostgreSQL is available."
else
    echo "✅ PostgreSQL client found"
fi

# Check Tesseract
if ! command -v tesseract &> /dev/null; then
    echo "⚠️  Tesseract not found. Install with:"
    echo "   macOS: brew install tesseract tesseract-lang"
    echo "   Linux: sudo apt-get install tesseract-ocr tesseract-ocr-ara"
else
    echo "✅ Tesseract found: $(tesseract --version | head -n 1)"
fi

echo ""
echo "=================================="
echo "Installing dependencies..."
echo "=================================="

# Backend
echo ""
echo "Installing backend dependencies..."
cd backend
pip install -r requirements.txt
cd ..

# Frontend
echo ""
echo "Installing frontend dependencies..."
cd frontend
npm install
cd ..

echo ""
echo "=================================="
echo "Setup complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and configure:"
echo "   cp .env.example .env"
echo ""
echo "2. Start PostgreSQL with pgvector:"
echo "   docker run -d --name pgvector -p 5432:5432 -e POSTGRES_PASSWORD=postgres ankane/pgvector"
echo ""
echo "3. Initialize database:"
echo "   make setup-db"
echo ""
echo "4. Place PDF files in data/raw/ and run ingestion:"
echo "   make ingest"
echo ""
echo "5. Run the application:"
echo "   make run-backend  (Terminal 1)"
echo "   make run-frontend (Terminal 2)"
echo ""
echo "Visit http://localhost:3000 to use the application!"
