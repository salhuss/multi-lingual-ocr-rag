#!/bin/bash
# Run full ingestion with Google Cloud Vision API

export GOOGLE_APPLICATION_CREDENTIALS="/Users/sal_pal/Documents/fiqh_tool_prototype/multi-lingual-ocr-rag/huss-google-cloud-key.json"
export PATH="/opt/homebrew/bin:$PATH"

cd /Users/sal_pal/Documents/fiqh_tool_prototype/multi-lingual-ocr-rag/ingest/scripts

echo "==================================="
echo "Full Ingestion with Google Cloud Vision API"
echo "==================================="
echo "Starting at: $(date)"
echo ""

/opt/miniconda3/bin/python3 ingest_hajj_books.py

echo ""
echo "Completed at: $(date)"
