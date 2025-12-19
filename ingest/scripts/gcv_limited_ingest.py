"""Limited ingestion with Google Cloud Vision - 10 pages per book."""
import sys
from pathlib import Path
import os

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from ocr_pipeline import OCRPipeline
from app.database import SessionLocal, init_db
from sqlalchemy import text

# Set credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(
    Path(__file__).parent.parent.parent / 'huss-google-cloud-key.json'
)

class LimitedOCRPipeline(OCRPipeline):
    """OCR Pipeline with page limit."""

    def convert_pdf_to_images(self, pdf_path, output_dir, max_pages=10):
        """Convert only first N pages."""
        from pdf2image import convert_from_path

        print(f"Converting first {max_pages} pages of {pdf_path.name}...")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Explicitly pass poppler_path
        poppler_path = "/opt/homebrew/bin" if Path("/opt/homebrew/bin/pdfinfo").exists() else "/usr/local/bin"
        images = convert_from_path(str(pdf_path), dpi=300, first_page=1, last_page=max_pages, poppler_path=poppler_path)
        image_paths = []

        for i, image in enumerate(images):
            image_path = output_dir / f"page_{i+1:04d}.png"
            image.save(str(image_path), "PNG")
            image_paths.append(image_path)

        print(f"  Converted {len(images)} pages")
        return image_paths

def main():
    """Ingest 10 pages per book with Google Cloud Vision."""
    hajj_books_dir = Path(__file__).parent.parent.parent / "hajj-books"
    processed_data_dir = Path(__file__).parent.parent.parent / "data" / "processed_gcv"

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

    print("="*70)
    print("LIMITED INGESTION WITH GOOGLE CLOUD VISION API")
    print("Processing 10 pages per book to demonstrate improvement")
    print("="*70)
    print()

    pipeline = LimitedOCRPipeline(str(hajj_books_dir), str(processed_data_dir))

    print("Initializing database...")
    init_db()
    db = SessionLocal()

    try:
        for book in books:
            print(f"\n{'='*70}")
            print(f"Processing: {book['book_title']}")
            print(f"File: {book['pdf_path'].name}")
            print(f"{'='*70}\n")

            chunks = pipeline.process_book(
                book["pdf_path"],
                book["book_id"],
                book["book_title"]
            )

            if chunks:
                print(f"\nIndexing {len(chunks)} chunks...")
                pipeline.index_chunks(chunks, db)
                print(f"✓ Indexed {book['book_title']}")

        print(f"\n{'='*70}")
        print("INGESTION COMPLETE")
        print(f"{'='*70}\n")

        # Summary
        total_chunks = db.execute(text("SELECT COUNT(*) FROM document_chunks")).scalar()
        print(f"Total chunks: {total_chunks}")

        for book in books:
            count = db.execute(
                text("SELECT COUNT(*) FROM document_chunks WHERE book_id = :book_id"),
                {"book_id": book['book_id']}
            ).scalar()
            print(f"  {book['book_id']}: {count} chunks")

        # Show sample text quality
        print(f"\n{'='*70}")
        print("SAMPLE OCR OUTPUT (First chunk)")
        print(f"{'='*70}\n")

        sample = db.execute(
            text("SELECT arabic_text, book_title, page_number FROM document_chunks LIMIT 1")
        ).fetchone()

        if sample:
            print(f"Book: {sample[1]}")
            print(f"Page: {sample[2]}")
            print(f"Text preview (first 500 chars):")
            print(sample[0][:500])
            print("...")

    finally:
        db.close()

if __name__ == "__main__":
    main()
