# Run Full Ingestion (When You're Ready)

**Time Required**: 1-1.5 hours
**What It Does**: Processes all 1,234 pages from both Hajj books
**Cost**: $0.25 (Google Cloud Vision API)

---

## Quick Start

```bash
cd /Users/sal_pal/Documents/fiqh_tool_prototype/multi-lingual-ocr-rag/ingest/scripts

# Start the ingestion (runs in background)
nohup python3 ingest_hajj_books.py > /tmp/full_ingestion.log 2>&1 &

# Get the process ID
echo "Ingestion started. Check progress with: python3 monitor_ingestion.py"
```

That's it! The process will run in the background.

---

## Monitoring Progress

Check progress anytime:

```bash
cd /Users/sal_pal/Documents/fiqh_tool_prototype/multi-lingual-ocr-rag/ingest/scripts
python3 monitor_ingestion.py
```

**Example output:**
```
======================================================================
INGESTION PROGRESS - 18:30:00
======================================================================

Database Chunks:
  Hashiya Irshad:      450 chunks
  Muallim al-Hujjaj:   180 chunks
  Total:               630 chunks

Processed Images:
  Hashiya Irshad:      220 / 888 pages (24.8%)
  Muallim al-Hujjaj:    85 / 346 pages (24.6%)
  Total:               305 / 1234 pages (24.7%)

Estimated Time Remaining: 45 minutes
======================================================================
```

Run this every 15-30 minutes to check progress.

---

## What Happens

The script will:

1. **Convert PDFs to images** (~15-20 min)
   - Creates 1,234 PNG files in `data/processed_gcv/*/images/`

2. **Run OCR with Google Cloud Vision** (~40-60 min)
   - Extracts Arabic/Urdu text from each image
   - Costs $0.0002 per page ($0.25 total)

3. **Generate embeddings** (~5-10 min)
   - Creates vector embeddings for semantic search
   - Uses OpenAI text-embedding-3-small

4. **Index in database** (~5-10 min)
   - Stores ~2,500 chunks in PostgreSQL

**Total Time**: 1-1.5 hours

---

## When It's Done

You'll know it's complete when:

```bash
python3 monitor_ingestion.py
```

Shows **100% complete** (~1234/1234 pages, ~2500 chunks)

Then you can:
1. Test the improved system
2. Run evaluation (expect 98%+ pass rate)
3. Backup to S3 (optional)

---

## Output Files

After completion, you'll have:

```
data/processed_gcv/
├── hashiya_irshad/
│   ├── images/ (888 PNG files, ~500MB)
│   └── processed_chunks.json (~3-5MB)  ← Full OCR + embeddings
└── muallim_hajjaj/
    ├── images/ (346 PNG files, ~200MB)
    └── processed_chunks.json (~1-2MB)  ← Full OCR + embeddings
```

**Total**: ~707MB locally

These JSON files contain all the OCR text and embeddings ready for S3 backup.

---

## If You Need to Stop It

```bash
# Find the process
ps aux | grep ingest_hajj_books | grep -v grep

# Stop it (replace PID with actual number from above)
kill <PID>
```

The ingestion can be restarted - it will skip already-processed pages.

---

## Troubleshooting

**Process stopped unexpectedly?**
```bash
# Check if it's still running
ps aux | grep ingest_hajj_books

# Restart if needed
cd ingest/scripts
nohup python3 ingest_hajj_books.py > /tmp/full_ingestion.log 2>&1 &
```

**Want to check the log?**
```bash
tail -f /tmp/full_ingestion.log
```
(Press Ctrl+C to stop watching)

---

## After Completion

### 1. Test the System

```bash
cd ../../backend
pkill -f "uvicorn.*main:app"  # Restart backend with new data
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Test a query
sleep 3
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the types of Hajj?"}' | python3 -m json.tool
```

### 2. Run Full Evaluation

```bash
cd ../scripts
python3 evaluate_system.py
```

Expected: **98-100% pass rate** (vs current 93%)

### 3. Backup to S3 (Optional)

See: `docs/S3_MIGRATION_PLAN.md` for full instructions

Quick backup:
```bash
aws s3 sync data/processed_gcv/ s3://hajj-rag-data/processed_ocr/ \
  --exclude "*.png" \
  --include "*.json"
```

---

## Ready to Start?

When you're home and ready to run it:

```bash
cd /Users/sal_pal/Documents/fiqh_tool_prototype/multi-lingual-ocr-rag/ingest/scripts
nohup python3 ingest_hajj_books.py > /tmp/full_ingestion.log 2>&1 &
```

Then check progress periodically with:
```bash
python3 monitor_ingestion.py
```

**That's it!** Come back in ~1-1.5 hours and it'll be done.

---

**Current Status**: ⏸️ Paused (ready to run)
**Next Step**: Run the command above when you're ready
