"""Show book information before full ingestion."""
from pdf2image.pdf2image import pdfinfo_from_path
from pathlib import Path

books = [
    ('Hashiya Irshad', Path('../../hajj-books/Hashiya-Irshad-al-Sari-ila-Manasik-al-Mulla-Ali-al-Qari.pdf')),
    ('Muallim al-Hujjaj', Path('../../hajj-books/Muallim Ul Hajjaj.pdf'))
]

print('Book Information:')
print('='*60)
total = 0
for name, path in books:
    info = pdfinfo_from_path(str(path))
    pages = info['Pages']
    total += pages
    size_mb = path.stat().st_size / (1024*1024)
    print(f'{name:25} {pages:4} pages  ({size_mb:.1f} MB)')

print('='*60)
print(f'Total:                    {total:4} pages')
print()
print(f'Estimated processing time: {total * 3 / 60:.0f}-{total * 5 / 60:.0f} minutes')
print(f'Estimated GCV API cost: ${total * 0.0002:.2f}')
print()
print('Current status: 20 pages processed (10 per book)')
print(f'Remaining: {total - 20} pages')
