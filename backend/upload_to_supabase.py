"""Upload local database to Supabase via API."""
import os
import sys
from pathlib import Path
from sqlalchemy import text
from app.database import SessionLocal
from supabase import create_client, Client
from tqdm import tqdm
import time

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # Use service role key for admin access

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Set SUPABASE_URL and SUPABASE_KEY environment variables")
    print("\nExample:")
    print('export SUPABASE_URL="https://your-project.supabase.co"')
    print('export SUPABASE_KEY="your-service-role-key"')
    print("\nGet your keys from: Supabase Dashboard > Project Settings > API")
    sys.exit(1)

def upload_chunks():
    """Upload document chunks to Supabase."""
    print("Connecting to local database...")
    local_db = SessionLocal()

    print("Connecting to Supabase...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    try:
        # Get all chunks from local database
        result = local_db.execute(text("""
            SELECT
                book_id, book_title, page_number, arabic_text,
                english_translation, chunk_index, image_path, embedding
            FROM document_chunks
            ORDER BY id
        """))

        rows = result.fetchall()
        total = len(rows)

        print(f"\nFound {total} chunks in local database")
        print("Starting upload to Supabase...")

        # Upload in batches
        batch_size = 100
        success_count = 0
        error_count = 0

        for i in tqdm(range(0, total, batch_size), desc="Uploading batches"):
            batch = rows[i:i+batch_size]

            # Prepare batch data
            batch_data = []
            for row in batch:
                chunk = {
                    'book_id': row[0],
                    'book_title': row[1],
                    'page_number': row[2],
                    'arabic_text': row[3],
                    'english_translation': row[4],
                    'chunk_index': row[5],
                    'image_path': row[6],
                    'embedding': row[7]  # List of floats
                }
                batch_data.append(chunk)

            try:
                # Insert batch
                response = supabase.table('document_chunks').insert(batch_data).execute()
                success_count += len(batch_data)

                # Rate limiting - avoid hitting API limits
                time.sleep(0.5)

            except Exception as e:
                print(f"\nError uploading batch {i//batch_size + 1}: {e}")
                error_count += len(batch_data)

                # Try individual inserts for failed batch
                print(f"Retrying batch individually...")
                for chunk in batch_data:
                    try:
                        supabase.table('document_chunks').insert(chunk).execute()
                        success_count += 1
                        error_count -= 1
                    except Exception as e2:
                        print(f"  Failed chunk (book={chunk['book_id']}, page={chunk['page_number']}): {e2}")
                        time.sleep(0.1)

        print(f"\n{'='*60}")
        print(f"Upload complete!")
        print(f"{'='*60}")
        print(f"Successfully uploaded: {success_count}/{total} chunks")
        if error_count > 0:
            print(f"Failed: {error_count} chunks")

        # Verify count in Supabase
        print("\nVerifying data in Supabase...")
        response = supabase.table('document_chunks').select('id', count='exact').execute()
        supabase_count = response.count
        print(f"Total chunks in Supabase: {supabase_count}")

        # Count by book
        for book_id in ['hashiya_irshad', 'muallim_hajjaj']:
            response = supabase.table('document_chunks')\
                .select('id', count='exact')\
                .eq('book_id', book_id)\
                .execute()
            print(f"  {book_id}: {response.count} chunks")

    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        local_db.close()

if __name__ == "__main__":
    print("="*60)
    print("SUPABASE DATA UPLOAD")
    print("="*60)
    print(f"Supabase URL: {SUPABASE_URL}")
    print(f"Service Key: {SUPABASE_KEY[:20]}..." if SUPABASE_KEY else "Not set")
    print("="*60)

    input("\nPress Enter to start upload (or Ctrl+C to cancel)...")

    upload_chunks()
