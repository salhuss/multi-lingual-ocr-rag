"""Export local database to Supabase-compatible SQL dump."""
import sys
from pathlib import Path
from sqlalchemy import text
from app.database import SessionLocal
import json

def export_to_sql():
    """Export document_chunks to SQL INSERT statements."""
    db = SessionLocal()

    output_file = Path(__file__).parent / "supabase_data.sql"

    try:
        # Get all chunks
        result = db.execute(text("""
            SELECT
                book_id, book_title, page_number, arabic_text,
                english_translation, chunk_index, image_path, embedding
            FROM document_chunks
            ORDER BY id
        """))

        rows = result.fetchall()
        total = len(rows)

        print(f"Exporting {total} chunks to {output_file}...")

        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write("-- Supabase Data Import for Hajj RAG System\n")
            f.write(f"-- Total chunks: {total}\n")
            f.write("-- Generated from local database\n\n")

            # Write data in batches
            batch_size = 100
            for i in range(0, total, batch_size):
                batch = rows[i:i+batch_size]

                f.write(f"\n-- Batch {i//batch_size + 1} ({i+1}-{min(i+batch_size, total)})\n")
                f.write("INSERT INTO document_chunks ")
                f.write("(book_id, book_title, page_number, arabic_text, english_translation, chunk_index, image_path, embedding)\n")
                f.write("VALUES\n")

                values = []
                for row in batch:
                    # Escape single quotes in text
                    book_id = row[0].replace("'", "''")
                    book_title = row[1].replace("'", "''")
                    arabic_text = row[3].replace("'", "''") if row[3] else ''
                    english_translation = row[4].replace("'", "''") if row[4] else None
                    image_path = row[6].replace("'", "''") if row[6] else None

                    # Convert embedding list to pgvector format
                    embedding = row[7]
                    if embedding:
                        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
                    else:
                        embedding_str = "NULL"

                    # Build value tuple
                    value = f"('{book_id}', '{book_title}', {row[2]}, '{arabic_text}', "

                    if english_translation:
                        value += f"'{english_translation}', "
                    else:
                        value += "NULL, "

                    value += f"{row[5]}, "

                    if image_path:
                        value += f"'{image_path}', "
                    else:
                        value += "NULL, "

                    if embedding_str != "NULL":
                        value += f"'{embedding_str}'::vector)"
                    else:
                        value += "NULL)"

                    values.append(value)

                f.write(",\n".join(values))
                f.write(";\n")

                if (i + batch_size) % 500 == 0:
                    print(f"  Progress: {min(i+batch_size, total)}/{total} ({min(i+batch_size, total)/total*100:.1f}%)")

        print(f"\n✓ Export complete: {output_file}")
        print(f"\nTo import into Supabase:")
        print(f"1. Go to your Supabase project dashboard")
        print(f"2. Open SQL Editor")
        print(f"3. Copy and paste the contents of {output_file.name}")
        print(f"4. Execute the SQL")
        print(f"\nWarning: Large file! May need to split into smaller batches.")
        print(f"Current file will have ~{total} INSERT statements.")

        # Also export as JSON for backup
        json_file = Path(__file__).parent / "supabase_data.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            chunks_data = []
            for row in rows:
                chunks_data.append({
                    'book_id': row[0],
                    'book_title': row[1],
                    'page_number': row[2],
                    'arabic_text': row[3],
                    'english_translation': row[4],
                    'chunk_index': row[5],
                    'image_path': row[6],
                    'embedding': row[7]
                })
            json.dump(chunks_data, f, ensure_ascii=False, indent=2)

        print(f"\n✓ JSON backup created: {json_file}")

    except Exception as e:
        print(f"Error exporting data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    export_to_sql()
