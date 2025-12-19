"""Quick test ingestion - process only first 3 pages of each book."""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from ocr_pipeline import OCRPipeline
from app.database import SessionLocal, init_db
import os

# Ensure PATH includes poppler
os.environ['PATH'] = '/opt/homebrew/bin:' + os.environ.get('PATH', '')

def main():
    """Quick test - 3 pages per book."""
    hajj_books_dir = Path(__file__).parent.parent.parent / "hajj-books"
    processed_data_dir = Path(__file__).parent.parent.parent / "data" / "processed"

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

    # Initialize pipeline with modified process_book
    class QuickOCRPipeline(OCRPipeline):
        def convert_pdf_to_images(self, pdf_path, output_dir, max_pages=3):
            """Convert only first few pages."""
            print(f"Converting first {max_pages} pages of {pdf_path.name}...")
            output_dir.mkdir(parents=True, exist_ok=True)

            from pdf2image import convert_from_path
            # Get only first few pages
            images = convert_from_path(str(pdf_path), dpi=300, first_page=1, last_page=max_pages)
            image_paths = []

            for i, image in enumerate(images):
                image_path = output_dir / f"page_{i+1:04d}.png"
                image.save(str(image_path), "PNG")
                image_paths.append(image_path)

            print(f"  Converted {len(images)} pages")
            return image_paths

    pipeline = QuickOCRPipeline(str(hajj_books_dir), str(processed_data_dir))

    print("Initializing database...")
    init_db()
    db = SessionLocal()

    try:
        for book in books:
            print(f"\n{'='*70}")
            print(f"Processing: {book['book_title']}")
            print(f"File: {book['pdf_path'].name}")
            print(f"{'='*70}")

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
        print("QUICK TEST INGESTION COMPLETE")
        print(f"{'='*70}")

        # Summary
        from sqlalchemy import text
        total_chunks = db.execute(text("SELECT COUNT(*) FROM document_chunks")).scalar()
        print(f"Total chunks: {total_chunks}")

        for book in books:
            count = db.execute(
                text(f"SELECT COUNT(*) FROM document_chunks WHERE book_id = :book_id"),
                {"book_id": book['book_id']}
            ).scalar()
            print(f"  {book['book_id']}: {count} chunks")

    finally:
        db.close()

if __name__ == "__main__":
    main()
