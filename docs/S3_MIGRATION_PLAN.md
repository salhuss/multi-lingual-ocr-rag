# S3 Storage Migration Plan

**Purpose**: Move OCR-processed data from local storage to AWS S3 for production deployment
**Status**: Planning Phase
**Target**: Production deployment readiness

---

## Current Architecture (Local)

### Files Stored Locally

```
data/processed_gcv/
├── hashiya_irshad/
│   ├── images/                    # 888 PNG files (~500MB)
│   │   ├── page_0001.png
│   │   ├── page_0002.png
│   │   └── ...
│   └── processed_chunks.json      # Full text + metadata (~2-5MB)
└── muallim_hajjaj/
    ├── images/                    # 346 PNG files (~200MB)
    │   ├── page_0001.png
    │   ├── page_0002.png
    │   └── ...
    └── processed_chunks.json      # Full text + metadata (~1-2MB)
```

**Total Local Storage**: ~700MB (images) + ~7MB (JSON) = ~707MB

### Current Data Flow

1. **Ingestion** (one-time):
   - PDF → Images (local)
   - Images → OCR via Google Cloud Vision
   - OCR → processed_chunks.json (local)
   - JSON → PostgreSQL with embeddings

2. **Runtime** (query time):
   - User query → FastAPI backend
   - Backend → PostgreSQL (vector search)
   - PostgreSQL → Return chunks with metadata
   - Backend → LLM for answer generation
   - LLM → User response

---

## Proposed Architecture (S3)

### S3 Bucket Structure

```
s3://hajj-rag-data/
├── processed_ocr/
│   ├── hashiya_irshad/
│   │   ├── images/                    # Optional: Keep for reference
│   │   │   └── *.png (compressed)
│   │   ├── processed_chunks.json      # Primary: Full OCR + metadata
│   │   └── embeddings.jsonl           # Optional: Pre-computed embeddings
│   └── muallim_hajjaj/
│       ├── images/
│       ├── processed_chunks.json
│       └── embeddings.jsonl
├── raw_pdfs/                          # Optional: Original PDFs for reprocessing
│   ├── Hashiya-Irshad-al-Sari-ila-Manasik-al-Mulla-Ali-al-Qari.pdf
│   └── Muallim-Ul-Hajjaj.pdf
└── backups/                           # Database dumps
    └── postgres_dump_YYYYMMDD.sql
```

---

## Migration Strategy

### Phase 1: Upload Processed Data (IMMEDIATE)

**Goal**: Backup and share processed OCR results

**Steps**:
1. Compress and upload processed JSON files
2. Upload sample images (optional)
3. Upload database dump

**Commands**:
```bash
# Setup AWS CLI
pip install awscli
aws configure

# Create S3 bucket
aws s3 mb s3://hajj-rag-data --region us-east-1

# Upload processed data
cd /Users/sal_pal/Documents/fiqh_tool_prototype/multi-lingual-ocr-rag/data
aws s3 sync processed_gcv/ s3://hajj-rag-data/processed_ocr/ \
  --exclude "*.png"  # Exclude large images for now

# Upload database backup
pg_dump -U hajj_user -h localhost hajj_qa | gzip > hajj_qa_backup.sql.gz
aws s3 cp hajj_qa_backup.sql.gz s3://hajj-rag-data/backups/hajj_qa_$(date +%Y%m%d).sql.gz
```

**Benefits**:
- ✅ Backup of processed data
- ✅ Shareable across team/machines
- ✅ Disaster recovery
- ✅ Can rebuild database from S3

**Cost**: ~$0.02/month for 10MB JSON files

---

### Phase 2: Production Backend Integration (WHEN DEPLOYING)

**Goal**: Backend retrieves data from S3 when needed

**When to Implement**: Before production deployment to AWS/Cloud

**Architecture Changes**:

```python
# New file: backend/app/storage.py
import boto3
import json
from functools import lru_cache

class S3DataStore:
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.bucket = 'hajj-rag-data'

    @lru_cache(maxsize=10)
    def get_processed_chunks(self, book_id: str) -> dict:
        """Load processed chunks from S3 (cached)."""
        key = f"processed_ocr/{book_id}/processed_chunks.json"
        obj = self.s3.get_object(Bucket=self.bucket, Key=key)
        return json.loads(obj['Body'].read())

    def get_page_image(self, book_id: str, page_number: int) -> bytes:
        """Get image from S3 (if needed for display)."""
        key = f"processed_ocr/{book_id}/images/page_{page_number:04d}.png"
        obj = self.s3.get_object(Bucket=self.bucket, Key=key)
        return obj['Body'].read()
```

**Use Cases**:
1. **Initial Database Seeding** (deployment time):
   ```python
   # Load from S3 on first deploy
   store = S3DataStore()
   for book_id in ['hashiya_irshad', 'muallim_hajjaj']:
       chunks = store.get_processed_chunks(book_id)
       # Insert into PostgreSQL
   ```

2. **Serving Images** (optional feature):
   ```python
   @app.get("/image/{book_id}/{page_number}")
   def get_page_image(book_id: str, page_number: int):
       store = S3DataStore()
       image_bytes = store.get_page_image(book_id, page_number)
       return Response(content=image_bytes, media_type="image/png")
   ```

**Cost**:
- Storage: $0.023/GB/month (~$0.02/month for 1GB)
- Requests: $0.0004 per 1000 GET requests (negligible)

---

### Phase 3: Complete Cloud Migration (FUTURE)

**Goal**: Fully serverless/cloud-native architecture

**Components**:
- **Database**: Amazon RDS PostgreSQL with pgvector
- **Backend**: AWS Lambda or ECS (containerized FastAPI)
- **Storage**: S3 for all processed data
- **Frontend**: S3 + CloudFront (static site)

**Benefits**:
- ✅ Fully scalable
- ✅ No server maintenance
- ✅ Global CDN delivery
- ✅ Automatic backups

**Estimated Monthly Cost** (low traffic):
- RDS PostgreSQL (t3.micro): $15-20
- Lambda/ECS: $5-10
- S3: $0.02
- CloudFront: $1-5
- **Total: ~$20-35/month**

---

## Detailed Migration Steps

### Step 1: Prepare Local Data

```bash
# Navigate to project
cd /Users/sal_pal/Documents/fiqh_tool_prototype/multi-lingual-ocr-rag

# Verify processed data exists
ls -lh data/processed_gcv/*/processed_chunks.json

# Create metadata file
cat > data/processed_gcv/metadata.json <<EOF
{
  "generated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "ocr_provider": "Google Cloud Vision API",
  "embedding_model": "text-embedding-3-small",
  "similarity_threshold": 0.35,
  "books": [
    {
      "book_id": "hashiya_irshad",
      "title": "حاشية إرشاد الساري إلى مناسك الملا علي القاري",
      "pages": 888,
      "chunks": $(cat data/processed_gcv/hashiya_irshad/processed_chunks.json | python3 -c "import json,sys; print(len(json.load(sys.stdin)))")
    },
    {
      "book_id": "muallim_hajjaj",
      "title": "معلم الحجاج",
      "pages": 346,
      "chunks": $(cat data/processed_gcv/muallim_hajjaj/processed_chunks.json | python3 -c "import json,sys; print(len(json.load(sys.stdin)))")
    }
  ]
}
EOF
```

### Step 2: Setup AWS S3

```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure
# Enter:
#   AWS Access Key ID: [your_key]
#   AWS Secret Access Key: [your_secret]
#   Default region: us-east-1
#   Default output format: json

# Create S3 bucket
aws s3 mb s3://hajj-rag-data --region us-east-1

# Enable versioning (recommended)
aws s3api put-bucket-versioning \
  --bucket hajj-rag-data \
  --versioning-configuration Status=Enabled

# Set lifecycle policy (optional - archive old versions)
aws s3api put-bucket-lifecycle-configuration \
  --bucket hajj-rag-data \
  --lifecycle-configuration file://s3_lifecycle.json
```

### Step 3: Upload to S3

```bash
# Upload processed JSON files (primary data)
aws s3 sync data/processed_gcv/ s3://hajj-rag-data/processed_ocr/ \
  --exclude "*.png" \
  --exclude "*.jpg" \
  --include "*.json"

# Verify upload
aws s3 ls s3://hajj-rag-data/processed_ocr/ --recursive --human-readable

# Create database backup
docker exec hajj-postgres pg_dump -U hajj_user hajj_qa | gzip > hajj_qa_backup.sql.gz

# Upload database backup
aws s3 cp hajj_qa_backup.sql.gz \
  s3://hajj-rag-data/backups/hajj_qa_$(date +%Y%m%d).sql.gz
```

### Step 4: Verify and Test

```bash
# Download from S3 to verify
aws s3 cp s3://hajj-rag-data/processed_ocr/hashiya_irshad/processed_chunks.json /tmp/test_download.json

# Verify file integrity
python3 -c "import json; data=json.load(open('/tmp/test_download.json')); print(f'Chunks: {len(data)}'); print(f'First chunk keys: {data[0].keys()}')"

# Test restore from backup
aws s3 cp s3://hajj-rag-data/backups/hajj_qa_$(date +%Y%m%d).sql.gz /tmp/
gunzip /tmp/hajj_qa_*.sql.gz
# psql -U hajj_user -h localhost hajj_qa < /tmp/hajj_qa_*.sql
```

---

## Python Script: Upload to S3

```python
# scripts/upload_to_s3.py
"""Upload processed OCR data to S3."""
import boto3
import json
from pathlib import Path
from datetime import datetime
import sys

def upload_processed_data():
    """Upload all processed data to S3."""
    s3 = boto3.client('s3')
    bucket = 'hajj-rag-data'

    # Base directory
    base_dir = Path(__file__).parent.parent / 'data' / 'processed_gcv'

    print(f"Uploading processed data from {base_dir}")
    print("="*70)

    # Upload each book's data
    for book_dir in base_dir.iterdir():
        if not book_dir.is_dir():
            continue

        book_id = book_dir.name
        print(f"\nProcessing {book_id}...")

        # Upload processed_chunks.json
        chunks_file = book_dir / 'processed_chunks.json'
        if chunks_file.exists():
            s3_key = f'processed_ocr/{book_id}/processed_chunks.json'
            print(f"  Uploading {chunks_file.name}...")

            s3.upload_file(
                str(chunks_file),
                bucket,
                s3_key,
                ExtraArgs={
                    'ContentType': 'application/json',
                    'Metadata': {
                        'uploaded_at': datetime.utcnow().isoformat(),
                        'book_id': book_id
                    }
                }
            )
            print(f"  ✓ Uploaded to s3://{bucket}/{s3_key}")

            # Verify
            obj = s3.head_object(Bucket=bucket, Key=s3_key)
            size_mb = obj['ContentLength'] / (1024*1024)
            print(f"    Size: {size_mb:.2f} MB")

    print("\n" + "="*70)
    print("✓ Upload complete!")
    print(f"\nView files: aws s3 ls s3://{bucket}/processed_ocr/ --recursive")

if __name__ == "__main__":
    try:
        upload_processed_data()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
```

---

## Restore from S3

### Restore Database from Backup

```bash
# Download latest backup
aws s3 cp s3://hajj-rag-data/backups/$(aws s3 ls s3://hajj-rag-data/backups/ | tail -1 | awk '{print $4}') /tmp/backup.sql.gz

# Restore to PostgreSQL
gunzip /tmp/backup.sql.gz
docker exec -i hajj-postgres psql -U hajj_user hajj_qa < /tmp/backup.sql

# Verify
psql -U hajj_user -h localhost hajj_qa -c "SELECT COUNT(*) FROM document_chunks;"
```

### Rebuild Database from S3 JSON

```python
# scripts/restore_from_s3.py
"""Rebuild database from S3 processed chunks."""
import boto3
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from app.database import SessionLocal, init_db
from ingest.scripts.ocr_pipeline import OCRPipeline

def restore_from_s3():
    """Download S3 data and rebuild database."""
    s3 = boto3.client('s3')
    bucket = 'hajj-rag-data'

    print("Restoring database from S3...")
    print("="*70)

    init_db()
    db = SessionLocal()
    pipeline = OCRPipeline("", "")

    try:
        for book_id in ['hashiya_irshad', 'muallim_hajjaj']:
            print(f"\nRestoring {book_id}...")

            # Download processed_chunks.json from S3
            key = f'processed_ocr/{book_id}/processed_chunks.json'
            obj = s3.get_object(Bucket=bucket, Key=key)
            chunks = json.loads(obj['Body'].read())

            print(f"  Downloaded {len(chunks)} chunks")

            # Index in database
            pipeline.index_chunks(chunks, db)
            print(f"  ✓ Indexed {book_id}")

        print("\n" + "="*70)
        print("✓ Database restored successfully!")

    finally:
        db.close()

if __name__ == "__main__":
    restore_from_s3()
```

---

## Security Best Practices

### S3 Bucket Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowBackendRead",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT_ID:role/HajjRAGBackendRole"
      },
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::hajj-rag-data/*",
        "arn:aws:s3:::hajj-rag-data"
      ]
    }
  ]
}
```

### IAM Policy for Backend

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::hajj-rag-data/*",
        "arn:aws:s3:::hajj-rag-data"
      ]
    }
  ]
}
```

### Environment Variables

```bash
# .env (DO NOT COMMIT)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=hajj-rag-data
S3_OCR_PREFIX=processed_ocr/
```

---

## Cost Optimization

### Storage Classes

| Data Type | Storage Class | Cost | Use Case |
|-----------|--------------|------|----------|
| Processed JSON | S3 Standard | $0.023/GB | Frequent access |
| Images | S3 Standard-IA | $0.0125/GB | Rare access |
| Old backups | S3 Glacier | $0.004/GB | Archive only |

### Lifecycle Policy

```json
{
  "Rules": [
    {
      "Id": "ArchiveOldBackups",
      "Status": "Enabled",
      "Prefix": "backups/",
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "GLACIER"
        }
      ]
    },
    {
      "Id": "DeleteOldVersions",
      "Status": "Enabled",
      "NoncurrentVersionExpiration": {
        "NoncurrentDays": 90
      }
    }
  ]
}
```

---

## Monitoring

### S3 Metrics to Track

```bash
# Check bucket size
aws s3 ls s3://hajj-rag-data --recursive --human-readable --summarize

# Monitor costs
aws ce get-cost-and-usage \
  --time-period Start=2025-12-01,End=2025-12-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --filter file://s3_cost_filter.json
```

### Alerts

```bash
# CloudWatch alarm for high S3 costs
aws cloudwatch put-metric-alarm \
  --alarm-name HighS3Costs \
  --alarm-description "Alert if S3 costs exceed $5/month" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 86400 \
  --evaluation-periods 1 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold
```

---

## Timeline

| Phase | Task | Duration | When |
|-------|------|----------|------|
| **Phase 1** | Upload JSON to S3 | 1 hour | **NOW** (after full ingestion) |
| **Phase 1** | Create backup scripts | 2 hours | **NOW** |
| **Phase 2** | Add S3 backend integration | 1 day | Before production deploy |
| **Phase 2** | Test restore procedures | 2 hours | Before production deploy |
| **Phase 3** | Full cloud migration | 1 week | Future (3-6 months) |

---

## Next Steps (After Full Ingestion Completes)

1. ✅ **Immediate** - Upload processed_chunks.json files to S3
2. ✅ **Immediate** - Create database backup and upload to S3
3. ⏰ **Before Production** - Add S3 backend integration
4. ⏰ **Before Production** - Test full restore procedure
5. 🔮 **Future** - Complete cloud migration (RDS + Lambda/ECS)

---

## Conclusion

**Current State**: All data stored locally (~707MB)

**After Phase 1** (Immediate):
- ✅ JSON files backed up to S3 (~7MB)
- ✅ Database backups automated
- ✅ Disaster recovery ready
- 💰 Cost: ~$0.02/month

**After Phase 2** (Production):
- ✅ Backend can restore from S3
- ✅ Multi-environment support (dev/staging/prod)
- ✅ Team collaboration enabled
- 💰 Cost: Same (~$0.02/month)

**After Phase 3** (Future):
- ✅ Fully cloud-native
- ✅ Globally scalable
- ✅ Minimal ops overhead
- 💰 Cost: ~$20-35/month (full cloud stack)

**Recommendation**: Implement Phase 1 immediately after full ingestion completes.
