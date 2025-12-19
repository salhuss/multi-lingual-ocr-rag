# Deployment Guide

This guide covers deploying the Hajj RAG application to production.

## Architecture Overview

- **Frontend**: Next.js app deployed to Vercel
- **Backend**: FastAPI app deployed to Render/Fly.io/Railway
- **Database**: PostgreSQL with pgvector (managed service)
- **Storage**: Document chunks and embeddings in PostgreSQL

## Prerequisites

1. OpenAI API key
2. PostgreSQL database with pgvector extension
3. Accounts on:
   - Vercel (frontend)
   - Render/Fly.io/Railway (backend)

## Database Setup

### Option 1: Render Managed PostgreSQL

1. Create a new PostgreSQL instance on Render:
   - Go to https://dashboard.render.com
   - Click "New" → "PostgreSQL"
   - Choose instance type (Starter or higher)
   - Note the connection string

2. Enable pgvector extension:
   ```bash
   # Connect to database
   psql <your_database_url>

   # Enable extension
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

### Option 2: Supabase (Free Tier Available)

1. Create project at https://supabase.com
2. Get connection string from Settings → Database
3. pgvector is pre-installed on Supabase

### Option 3: Railway PostgreSQL

1. Create new project at https://railway.app
2. Add PostgreSQL service
3. Get DATABASE_URL from Variables tab
4. Connect and enable pgvector

## Backend Deployment

### Option 1: Render

1. **Create Web Service**:
   - Go to https://dashboard.render.com
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Name**: hajj-rag-api
     - **Root Directory**: `backend`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

2. **Environment Variables**:
   ```
   OPENAI_API_KEY=your_key
   DATABASE_URL=your_postgres_url
   PYTHON_ENV=production
   ```

3. Deploy and note the service URL (e.g., `https://hajj-rag-api.onrender.com`)

### Option 2: Fly.io

1. **Install Fly CLI**:
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login and Launch**:
   ```bash
   cd backend
   fly auth login
   fly launch
   ```

3. **Set Secrets**:
   ```bash
   fly secrets set OPENAI_API_KEY=your_key
   fly secrets set DATABASE_URL=your_postgres_url
   ```

4. **Deploy**:
   ```bash
   fly deploy
   ```

### Option 3: Railway

1. **Create Project**:
   - Go to https://railway.app
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository

2. **Configure Service**:
   - Set root directory: `backend`
   - Add environment variables:
     ```
     OPENAI_API_KEY=your_key
     DATABASE_URL=your_postgres_url
     ```

3. Railway will auto-deploy on git push

## Frontend Deployment (Vercel)

1. **Connect Repository**:
   - Go to https://vercel.com
   - Click "New Project"
   - Import your GitHub repository

2. **Configure Project**:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (default)
   - **Output Directory**: `.next` (default)

3. **Environment Variables**:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-url.onrender.com
   ```

4. Deploy - Vercel will automatically deploy on git push

5. Get your frontend URL (e.g., `https://hajj-rag.vercel.app`)

## Data Ingestion (One-Time)

After deploying backend and database:

1. **Setup Local Environment**:
   ```bash
   cd ingest
   cp ../.env.example ../.env
   # Edit .env with production DATABASE_URL and OPENAI_API_KEY
   ```

2. **Place PDF Files**:
   ```bash
   # Copy your 3 Arabic Hajj books to data/raw/
   cp /path/to/books/*.pdf data/raw/
   ```

3. **Update Book Configuration**:
   Edit `ingest/scripts/ocr_pipeline.py` and update the books array with actual titles:
   ```python
   books = [
       {
           "pdf_path": raw_data_dir / "book1.pdf",
           "book_id": "fiqh_hajj_vol1",
           "book_title": "فقه الحج والعمرة - المجلد الأول"
       },
       # ... etc
   ]
   ```

4. **Run Ingestion**:
   ```bash
   # Install dependencies
   pip install -r ../backend/requirements.txt

   # Install Tesseract (if not installed)
   # macOS: brew install tesseract tesseract-lang
   # Linux: sudo apt-get install tesseract-ocr tesseract-ocr-ara

   # Install poppler
   # macOS: brew install poppler
   # Linux: sudo apt-get install poppler-utils

   # Run pipeline
   python scripts/ocr_pipeline.py
   ```

This will:
- Convert PDFs to images
- Extract Arabic text via OCR
- Chunk and embed text
- Index in PostgreSQL

**Note**: Ingestion can take 1-2 hours for 3 books depending on size.

## Verification

1. **Check Backend Health**:
   ```bash
   curl https://your-backend-url.onrender.com/health
   ```

2. **Test Chat Endpoint**:
   ```bash
   curl -X POST https://your-backend-url.onrender.com/chat \
     -H "Content-Type: application/json" \
     -d '{"query": "How do I perform tawaf?"}'
   ```

3. **Test Frontend**:
   - Visit your Vercel URL
   - Ask a Hajj question
   - Verify you get an answer with citations

## Monitoring

### Render
- View logs in Render dashboard
- Set up health check endpoint: `/health`

### Vercel
- View deployment logs and analytics in Vercel dashboard
- Monitor function errors

### Database
- Monitor connection count
- Check query performance
- Set up backups

## Cost Estimates (Monthly)

- **Render Web Service**: $7-25/month (Starter to Standard)
- **Render PostgreSQL**: $7-20/month (Starter)
- **Vercel**: Free tier (hobby projects)
- **OpenAI API**:
  - Embeddings: ~$0.02 per 1000 chunks (one-time)
  - LLM (gpt-4o-mini): ~$0.15 per 1000 requests

**Total**: ~$15-50/month depending on usage

## Scaling Considerations

1. **Database**:
   - Add read replicas for high traffic
   - Consider pgvector indexing optimizations

2. **Backend**:
   - Increase Render instance size
   - Add caching layer (Redis)

3. **Frontend**:
   - Vercel scales automatically
   - Add CDN for static assets

## Security

1. **API Keys**: Store in environment variables, never commit
2. **CORS**: Update backend CORS settings for production domains
3. **Rate Limiting**: Add rate limiting to backend endpoints
4. **Database**: Use SSL connections, restrict IP access

## Troubleshooting

### Backend won't start
- Check logs for missing environment variables
- Verify DATABASE_URL is correct
- Ensure pgvector extension is enabled

### Frontend can't connect to backend
- Verify NEXT_PUBLIC_API_URL is correct
- Check CORS settings in backend
- Verify backend is running and healthy

### No results returned
- Check if data ingestion completed successfully
- Verify embeddings are in database: `SELECT COUNT(*) FROM document_chunks;`
- Check similarity threshold in config

### OCR quality issues
- Increase PDF to image DPI (default: 300)
- Ensure Arabic language pack is installed
- Consider alternative OCR services (Google Cloud Vision, AWS Textract)
