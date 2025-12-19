# How to Check Ingestion Progress

**Process started**: 5:19 PM (PID 48150)
**Expected completion**: ~6:30-7:00 PM

---

## **Option 1: Monitoring Script** (Easiest)

```bash
cd /Users/sal_pal/Documents/fiqh_tool_prototype/multi-lingual-ocr-rag/ingest/scripts
python3 monitor_ingestion.py
```

Shows:
- Chunks in database
- Pages processed
- Percentage complete

**Run this every 10-15 minutes** to track progress

---

## **Option 2: Check Process**

```bash
ps aux | grep 48150 | grep -v grep
```

If you see output → it's running ✅
If no output → it stopped ❌

---

## **Option 3: Check Image Files**

```bash
ls -1 /Users/sal_pal/Documents/fiqh_tool_prototype/multi-lingual-ocr-rag/data/processed_gcv/hashiya_irshad/images/*.png | wc -l
```

This shows how many PNG files have been created. Should increase over time.

---

## **Option 4: Check Database**

```bash
cd /Users/sal_pal/Documents/fiqh_tool_prototype/multi-lingual-ocr-rag/ingest/scripts

python3 -c "
import sys
sys.path.insert(0, '../../backend')
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
count = db.execute(text('SELECT COUNT(*) FROM document_chunks')).scalar()
print(f'Total chunks in database: {count}')
db.close()
"
```

---

## What You'll See Over Time

### ~5:20-5:30 PM (10 min): PDF → Images
- Image count growing: 20 → 100 → 200 ...
- Database chunks: Still 0

### ~5:30-6:30 PM (60 min): OCR Processing
- Image count: All 1,234 pages converted
- Database chunks growing: 0 → 500 → 1000 → 2500

### ~6:30-7:00 PM: Completion
- Images: 1,234 PNG files
- Database: ~2,500 chunks
- Process stops (PID 48150 disappears)

---

## Quick Check Commands

**Is it still running?**
```bash
ps aux | grep 48150 | grep -v grep && echo "✅ Running" || echo "❌ Stopped"
```

**How many images?**
```bash
find /Users/sal_pal/Documents/fiqh_tool_prototype/multi-lingual-ocr-rag/data/processed_gcv -name "*.png" | wc -l
```

**How many chunks?**
```bash
cd ingest/scripts
python3 -c "import sys; sys.path.insert(0, '../../backend'); from app.database import SessionLocal; from sqlalchemy import text; db = SessionLocal(); print(f'{db.execute(text(\"SELECT COUNT(*) FROM document_chunks\")).scalar()} chunks'); db.close()"
```

---

## If Something Seems Wrong

**Process stopped unexpectedly?**
```bash
# Check if it completed or failed
ps aux | grep ingest_hajj_books

# Look for error in recent system logs
dmesg | tail -50 | grep python
```

**Want to restart?**
```bash
# Kill current process
kill 48150

# Restart (will resume from where it left off)
cd /Users/sal_pal/Documents/fiqh_tool_prototype/multi-lingual-ocr-rag/ingest/scripts
nohup python3 ingest_hajj_books.py > /tmp/full_ingestion.log 2>&1 &
```

---

## When It's Done

You'll know it's complete when:
1. ✅ Process PID 48150 no longer exists
2. ✅ ~1,234 PNG files in data/processed_gcv/*/images/
3. ✅ ~2,500 chunks in database
4. ✅ JSON files created with full data

Then run:
```bash
python3 monitor_ingestion.py
```

Should show 100% complete!

---

**Current Status**: 🏃 Running (started 5:19 PM)
**Check again in**: 10-15 minutes
