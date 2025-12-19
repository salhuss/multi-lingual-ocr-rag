# Hajj RAG System - Production Runbook

**Last Updated**: 2025-12-19
**System Status**: ✅ Production Ready (MVP)
**Success Rate**: 93.3% on Hajj questions

---

## Quick Start (5 minutes)

### 1. Start the Backend

```bash
cd /Users/sal_pal/Documents/fiqh_tool_prototype/multi-lingual-ocr-rag/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Expected Output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 2. Verify Health

```bash
curl http://localhost:8000/health
```

**Expected**: `{"status":"healthy"}`

### 3. Test a Query

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I perform tawaf?", "use_arabic_translation": true}'
```

**Expected**: JSON response with answer and citations

---

## API Endpoints

### Health Check
```
GET /health
```

**Response**:
```json
{"status": "healthy"}
```

### Chat (Main Endpoint)
```
POST /chat
```

**Request Body**:
```json
{
  "query": "Your question about Hajj",
  "use_arabic_translation": true  // Optional, defaults to true
}
```

**Response**:
```json
{
  "answer": "Answer text with citations [Book, Page X]",
  "citations": [
    {
      "book": "معلم الحجاج",
      "page": 6,
      "excerpt": "Relevant text excerpt"
    }
  ],
  "status": "success",  // or "refused", "no_sources", "error"
  "retrieved_chunks": 1
}
```

**Status Values**:
- `success`: Answer generated with valid citations
- `refused`: Question refused (not Hajj-related, fatwa request, etc.)
- `no_sources`: No relevant sources found in books
- `error`: System error occurred

---

## Database Management

### Connect to Database

```bash
# Using Docker
docker exec -it hajj-postgres psql -U hajj_user -d hajj_qa

# Or directly
psql postgresql://hajj_user:hajj_pass@localhost:5432/hajj_qa
```

### Useful Queries

**Check chunk count**:
```sql
SELECT COUNT(*) FROM document_chunks;
```

**View sample chunks**:
```sql
SELECT book_id, page_number, LEFT(arabic_text, 100)
FROM document_chunks
LIMIT 5;
```

**Check query logs**:
```sql
SELECT query, was_refused, timestamp
FROM query_logs
ORDER BY timestamp DESC
LIMIT 10;
```

**Clear database** (⚠️ DESTRUCTIVE):
```sql
DELETE FROM document_chunks;
DELETE FROM query_logs;
```

---

## Ingestion

### Current Status
- **Chunks**: 53
- **Pages**: 20 (10 per book)
- **Books**: 2 (Hashiya Irshad, Muallim al-Hujjaj)

### Re-run Limited Ingestion (10 pages/book)

```bash
cd /Users/sal_pal/Documents/fiqh_tool_prototype/multi-lingual-ocr-rag/ingest/scripts

# Clear old data first
python3 -c "from app.database import SessionLocal; from sqlalchemy import text; db = SessionLocal(); db.execute(text('DELETE FROM document_chunks')); db.commit()"

# Run ingestion
python3 gcv_limited_ingest.py
```

**Expected Time**: ~2-3 minutes
**Expected Output**: 53 chunks

### Full Book Ingestion (RECOMMENDED)

⚠️ **Note**: Currently has poppler PATH issue with miniconda. Use system python:

```bash
cd /Users/sal_pal/Documents/fiqh_tool_prototype/multi-lingual-ocr-rag/ingest/scripts

# Clear old data
psql postgresql://hajj_user:hajj_pass@localhost:5432/hajj_qa -c "DELETE FROM document_chunks;"

# Run with system python (not miniconda)
export GOOGLE_APPLICATION_CREDENTIALS="/Users/sal_pal/Documents/fiqh_tool_prototype/multi-lingual-ocr-rag/huss-google-cloud-key.json"
export PATH="/opt/homebrew/bin:$PATH"

python3 ingest_hajj_books.py
```

**Expected Time**: ~10-15 minutes
**Expected Chunks**: ~200+

---

## Testing & Evaluation

### Run Full Test Suite

```bash
cd /Users/sal_pal/Documents/fiqh_tool_prototype/multi-lingual-ocr-rag/scripts
python3 evaluate_system.py
```

**Tests**:
- 15 Hajj questions
- 5 non-Hajj questions (should be refused)
- 5 edge cases

**Expected Pass Rate**: 96% (24/25)

### Manual Testing

**Good Query** (should answer):
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is ihram?"}'
```

**Off-topic Query** (should refuse):
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I pray Fajr?"}'
```

---

## Configuration

### Environment Variables (.env)

```bash
# API Keys
OPENAI_API_KEY=sk-proj-...

# Database
DATABASE_URL=postgresql://hajj_user:hajj_pass@localhost:5432/hajj_qa

# Server
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0

# Models
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.1
MAX_TOKENS=800

# Retrieval
RETRIEVAL_TOP_K=5
SIMILARITY_THRESHOLD=0.35  # ⚠️ DO NOT raise above 0.5 for cross-lingual retrieval
```

### Critical Settings

**SIMILARITY_THRESHOLD**: Currently **0.35**
- ⚠️ **DO NOT** increase above 0.5 without full evaluation
- Cross-lingual retrieval (English → Arabic/Urdu) produces scores 0.35-0.43
- Higher threshold = zero results

**RETRIEVAL_TOP_K**: Currently **5**
- Retrieve top 5 most similar chunks
- LLM synthesizes answer from these
- Can adjust 3-10 range

---

## Troubleshooting

### Issue: "No sources found" for all queries

**Symptoms**:
```json
{"status": "refused", "retrieved_chunks": 0}
```

**Causes & Solutions**:

1. **Database empty**
   ```bash
   psql postgresql://hajj_user:hajj_pass@localhost:5432/hajj_qa -c "SELECT COUNT(*) FROM document_chunks;"
   ```
   If 0, run ingestion: `python3 gcv_limited_ingest.py`

2. **Similarity threshold too high**
   ```bash
   # Check .env
   cat .env | grep SIMILARITY_THRESHOLD
   ```
   Should be `0.35`, not `0.7`

3. **Backend not restarted after .env change**
   ```bash
   pkill -f "uvicorn.*main:app"
   python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

### Issue: Backend won't start

**Error**: `pydantic_core.ValidationError: Extra inputs are not permitted`

**Solution**: Check `backend/app/config.py` line 31:
```python
class Config:
    env_file = ".env"
    extra = "ignore"  # Must be present
```

### Issue: OCR ingestion fails

**Error**: `PDFInfoNotInstalledError: Unable to get page count`

**Solution**: Install poppler:
```bash
brew install poppler
export PATH="/opt/homebrew/bin:$PATH"
```

### Issue: OpenAI API error "must contain word json"

**Error**: `'messages' must contain the word 'json' in some form`

**Solution**: Check `backend/app/llm.py` line 53 contains:
```python
Respond in JSON format with the following structure:
```

### Issue: Database connection refused

**Check PostgreSQL**:
```bash
docker ps | grep postgres
```

If not running:
```bash
docker start hajj-postgres
```

Or create new:
```bash
docker run --name hajj-postgres \
  -e POSTGRES_USER=hajj_user \
  -e POSTGRES_PASSWORD=hajj_pass \
  -e POSTGRES_DB=hajj_qa \
  -p 5432:5432 \
  -d ankane/pgvector
```

---

## Monitoring

### Key Metrics to Track

1. **Query Success Rate**
   ```sql
   SELECT
     COUNT(*) as total,
     SUM(CASE WHEN was_refused = 0 THEN 1 ELSE 0 END) as successful,
     ROUND(100.0 * SUM(CASE WHEN was_refused = 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
   FROM query_logs
   WHERE timestamp > NOW() - INTERVAL '24 hours';
   ```

2. **Response Times**
   - Check backend logs: `tail -f /tmp/backend.log`
   - Should be < 5s for most queries

3. **Top Queries**
   ```sql
   SELECT query, COUNT(*) as count
   FROM query_logs
   GROUP BY query
   ORDER BY count DESC
   LIMIT 10;
   ```

4. **Refused Queries** (may indicate missing coverage)
   ```sql
   SELECT query, timestamp
   FROM query_logs
   WHERE was_refused = 1
   ORDER BY timestamp DESC
   LIMIT 20;
   ```

---

## Backup & Restore

### Backup Database

```bash
docker exec hajj-postgres pg_dump -U hajj_user hajj_qa > backup_$(date +%Y%m%d).sql
```

### Restore Database

```bash
docker exec -i hajj-postgres psql -U hajj_user hajj_qa < backup_20251219.sql
```

### Backup Processed Data

```bash
cd /Users/sal_pal/Documents/fiqh_tool_prototype/multi-lingual-ocr-rag
tar -czf data_backup_$(date +%Y%m%d).tar.gz data/processed_gcv/
```

---

## Performance Optimization

### Current Performance
- **Average latency**: 1.52s
- **P95 latency**: ~4.5s
- **Bottleneck**: LLM answer generation

### Optimization Options

1. **Add embedding cache** (for common queries)
2. **Use faster LLM** (gpt-4o-mini already optimal for cost/speed)
3. **Reduce top_k** (5 → 3) if quality remains high
4. **Add response cache** (Redis) for exact query matches
5. **Async processing** (already using FastAPI async)

---

## Security Checklist

### Before Production Deployment

- [ ] Remove or rotate `OPENAI_API_KEY` in .env
- [ ] Change database password from default
- [ ] Add authentication to `/chat` endpoint
- [ ] Set up HTTPS/SSL certificates
- [ ] Add rate limiting (by IP address)
- [ ] Restrict CORS origins (currently allows `*`)
- [ ] Store credentials in environment variables (not .env file)
- [ ] Set up firewall rules (only open port 443)
- [ ] Enable database backups
- [ ] Set up monitoring/alerting

---

## Support & Documentation

### Key Files

- **Evaluation Summary**: `logs/EVALUATION_SUMMARY.md`
- **GCV Results**: `logs/gcv_evaluation_results.md`
- **OCR Comparison**: `logs/ocr_comparison.md`
- **This Runbook**: `RUNBOOK.md`

### Quick Commands

```bash
# Start backend
cd backend && python3 -m uvicorn app.main:app --port 8000

# Run tests
cd scripts && python3 evaluate_system.py

# Check database
psql postgresql://hajj_user:hajj_pass@localhost:5432/hajj_qa -c "SELECT COUNT(*) FROM document_chunks;"

# Re-ingest (limited)
cd ingest/scripts && python3 gcv_limited_ingest.py

# View logs
tail -f /tmp/backend.log
```

### Success Indicators

✅ Backend healthy: `curl localhost:8000/health`
✅ Database has 53+ chunks: `SELECT COUNT(*) FROM document_chunks`
✅ Test query works: Query "How do I perform tawaf?" returns success
✅ Guardrails work: Query "What is zakat?" returns refused
✅ Evaluation passes: 24/25 tests passing (96%)

---

## FAQ

**Q: Why is the threshold so low (0.35)?**
A: Cross-lingual retrieval (English → Arabic/Urdu) produces lower similarity scores. Empirical testing showed best matches at 0.35-0.43.

**Q: Can I add more books?**
A: Yes, add PDF to `hajj-books/` directory and update `ingest_hajj_books.py` books list.

**Q: Why use Google Cloud Vision instead of Tesseract?**
A: Tesseract had 35% accuracy on classical Arabic/Urdu. Google Cloud Vision achieves 85-90% accuracy, making the difference between 0% and 93% system success rate.

**Q: How much does it cost per query?**
A: ~$0.000053 per query (~18,867 queries per dollar).

**Q: Is the system production-ready?**
A: Yes for MVP (with 20 pages). Recommended to process full books (200+ pages) before public launch.

**Q: What if a query returns no sources?**
A: Either (1) the question isn't covered in the 20 pages ingested, or (2) similarity score too low. Process full books for better coverage.

---

**System Ready** ✅
**Last Verified**: 2025-12-19
**Contact**: See project documentation
