"""Ingestion script for actual hajj-books PDFs."""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from ocr_pipeline import OCRPipeline
from app.database import SessionLocal, init_db

def main():
    """Ingest the two PDFs from hajj-books/ directory."""
    # Use hajj-books directory in repo root
    hajj_books_dir = Path(__file__).parent.parent.parent / "hajj-books"
    processed_data_dir = Path(__file__).parent.parent.parent / "data" / "processed"

    # Books configuration - using actual file names
    books = [
        {
            "pdf_path": hajj_books_dir / "Hashiya-Irshad-al-Sari-ila-Manasik-al-Mulla-Ali-al-Qari.pdf",
            "book_id": "hashiya_irshad",
            "book_title": "حاشية إرشاد الساري إلى مناسك الملا علي القاري"
        },
        {
            "pdf_path": hajj_books_dir / "Muallim Ul Hajjaj.pdf",
            "book_id": "muallim_hajjaj",
            "book_title": "معلم الحجاج"
        }
    ]

    # Verify PDFs exist
    for book in books:
        if not book["pdf_path"].exists():
            print(f"ERROR: {book['pdf_path']} not found!")
            return
        print(f"Found: {book['pdf_path'].name} ({book['pdf_path'].stat().st_size / 1024 / 1024:.1f} MB)")

    # Initialize pipeline
    pipeline = OCRPipeline(str(hajj_books_dir), str(processed_data_dir))

    # Initialize database
    print("\nInitializing database...")
    init_db()
    db = SessionLocal()

    try:
        # Process each book
        for book in books:
            print(f"\n{'='*70}")
            print(f"Processing: {book['book_title']}")
            print(f"File: {book['pdf_path'].name}")
            print(f"{'='*70}")

            # OCR and chunk
            chunks = pipeline.process_book(
                book["pdf_path"],
                book["book_id"],
                book["book_title"]
            )

            # Index in database
            if chunks:
                print(f"\nIndexing {len(chunks)} chunks into database...")
                pipeline.index_chunks(chunks, db)
                print(f"✓ Successfully indexed {book['book_title']}")
            else:
                print(f"✗ No chunks extracted from {book['book_title']}")

        # Summary
        print(f"\n{'='*70}")
        print("INGESTION COMPLETE")
        print(f"{'='*70}")

        # Count total chunks
        total_chunks = db.execute("SELECT COUNT(*) FROM document_chunks").scalar()
        print(f"Total chunks in database: {total_chunks}")

        # Chunks per book
        for book in books:
            count = db.execute(
                f"SELECT COUNT(*) FROM document_chunks WHERE book_id = '{book['book_id']}'"
            ).scalar()
            print(f"  {book['book_title']}: {count} chunks")

    except Exception as e:
        print(f"\nError during ingestion: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
