"""Get page counts for PDFs."""
from pathlib import Path
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFInfoNotInstalledError
import os

# Ensure poppler is in PATH
os.environ['PATH'] = '/opt/homebrew/bin:' + os.environ.get('PATH', '')

hajj_books_dir = Path(__file__).parent / "hajj-books"

books = [
    hajj_books_dir / "Hashiya-Irshad-al-Sari-ila-Manasik-al-Mulla-Ali-al-Qari.pdf",
    hajj_books_dir / "Muallim Ul Hajjaj.pdf"
]

for book_path in books:
    try:
        # Use pdfinfo to get page count
        from pdf2image.pdf2image import pdfinfo_from_path
        info = pdfinfo_from_path(str(book_path))
        pages = info.get('Pages', 'unknown')
        size_mb = book_path.stat().st_size / (1024 * 1024)
        print(f"{book_path.name}")
        print(f"  Pages: {pages}")
        print(f"  Size: {size_mb:.1f} MB")
        print()
    except Exception as e:
        print(f"Error for {book_path.name}: {e}")
