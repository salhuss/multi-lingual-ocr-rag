"""Retrieval logic for document chunks."""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import DocumentChunk
from app.embeddings import get_embedding
from app.config import settings


def retrieve_relevant_chunks(
    query: str,
    db: Session,
    top_k: int = None,
    similarity_threshold: float = None,
    diversify_books: bool = True
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant document chunks using vector similarity.

    Args:
        query: The search query (can be English or Arabic)
        db: Database session
        top_k: Number of chunks to retrieve
        similarity_threshold: Minimum similarity score
        diversify_books: If True, ensure results include chunks from multiple books

    Returns:
        List of relevant chunks with metadata
    """
    if top_k is None:
        top_k = settings.retrieval_top_k
    if similarity_threshold is None:
        similarity_threshold = settings.similarity_threshold

    # Generate embedding for query
    query_embedding = get_embedding(query)

    # Convert embedding to pgvector format
    embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

    if diversify_books:
        # Retrieve top chunks from each book separately, then merge
        # Get list of unique books
        books_result = db.execute(text("SELECT DISTINCT book_id FROM document_chunks"))
        book_ids = [row[0] for row in books_result]

        all_chunks = []
        chunks_per_book = max(3, top_k // len(book_ids))  # At least 3 per book

        for book_id in book_ids:
            sql = text(f"""
                SELECT
                    id,
                    book_id,
                    book_title,
                    page_number,
                    arabic_text,
                    english_translation,
                    chunk_index,
                    image_path,
                    1 - (embedding <=> '{embedding_str}'::vector) as similarity
                FROM document_chunks
                WHERE book_id = :book_id
                    AND 1 - (embedding <=> '{embedding_str}'::vector) >= :threshold
                ORDER BY embedding <=> '{embedding_str}'::vector
                LIMIT :limit
            """)

            result = db.execute(sql, {
                "book_id": book_id,
                "threshold": similarity_threshold,
                "limit": chunks_per_book
            })

            for row in result:
                all_chunks.append({
                    "id": row[0],
                    "book_id": row[1],
                    "book_title": row[2],
                    "page_number": row[3],
                    "arabic_text": row[4],
                    "english_translation": row[5],
                    "chunk_index": row[6],
                    "image_path": row[7],
                    "similarity": float(row[8])
                })

        # Sort all chunks by similarity and take top_k
        all_chunks.sort(key=lambda x: x["similarity"], reverse=True)
        return all_chunks[:top_k]

    else:
        # Original behavior: retrieve globally by similarity
        sql = text(f"""
            SELECT
                id,
                book_id,
                book_title,
                page_number,
                arabic_text,
                english_translation,
                chunk_index,
                image_path,
                1 - (embedding <=> '{embedding_str}'::vector) as similarity
            FROM document_chunks
            WHERE 1 - (embedding <=> '{embedding_str}'::vector) >= :threshold
            ORDER BY embedding <=> '{embedding_str}'::vector
            LIMIT :limit
        """)

        result = db.execute(
            sql,
            {
                "threshold": similarity_threshold,
                "limit": top_k
            }
        )

        chunks = []
        for row in result:
            chunks.append({
                "id": row[0],
                "book_id": row[1],
                "book_title": row[2],
                "page_number": row[3],
                "arabic_text": row[4],
                "english_translation": row[5],
                "chunk_index": row[6],
                "image_path": row[7],
                "similarity": float(row[8])
            })

        return chunks
