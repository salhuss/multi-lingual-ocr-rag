# Supabase Upload Guide

## Problem
The SQL export file is too large for Supabase's SQL Editor. We'll use the Supabase API instead.

## Solution: Python Script Upload

### Step 1: Get Supabase Credentials

1. Go to your Supabase project dashboard
2. Click **Settings** (gear icon) > **API**
3. Copy two values:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **service_role key** (NOT anon key - scroll down to find it)

⚠️ **Important:** Use the `service_role` key, not the `anon` key. The service role key bypasses Row Level Security and is needed for bulk inserts.

### Step 2: Install Dependencies

```bash
cd backend
pip install supabase tqdm
```

Or:

```bash
pip install -r upload_requirements.txt
```

### Step 3: Set Environment Variables

**Option A: Export in terminal (temporary)**
```bash
export SUPABASE_URL="https://xxxxx.supabase.co"
export SUPABASE_KEY="eyJhbGc..."
```

**Option B: Create .env file (recommended)**
```bash
# backend/.env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGc...
```

### Step 4: Create Tables in Supabase

Before uploading data, create the tables in Supabase SQL Editor:

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create document_chunks table
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

-- Create indexes
CREATE INDEX idx_book_id ON document_chunks(book_id);
CREATE INDEX idx_embedding ON document_chunks
USING ivfflat (embedding vector_cosine_ops);

-- Create query_logs table
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

### Step 5: Run Upload Script

```bash
cd backend
python3 upload_to_supabase.py
```

The script will:
1. Connect to your local database
2. Read all 5,698 chunks
3. Upload in batches of 100 to Supabase
4. Show progress bar
5. Verify count after upload
6. Retry failed chunks individually

**Expected time:** 5-10 minutes

### Step 6: Verify Upload

```sql
-- In Supabase SQL Editor
SELECT COUNT(*) FROM document_chunks;
-- Should return: 5698

-- Check by book
SELECT book_id, COUNT(*)
FROM document_chunks
GROUP BY book_id;

-- Verify embeddings
SELECT COUNT(*)
FROM document_chunks
WHERE embedding IS NOT NULL;
-- Should return: 5698
```

## Troubleshooting

### Error: "supabase module not found"
```bash
pip install supabase tqdm
```

### Error: "SUPABASE_URL not set"
```bash
export SUPABASE_URL="https://xxxxx.supabase.co"
export SUPABASE_KEY="eyJhbGc..."
```

### Error: "permission denied" or "row level security"
- Make sure you're using the **service_role key**, not the anon key
- The service_role key is longer and starts with `eyJhbGc...`

### Error: "relation 'document_chunks' does not exist"
- Create the tables first (Step 4)
- Run the SQL schema in Supabase SQL Editor

### Upload is slow
- Normal! Uploading 5,698 chunks takes 5-10 minutes
- The script includes 0.5s delay between batches to avoid rate limits

### Some chunks failed
- The script automatically retries failed chunks individually
- Check the error messages for specific issues
- Most common: network timeout (just rerun the script, it will skip existing chunks)

## Alternative: Use Supabase CLI

If the Python script has issues, you can use Supabase CLI:

```bash
# Install Supabase CLI
npm install -g supabase

# Login
supabase login

# Link to your project
supabase link --project-ref xxxxx

# Push local schema
supabase db push

# Or use db dump/restore
pg_dump $LOCAL_DATABASE_URL > dump.sql
psql $SUPABASE_DATABASE_URL < dump.sql
```

## After Upload

Update your backend environment variables in Render:

```bash
DATABASE_URL=postgresql://postgres:[PASSWORD]@[PROJECT].supabase.co:5432/postgres
```

Replace `[PASSWORD]` with your Supabase database password and `[PROJECT]` with your project reference.

## Security Note

⚠️ **Never commit your service_role key to git!**

The `.gitignore` already excludes `.env` files. Keep your keys secure.
