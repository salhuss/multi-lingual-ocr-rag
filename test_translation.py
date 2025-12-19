"""Test if Arabic query translation improves retrieval."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.database import SessionLocal
from sqlalchemy import text
from app.llm import translate_query_to_arabic
from app.embeddings import get_embedding

def test_query(query: str, db):
    """Test query with and without translation."""
    print(f"\n{'='*70}")
    print(f"Query: {query}")
    print('='*70)

    # Get Arabic translation
    arabic_query = translate_query_to_arabic(query)
    print(f"Arabic translation: {arabic_query}")

    # Test English query
    print(f"\n--- English Query Results ---")
    eng_embedding = get_embedding(query)
    eng_emb_str = "[" + ",".join(str(x) for x in eng_embedding) + "]"

    sql = text(f"""
        SELECT
            book_id,
            page_number,
            LEFT(arabic_text, 100) as preview,
            1 - (embedding <=> '{eng_emb_str}'::vector) as similarity
        FROM document_chunks
        ORDER BY embedding <=> '{eng_emb_str}'::vector
        LIMIT 3
    """)

    results = db.execute(sql).fetchall()
    for i, row in enumerate(results, 1):
        print(f"{i}. {row[0]} p{row[1]} - Similarity: {row[3]:.4f}")
        print(f"   {row[2][:80]}...")

    # Test Arabic query
    print(f"\n--- Arabic Query Results ---")
    ar_embedding = get_embedding(arabic_query)
    ar_emb_str = "[" + ",".join(str(x) for x in ar_embedding) + "]"

    sql = text(f"""
        SELECT
            book_id,
            page_number,
            LEFT(arabic_text, 100) as preview,
            1 - (embedding <=> '{ar_emb_str}'::vector) as similarity
        FROM document_chunks
        ORDER BY embedding <=> '{ar_emb_str}'::vector
        LIMIT 3
    """)

    results = db.execute(sql).fetchall()
    for i, row in enumerate(results, 1):
        print(f"{i}. {row[0]} p{row[1]} - Similarity: {row[3]:.4f}")
        print(f"   {row[2][:80]}...")

def main():
    db = SessionLocal()

    try:
        test_queries = [
            "What are the types of Hajj?",
            "When should I enter ihram?",
            "How do I perform tawaf?"
        ]

        for query in test_queries:
            test_query(query, db)

    finally:
        db.close()

if __name__ == "__main__":
    main()
