"""Monitor ongoing ingestion progress."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from app.database import SessionLocal
from sqlalchemy import text
from datetime import datetime
import time

def monitor():
    """Show ingestion progress."""
    db = SessionLocal()

    try:
        # Get current chunk count
        count = db.execute(text("SELECT COUNT(*) FROM document_chunks")).scalar()

        # Get counts per book
        hashiya_count = db.execute(
            text("SELECT COUNT(*) FROM document_chunks WHERE book_id = 'hashiya_irshad'")
        ).scalar()

        muallim_count = db.execute(
            text("SELECT COUNT(*) FROM document_chunks WHERE book_id = 'muallim_hajjaj'")
        ).scalar()

        # Check for processed files
        data_dir = Path(__file__).parent.parent.parent / "data" / "processed_gcv"

        hashiya_images = len(list((data_dir / "hashiya_irshad" / "images").glob("*.png"))) if (data_dir / "hashiya_irshad" / "images").exists() else 0
        muallim_images = len(list((data_dir / "muallim_hajjaj" / "images").glob("*.png"))) if (data_dir / "muallim_hajjaj" / "images").exists() else 0

        print(f"\n{'='*70}")
        print(f"INGESTION PROGRESS - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*70}")
        print(f"\nDatabase Chunks:")
        print(f"  Hashiya Irshad:    {hashiya_count:5} chunks")
        print(f"  Muallim al-Hujjaj: {muallim_count:5} chunks")
        print(f"  Total:             {count:5} chunks")

        print(f"\nProcessed Images:")
        print(f"  Hashiya Irshad:    {hashiya_images:5} / 888 pages ({hashiya_images/888*100:.1f}%)")
        print(f"  Muallim al-Hujjaj: {muallim_images:5} / 346 pages ({muallim_images/346*100:.1f}%)")
        print(f"  Total:             {hashiya_images + muallim_images:5} / 1234 pages ({(hashiya_images + muallim_images)/1234*100:.1f}%)")

        if count > 0:
            total_pages = hashiya_images + muallim_images
            if total_pages > 20:  # More than the initial 20 pages
                pages_per_minute = total_pages / ((time.time() - start_time) / 60) if 'start_time' in globals() else 0
                if pages_per_minute > 0:
                    remaining_pages = 1234 - total_pages
                    eta_minutes = remaining_pages / pages_per_minute
                    print(f"\nEstimated Time Remaining: {eta_minutes:.0f} minutes")

        print(f"\n{'='*70}\n")

    finally:
        db.close()

if __name__ == "__main__":
    monitor()
