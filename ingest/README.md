# OCR and Ingestion Pipeline

This directory contains the OCR and document ingestion pipeline for processing Arabic PDF books.

## Prerequisites

1. Install Tesseract OCR with Arabic support:
   ```bash
   # macOS
   brew install tesseract tesseract-lang

   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr tesseract-ocr-ara

   # Verify installation
   tesseract --list-langs
   ```

2. Install poppler for PDF processing:
   ```bash
   # macOS
   brew install poppler

   # Ubuntu/Debian
   sudo apt-get install poppler-utils
   ```

## Usage

1. Place your PDF files in `data/raw/`:
   ```
   data/raw/
   ├── book1.pdf
   ├── book2.pdf
   └── book3.pdf
   ```

2. Update book configuration in `scripts/ocr_pipeline.py` with actual book titles.

3. Run the ingestion pipeline:
   ```bash
   cd ingest
   python scripts/ocr_pipeline.py
   ```

## What It Does

1. **PDF to Images**: Converts each PDF page to high-resolution PNG images
2. **OCR**: Extracts Arabic text from each page using Tesseract
3. **Chunking**: Splits text into overlapping chunks with page metadata
4. **Embedding**: Generates vector embeddings for each chunk
5. **Indexing**: Stores chunks and embeddings in PostgreSQL with pgvector

## Output

- `data/processed/{book_id}/images/`: Page images
- `data/processed/{book_id}/processed_chunks.json`: Extracted and chunked text
- Database: Chunks with embeddings indexed for retrieval
