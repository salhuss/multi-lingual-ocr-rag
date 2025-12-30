"""Full ingestion with Google Cloud Vision - ALL pages."""
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

class FullOCRPipeline(OCRPipeline):
    """OCR Pipeline processing ALL pages with explicit poppler path."""

    def convert_pdf_to_images(self, pdf_path, output_dir):
        """Convert ALL pages in batches with explicit poppler_path."""
        from pdf2image import convert_from_path
        from pdf2image.pdf2image import pdfinfo_from_path

        print(f"Converting ALL pages of {pdf_path.name}...")
        output_dir.mkdir(parents=True, exist_ok=True)

        # CRITICAL: Explicitly pass poppler_path to avoid PATH issues
        poppler_path = "/opt/homebrew/bin"
        print(f"  Using poppler from: {poppler_path}")

        # Get total page count
        info = pdfinfo_from_path(str(pdf_path), poppler_path=poppler_path)
        total_pages = info['Pages']
        print(f"  Total pages: {total_pages}")

        # Convert in batches of 50 pages to avoid memory issues
        batch_size = 50
        image_paths = []

        for start_page in range(1, total_pages + 1, batch_size):
            end_page = min(start_page + batch_size - 1, total_pages)
            print(f"  Converting pages {start_page}-{end_page}/{total_pages}...")

            images = convert_from_path(
                str(pdf_path),
                dpi=300,
                first_page=start_page,
                last_page=end_page,
                poppler_path=poppler_path
            )

            for i, image in enumerate(images):
                page_num = start_page + i
                image_path = output_dir / f"page_{page_num:04d}.png"
                image.save(str(image_path), "PNG")
                image_paths.append(image_path)

            if end_page % 100 == 0 or end_page == total_pages:
                print(f"    Progress: {end_page}/{total_pages} pages ({end_page/total_pages*100:.1f}%)")

        print(f"  ✓ Converted {len(image_paths)} pages")
        return image_paths

def main():
    """Ingest ALL pages from both books with Google Cloud Vision."""
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
    print("FULL INGESTION WITH GOOGLE CLOUD VISION API")
    print("Processing ALL pages from both books")
    print("="*70)
    print()

    pipeline = FullOCRPipeline(str(hajj_books_dir), str(processed_data_dir))

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

    except Exception as e:
        print(f"\nError during ingestion: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
