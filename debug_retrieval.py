"""Debug retrieval to find why no results are returned."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.database import SessionLocal
from sqlalchemy import text
import json
import openai
from dotenv import load_dotenv
import os

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_embedding(text: str):
    """Get embedding for text."""
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def main():
    db = SessionLocal()

    try:
        # 1. Check database state
        print("="*70)
        print("DATABASE STATE CHECK")
        print("="*70)

        total = db.execute(text("SELECT COUNT(*) FROM document_chunks")).scalar()
        print(f"\nTotal chunks: {total}")

        # Check if embeddings exist
        sample = db.execute(text("""
            SELECT
                book_id,
                page_number,
                LENGTH(arabic_text) as text_len,
                LENGTH(embedding::text) as emb_len,
                LEFT(arabic_text, 100) as preview
            FROM document_chunks
            LIMIT 3
        """)).fetchall()

        print(f"\nSample chunks:")
        for row in sample:
            print(f"  Book: {row[0]}, Page: {row[1]}, Text len: {row[2]}, Emb len: {row[3]}")
            print(f"  Preview: {row[4]}")
            print()

        # 2. Test similarity scores with actual query
        print("="*70)
        print("SIMILARITY SCORE TEST")
        print("="*70)

        test_queries = [
            "What are the types of Hajj?",
            "Hajj ihram",
            "حج"  # Arabic: Hajj
        ]

        for query in test_queries:
            print(f"\nQuery: '{query}'")
            print("-" * 50)

            # Get query embedding
            query_embedding = get_embedding(query)
            embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

            # Test with different thresholds
            for threshold in [0.5, 0.6, 0.7]:
                sql = text(f"""
                    SELECT
                        book_id,
                        page_number,
                        LEFT(arabic_text, 100) as preview,
                        1 - (embedding <=> '{embedding_str}'::vector) as similarity
                    FROM document_chunks
                    WHERE 1 - (embedding <=> '{embedding_str}'::vector) >= :threshold
                    ORDER BY embedding <=> '{embedding_str}'::vector
                    LIMIT 3
                """)

                results = db.execute(sql, {"threshold": threshold}).fetchall()
                print(f"  Threshold {threshold}: {len(results)} results")

                if results:
                    for row in results:
                        print(f"    - {row[0]} p{row[1]}: similarity={row[3]:.4f}")
                        print(f"      {row[2][:80]}...")

        # 3. Show top matches regardless of threshold
        print("\n" + "="*70)
        print("TOP 5 MATCHES (No threshold)")
        print("="*70)

        query = "What are the types of Hajj?"
        query_embedding = get_embedding(query)
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        sql = text(f"""
            SELECT
                book_id,
                page_number,
                LEFT(arabic_text, 150) as preview,
                1 - (embedding <=> '{embedding_str}'::vector) as similarity
            FROM document_chunks
            ORDER BY embedding <=> '{embedding_str}'::vector
            LIMIT 5
        """)

        results = db.execute(sql).fetchall()
        print(f"\nQuery: '{query}'")
        print(f"Top {len(results)} matches:\n")

        for i, row in enumerate(results, 1):
            print(f"{i}. {row[0]} page {row[1]} - Similarity: {row[3]:.4f}")
            print(f"   {row[2]}")
            print()

    finally:
        db.close()

if __name__ == "__main__":
    main()
