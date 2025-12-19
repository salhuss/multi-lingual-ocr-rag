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
    similarity_threshold: float = None
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant document chunks using vector similarity.

    Args:
        query: The search query (can be English or Arabic)
        db: Database session
        top_k: Number of chunks to retrieve
        similarity_threshold: Minimum similarity score

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

    # Query for similar chunks using cosine similarity
    # Note: Use text() with direct substitution for the embedding string
    # since PostgreSQL parameter binding doesn't work with ::vector cast
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
