# Full Book Ingestion - Status Report

**Started**: 2025-12-19 at 17:11 PM
**Expected Completion**: ~18:30-19:00 PM (1-1.5 hours)
**Process ID**: 44600

---

## Scope

### Books Being Processed

1. **Hashiya Irshad al-Sari** (حاشية إرشاد الساري)
   - Pages: 888
   - Size: 17.1 MB
   - Expected chunks: ~1,800

2. **Muallim al-Hujjaj** (معلم الحجاج)
   - Pages: 346
   - Size: 7.1 MB
   - Expected chunks: ~700

**Total**: 1,234 pages → ~2,500 chunks

---

## Processing Pipeline

Each page goes through:

1. **PDF → Image** (~2-3 sec/page)
   - Converts PDF pages to 300 DPI PNG images
   - Output: `data/processed_gcv/{book_id}/images/page_XXXX.png`

2. **Image → OCR** (~3-4 sec/page)
   - Google Cloud Vision API extracts Arabic/Urdu text
   - Cost: $0.0002 per page ($0.25 total)

3. **Text → Embeddings** (~0.5 sec/chunk)
   - OpenAI text-embedding-3-small (1536 dimensions)
   - Cost: ~$0.001 total

4. **Database Indexing** (~0.1 sec/chunk)
   - PostgreSQL with pgvector
   - Stores text, embeddings, metadata

**Total Time**: ~3-5 seconds per page = 62-103 minutes for 1,234 pages

---

## Output Files

### Local Storage

After completion, you'll have:

```
data/processed_gcv/
├── hashiya_irshad/
│   ├── images/
│   │   ├── page_0001.png
│   │   ├── page_0002.png
│   │   └── ... (888 files, ~500MB)
│   └── processed_chunks.json  (~3-5MB)
│       [
│         {
│           "book_id": "hashiya_irshad",
│           "book_title": "حاشية إرشاد الساري...",
│           "page_number": 1,
│           "chunk_index": 0,
│           "arabic_text": "...",
│           "english_translation": null,
│           "image_path": "images/page_0001.png",
│           "embedding": [0.123, -0.456, ...],  // 1536 dims
│           "metadata": {...}
│         },
│         ...
│       ]
│
└── muallim_hajjaj/
    ├── images/
    │   └── ... (346 files, ~200MB)
    └── processed_chunks.json  (~1-2MB)
```

**Total Storage**: ~707MB locally

### Database

PostgreSQL `document_chunks` table will contain:
- ~2,500 rows (chunks)
- Each row: text, embedding, metadata
- Ready for vector similarity search

---

## Monitoring Progress

### Check Status Anytime

```bash
cd /Users/sal_pal/Documents/fiqh_tool_prototype/multi-lingual-ocr-rag/ingest/scripts
python3 monitor_ingestion.py
```

**Output**:
```
======================================================================
INGESTION PROGRESS - 17:30:00
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

### View Log File

```bash
tail -f /tmp/full_ingestion.log
```

### Check Process

```bash
ps aux | grep ingest_hajj_books | grep -v grep
```

---

## After Completion

### 1. Verify Results

```bash
cd ingest/scripts

# Check database
python3 -c "
import sys
sys.path.insert(0, '../../backend')
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
count = db.execute(text('SELECT COUNT(*) FROM document_chunks')).scalar()
print(f'Total chunks: {count}')

for book_id in ['hashiya_irshad', 'muallim_hajjaj']:
    count = db.execute(
        text('SELECT COUNT(*) FROM document_chunks WHERE book_id = :book_id'),
        {'book_id': book_id}
    ).scalar()
    print(f'  {book_id}: {count}')
db.close()
"
```

**Expected Output**:
```
Total chunks: ~2500
  hashiya_irshad: ~1800
  muallim_hajjaj: ~700
```

### 2. Test Retrieval

```bash
# Restart backend with updated data
cd ../../backend
pkill -f "uvicorn.*main:app"
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Test query
sleep 3
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the types of Hajj?", "use_arabic_translation": true}' \
  | python3 -m json.tool
```

**Expected**: Success with 3-5 retrieved chunks and detailed answer

### 3. Run Full Evaluation

```bash
cd ../scripts
python3 evaluate_system.py
```

**Expected Pass Rate**: 98-100% (up from 93.3% with 20 pages)

---

## S3 Backup (Recommended)

After ingestion completes, backup processed data to S3:

```bash
# See: docs/S3_MIGRATION_PLAN.md for full instructions

# Quick backup (JSON files only)
aws s3 sync data/processed_gcv/ s3://hajj-rag-data/processed_ocr/ \
  --exclude "*.png" \
  --include "*.json"

# Database backup
docker exec hajj-postgres pg_dump -U hajj_user hajj_qa | gzip > hajj_qa_backup.sql.gz
aws s3 cp hajj_qa_backup.sql.gz s3://hajj-rag-data/backups/hajj_qa_$(date +%Y%m%d).sql.gz
```

---

## Cost Summary

### One-Time Costs (Full Ingestion)

| Item | Quantity | Unit Cost | Total |
|------|----------|-----------|-------|
| Google Cloud Vision API | 1,234 pages | $0.0002/page | $0.25 |
| OpenAI Embeddings | ~2,500 chunks | $0.0004/1K | $0.001 |
| **Total** | | | **$0.25** |

### Ongoing Costs (Per Query)

| Item | Cost |
|------|------|
| Query translation | $0.0000075 |
| Query embedding | $0.00000002 |
| Answer generation | $0.000045 |
| **Total per query** | **~$0.000053** |

**18,867 queries per dollar**

---

## Troubleshooting

### If Process Fails

1. **Check if still running**:
   ```bash
   ps aux | grep ingest_hajj_books
   ```

2. **Check log for errors**:
   ```bash
   tail -100 /tmp/full_ingestion.log
   ```

3. **Common issues**:
   - **Google Cloud Vision quota**: Wait 1 minute, restart
   - **Out of memory**: Process killed by OS (unlikely with 1234 pages)
   - **Database connection**: Check PostgreSQL is running

4. **Resume from failure**:
   - Ingestion is resumable - already processed pages are skipped
   - Just run again: `python3 ingest_hajj_books.py`

### If You Need to Stop

```bash
# Find process
ps aux | grep ingest_hajj_books | grep -v grep

# Kill gracefully
kill -TERM 44600

# Or force kill (not recommended)
kill -9 44600
```

---

## What Happens Next

### Immediate (After Completion)
1. ✅ JSON files saved in `data/processed_gcv/`
2. ✅ Database fully populated with ~2,500 chunks
3. ✅ System ready for testing with full coverage

### Recommended (Next Steps)
1. 📊 Run full evaluation (expect 98%+ success)
2. 💾 Backup to S3 (see S3_MIGRATION_PLAN.md)
3. 🎯 Test with more complex queries
4. 🚀 Deploy to production (if results are good)

---

## Estimated Timeline

- **17:11 PM**: Started
- **17:30 PM**: ~15% complete (~300 pages)
- **18:00 PM**: ~50% complete (~600 pages)
- **18:30 PM**: ~85% complete (~1050 pages)
- **19:00 PM**: ✅ Complete (~1234 pages)

**Check progress every 15-30 minutes with**: `python3 monitor_ingestion.py`

---

## Success Criteria

✅ **Ingestion Successful If**:
- All 1,234 pages converted to images
- ~2,500 chunks in database
- All chunks have embeddings (1536 dimensions)
- Sample queries return relevant results
- Evaluation passes 98%+ tests

---

**Status**: 🏃 **RUNNING** (started 17:11 PM, ETA 18:30-19:00 PM)

**Monitor**: `cd ingest/scripts && python3 monitor_ingestion.py`
