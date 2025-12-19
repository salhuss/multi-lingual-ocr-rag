"""FastAPI application main entry point."""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from app.database import get_db, init_db, QueryLog
from app.config import settings
from app.guardrails import is_hajj_related, create_refusal_response, validate_citations
from app.retrieval import retrieve_relevant_chunks
from app.llm import generate_answer, translate_query_to_arabic

app = FastAPI(title="Hajj RAG API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """Chat request model."""
    query: str
    use_arabic_translation: bool = True


class Citation(BaseModel):
    """Citation model."""
    book: str
    page: int
    excerpt: str


class ChatResponse(BaseModel):
    """Chat response model."""
    answer: str
    citations: List[Dict[str, Any]]
    status: str
    retrieved_chunks: Optional[int] = None


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Hajj RAG API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/chat",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Main chat endpoint with strict grounding and guardrails.

    Flow:
    1. Topic gate (must be Hajj-related)
    2. Translate query to Arabic (optional)
    3. Retrieve relevant chunks
    4. Generate answer with citations
    5. Validate citations
    6. Log query and response
    """
    query = request.query.strip()

    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Step 1: Topic gate
    if not is_hajj_related(query):
        response = create_refusal_response("not_hajj")
        log_query(db, query, response, [], refused=True)
        return ChatResponse(**response, retrieved_chunks=0)

    # Step 2: Prepare search queries (English + Arabic translation)
    search_queries = [query]
    if request.use_arabic_translation:
        arabic_query = translate_query_to_arabic(query)
        if arabic_query and arabic_query != query:
            search_queries.append(arabic_query)

    # Step 3: Retrieve relevant chunks (try both queries)
    all_chunks = []
    seen_ids = set()

    for search_query in search_queries:
        chunks = retrieve_relevant_chunks(search_query, db)
        for chunk in chunks:
            if chunk["id"] not in seen_ids:
                all_chunks.append(chunk)
                seen_ids.add(chunk["id"])

    # Sort by similarity
    all_chunks.sort(key=lambda x: x["similarity"], reverse=True)

    # Take top K
    retrieved_chunks = all_chunks[:settings.retrieval_top_k]

    # Check if we have sufficient sources
    if not retrieved_chunks or retrieved_chunks[0]["similarity"] < settings.similarity_threshold:
        response = create_refusal_response("no_sources")
        log_query(db, query, response, [], refused=True)
        return ChatResponse(**response, retrieved_chunks=len(retrieved_chunks))

    # Step 4: Generate answer
    llm_response = generate_answer(query, retrieved_chunks)

    # Step 5: Validate citations
    if llm_response["status"] == "success":
        has_valid_citations = validate_citations(
            llm_response["answer"],
            retrieved_chunks
        )

        if not has_valid_citations:
            response = create_refusal_response("low_confidence")
            log_query(db, query, response, retrieved_chunks, refused=True)
            return ChatResponse(**response, retrieved_chunks=len(retrieved_chunks))

    # Step 6: Log query
    log_query(db, query, llm_response, retrieved_chunks, refused=False)

    return ChatResponse(
        **llm_response,
        retrieved_chunks=len(retrieved_chunks)
    )


def log_query(
    db: Session,
    query: str,
    response: Dict[str, Any],
    chunks: List[Dict[str, Any]],
    refused: bool
):
    """Log query and response to database."""
    chunk_ids = [chunk["id"] for chunk in chunks] if chunks else []

    log_entry = QueryLog(
        query=query,
        response=json.dumps(response),
        chunk_ids=json.dumps(chunk_ids),
        timestamp=datetime.utcnow().isoformat(),
        was_refused=1 if refused else 0
    )

    db.add(log_entry)
    db.commit()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True
    )
