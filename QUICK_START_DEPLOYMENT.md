# Quick Start: Deploy to Production (Free)

**Total time:** ~30-45 minutes
**Total cost:** $0/month

## Prerequisites

- [ ] GitHub account
- [ ] OpenAI API key
- [ ] All code committed to GitHub repo

## 3-Step Deployment

### Step 1: Database (Supabase) - 10 min

```bash
# 1. Create account at https://supabase.com
# 2. New Project → Name: hajj-rag → Save password
# 3. SQL Editor → Run:

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    book_id VARCHAR(100),
    book_title TEXT,
    page_number INTEGER,
    arabic_text TEXT,
    english_translation TEXT,
    chunk_index INTEGER,
    image_path TEXT,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_embedding ON document_chunks
USING ivfflat (embedding vector_cosine_ops);

CREATE TABLE query_logs (
    id SERIAL PRIMARY KEY,
    query TEXT,
    response TEXT,
    chunk_ids TEXT,
    timestamp TEXT,
    was_refused INTEGER DEFAULT 0
);

# 4. Export local data
cd backend
python3 export_to_supabase.py

# 5. Load data (use JSON for easier import)
# Copy contents of supabase_data.json
# Use Supabase dashboard to bulk insert via API/CLI

# 6. Copy connection string
# Settings > Database > Connection String (URI)
# postgresql://postgres:[PASSWORD]@[PROJECT].supabase.co:5432/postgres
```

### Step 2: Backend (Render) - 15 min

```bash
# 1. Go to https://render.com
# 2. Sign up with GitHub
# 3. New+ > Web Service
# 4. Select repo: multi-lingual-ocr-rag
# 5. Settings:
#    - Name: hajj-rag-backend
#    - Root: backend
#    - Build: pip install -r requirements.txt
#    - Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT
#    - Plan: Free
# 6. Environment Variables:
DATABASE_URL=postgresql://postgres:[PASSWORD]@[PROJECT].supabase.co:5432/postgres
OPENAI_API_KEY=sk-...
SIMILARITY_THRESHOLD=0.35
RETRIEVAL_TOP_K=5

# 7. Deploy
# 8. Copy URL: https://hajj-rag-backend.onrender.com
```

### Step 3: Frontend (Vercel) - 10 min

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd /path/to/multi-lingual-ocr-rag
vercel

# Follow prompts:
# - Project name: hajj-rag
# - Root: ./
# - Settings: Default (auto-detected)

# Set environment variable
# Dashboard > Project > Settings > Environment Variables
NEXT_PUBLIC_API_URL=https://hajj-rag-backend.onrender.com

# Deploy to production
vercel --prod
```

## Done! 🎉

Your app is live at: `https://your-app.vercel.app`

**Test it:**
1. Open the URL
2. Ask: "What is Tawaf?"
3. Verify you get an answer with citations

## Common Issues

**Backend cold starts (30s delay):**
- Expected on Render free tier
- Add loading message in frontend
- Or use uptimerobot.com to ping every 14 min

**CORS errors:**
```python
# backend/app/main.py - Update allowed origins
allow_origins=["https://your-app.vercel.app", "http://localhost:3000"]
```

**Data not loading:**
```bash
# Verify Supabase has data
# SQL Editor:
SELECT COUNT(*) FROM document_chunks;
# Should return 5698
```

## Upgrade Later (If Needed)

If you outgrow free tier:
- **Render Starter**: $7/mo (no cold starts)
- **Supabase Pro**: $25/mo (8GB database)

## Support

See `DEPLOYMENT_CHECKLIST.md` for detailed step-by-step guide.
