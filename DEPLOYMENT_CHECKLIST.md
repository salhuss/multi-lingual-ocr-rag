# Deployment Checklist

## Pre-Deployment

- [ ] All tests passing locally
- [ ] Frontend works at http://localhost:3000
- [ ] Backend works at http://localhost:8000
- [ ] Database has all 5,698 chunks with embeddings
- [ ] .gitignore updated (no secrets or large files)
- [ ] Code committed to GitHub

## 1. Supabase Setup (10 min)

### Create Project
- [ ] Go to https://supabase.com/dashboard
- [ ] Click "New Project"
- [ ] Name: `hajj-rag`
- [ ] Database Password: **[SAVE THIS SECURELY]**
- [ ] Region: `US West` or closest to your users
- [ ] Wait for project to be provisioned (~2 min)

### Enable pgvector
- [ ] Go to SQL Editor
- [ ] Run: `CREATE EXTENSION IF NOT EXISTS vector;`
- [ ] Verify: Should see "Success"

### Create Tables
- [ ] Copy schema from `backend/app/database.py`
- [ ] Run in SQL Editor:
```sql
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

### Export and Load Data
- [ ] Run: `cd backend && python3 export_to_supabase.py`
- [ ] This creates `supabase_data.sql` (~50MB)
- [ ] Copy contents of `supabase_data.sql`
- [ ] Paste in Supabase SQL Editor (may need to split into batches)
- [ ] Execute
- [ ] Verify: `SELECT COUNT(*) FROM document_chunks;` should return 5698

**Alternative (if SQL file too large):**
- [ ] Use the JSON export: `supabase_data.json`
- [ ] Write a Python script to INSERT via Supabase API
- [ ] Or use Supabase CLI: `supabase db push`

### Get Connection String
- [ ] Go to Project Settings > Database
- [ ] Copy Connection String (URI format)
- [ ] Format: `postgresql://postgres:[YOUR-PASSWORD]@[PROJECT-REF].supabase.co:5432/postgres`
- [ ] **Save this for backend deployment**

## 2. Render Backend Deployment (15 min)

### Prepare Repository
- [ ] Ensure `backend/render.yaml` exists
- [ ] Ensure `backend/requirements.txt` is complete
- [ ] Commit and push to GitHub

### Create Render Account
- [ ] Go to https://render.com
- [ ] Sign up with GitHub
- [ ] Authorize Render to access your repos

### Deploy Web Service
- [ ] Click "New +" > "Web Service"
- [ ] Select your GitHub repo: `multi-lingual-ocr-rag`
- [ ] Name: `hajj-rag-backend`
- [ ] Root Directory: `backend`
- [ ] Environment: `Python 3`
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Plan: `Free`

### Set Environment Variables
Go to Environment tab and add:

- [ ] `DATABASE_URL` = `postgresql://postgres:[PASSWORD]@[PROJECT].supabase.co:5432/postgres`
- [ ] `OPENAI_API_KEY` = `sk-...` (your OpenAI key)
- [ ] `SIMILARITY_THRESHOLD` = `0.35`
- [ ] `RETRIEVAL_TOP_K` = `5`
- [ ] `LLM_MODEL` = `gpt-4o-mini`
- [ ] `EMBEDDING_MODEL` = `text-embedding-3-small`

### Deploy
- [ ] Click "Create Web Service"
- [ ] Wait for build (~5 min)
- [ ] Check logs for errors
- [ ] Test: `curl https://your-app.onrender.com/health`
- [ ] Should return: `{"status": "healthy"}`

### Save Backend URL
- [ ] Copy URL: `https://hajj-rag-backend.onrender.com`
- [ ] **Save this for frontend deployment**

## 3. Vercel Frontend Deployment (10 min)

### Prepare Frontend
- [ ] Ensure `frontend/.env.local` has correct API URL (for local dev)
- [ ] Do NOT commit `.env.local` to git
- [ ] Commit all frontend code

### Deploy with Vercel CLI
```bash
# Install Vercel CLI (if not installed)
npm install -g vercel

# Navigate to project root
cd /path/to/multi-lingual-ocr-rag

# Deploy
vercel

# Follow prompts:
# - Set up and deploy? Y
# - Which scope? Your account
# - Link to existing project? N
# - What's your project's name? hajj-rag
# - In which directory is your code located? ./
# - Override settings? N

# Deploy production
vercel --prod
```

### Or Deploy via Dashboard
- [ ] Go to https://vercel.com/dashboard
- [ ] Click "Add New" > "Project"
- [ ] Import your GitHub repo
- [ ] Framework Preset: `Next.js`
- [ ] Root Directory: `frontend`
- [ ] Build Command: (auto-detected)
- [ ] Output Directory: (auto-detected)

### Set Environment Variables
- [ ] Go to Project Settings > Environment Variables
- [ ] Add: `NEXT_PUBLIC_API_URL` = `https://hajj-rag-backend.onrender.com`
- [ ] Save
- [ ] Redeploy (if already deployed)

### Test Deployment
- [ ] Open Vercel URL: `https://your-app.vercel.app`
- [ ] Try asking a question
- [ ] Verify citations appear
- [ ] Check browser console for errors

## 4. Post-Deployment Configuration

### Update Backend CORS
- [ ] Edit `backend/app/main.py`
- [ ] Update `allow_origins` to include your Vercel URL:
```python
allow_origins=[
    "https://your-app.vercel.app",
    "http://localhost:3000"
]
```
- [ ] Commit and push (Render auto-deploys)

### Custom Domain (Optional)
Vercel:
- [ ] Go to Project Settings > Domains
- [ ] Add custom domain
- [ ] Follow DNS setup instructions

Render:
- [ ] Go to Settings > Custom Domain
- [ ] Add domain
- [ ] Update frontend env var with new backend URL

## 5. Testing & Verification

### Backend Tests
- [ ] Health check: `curl https://backend.onrender.com/health`
- [ ] Test query:
```bash
curl -X POST https://backend.onrender.com/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"What is Tawaf?"}'
```
- [ ] Verify response has citations

### Frontend Tests
- [ ] Open https://your-app.vercel.app
- [ ] Ask: "What is Tawaf?"
- [ ] Verify answer appears
- [ ] Verify citations show book names and pages
- [ ] Try multiple questions
- [ ] Check Arabic translation toggle works

### End-to-End Tests
- [ ] Ask 5 different Hajj questions
- [ ] Verify all get responses with citations
- [ ] Test non-Hajj question (should be refused)
- [ ] Check query logs in Supabase database

## 6. Monitoring & Maintenance

### Set Up Monitoring
- [ ] Render: Check "Alerts" for downtime notifications
- [ ] Vercel: Check "Analytics" for usage
- [ ] Supabase: Check "Database" > "Usage" for storage

### Usage Limits
Monitor these monthly:
- [ ] Render: 750 hours/month (free tier)
- [ ] Supabase: 500MB database, 1GB storage
- [ ] Vercel: Unlimited (but check fair use)

### Backup Strategy
- [ ] Export Supabase data monthly: `python3 export_to_supabase.py`
- [ ] Store JSON backups in version control (git)
- [ ] Or backup to Google Drive / Dropbox

## Troubleshooting

### Backend cold starts (Render free tier)
**Problem:** First request takes 30 seconds
**Solution:**
- Add loading message in frontend
- Or upgrade to Render Starter plan ($7/mo)
- Or use https://uptimerobot.com to ping every 14 min

### CORS errors
**Problem:** Frontend can't reach backend
**Solution:**
- Check `allow_origins` includes your Vercel URL
- Verify `NEXT_PUBLIC_API_URL` is correct
- Check browser console for exact error

### Database connection errors
**Problem:** Backend can't connect to Supabase
**Solution:**
- Verify `DATABASE_URL` env var is correct
- Check Supabase project is not paused
- Test connection: `psql $DATABASE_URL`

### No results / empty responses
**Problem:** Queries return no citations
**Solution:**
- Check data loaded: `SELECT COUNT(*) FROM document_chunks`
- Verify embeddings exist: `SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL`
- Lower `SIMILARITY_THRESHOLD` to 0.3

## Cost Summary

| Service | Free Tier | Current Usage | Cost |
|---------|-----------|---------------|------|
| Vercel | Unlimited | ~1GB | $0 |
| Render | 750 hrs/month | ~720 hrs | $0 |
| Supabase | 500MB DB + 1GB storage | ~50MB + 6MB | $0 |
| **Total** | | | **$0/month** |

## Upgrade Paths (If Needed)

If you outgrow free tier:

1. **Render Starter** ($7/mo)
   - No cold starts
   - Always on
   - Better performance

2. **Supabase Pro** ($25/mo)
   - 8GB database
   - 100GB storage
   - Daily backups

3. **Alternative: Railway** ($5/mo credit)
   - Includes PostgreSQL
   - No cold starts
   - ~100 hours always-on

## Done! 🎉

Your Hajj RAG system is now live:
- ✅ Frontend: https://your-app.vercel.app
- ✅ Backend: https://hajj-rag-backend.onrender.com
- ✅ Database: Supabase (5,698 chunks)
- ✅ Cost: $0/month

Share the Vercel URL with users!
