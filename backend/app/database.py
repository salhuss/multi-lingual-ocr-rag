"""Database setup with pgvector support."""
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/hajj_rag")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class DocumentChunk(Base):
    """Document chunk with embeddings."""
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(String, index=True)
    book_title = Column(String)
    page_number = Column(Integer)
    arabic_text = Column(Text)
    english_translation = Column(Text, nullable=True)
    chunk_index = Column(Integer)
    image_path = Column(String, nullable=True)
    embedding = Column(Vector(1536))  # OpenAI text-embedding-3-small dimension


class QueryLog(Base):
    """Audit log for queries and responses."""
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text)
    response = Column(Text)
    chunk_ids = Column(String)  # JSON string of chunk IDs used
    timestamp = Column(String)
    was_refused = Column(Integer)  # 1 if refused, 0 if answered


def init_db():
    """Initialize database and create tables."""
    # Enable pgvector extension
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
