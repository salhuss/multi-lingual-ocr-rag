# Free Hosting Deployment Plan

## Architecture Overview

**Stack (100% Free):**
- **Frontend:** Vercel (unlimited)
- **Backend:** Render (750 hrs/month)
- **Database:** Supabase (500MB, includes pgvector)
- **Storage:** Supabase Storage (1GB free) or Cloudflare R2 (10GB free)

## Data Requirements

**Current data size:**
- PNG images: ~700MB (NOT needed for production - intermediate files)
- JSON files with embeddings: ~6MB ✅
- PDF source files: ~25MB ✅
- **Total needed:** ~31MB

**What to upload:**
- `data/processed_gcv/hashiya_irshad/processed_chunks.json` (4.2 MB)
- `data/processed_gcv/muallim_hajjaj/processed_chunks.json` (1.5 MB)
- `hajj-books/*.pdf` (optional, for reference)

## Step 1: Database Setup (Supabase)

### 1.1 Create Supabase Project

```bash
# Go to https://supabase.com
# Click "New Project"
# Project name: hajj-rag
# Database password: [save this securely]
# Region: Choose closest to your users
```

### 1.2 Enable pgvector Extension

```sql
-- In Supabase SQL Editor
CREATE EXTENSION IF NOT EXISTS vector;
```

### 1.3 Create Tables

```sql
-- Run in Supabase SQL Editor
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    book_id VARCHAR(100) NOT NULL,
    book_title TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    arabic_text TEXT NOT NULL,
    english_translation TEXT,
    chunk_index INTEGER NOT NULL,
    image_path TEXT,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_book_id ON document_chunks(book_id);
CREATE INDEX idx_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops);

CREATE TABLE query_logs (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    response TEXT,
    chunk_ids TEXT,
    timestamp TEXT,
    was_refused INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 1.4 Load Data into Supabase

```bash
# Export local database to SQL
cd backend
python3 export_to_supabase.py
```

## Step 2: Storage Setup (Supabase Storage)

### 2.1 Create Storage Bucket

```bash
# In Supabase Dashboard > Storage
# Create bucket: "hajj-books"
# Make it public for read access
```

### 2.2 Upload Data Files

```bash
# Upload JSON files with embeddings
cd data/processed_gcv
# Upload via Supabase dashboard or CLI
```

## Step 3: Backend Deployment (Render)

### 3.1 Create render.yaml

```yaml
# Already created at backend/render.yaml
services:
  - type: web
    name: hajj-rag-backend
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: DATABASE_URL
        sync: false  # Set manually from Supabase
      - key: OPENAI_API_KEY
        sync: false  # Set manually
      - key: PYTHON_VERSION
        value: "3.11.0"
```

### 3.2 Deploy to Render

```bash
# 1. Push to GitHub (if not already)
git add .
git commit -m "Prepare for deployment"
git push

# 2. Go to https://render.com
# 3. Click "New +" > "Web Service"
# 4. Connect your GitHub repo
# 5. Select the backend directory
# 6. Render will auto-detect render.yaml
```

### 3.3 Set Environment Variables

```bash
# In Render Dashboard > Environment
DATABASE_URL=postgresql://postgres:[password]@[project].supabase.co:5432/postgres
OPENAI_API_KEY=sk-...
SIMILARITY_THRESHOLD=0.35
RETRIEVAL_TOP_K=5
```

**Important:** Free tier sleeps after 15 min inactivity. First request will take ~30s to wake up.

## Step 4: Frontend Deployment (Vercel)

### 4.1 Create vercel.json

```json
{
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/.next",
  "framework": "nextjs"
}
```

### 4.2 Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy from project root
cd /path/to/multi-lingual-ocr-rag
vercel

# Follow prompts:
# - Project name: hajj-rag-frontend
# - Framework: Next.js
# - Root directory: frontend/
```

### 4.3 Set Environment Variables

```bash
# In Vercel Dashboard > Settings > Environment Variables
NEXT_PUBLIC_API_URL=https://hajj-rag-backend.onrender.com
```

## Step 5: Post-Deployment Setup

### 5.1 Update CORS in Backend

```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-app.vercel.app",
        "http://localhost:3000"  # for local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5.2 Test the Deployment

```bash
# Test backend
curl https://hajj-rag-backend.onrender.com/health

# Test frontend
open https://your-app.vercel.app
```

## Cost Breakdown (Monthly)

- **Vercel:** $0 (unlimited)
- **Render:** $0 (750 hours free, backend only)
- **Supabase:** $0 (500MB database + 1GB storage)
- **Total:** $0/month ✅

## Limitations of Free Tier

1. **Render Backend:**
   - Sleeps after 15 min inactivity
   - First request takes ~30s to wake up
   - 750 hours/month limit (enough for ~25 active hours/day)

2. **Supabase:**
   - 500MB database limit (current: ~50MB used)
   - 1GB storage limit (current: ~6MB used)
   - 2GB bandwidth/month

3. **Solutions:**
   - Add loading indicator for cold starts
   - Consider upgrading to Render paid ($7/mo) if cold starts are problematic
   - Monitor Supabase usage

## Alternative Free Options

**If you need always-on backend:**
- **Railway:** $5 free credit/month (~100 hours of always-on)
- **Fly.io:** Free tier includes 3 small VMs

**If you need more storage:**
- **Cloudflare R2:** 10GB free storage
- **Backblaze B2:** 10GB free storage

## Next Steps

1. Create Supabase account and database
2. Export local data to Supabase
3. Deploy backend to Render
4. Deploy frontend to Vercel
5. Test end-to-end

**Estimated setup time:** 30-45 minutes
