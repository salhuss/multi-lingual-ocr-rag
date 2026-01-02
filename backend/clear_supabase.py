"""Clear all data from Supabase document_chunks table."""
import os
import sys
from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Set SUPABASE_URL and SUPABASE_KEY environment variables")
    sys.exit(1)

def clear_database():
    """Delete all chunks from Supabase."""
    print("Connecting to Supabase...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    try:
        # Check current count
        response = supabase.table('document_chunks').select('id', count='exact').execute()
        current_count = response.count
        print(f"Current chunks in Supabase: {current_count}")

        if current_count == 0:
            print("Database is already empty!")
            return

        # Confirm deletion
        confirm = input(f"\nAre you sure you want to delete {current_count} chunks? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Cancelled.")
            return

        print("\nDeleting chunks in batches...")
        deleted_total = 0
        batch_size = 1000

        while True:
            # Get batch of IDs to delete
            response = supabase.table('document_chunks')\
                .select('id')\
                .limit(batch_size)\
                .execute()

            if not response.data:
                break

            ids_to_delete = [row['id'] for row in response.data]

            # Delete this batch
            supabase.table('document_chunks')\
                .delete()\
                .in_('id', ids_to_delete)\
                .execute()

            deleted_total += len(ids_to_delete)
            print(f"Deleted {deleted_total} chunks...", end='\r')

            if len(ids_to_delete) < batch_size:
                break

        # Verify deletion
        response = supabase.table('document_chunks').select('id', count='exact').execute()
        final_count = response.count

        print(f"\n{'='*60}")
        print(f"Database cleared!")
        print(f"{'='*60}")
        print(f"Total deleted: {deleted_total}")
        print(f"Remaining chunks: {final_count}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("="*60)
    print("CLEAR SUPABASE DATABASE")
    print("="*60)
    print(f"Supabase URL: {SUPABASE_URL}")
    print("="*60)

    clear_database()
