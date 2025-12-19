# Hajj Knowledge Assistant - RAG MVP

A production-ready chat application that answers Hajj-related questions in English, strictly grounded in three Arabic reference books. Features OCR for scanned PDFs, semantic search with embeddings, and strong guardrails to ensure accurate, source-backed responses.

## 🎯 Key Features

- ✅ **English Q&A Interface**: Ask in English, get answers in English
- ✅ **Strict Source Grounding**: Answers only from provided Arabic books
- ✅ **Citation Required**: Every answer includes book name, page number, and excerpt
- ✅ **Topic Guardrails**: Rejects non-Hajj questions politely
- ✅ **OCR Pipeline**: Processes scanned Arabic PDFs
- ✅ **Semantic Search**: Vector similarity with pgvector
- ✅ **Lightweight LLM**: Uses GPT-4o-mini for fast, cost-effective responses
- ✅ **Production Deployment**: Ready for Vercel + Render/Fly.io

## 📋 Architecture

```
┌─────────────┐      ┌──────────────┐      ┌──────────────┐
│  Frontend   │─────▶│   Backend    │─────▶│  PostgreSQL  │
│  (Next.js)  │      │  (FastAPI)   │      │  + pgvector  │
└─────────────┘      └──────────────┘      └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  OpenAI API  │
                     │  (Embeddings │
                     │   + LLM)     │
                     └──────────────┘
```

### Components

1. **Frontend** (`/frontend`): Next.js TypeScript chat UI
2. **Backend** (`/backend`): FastAPI with retrieval + guardrails
3. **Ingestion** (`/ingest`): OCR pipeline for PDF processing
4. **Database**: PostgreSQL with pgvector for embeddings

### Query Flow

```
User Query (English)
    ↓
[Topic Gate: Is it Hajj-related?] → NO → Refuse
    ↓ YES
[Translate to Arabic]
    ↓
[Retrieve relevant chunks (top-K)]
    ↓
[Similarity threshold check] → FAIL → Refuse
    ↓ PASS
[Generate answer with citations]
    ↓
[Validate citations] → INVALID → Refuse
    ↓ VALID
Return answer + citations
```

## 🚀 Quick Start (Local Development)

### Prerequisites

1. **PostgreSQL with pgvector**:
   ```bash
   # Option 1: Using Docker
   docker run -d --name pgvector -p 5432:5432 \
     -e POSTGRES_PASSWORD=postgres \
     ankane/pgvector

   # Option 2: Install locally
   # macOS: brew install postgresql
   # Then install pgvector extension
   ```

2. **Tesseract OCR with Arabic support**:
   ```bash
   # macOS
   brew install tesseract tesseract-lang

   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr tesseract-ocr-ara

   # Verify
   tesseract --list-langs  # Should show 'ara'
   ```

3. **Poppler (PDF processing)**:
   ```bash
   # macOS
   brew install poppler

   # Ubuntu/Debian
   sudo apt-get install poppler-utils
   ```

4. **Python 3.11+** and **Node.js 18+**

### One-Command Setup

```bash
# Clone repository
git clone <your-repo-url>
cd multi-lingual-ocr-rag

# Copy environment file
cp .env.example .env

# Edit .env with your credentials:
# - OPENAI_API_KEY=your_key
# - DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hajj_rag

# Install all dependencies
make install

# Initialize database
make setup-db
```

### Data Ingestion (One-Time)

```bash
# 1. Place your 3 Arabic Hajj PDF books in data/raw/
mkdir -p data/raw
cp /path/to/your/books/*.pdf data/raw/

# 2. Update book metadata in ingest/scripts/ocr_pipeline.py
# Edit the 'books' array with actual titles

# 3. Run ingestion pipeline
make ingest

# This will:
# - Convert PDFs to images
# - Extract Arabic text via OCR
# - Chunk text with overlap
# - Generate embeddings
# - Index in PostgreSQL
#
# ⏱️  Takes 1-2 hours for 3 books
```

### Run Application

**Option 1: Using Make (Recommended)**

```bash
# Terminal 1: Run backend
make run-backend

# Terminal 2: Run frontend
make run-frontend

# Or use Docker Compose:
docker-compose up
```

**Option 2: Manual**

```bash
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

**Access Application**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🧪 Testing

Run comprehensive test suite:

```bash
make test
```

Or manually:

```bash
# Backend tests
cd backend
pytest tests/ -v

# Ingestion tests
cd ingest
pytest tests/ -v
```

### Test Coverage

- ✅ **Guardrails**: Topic filtering, refusal behavior
- ✅ **Retrieval**: Vector search, similarity thresholds
- ✅ **API**: Chat endpoint, health checks, error handling
- ✅ **OCR**: Text chunking, metadata preservation

## 📦 Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment instructions.

### Quick Deployment Steps

1. **Database**: Deploy PostgreSQL with pgvector (Render/Supabase/Railway)
2. **Backend**: Deploy to Render/Fly.io/Railway
3. **Frontend**: Deploy to Vercel
4. **Ingest Data**: Run ingestion pipeline locally, pointing to production DB

### Example URLs (After Deployment)

- Frontend: `https://hajj-rag.vercel.app`
- Backend: `https://hajj-rag-api.onrender.com`

### Cost Estimate

~$15-50/month:
- PostgreSQL: $7-20/month
- Backend hosting: $7-25/month
- Frontend: Free (Vercel hobby)
- OpenAI API: ~$0.15/1000 queries

## 🎮 Usage Examples

### Valid Hajj Questions (Accepted)

```
✅ "How do I perform tawaf?"
✅ "What are the types of Hajj?"
✅ "What is the significance of standing at Arafat?"
✅ "Tell me about sa'i between Safa and Marwa"
✅ "What are the restrictions of ihram?"
```

### Non-Hajj Questions (Refused)

```
❌ "What is zakat?" → "I can only answer questions about Hajj..."
❌ "How do I pray?" → Refused
❌ "Tell me about Ramadan" → Refused
```

### Questions Not in Sources (Refused)

```
❌ "What did Prophet Muhammad eat during Hajj?"
   → "I don't know based on the provided books."
```

## 📁 Project Structure

```
multi-lingual-ocr-rag/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── main.py         # API endpoints
│   │   ├── database.py     # PostgreSQL + pgvector
│   │   ├── embeddings.py   # OpenAI embeddings
│   │   ├── retrieval.py    # Vector search
│   │   ├── guardrails.py   # Topic filtering + validation
│   │   ├── llm.py          # Answer generation
│   │   └── config.py       # Settings
│   ├── tests/              # Backend tests
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/               # Next.js application
│   ├── app/
│   │   ├── page.tsx       # Main page
│   │   └── layout.tsx     # Layout
│   ├── components/
│   │   └── ChatInterface.tsx  # Chat UI
│   ├── package.json
│   └── Dockerfile
│
├── ingest/                # OCR & ingestion pipeline
│   ├── scripts/
│   │   └── ocr_pipeline.py  # PDF → OCR → Embeddings
│   ├── tests/
│   └── README.md
│
├── data/
│   ├── raw/               # Input PDFs (not in git)
│   ├── processed/         # OCR output (not in git)
│   └── vectors/           # Embeddings (not in git)
│
├── docs/
│   └── DEPLOYMENT.md      # Deployment guide
│
├── .env.example           # Environment template
├── docker-compose.yml     # Local development
├── Makefile              # Convenience commands
└── README.md             # This file
```

## 🔧 Configuration

### Environment Variables

**Required**:
- `OPENAI_API_KEY`: OpenAI API key for embeddings + LLM
- `DATABASE_URL`: PostgreSQL connection string

**Optional**:
- `LLM_MODEL`: Default `gpt-4o-mini` (lightweight, fast)
- `EMBEDDING_MODEL`: Default `text-embedding-3-small`
- `RETRIEVAL_TOP_K`: Number of chunks to retrieve (default: 5)
- `SIMILARITY_THRESHOLD`: Minimum similarity score (default: 0.7)
- `LLM_TEMPERATURE`: LLM temperature (default: 0.1)
- `MAX_TOKENS`: Max response tokens (default: 800)

### Model Selection Rationale

- **LLM**: `gpt-4o-mini`
  - Cost: $0.150 per 1M input tokens
  - Latency: ~1-2 seconds
  - Quality: Sufficient for RAG tasks with structured prompts
  - Alternative: `gpt-4o` for higher quality (more expensive)

- **Embeddings**: `text-embedding-3-small`
  - Cost: $0.020 per 1M tokens
  - Dimension: 1536
  - Quality: Excellent for semantic search
  - Supports multilingual (Arabic + English)

## 🛡️ Guardrails & Safety

### Multiple Enforcement Layers

1. **Topic Gate**: Fast keyword + LLM check for Hajj relevance
2. **Retrieval Threshold**: Minimum similarity score (default: 0.7)
3. **Citation Requirement**: LLM must cite sources
4. **Citation Validation**: Verifies cited pages exist in retrieved chunks
5. **Structured Output**: Forces JSON response format
6. **System Prompt**: Explicit rules against external knowledge

### Refusal Scenarios

- Non-Hajj topics → Polite refusal with scope explanation
- No relevant sources → "I don't know based on the provided books"
- Low confidence → Refuses rather than hallucinating
- Missing citations → Regenerate or refuse

## 🔍 Technical Details

### Chunking Strategy

- **Chunk Size**: 500 characters (configurable)
- **Overlap**: 100 characters to preserve context
- **Metadata**: Book ID, title, page number, chunk index
- **Preserved**: Page numbers for accurate citations

### Retrieval Strategy

- **Vector Search**: Cosine similarity with pgvector
- **Query Translation**: English → Arabic for better recall
- **Bilingual Search**: Retrieves from both English and Arabic queries
- **Top-K**: Default 5 chunks (configurable)
- **Deduplication**: Removes duplicate chunks across queries

### Prompt Engineering

- **System Prompt**: Clear rules + output format
- **Few-Shot**: Implicit via structured examples in prompt
- **Output Schema**: JSON with answer + citations array
- **Temperature**: Low (0.1) for consistency

## 📊 Database Schema

```sql
-- Document chunks with embeddings
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    book_id VARCHAR,
    book_title VARCHAR,
    page_number INTEGER,
    arabic_text TEXT,
    english_translation TEXT,
    chunk_index INTEGER,
    image_path VARCHAR,
    embedding VECTOR(1536)  -- pgvector
);

-- Query audit log
CREATE TABLE query_logs (
    id SERIAL PRIMARY KEY,
    query TEXT,
    response TEXT,
    chunk_ids TEXT,  -- JSON array
    timestamp VARCHAR,
    was_refused INTEGER
);
```

## 🐛 Troubleshooting

### "No module named 'app'"
```bash
# Make sure you're in the backend directory
cd backend
python -m pytest tests/
```

### "Tesseract not found"
```bash
# Install Tesseract with Arabic support
brew install tesseract tesseract-lang  # macOS
```

### "pgvector extension not found"
```bash
# Connect to PostgreSQL and enable extension
psql $DATABASE_URL -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### "API returns 500 error"
- Check backend logs for errors
- Verify OPENAI_API_KEY is set
- Verify DATABASE_URL is correct
- Ensure database has data (run ingestion)

### "No results for Hajj questions"
- Check if ingestion completed successfully
- Verify chunks in database: `SELECT COUNT(*) FROM document_chunks;`
- Lower similarity threshold in .env
- Check if embeddings were generated

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Add tests for new features
4. Ensure all tests pass: `make test`
5. Submit pull request

## 📄 License

See [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- OCR: Tesseract
- Embeddings: OpenAI
- Vector DB: pgvector
- Frontend: Next.js
- Backend: FastAPI

---

## ⚡ Quick Reference

```bash
# Setup
make install && make setup-db

# Ingest data
make ingest

# Run
make run-backend  # Terminal 1
make run-frontend # Terminal 2

# Test
make test

# Deploy (see docs/DEPLOYMENT.md)
# 1. Deploy PostgreSQL
# 2. Deploy backend to Render/Fly.io
# 3. Deploy frontend to Vercel
# 4. Run ingestion pointing to production DB
```

**Questions?** Open an issue or see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for more details
