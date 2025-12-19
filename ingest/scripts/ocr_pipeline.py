"""OCR pipeline for Arabic PDF processing."""
import os
import sys
from pathlib import Path

# CRITICAL: Add poppler to PATH before importing pdf2image
os.environ['PATH'] = '/opt/homebrew/bin:/usr/local/bin:' + os.environ.get('PATH', '')

from pdf2image import convert_from_path
from PIL import Image
import pytesseract
from typing import List, Dict, Any
import json

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from app.database import SessionLocal, init_db, DocumentChunk
from app.embeddings import get_embedding


class OCRPipeline:
    """Pipeline for OCR and document processing."""

    def __init__(self, raw_data_dir: str, processed_data_dir: str):
        """
        Initialize OCR pipeline.

        Args:
            raw_data_dir: Directory containing raw PDF files
            processed_data_dir: Directory to save processed data
        """
        self.raw_data_dir = Path(raw_data_dir)
        self.processed_data_dir = Path(processed_data_dir)
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)

    def convert_pdf_to_images(self, pdf_path: Path, output_dir: Path) -> List[Path]:
        """
        Convert PDF pages to images.

        Args:
            pdf_path: Path to PDF file
            output_dir: Directory to save images

        Returns:
            List of image paths
        """
        print(f"Converting {pdf_path.name} to images...")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Explicitly pass poppler_path for pdf2image
        poppler_path = "/opt/homebrew/bin" if Path("/opt/homebrew/bin/pdfinfo").exists() else "/usr/local/bin"
        images = convert_from_path(str(pdf_path), dpi=300, poppler_path=poppler_path)
        image_paths = []

        for i, image in enumerate(images):
            image_path = output_dir / f"page_{i+1:04d}.png"
            image.save(str(image_path), "PNG")
            image_paths.append(image_path)

        print(f"  Converted {len(images)} pages")
        return image_paths

    def ocr_image(self, image_path: Path) -> str:
        """
        Perform OCR on image to extract Arabic text using Google Cloud Vision API.

        Args:
            image_path: Path to image file

        Returns:
            Extracted text
        """
        from google.cloud import vision
        import os

        # Ensure credentials are set
        if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(
                Path(__file__).parent.parent.parent / 'huss-google-cloud-key.json'
            )

        client = vision.ImageAnnotatorClient()

        # Read image file
        with open(image_path, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)

        # Perform document text detection with Arabic language hint
        response = client.document_text_detection(
            image=image,
            image_context={"language_hints": ["ar"]}
        )

        if response.error.message:
            raise Exception(f'Google Cloud Vision API Error: {response.error.message}')

        # Extract full text
        text = response.full_text_annotation.text

        return text.strip() if text else ""

    def chunk_text(
        self,
        text: str,
        page_number: int,
        chunk_size: int = 500,
        overlap: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Chunk text with overlap while preserving page metadata.

        Args:
            text: Text to chunk
            page_number: Page number
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks

        Returns:
            List of chunks with metadata
        """
        if not text or len(text.strip()) == 0:
            return []

        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]

            if chunk_text.strip():
                chunks.append({
                    "text": chunk_text,
                    "page_number": page_number,
                    "chunk_index": chunk_index,
                    "start_pos": start,
                    "end_pos": end
                })
                chunk_index += 1

            start += (chunk_size - overlap)

        return chunks

    def process_book(
        self,
        pdf_path: Path,
        book_id: str,
        book_title: str
    ) -> List[Dict[str, Any]]:
        """
        Process a single book: PDF -> images -> OCR -> chunks.

        Args:
            pdf_path: Path to PDF file
            book_id: Unique book identifier
            book_title: Book title

        Returns:
            List of processed chunks with metadata
        """
        print(f"\n{'='*60}")
        print(f"Processing: {book_title}")
        print(f"{'='*60}")

        # Create output directory for this book
        book_dir = self.processed_data_dir / book_id
        images_dir = book_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        # Convert PDF to images
        image_paths = self.convert_pdf_to_images(pdf_path, images_dir)

        # OCR each page and create chunks
        all_chunks = []
        for page_num, image_path in enumerate(image_paths, start=1):
            print(f"  OCR page {page_num}/{len(image_paths)}...")

            # Extract text
            text = self.ocr_image(image_path)

            if not text:
                print(f"    Warning: No text extracted from page {page_num}")
                continue

            # Create chunks
            chunks = self.chunk_text(text, page_num)

            # Add metadata
            for chunk in chunks:
                chunk.update({
                    "book_id": book_id,
                    "book_title": book_title,
                    "image_path": str(image_path.relative_to(self.processed_data_dir))
                })
                all_chunks.append(chunk)

            print(f"    Extracted {len(chunks)} chunks")

        # Save processed data
        output_file = book_dir / "processed_chunks.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_chunks, f, ensure_ascii=False, indent=2)

        print(f"\nTotal chunks for {book_title}: {len(all_chunks)}")
        print(f"Saved to: {output_file}")

        return all_chunks

    def index_chunks(self, chunks: List[Dict[str, Any]], db_session):
        """
        Generate embeddings and index chunks in database.

        Args:
            chunks: List of chunks to index
            db_session: Database session
        """
        print(f"\nIndexing {len(chunks)} chunks...")

        for i, chunk in enumerate(chunks):
            if i % 10 == 0:
                print(f"  Indexing chunk {i+1}/{len(chunks)}...")

            # Generate embedding
            embedding = get_embedding(chunk["text"])

            # Create database record
            db_chunk = DocumentChunk(
                book_id=chunk["book_id"],
                book_title=chunk["book_title"],
                page_number=chunk["page_number"],
                arabic_text=chunk["text"],
                chunk_index=chunk["chunk_index"],
                image_path=chunk.get("image_path"),
                embedding=embedding
            )

            db_session.add(db_chunk)

            # Commit in batches
            if (i + 1) % 50 == 0:
                db_session.commit()

        db_session.commit()
        print(f"Successfully indexed {len(chunks)} chunks")


def main():
    """Main ingestion pipeline."""
    # Configuration
    raw_data_dir = Path(__file__).parent.parent.parent / "data" / "raw"
    processed_data_dir = Path(__file__).parent.parent.parent / "data" / "processed"

    # Books configuration (update with actual book details)
    books = [
        {
            "pdf_path": raw_data_dir / "book1.pdf",
            "book_id": "book1",
            "book_title": "Hajj Book 1"
        },
        {
            "pdf_path": raw_data_dir / "book2.pdf",
            "book_id": "book2",
            "book_title": "Hajj Book 2"
        },
        {
            "pdf_path": raw_data_dir / "book3.pdf",
            "book_id": "book3",
            "book_title": "Hajj Book 3"
        }
    ]

    # Initialize pipeline
    pipeline = OCRPipeline(str(raw_data_dir), str(processed_data_dir))

    # Initialize database
    print("Initializing database...")
    init_db()
    db = SessionLocal()

    try:
        # Process each book
        for book in books:
            if not book["pdf_path"].exists():
                print(f"Warning: {book['pdf_path']} not found, skipping...")
                continue

            # OCR and chunk
            chunks = pipeline.process_book(
                book["pdf_path"],
                book["book_id"],
                book["book_title"]
            )

            # Index in database
            if chunks:
                pipeline.index_chunks(chunks, db)

        print("\n" + "="*60)
        print("Ingestion pipeline completed successfully!")
        print("="*60)

    except Exception as e:
        print(f"Error during ingestion: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
